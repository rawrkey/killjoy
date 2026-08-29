"""Option contract parsing and selection utilities."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal

from killjoy.agent.models import OptionContract, OptionType

logger = logging.getLogger(__name__)


def parse_option_symbol(symbol: str) -> dict:
    """Parse an OCC option symbol like 'AAPL250117C00150000' into components.

    Format: ROOT + YYMMDD + C/P + PRICE (8 digits, price * 1000)
    """
    # Find where the date part starts (first digit after letters)
    i = 0
    while i < len(symbol) and not symbol[i].isdigit():
        i += 1
    root = symbol[:i]

    # Parse date (6 digits) + type (1 char) + price (8 digits)
    date_str = symbol[i : i + 6]
    opt_type = symbol[i + 6]
    price_str = symbol[i + 7 :]

    year = 2000 + int(date_str[:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    strike = Decimal(price_str) / Decimal("1000")

    return {
        "root": root,
        "underlying": root,
        "expiration": date(year, month, day),
        "option_type": OptionType.CALL if opt_type == "C" else OptionType.PUT,
        "strike": strike,
    }


def filter_by_dte(
    contracts: list[OptionContract],
    min_dte: int = 7,
    max_dte: int = 45,
    target_date: date | None = None,
) -> list[OptionContract]:
    """Filter contracts by days-to-expiration."""
    ref = target_date or date.today()
    return [
        c
        for c in contracts
        if min_dte <= (c.expiration - ref).days <= max_dte
    ]


def filter_by_moneyness(
    contracts: list[OptionContract],
    underlying_price: Decimal,
    option_type: OptionType | None = None,
    min_otm_pct: float = 0.0,
    max_otm_pct: float = 0.30,
) -> list[OptionContract]:
    """Filter contracts by OTM percentage. Returns OTM options only."""
    result = []
    for c in contracts:
        if option_type and c.option_type != option_type:
            continue
        if underlying_price == 0:
            continue
        pct = abs(c.strike - underlying_price) / underlying_price
        if not (Decimal(str(min_otm_pct)) <= pct <= Decimal(str(max_otm_pct))):
            continue
        # Only include OTM options
        if c.option_type == OptionType.CALL and c.strike > underlying_price:
            result.append(c)
        elif c.option_type == OptionType.PUT and c.strike < underlying_price:
            result.append(c)
    return result


def select_strike(
    contracts: list[OptionContract],
    target_delta: Decimal | None = None,
    underlying_price: Decimal | None = None,
) -> OptionContract | None:
    """Select the best contract by delta proximity or moneyness."""
    if not contracts:
        return None
    if target_delta is not None:
        return min(contracts, key=lambda c: abs(c.delta - target_delta))
    if underlying_price is not None:
        # Pick closest to ATM
        return min(contracts, key=lambda c: abs(c.strike - underlying_price))
    return contracts[0]


def select_expiration(
    contracts: list[OptionContract],
    target_dte: int = 30,
) -> date | None:
    """Select the expiration date closest to target DTE."""
    if not contracts:
        return None
    expirations = sorted(set(c.expiration for c in contracts))
    today = date.today()
    return min(expirations, key=lambda e: abs((e - today).days - target_dte))
