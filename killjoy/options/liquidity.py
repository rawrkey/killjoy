"""Liquidity checks for option contracts."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import OptionContract


# Configurable defaults — engineering assumptions, not trading advice
DEFAULT_MIN_VOLUME = 10
DEFAULT_MIN_OPEN_INTEREST = 50
DEFAULT_MAX_BID_ASK_SPREAD_PCT = Decimal("0.15")  # 15% of mid price


def check_liquidity(
    contract: OptionContract,
    min_volume: int = DEFAULT_MIN_VOLUME,
    min_open_interest: int = DEFAULT_MIN_OPEN_INTEREST,
    max_spread_pct: Decimal = DEFAULT_MAX_BID_ASK_SPREAD_PCT,
) -> tuple[bool, str]:
    """Check if a contract meets minimum liquidity requirements.

    Returns (is_liquid, reason).
    """
    if contract.volume < min_volume:
        return False, f"Volume {contract.volume} < minimum {min_volume}"

    if contract.open_interest < min_open_interest:
        return False, f"Open interest {contract.open_interest} < minimum {min_open_interest}"

    mid = contract.mid if contract.mid > 0 else (contract.bid + contract.ask) / 2
    if mid > 0:
        spread = contract.ask - contract.bid
        spread_pct = spread / mid
        if spread_pct > max_spread_pct:
            return False, f"Bid-ask spread {spread_pct:.1%} exceeds {max_spread_pct:.1%}"

    return True, "Liquidity OK"


def filter_liquid(
    contracts: list[OptionContract],
    min_volume: int = DEFAULT_MIN_VOLUME,
    min_open_interest: int = DEFAULT_MIN_OPEN_INTEREST,
    max_spread_pct: Decimal = DEFAULT_MAX_BID_ASK_SPREAD_PCT,
) -> list[OptionContract]:
    """Return only contracts that pass liquidity checks."""
    return [
        c
        for c in contracts
        if check_liquidity(c, min_volume, min_open_interest, max_spread_pct)[0]
    ]
