"""Position monitoring — watches open positions and manages exits."""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import PositionSnapshot, TradeProposal

logger = logging.getLogger(__name__)


class PositionAction:
    HOLD = "hold"
    EXIT = "exit"


def evaluate_position(
    position: PositionSnapshot,
    proposal: TradeProposal | None = None,
    max_loss_pct: Decimal = Decimal("0.20"),
    max_days_held: int = 45,
    days_held: int = 0,
) -> str:
    """Evaluate whether to hold or exit a position.

    Returns PositionAction.HOLD or PositionAction.EXIT.
    """
    reasons = []

    # Check unrealized P&L percentage
    if position.avg_entry_price > 0 and position.unrealized_plpc != 0:
        loss_pct = abs(position.unrealized_plpc) if position.unrealized_pl < 0 else Decimal("0")
        if position.unrealized_pl < 0 and loss_pct > max_loss_pct:
            reasons.append(f"Loss exceeds {max_loss_pct:.0%}: {position.unrealized_plpc:.1%}")

    # Check time held
    if days_held > max_days_held:
        reasons.append(f"Position held {days_held} days (max {max_days_held})")

    if reasons:
        logger.info("EXIT signal for %s: %s", position.symbol, "; ".join(reasons))
        return PositionAction.EXIT

    return PositionAction.HOLD


def get_position_summary(positions: list[PositionSnapshot]) -> dict:
    """Get a summary of all open positions."""
    total_unrealized = sum(p.unrealized_pl for p in positions)
    return {
        "count": len(positions),
        "total_unrealized_pl": total_unrealized,
        "positions": [
            {
                "symbol": p.symbol,
                "qty": float(p.quantity),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
            }
            for p in positions
        ],
    }
