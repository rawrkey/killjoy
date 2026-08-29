"""Portfolio exposure calculations."""

from __future__ import annotations

from decimal import Decimal


def calculate_total_exposure(positions: list) -> Decimal:
    """Calculate total dollar exposure across all positions."""
    total = Decimal("0")
    for pos in positions:
        mv = getattr(pos, "market_value", None)
        if mv is None and isinstance(pos, dict):
            mv = pos.get("market_value", 0)
        total += Decimal(str(abs(float(mv or 0))))
    return total


def calculate_options_exposure(positions: list) -> Decimal:
    """Calculate exposure specifically for options positions."""
    total = Decimal("0")
    for pos in positions:
        sym = str(getattr(pos, "symbol", "") if hasattr(pos, "symbol") else pos.get("symbol", ""))
        # Options symbols are longer than stock symbols
        if sym and len(sym) > 4:
            mv = getattr(pos, "market_value", None)
            if mv is None and isinstance(pos, dict):
                mv = pos.get("market_value", 0)
            total += Decimal(str(abs(float(mv or 0))))
    return total


def calculate_underlying_exposure(positions: list, underlying: str) -> Decimal:
    """Calculate exposure to a specific underlying."""
    total = Decimal("0")
    for pos in positions:
        sym = str(getattr(pos, "symbol", "") if hasattr(pos, "symbol") else pos.get("symbol", ""))
        if underlying in sym:
            mv = getattr(pos, "market_value", None)
            if mv is None and isinstance(pos, dict):
                mv = pos.get("market_value", 0)
            total += Decimal(str(abs(float(mv or 0))))
    return total
