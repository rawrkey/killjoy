"""Options pricing helpers."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import OptionContract, OptionLeg


def compute_mid_price(contract: OptionContract) -> Decimal:
    """Compute mid price from bid/ask."""
    if contract.bid > 0 and contract.ask > 0:
        return (contract.bid + contract.ask) / 2
    if contract.last > 0:
        return contract.last
    return Decimal("0")


def compute_reward_risk(
    legs: list[OptionLeg],
    max_loss: Decimal,
    max_profit: Decimal,
) -> Decimal:
    """Compute reward/risk ratio."""
    if max_loss == 0:
        return Decimal("0")
    return max_profit / abs(max_loss)


def estimate_max_loss_spread(legs: list[OptionLeg]) -> Decimal:
    """Estimate max loss for a spread (width - net debit)."""
    if len(legs) < 2:
        return Decimal("0")
    # For a spread: max loss = net debit paid
    net_debit = Decimal("0")
    for leg in legs:
        price = leg.mid if leg.mid > 0 else leg.bid
        if leg.side == "buy":
            net_debit += price * leg.quantity * 100
        else:
            net_debit -= price * leg.quantity * 100
    return abs(net_debit)


def estimate_max_profit_spread(
    legs: list[OptionLeg],
    width: Decimal | None = None,
) -> Decimal:
    """Estimate max profit for a spread."""
    if len(legs) < 2:
        return Decimal("0")
    # For bull call spread: max profit = width - net debit
    # For simplicity, use width if provided
    net_debit = Decimal("0")
    for leg in legs:
        price = leg.mid if leg.mid > 0 else leg.bid
        if leg.side == "buy":
            net_debit += price * leg.quantity * 100
        else:
            net_debit -= price * leg.quantity * 100

    if width is not None:
        return (width * 100) - abs(net_debit) if net_debit > 0 else Decimal("0")
    # Fallback: assume 2x the debit for undefined
    return abs(net_debit)
