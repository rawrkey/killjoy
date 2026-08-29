"""Liquidity validation for risk engine."""

from __future__ import annotations

from decimal import Decimal


def check_liquidity(
    bid: Decimal,
    ask: Decimal,
    volume: int,
    max_spread_pct: Decimal = Decimal("0.10"),
    min_volume: int = 10,
) -> tuple[bool, str]:
    """Check if a position can be entered/exited with acceptable liquidity."""
    if volume < min_volume:
        return False, f"Volume {volume} < minimum {min_volume}"

    mid = (bid + ask) / 2 if bid > 0 and ask > 0 else Decimal("0")
    if mid > 0:
        spread_pct = (ask - bid) / mid
        if spread_pct > max_spread_pct:
            return False, f"Spread {spread_pct:.1%} > {max_spread_pct:.0%}"

    return True, "Liquidity OK"
