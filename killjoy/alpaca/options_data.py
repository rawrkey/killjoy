"""Alpaca options data adapter."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import (
    OptionChainRequest,
    OptionSnapshotRequest,
)
from alpaca.trading.enums import ContractType

from killjoy.agent.models import OptionContract, OptionType
from killjoy.config.settings import Settings
from killjoy.options.chain import parse_option_chain

logger = logging.getLogger(__name__)


class OptionsDataClient:
    """Read-only options data adapter wrapping Alpaca's OptionHistoricalDataClient."""

    def __init__(self, settings: Settings) -> None:
        api_key, secret_key = settings.require_alpaca_credentials()
        self._client = OptionHistoricalDataClient(api_key, secret_key)

    def get_option_chain(
        self,
        underlying: str,
        expiration_date: date | None = None,
        expiration_date_gte: date | None = None,
        expiration_date_lte: date | None = None,
        option_type: OptionType | None = None,
        strike_price_gte: float | None = None,
        strike_price_lte: float | None = None,
    ) -> list[OptionContract]:
        """Fetch and parse the option chain for an underlying."""
        try:
            kwargs: dict[str, Any] = {"underlying_symbol": underlying}
            if expiration_date:
                kwargs["expiration_date"] = expiration_date
            if expiration_date_gte:
                kwargs["expiration_date_gte"] = expiration_date_gte
            if expiration_date_lte:
                kwargs["expiration_date_lte"] = expiration_date_lte
            if option_type == OptionType.CALL:
                kwargs["type"] = ContractType.CALL
            elif option_type == OptionType.PUT:
                kwargs["type"] = ContractType.PUT
            if strike_price_gte is not None:
                kwargs["strike_price_gte"] = strike_price_gte
            if strike_price_lte is not None:
                kwargs["strike_price_lte"] = strike_price_lte

            req = OptionChainRequest(**kwargs)
            raw = self._client.get_option_chain(req)
            return parse_option_chain(raw, underlying)
        except Exception as e:
            logger.warning("Failed to get option chain for %s: %s", underlying, e)
            return []

    def get_option_snapshot(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Get snapshots for specific option contract symbols."""
        try:
            req = OptionSnapshotRequest(symbol_or_symbols=symbols)
            raw = self._client.get_option_snapshot(req)
            result: dict[str, dict[str, Any]] = {}
            for sym, snap in (raw.items() if isinstance(raw, dict) else []):
                entry: dict[str, Any] = {"symbol": sym}
                if hasattr(snap, "latest_trade") and snap.latest_trade:
                    entry["last"] = Decimal(str(getattr(snap.latest_trade, "price", 0)))
                if hasattr(snap, "latest_quote") and snap.latest_quote:
                    entry["bid"] = Decimal(str(getattr(snap.latest_quote, "bid_price", 0)))
                    entry["ask"] = Decimal(str(getattr(snap.latest_quote, "ask_price", 0)))
                if hasattr(snap, "greeks") and snap.greeks:
                    g = snap.greeks
                    entry["delta"] = Decimal(str(getattr(g, "delta", 0)))
                    entry["gamma"] = Decimal(str(getattr(g, "gamma", 0)))
                    entry["theta"] = Decimal(str(getattr(g, "theta", 0)))
                    entry["vega"] = Decimal(str(getattr(g, "vega", 0)))
                if hasattr(snap, "implied_volatility") and snap.implied_volatility:
                    entry["iv"] = Decimal(str(snap.implied_volatility))
                result[sym] = entry
            return result
        except Exception as e:
            logger.warning("Failed to get option snapshots: %s", e)
            return {}
