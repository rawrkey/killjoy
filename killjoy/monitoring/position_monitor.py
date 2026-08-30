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
    take_profit_pct: Decimal = Decimal("0.50"),
    trailing_stop_pct: Decimal = Decimal("0.10"),
    max_days_held: int = 45,
    days_held: int = 0,
    high_water_mark: Decimal | None = None,
) -> tuple[str, str]:
    """Evaluate whether to hold or exit a position.

    Returns (PositionAction, reason).
    """
    reasons = []

    # Take-profit: close if up >= take_profit_pct
    if position.unrealized_plpc > 0 and position.unrealized_plpc >= take_profit_pct:
        reasons.append(f"Take-profit hit: {position.unrealized_plpc:.1%} >= {take_profit_pct:.0%}")

    # Stop-loss: close if down >= max_loss_pct
    if position.unrealized_pl < 0 and position.unrealized_plpc != 0:
        loss_pct = abs(position.unrealized_plpc)
        if loss_pct >= max_loss_pct:
            reasons.append(f"Stop-loss hit: {loss_pct:.1%} >= {max_loss_pct:.0%}")

    # Trailing stop: if position was up more and now dropped from peak
    if high_water_mark is not None and high_water_mark > 0 and position.unrealized_plpc < high_water_mark:
        drop_from_peak = high_water_mark - position.unrealized_plpc
        if drop_from_peak >= trailing_stop_pct:
            reasons.append(f"Trailing stop: dropped {drop_from_peak:.1%} from peak {high_water_mark:.1%}")

    # Time held
    if days_held > max_days_held:
        reasons.append(f"Held {days_held} days (max {max_days_held})")

    if reasons:
        logger.info("EXIT signal for %s: %s", position.symbol, "; ".join(reasons))
        return PositionAction.EXIT, "; ".join(reasons)

    return PositionAction.HOLD, ""


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
