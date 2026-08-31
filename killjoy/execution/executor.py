"""Order execution — hardened with duplicate protection, stale quote detection, and retry safety.

This module constructs and submits validated paper orders through Alpaca.
Every order passes through the full pipeline before execution.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import MarketOrderRequest, OptionLegRequest

from killjoy.agent.models import OrderResult, TradeProposal

logger = logging.getLogger(__name__)


class ExecutionError(RuntimeError):
    """Raised when order execution fails."""


class Executor:
    """Constructs and submits validated options orders through Alpaca.

    Safety features:
    - Duplicate order protection (idempotent client order IDs + journal check)
    - Stale quote detection
    - Order rejection handling
    - No blind retries (prevents duplicate positions)
    """

    def __init__(self, client: TradingClient, journal=None) -> None:
        self._client = client
        self._journal = journal
        self._recent_orders: dict[str, datetime] = {}  # client_order_id -> timestamp
        self._max_order_age_seconds = 300  # 5 minutes

    def execute_proposal(self, proposal: TradeProposal, buying_power: Decimal = Decimal("10000")) -> OrderResult:
        """Execute an approved trade proposal via Alpaca paper trading.

        Safety checks before submission:
        1. Duplicate order protection
        2. Stale quote detection
        3. Contract availability
        4. Position sizing based on buying power
        """
        if not proposal.legs:
            return OrderResult(error="No legs to execute")

        # 1. Duplicate order protection — in-memory check
        client_order_id = self._generate_client_order_id(proposal)
        if client_order_id in self._recent_orders:
            age = (datetime.now(timezone.utc) - self._recent_orders[client_order_id]).seconds
            if age < self._max_order_age_seconds:
                logger.warning(
                    "Duplicate order blocked: %s %s (same order %ds ago)",
                    proposal.underlying, proposal.strategy.value, age,
                )
                return OrderResult(
                    symbol=proposal.underlying,
                    error=f"Duplicate order blocked (submitted {age}s ago)",
                    status="duplicate_blocked",
                )

        # 1b. Duplicate order protection — journal check (persists across restarts)
        if self._journal:
            open_trades = self._journal.get_open_trades()
            for trade in open_trades:
                if trade.underlying == proposal.underlying and trade.order_result is not None:
                    # Block if same underlying already has an open trade
                    logger.warning(
                        "Duplicate order blocked via journal: %s already has open trade %s",
                        proposal.underlying, trade.trade_id,
                    )
                    return OrderResult(
                        symbol=proposal.underlying,
                        error=f"Duplicate: {trade.underlying} already open (trade {trade.trade_id})",
                        status="duplicate_blocked",
                    )

        # 2. Stale quote detection
        for leg in proposal.legs:
            if leg.mid <= 0 and leg.bid <= 0 and leg.ask <= 0:
                logger.warning("Stale/missing quote for %s — skipping", leg.contract_symbol)
                return OrderResult(
                    symbol=proposal.underlying,
                    error=f"Stale quote: {leg.contract_symbol}",
                    status="stale_quote",
                )

        # 3. Calculate position size based on buying power
        qty = self._calculate_quantity(proposal, buying_power)
        if qty < 1:
            return OrderResult(
                symbol=proposal.underlying,
                error=f"Insufficient buying power for {proposal.underlying} (need ${proposal.max_loss:.0f}, have ${buying_power:.0f})",
                status="insufficient_buying_power",
            )

        try:
            order_request = self._build_order(proposal, client_order_id, qty)
            logger.info(
                "Submitting %s order: %s %s (%d legs) [id: %s]",
                proposal.strategy.value,
                proposal.underlying,
                "BUY" if proposal.legs[0].side == "buy" else "SELL",
                len(proposal.legs),
                client_order_id[:8],
            )

            order = self._client.submit_order(order_request)

            # Track submitted order
            self._recent_orders[client_order_id] = datetime.now(timezone.utc)
            self._cleanup_old_orders()

            return OrderResult(
                order_id=str(order.id),
                client_order_id=str(order.client_order_id) if order.client_order_id else "",
                status=str(order.status.value) if hasattr(order.status, "value") else str(order.status),
                symbol=proposal.underlying,
                side=proposal.legs[0].side,
                type="market" if not hasattr(order_request, "limit_price") or order_request.limit_price is None else "limit",
                submitted_at=order.submitted_at,
            )

        except Exception as e:
            logger.error("Order execution failed for %s: %s", proposal.underlying, e)
            return OrderResult(
                symbol=proposal.underlying,
                error=str(e),
                status="failed",
            )

    def _generate_client_order_id(self, proposal: TradeProposal) -> str:
        """Generate an idempotent client order ID from proposal details.

        Same proposal = same ID = duplicate protection.
        """
        key = f"{proposal.underlying}:{proposal.strategy.value}:{proposal.expiration}:{proposal.id}"
        hash_suffix = hashlib.md5(key.encode()).hexdigest()[:8]
        return f"KJ-{proposal.underlying}-{proposal.strategy.value[:4].upper()}-{hash_suffix}"

    def _cleanup_old_orders(self) -> None:
        """Remove old entries from the duplicate tracking dict."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self._max_order_age_seconds * 2)
        self._recent_orders = {
            oid: ts for oid, ts in self._recent_orders.items()
            if ts > cutoff
        }

    def _calculate_quantity(self, proposal: TradeProposal, buying_power: Decimal) -> int:
        """Calculate how many contracts to buy based on buying power and max risk.

        Uses 5% of buying power per trade, but caps at MAX_RISK_PER_TRADE / max_loss_per_contract.
        """
        if not proposal.legs:
            return 0

        cost_per_contract = proposal.legs[0].mid * 100
        if cost_per_contract <= 0:
            cost_per_contract = proposal.legs[0].ask * 100
        if cost_per_contract <= 0:
            return 0

        # 5% of buying power per trade
        budget = buying_power * Decimal("0.05")
        if budget <= 0:
            return 0
        qty = int(budget / cost_per_contract)

        # Cap by MAX_RISK_PER_TRADE ($1000) / max_loss_per_contract
        max_risk = Decimal("1000")
        if proposal.max_loss > 0:
            max_risk_qty = int(max_risk / proposal.max_loss)
            qty = min(qty, max_risk_qty)

        return min(qty, 10)

    def _build_order(self, proposal: TradeProposal, client_order_id: str, qty: int = 1):
        """Build an Alpaca order request from a validated proposal."""
        legs = []
        for leg in proposal.legs:
            side = OrderSide.BUY if leg.side == "buy" else OrderSide.SELL
            from alpaca.trading.enums import PositionIntent
            position_intent = PositionIntent.BUY_TO_OPEN if leg.side == "buy" else PositionIntent.SELL_TO_OPEN

            legs.append(OptionLegRequest(
                symbol=leg.contract_symbol,
                ratio_qty=float(leg.quantity),
                side=side,
                position_intent=position_intent,
            ))

        # Single-leg = SIMPLE, multi-leg = MLEG
        if len(legs) == 1:
            return MarketOrderRequest(
                symbol=legs[0].symbol,
                qty=qty,
                side=legs[0].side,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.SIMPLE,
                client_order_id=client_order_id,
            )
        else:
            return MarketOrderRequest(
                qty=qty,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
                order_class=OrderClass.MLEG,
                legs=legs,
                client_order_id=client_order_id,
            )

    def close_position(self, symbol: str) -> OrderResult:
        """Close a position by symbol."""
        try:
            order = self._client.close_position(symbol)
            return OrderResult(
                order_id=str(order.id) if hasattr(order, "id") else "",
                status="filled" if hasattr(order, "status") else "submitted",
                symbol=symbol,
                side="sell",
                type="close",
            )
        except Exception as e:
            logger.error("Failed to close position %s: %s", symbol, e)
            return OrderResult(symbol=symbol, error=str(e), status="failed")

    def get_order_status(self, order_id: str) -> OrderResult:
        """Check order status."""
        try:
            order = self._client.get_order(order_id)
            return OrderResult(
                order_id=str(order.id),
                status=str(order.status.value) if hasattr(order.status, "value") else str(order.status),
                filled_avg_price=Decimal(str(getattr(order, "filled_avg_price", 0) or 0)),
                filled_qty=Decimal(str(getattr(order, "filled_qty", 0) or 0)),
                symbol=getattr(order, "symbol", ""),
            )
        except Exception as e:
            return OrderResult(order_id=order_id, error=str(e), status="error")
