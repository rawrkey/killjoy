"""Paper-only, read-only wrapper around the official Alpaca trading client."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest, GetPortfolioHistoryRequest

from killjoy.config.settings import Settings

logger = logging.getLogger(__name__)


class AlpacaClientError(RuntimeError):
    """Raised when a safe Alpaca read operation cannot be completed."""


class TradingClientProtocol(Protocol):
    """Minimal SDK surface needed by the Phase 1 adapter, enabling mock tests."""

    def get_account(self) -> Any: ...

    def get_all_positions(self) -> Any: ...

    def get_orders(self, filter: GetOrdersRequest | None = None) -> Any: ...

    def get_portfolio_history(
        self, history_filter: GetPortfolioHistoryRequest | None = None
    ) -> Any: ...


class AlpacaPaperClient:
    """Own an official SDK client constrained to paper trading and read-only calls.

    This class intentionally has no order-submission method. A later execution layer
    must separately enforce risk and approval before adding any paper-order path.
    """

    def __init__(self, client: TradingClientProtocol) -> None:
        self._client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "AlpacaPaperClient":
        """Build a paper-only SDK client from validated settings."""
        if not settings.alpaca_paper:
            # Defense in depth; Settings currently rejects this before construction.
            raise AlpacaClientError("Refusing to construct an Alpaca client outside paper mode.")
        api_key, secret_key = settings.require_alpaca_credentials()
        return cls(TradingClient(api_key, secret_key, paper=True))

    def get_account(self) -> Any:
        return self._read("account", self._client.get_account)

    def get_positions(self) -> Any:
        return self._read("positions", self._client.get_all_positions)

    def get_orders(self) -> Any:
        request = GetOrdersRequest(status=QueryOrderStatus.ALL)
        return self._read("orders", self._client.get_orders, request)

    def get_portfolio_history(self) -> Any:
        return self._read("portfolio history", self._client.get_portfolio_history)

    @staticmethod
    def _read(operation: str, method: Any, *args: Any) -> Any:
        try:
            result = method(*args)
        except Exception as exc:  # SDK exceptions vary by transport/API response.
            logger.warning("Alpaca paper %s request failed: %s", operation, exc)
            raise AlpacaClientError(f"Unable to retrieve Alpaca {operation}.") from exc
        logger.info("Retrieved Alpaca paper %s.", operation)
        return result
