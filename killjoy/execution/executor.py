"""Order execution — constructs and submits validated paper orders through Alpaca."""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderClass, OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest, OptionLegRequest

from killjoy.agent.models import OrderResult, TradeProposal

logger = logging.getLogger(__name__)


class ExecutionError(RuntimeError):
    """Raised when order execution fails."""


class Executor:
    """Constructs and submits validated options orders through Alpaca.

    This class only executes orders that have passed through the full pipeline:
    Market Analysis → Strategy → Kill Agent → Portfolio Check → Risk Engine.
    """

    def __init__(self, client: TradingClient) -> None:
        self._client = client

    def execute_proposal(self, proposal: TradeProposal) -> OrderResult:
        """Execute an approved trade proposal via Alpaca paper trading.

        Args:
            proposal: A fully validated TradeProposal that has passed all gates.

        Returns:
            OrderResult with order details.
        """
        if not proposal.legs:
            return OrderResult(error="No legs to execute")

        try:
            order_request = self._build_order(proposal)
            logger.info(
                "Submitting %s order: %s %s (%d legs)",
                proposal.strategy.value,
                proposal.underlying,
                "BUY" if proposal.legs[0].side == "buy" else "SELL",
                len(proposal.legs),
            )

            order = self._client.submit_order(order_request)

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

    def _build_order(self, proposal: TradeProposal):
        """Build an Alpaca order request from a validated proposal."""
        legs = []
        for leg in proposal.legs:
            side = OrderSide.BUY if leg.side == "buy" else OrderSide.SELL
            intent_map = {
                "buy": "buy_to_open" if "open" not in leg.side else "buy_to_open",
                "sell": "sell_to_open",
            }
            from alpaca.trading.enums import PositionIntent
            position_intent = PositionIntent.BUY_TO_OPEN if leg.side == "buy" else PositionIntent.SELL_TO_OPEN

            legs.append(OptionLegRequest(
                symbol=leg.contract_symbol,
                ratio_qty=float(leg.quantity),
                side=side,
                position_intent=position_intent,
            ))

        # Use market order for simplicity; limit orders require price estimation
        return MarketOrderRequest(
            qty=1,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.MLEG,
            legs=legs,
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
