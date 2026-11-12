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
    """Read-only options data adapter wrapping Alpaca's OptionHistoricalDataClient.
    
    If Alpaca credentials are not configured, gracefully falls back to Zero-Config
    Sandbox mode with fully compliant synthetic OCC option chains, allowing full
    options spread construction, Greeks evaluation, and adversarial testing without API blockers.
    """

    def __init__(self, settings: Settings) -> None:
        self._is_sandbox = not settings.has_alpaca_credentials
        if self._is_sandbox:
            self._client = None
            logger.info("OptionsDataClient operating in ZERO-CONFIG SANDBOX mode")
        else:
            api_key, secret_key = settings.require_alpaca_credentials()
            self._client = OptionHistoricalDataClient(api_key, secret_key)

    def _generate_sandbox_chain(self, underlying: str) -> list[OptionContract]:
        from datetime import date, timedelta
        from killjoy.alpaca.market_data import SANDBOX_BASE_PRICES

        spot = SANDBOX_BASE_PRICES.get(underlying.upper(), Decimal("150.00"))
        today = date.today()
        # Standard expirations: 14, 30, 45 DTE
        expirations = [today + timedelta(days=d) for d in (14, 30, 45)]

        # Step size based on spot price
        step = Decimal("5.00") if spot >= 100 else Decimal("2.50") if spot >= 40 else Decimal("1.00")
        base_strike = (spot // step) * step
        strikes = [base_strike + (step * i) for i in range(-5, 6)]

        contracts: list[OptionContract] = []
        for exp in expirations:
            dte = (exp - today).days
            for strike in strikes:
                dist = (strike - spot) / spot
                # Calls
                c_delta = max(Decimal("0.05"), min(Decimal("0.95"), Decimal("0.50") - (dist * 2)))
                c_mid = max(Decimal("0.10"), (spot - strike) + Decimal("3.50") if strike < spot else Decimal("3.50") / (1 + abs(dist) * 10))
                c_bid = max(Decimal("0.05"), round(c_mid - Decimal("0.08"), 2))
                c_ask = round(c_mid + Decimal("0.08"), 2)
                c_sym = f"{underlying.upper()}{exp.strftime('%y%m%d')}C{int(strike * 1000):08d}"

                contracts.append(OptionContract(
                    symbol=c_sym,
                    underlying=underlying.upper(),
                    strike=strike,
                    expiration=exp,
                    option_type=OptionType.CALL,
                    bid=c_bid,
                    ask=c_ask,
                    mid=round(c_mid, 2),
                    last=round(c_mid, 2),
                    volume=1200,
                    open_interest=4500,
                    implied_volatility=Decimal("0.28"),
                    delta=round(c_delta, 2),
                    gamma=Decimal("0.04"),
                    theta=Decimal("-0.06"),
                    vega=Decimal("0.12"),
                ))

                # Puts
                p_delta = max(Decimal("-0.95"), min(Decimal("-0.05"), Decimal("-0.50") - (dist * 2)))
                p_mid = max(Decimal("0.10"), (strike - spot) + Decimal("3.50") if strike > spot else Decimal("3.50") / (1 + abs(dist) * 10))
                p_bid = max(Decimal("0.05"), round(p_mid - Decimal("0.08"), 2))
                p_ask = round(p_mid + Decimal("0.08"), 2)
                p_sym = f"{underlying.upper()}{exp.strftime('%y%m%d')}P{int(strike * 1000):08d}"

                contracts.append(OptionContract(
                    symbol=p_sym,
                    underlying=underlying.upper(),
                    strike=strike,
                    expiration=exp,
                    option_type=OptionType.PUT,
                    bid=p_bid,
                    ask=p_ask,
                    mid=round(p_mid, 2),
                    last=round(p_mid, 2),
                    volume=1100,
                    open_interest=3900,
                    implied_volatility=Decimal("0.29"),
                    delta=round(p_delta, 2),
                    gamma=Decimal("0.04"),
                    theta=Decimal("-0.06"),
                    vega=Decimal("0.12"),
                ))

        return contracts

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
        if self._is_sandbox or self._client is None:
            chain = self._generate_sandbox_chain(underlying)
            if expiration_date:
                chain = [c for c in chain if c.expiration == expiration_date]
            if expiration_date_gte:
                chain = [c for c in chain if c.expiration >= expiration_date_gte]
            if expiration_date_lte:
                chain = [c for c in chain if c.expiration <= expiration_date_lte]
            if option_type:
                chain = [c for c in chain if c.option_type == option_type]
            if strike_price_gte is not None:
                chain = [c for c in chain if float(c.strike) >= strike_price_gte]
            if strike_price_lte is not None:
                chain = [c for c in chain if float(c.strike) <= strike_price_lte]
            return chain
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
