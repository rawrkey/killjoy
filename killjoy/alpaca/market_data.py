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

# Default universe
DEFAULT_UNIVERSE = [
    "SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA",
    "AMZN", "META", "GOOGL", "TSLA",
]


class MarketDataClient:
    """Read-only market data adapter wrapping Alpaca's StockHistoricalDataClient."""

    def __init__(self, settings: Settings) -> None:
        api_key, secret_key = settings.require_alpaca_credentials()
        self._client = StockHistoricalDataClient(api_key, secret_key)

    def get_latest_quote(self, symbol: str) -> dict[str, Any]:
        """Get the latest quote for a symbol."""
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
            return {"symbol": symbol, "bid": Decimal("0"), "ask": Decimal("0"), "mid": Decimal("0")}

    def get_snapshot(self, symbol: str) -> dict[str, Any]:
        """Get a comprehensive snapshot for a symbol."""
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
                if result.get("last_trade") and result.get("prev_close"):
                    result["change_pct"] = (
                        (result["last_trade"] - result["prev_close"]) / result["prev_close"] * 100
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
