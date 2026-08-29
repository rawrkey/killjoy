"""Options chain fetching and parsing."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from killjoy.agent.models import OptionContract, OptionType

logger = logging.getLogger(__name__)


def parse_option_chain(raw_chain: Any, underlying: str) -> list[OptionContract]:
    """Parse raw Alpaca option chain response into typed OptionContract list.

    Accepts either a list of contract dicts/objects or an OptionChainResponse.
    """
    contracts: list[OptionContract] = []

    # Handle different response shapes
    if hasattr(raw_chain, "option_contracts"):
        items = raw_chain.option_contracts
    elif isinstance(raw_chain, dict) and "option_contracts" in raw_chain:
        items = raw_chain["option_contracts"]
    elif isinstance(raw_chain, list):
        items = raw_chain
    else:
        logger.warning("Unexpected option chain format: %s", type(raw_chain))
        return contracts

    for item in items:
        try:
            contract = _parse_single_contract(item, underlying)
            if contract:
                contracts.append(contract)
        except Exception as e:
            logger.debug("Skipping unparseable contract: %s", e)

    logger.info("Parsed %d option contracts for %s", len(contracts), underlying)
    return contracts


def _parse_single_contract(item: Any, underlying: str) -> OptionContract | None:
    """Parse a single option contract from SDK response."""
    if isinstance(item, dict):
        symbol = item.get("symbol", "")
        strike = Decimal(str(item.get("strike_price", item.get("strike", 0))))
        exp_str = item.get("expiration_date", item.get("expiration", ""))
        opt_type_str = item.get("type", item.get("contract_type", "call"))
        bid = Decimal(str(item.get("bid", item.get("bid_price", 0))))
        ask = Decimal(str(item.get("ask", item.get("ask_price", 0))))
        volume = int(item.get("volume", 0))
        oi = int(item.get("open_interest", 0))
        iv = Decimal(str(item.get("implied_volatility", 0)))
        delta = Decimal(str(item.get("delta", 0)))
        gamma = Decimal(str(item.get("gamma", 0)))
        theta = Decimal(str(item.get("theta", 0)))
        vega = Decimal(str(item.get("vega", 0)))
        last = Decimal(str(item.get("last", item.get("last_price", 0))))
    else:
        symbol = getattr(item, "symbol", "")
        strike = Decimal(str(getattr(item, "strike_price", getattr(item, "strike", 0))))
        exp_val = getattr(item, "expiration_date", getattr(item, "expiration", ""))
        if isinstance(exp_val, date):
            exp_str = exp_val.isoformat()
        else:
            exp_str = str(exp_val)
        opt_type_str = getattr(item, "type", getattr(item, "contract_type", "call"))
        bid = Decimal(str(getattr(item, "bid", getattr(item, "bid_price", 0))))
        ask = Decimal(str(getattr(item, "ask", getattr(item, "ask_price", 0))))
        volume = int(getattr(item, "volume", 0))
        oi = int(getattr(item, "open_interest", 0))
        iv = Decimal(str(getattr(item, "implied_volatility", 0)))
        delta = Decimal(str(getattr(item, "delta", 0)))
        gamma = Decimal(str(getattr(item, "gamma", 0)))
        theta = Decimal(str(getattr(item, "theta", 0)))
        vega = Decimal(str(getattr(item, "vega", 0)))
        last = Decimal(str(getattr(item, "last", getattr(item, "last_price", 0))))

    if not symbol or strike == 0:
        return None

    # Parse expiration
    if isinstance(exp_str, date):
        expiration = exp_str
    elif exp_str:
        expiration = date.fromisoformat(str(exp_str)[:10])
    else:
        return None

    option_type = OptionType.CALL if str(opt_type_str).lower() in ("call", "c") else OptionType.PUT
    mid = (bid + ask) / 2 if bid and ask else Decimal("0")

    return OptionContract(
        symbol=symbol,
        underlying=underlying,
        strike=strike,
        expiration=expiration,
        option_type=option_type,
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
