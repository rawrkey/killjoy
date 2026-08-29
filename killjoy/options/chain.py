"""Option chain fetching and parsing."""

from __future__ import annotations

import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any

from killjoy.agent.models import OptionContract, OptionType

logger = logging.getLogger(__name__)

# OCC option symbol format: ROOT + YYMMDD + C/P + PRICE (8 digits, price * 1000)
_SYMBOL_RE = re.compile(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$", re.IGNORECASE)


def parse_option_symbol(symbol: str) -> dict | None:
    """Parse an OCC option symbol into components."""
    m = _SYMBOL_RE.match(symbol)
    if not m:
        return None
    root, yy, mm, dd, cp, price_str = m.groups()
    try:
        year = 2000 + int(yy)
        month = int(mm)
        day = int(dd)
        strike = Decimal(price_str) / Decimal("1000")
    except (ValueError, InvalidOperation):
        return None
    return {
        "root": root,
        "expiration": date(year, month, day),
        "option_type": OptionType.CALL if cp.upper() == "C" else OptionType.PUT,
        "strike": strike,
    }


def parse_option_chain(raw_chain: Any, underlying: str) -> list[OptionContract]:
    """Parse raw Alpaca option chain response into typed OptionContract list.

    Handles the Alpaca SDK format: dict[symbol, OptionsSnapshot]
    Also handles legacy formats: list of dicts, object with option_contracts.
    """
    contracts: list[OptionContract] = []

    if isinstance(raw_chain, dict):
        # Primary SDK format: dict[symbol, OptionsSnapshot] or dict[symbol, dict]
        for sym, snap in raw_chain.items():
            try:
                contract = _parse_from_snapshot(sym, snap, underlying)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.debug("Skipping contract %s: %s", sym, e)
    elif hasattr(raw_chain, "option_contracts"):
        # Object with option_contracts attribute
        for item in raw_chain.option_contracts:
            try:
                contract = _parse_single_contract(item, underlying)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.debug("Skipping contract: %s", e)
    elif isinstance(raw_chain, list):
        for item in raw_chain:
            try:
                contract = _parse_single_contract(item, underlying)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.debug("Skipping contract: %s", e)
    else:
        logger.warning("Unexpected option chain format: %s", type(raw_chain))
        return contracts

    logger.info("Parsed %d option contracts for %s", len(contracts), underlying)
    return contracts


def _parse_from_snapshot(symbol: str, snap: Any, underlying: str) -> OptionContract | None:
    """Parse from Alpaca SDK OptionsSnapshot or dict."""
    parsed = parse_option_symbol(symbol)
    if not parsed:
        return None

    # Extract pricing from snapshot
    bid = Decimal("0")
    ask = Decimal("0")
    last = Decimal("0")
    volume = 0
    oi = 0
    iv = Decimal("0")
    delta = Decimal("0")
    gamma = Decimal("0")
    theta = Decimal("0")
    vega = Decimal("0")

    if isinstance(snap, dict):
        # Dict format from model_dump()
        quote = snap.get("latest_quote")
        if quote:
            bid = Decimal(str(quote.get("bid_price", 0) or 0))
            ask = Decimal(str(quote.get("ask_price", 0) or 0))
        trade = snap.get("latest_trade")
        if trade:
            last = Decimal(str(trade.get("price", 0) or 0))
        iv = Decimal(str(snap.get("implied_volatility", 0) or 0))
        greeks = snap.get("greeks")
        if greeks:
            delta = Decimal(str(greeks.get("delta", 0) or 0))
            gamma = Decimal(str(greeks.get("gamma", 0) or 0))
            theta = Decimal(str(greeks.get("theta", 0) or 0))
            vega = Decimal(str(greeks.get("vega", 0) or 0))
    else:
        # OptionsSnapshot Pydantic model
        if hasattr(snap, "latest_quote") and snap.latest_quote:
            q = snap.latest_quote
            bid = Decimal(str(getattr(q, "bid_price", 0) or 0))
            ask = Decimal(str(getattr(q, "ask_price", 0) or 0))
        if hasattr(snap, "latest_trade") and snap.latest_trade:
            t = snap.latest_trade
            last = Decimal(str(getattr(t, "price", 0) or 0))
        if hasattr(snap, "implied_volatility") and snap.implied_volatility:
            iv = Decimal(str(snap.implied_volatility))
        if hasattr(snap, "greeks") and snap.greeks:
            g = snap.greeks
            delta = Decimal(str(getattr(g, "delta", 0) or 0))
            gamma = Decimal(str(getattr(g, "gamma", 0) or 0))
            theta = Decimal(str(getattr(g, "theta", 0) or 0))
            vega = Decimal(str(getattr(g, "vega", 0) or 0))

    mid = (bid + ask) / 2 if bid > 0 and ask > 0 else last

    return OptionContract(
        symbol=symbol,
        underlying=underlying,
        strike=parsed["strike"],
        expiration=parsed["expiration"],
        option_type=parsed["option_type"],
        bid=bid,
        ask=ask,
        mid=mid,
        last=last,
        volume=volume,
        open_interest=oi,
        implied_volatility=iv,
        delta=delta,
        gamma=gamma,
        theta=theta,
        vega=vega,
    )


def _parse_single_contract(item: Any, underlying: str) -> OptionContract | None:
    """Parse a single option contract from dict or object."""
    if isinstance(item, dict):
        symbol = item.get("symbol", "")
        parsed = parse_option_symbol(symbol)
        if not parsed:
            return None
        quote = item.get("latest_quote", item)
        bid = Decimal(str(quote.get("bid_price", quote.get("bid", 0)) or 0))
        ask = Decimal(str(quote.get("ask_price", quote.get("ask", 0)) or 0))
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else Decimal("0")
        return OptionContract(
            symbol=symbol,
            underlying=underlying,
            strike=parsed["strike"],
            expiration=parsed["expiration"],
            option_type=parsed["option_type"],
            bid=bid,
            ask=ask,
            mid=mid,
        )
    else:
        symbol = getattr(item, "symbol", "")
        parsed = parse_option_symbol(symbol)
        if not parsed:
            return None
        bid = Decimal(str(getattr(item, "bid_price", getattr(item, "bid", 0)) or 0))
        ask = Decimal(str(getattr(item, "ask_price", getattr(item, "ask", 0)) or 0))
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else Decimal("0")
        return OptionContract(
            symbol=symbol,
            underlying=underlying,
            strike=parsed["strike"],
            expiration=parsed["expiration"],
            option_type=parsed["option_type"],
            bid=bid,
            ask=ask,
            mid=mid,
        )
