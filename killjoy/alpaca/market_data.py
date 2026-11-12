"""Alpaca market data adapter for stock quotes, bars, and snapshots."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import (
    StockBarsRequest,
    StockLatestQuoteRequest,
    StockSnapshotRequest,
)
from alpaca.data.timeframe import TimeFrame

from killjoy.config.settings import Settings

logger = logging.getLogger(__name__)

# Default universe — top 5 most liquid for fast cycle times
DEFAULT_UNIVERSE = [
    "SPY", "QQQ", "AAPL", "NVDA", "TSLA",
]

SANDBOX_BASE_PRICES: dict[str, Decimal] = {
    "SPY": Decimal("595.50"),
    "QQQ": Decimal("512.20"),
    "AAPL": Decimal("228.40"),
    "NVDA": Decimal("138.80"),
    "TSLA": Decimal("320.10"),
    "MSFT": Decimal("426.50"),
    "AMZN": Decimal("208.90"),
    "GOOGL": Decimal("178.60"),
    "META": Decimal("580.40"),
    "AMD": Decimal("146.30"),
}


class MarketDataClient:
    """Read-only market data adapter wrapping Alpaca's StockHistoricalDataClient.
    
    If Alpaca credentials are not configured, gracefully falls back to Zero-Config
    Sandbox mode with deterministic market data, allowing full pipeline execution
    and simulation on Agensi, Cursor, and local agents without API barriers.
    """

    def __init__(self, settings: Settings) -> None:
        self._is_sandbox = not settings.has_alpaca_credentials
        if self._is_sandbox:
            self._client = None
            logger.info("MarketDataClient operating in ZERO-CONFIG SANDBOX mode")
        else:
            api_key, secret_key = settings.require_alpaca_credentials()
            self._client = StockHistoricalDataClient(api_key, secret_key)

    def _get_sandbox_spot(self, symbol: str) -> Decimal:
        sym = symbol.upper()
        if sym in SANDBOX_BASE_PRICES:
            return SANDBOX_BASE_PRICES[sym]
        seed = sum(ord(c) for c in sym)
        return Decimal(str(50 + (seed % 350)))

    def _generate_sandbox_bars(self, symbol: str, limit: int = 20) -> list[dict[str, Any]]:
        spot = float(self._get_sandbox_spot(symbol))
        bars: list[dict[str, Any]] = []
        base = spot * 0.96
        for i in range(limit):
            pct = 1.0 + ((i % 5) - 2) * 0.008 + (i * 0.002)
            c = Decimal(str(round(base * pct, 2)))
            h = Decimal(str(round(float(c) * 1.008, 2)))
            l = Decimal(str(round(float(c) * 0.992, 2)))
            o = Decimal(str(round((float(h) + float(l)) / 2, 2)))
            bars.append({
                "timestamp": None,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": 2500000 + (i * 120000),
            })
        return bars

    def get_latest_quote(self, symbol: str) -> dict[str, Any]:
        """Get the latest quote for a symbol."""
        if self._is_sandbox or self._client is None:
            spot = self._get_sandbox_spot(symbol)
            return {
                "symbol": symbol,
                "bid": spot - Decimal("0.05"),
                "ask": spot + Decimal("0.05"),
                "mid": spot,
                "timestamp": datetime.now(),
            }
        try:
            req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            resp = self._client.get_stock_latest_quote(req)
            q = resp[symbol] if isinstance(resp, dict) else resp
            return {
                "symbol": symbol,
                "bid": Decimal(str(getattr(q, "bid_price", 0))),
                "ask": Decimal(str(getattr(q, "ask_price", 0))),
                "mid": Decimal(str((float(getattr(q, "bid_price", 0)) + float(getattr(q, "ask_price", 0))) / 2)),
                "timestamp": getattr(q, "timestamp", None),
            }
        except Exception as e:
            logger.warning("Failed to get quote for %s: %s", symbol, e)
            spot = self._get_sandbox_spot(symbol)
            return {"symbol": symbol, "bid": spot, "ask": spot, "mid": spot}

    def get_snapshot(self, symbol: str) -> dict[str, Any]:
        """Get a comprehensive snapshot for a symbol."""
        if self._is_sandbox or self._client is None:
            spot = self._get_sandbox_spot(symbol)
            prev = round(spot * Decimal("0.988"), 2)
            return {
                "symbol": symbol,
                "last_trade": spot,
                "bid": spot - Decimal("0.05"),
                "ask": spot + Decimal("0.05"),
                "open": prev,
                "close": spot,
                "high": spot + Decimal("2.10"),
                "low": spot - Decimal("1.40"),
                "volume": 18500000,
                "prev_close": prev,
                "change_pct": round(((spot - prev) / prev) * Decimal("100"), 2),
            }
        try:
            req = StockSnapshotRequest(symbol_or_symbols=symbol)
            resp = self._client.get_stock_snapshot(req)
            snap = resp[symbol] if isinstance(resp, dict) else resp
            result: dict[str, Any] = {"symbol": symbol}

            if hasattr(snap, "latest_trade") and snap.latest_trade:
                result["last_trade"] = Decimal(str(getattr(snap.latest_trade, "price", 0)))
            if hasattr(snap, "latest_quote") and snap.latest_quote:
                result["bid"] = Decimal(str(getattr(snap.latest_quote, "bid_price", 0)))
                result["ask"] = Decimal(str(getattr(snap.latest_quote, "ask_price", 0)))
            if hasattr(snap, "daily_bar") and snap.daily_bar:
                bar = snap.daily_bar
                result["open"] = Decimal(str(getattr(bar, "open", 0)))
                result["high"] = Decimal(str(getattr(bar, "high", 0)))
                result["low"] = Decimal(str(getattr(bar, "low", 0)))
                result["close"] = Decimal(str(getattr(bar, "close", 0)))
                result["volume"] = int(getattr(bar, "volume", 0))
            if hasattr(snap, "prev_daily_bar") and snap.prev_daily_bar:
                prev = snap.prev_daily_bar
                result["prev_close"] = Decimal(str(getattr(prev, "close", 0)))
            # Compute change_pct from available data
            if result.get("last_trade") and result.get("prev_close") and result["prev_close"] > 0:
                result["change_pct"] = (
                    (result["last_trade"] - result["prev_close"]) / result["prev_close"] * 100
                )
            elif result.get("last_trade") and result.get("open") and result["open"] > 0:
                result["change_pct"] = (
                    (result["last_trade"] - result["open"]) / result["open"] * 100
                )
            return result
        except Exception as e:
            logger.warning("Failed to get snapshot for %s: %s", symbol, e)
            return {"symbol": symbol}

    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.Day,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get historical bars for a symbol."""
        if self._is_sandbox or self._client is None:
            return self._generate_sandbox_bars(symbol, limit=limit)
        try:
            req = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                limit=limit,
            )
            resp = self._client.get_stock_bars(req)
            bars_data = resp[symbol] if isinstance(resp, dict) else resp
            bars = []
            for bar in bars_data:
                bars.append({
                    "timestamp": getattr(bar, "timestamp", None),
                    "open": Decimal(str(getattr(bar, "open", 0))),
                    "high": Decimal(str(getattr(bar, "high", 0))),
                    "low": Decimal(str(getattr(bar, "low", 0))),
                    "close": Decimal(str(getattr(bar, "close", 0))),
                    "volume": int(getattr(bar, "volume", 0)),
                })
            return bars
        except Exception as e:
            logger.warning("Failed to get bars for %s: %s", symbol, e)
            return []

    def get_multi_snapshots(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Get snapshots for multiple symbols."""
        results = {}
        for sym in symbols:
            results[sym] = self.get_snapshot(sym)
        return results
