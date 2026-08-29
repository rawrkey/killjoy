"""Trading operations — order submission and position management.

This module extends the read-only AlpacaPaperClient with write operations.
Orders are only submitted AFTER passing through the full risk pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from alpaca.trading.client import TradingClient

from killjoy.alpaca.client import AlpacaClientError, AlpacaPaperClient
from killjoy.config.settings import Settings

logger = logging.getLogger(__name__)


class AlpacaTradingClient(AlpacaPaperClient):
    """Extended Alpaca client with order submission capabilities.

    Inherits read-only methods from AlpacaPaperClient and adds write operations.
    All write operations are paper-only.
    """

    def __init__(self, client: TradingClient) -> None:
        super().__init__(client)
        self._trading_client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "AlpacaTradingClient":
        """Build a paper-only trading client from validated settings."""
        if not settings.alpaca_paper:
            raise AlpacaClientError("Refusing to construct an Alpaca client outside paper mode.")
        api_key, secret_key = settings.require_alpaca_credentials()
        return cls(TradingClient(api_key, secret_key, paper=True))

    def submit_order(self, order_request: Any) -> Any:
        """Submit an order through the Alpaca SDK."""
        try:
            order = self._trading_client.submit_order(order_request)
            logger.info("Order submitted: %s", getattr(order, "id", "unknown"))
            return order
        except Exception as exc:
            logger.warning("Order submission failed: %s", exc)
            raise AlpacaClientError("Order submission failed.") from exc

    def get_order(self, order_id: str) -> Any:
        """Get order by ID."""
        try:
            return self._trading_client.get_order(order_id)
        except Exception as exc:
            raise AlpacaClientError(f"Failed to get order {order_id}.") from exc

    def close_position(self, symbol: str) -> Any:
        """Close a position by symbol."""
        try:
            return self._trading_client.close_position(symbol)
        except Exception as exc:
            raise AlpacaClientError(f"Failed to close position {symbol}.") from exc
