"""Tests for the paper-only Alpaca client boundary, using no external calls."""

from __future__ import annotations

import pytest

from killjoy.alpaca.client import AlpacaClientError, AlpacaPaperClient


class FakeTradingClient:
    def __init__(self) -> None:
        self.orders_filter = None

    def get_account(self) -> dict[str, str]:
        return {"status": "ACTIVE"}

    def get_all_positions(self) -> list[dict[str, str]]:
        return [{"symbol": "SPY"}]

    def get_orders(self, filter: object = None) -> list[dict[str, str]]:
        self.orders_filter = filter
        return [{"id": "paper-order"}]

    def get_portfolio_history(self, history_filter: object = None) -> dict[str, list[int]]:
        return {"equity": [100_000]}


def test_read_only_operations_delegate_to_sdk_client() -> None:
    fake = FakeTradingClient()
    client = AlpacaPaperClient(fake)

    assert client.get_account() == {"status": "ACTIVE"}
    assert client.get_positions() == [{"symbol": "SPY"}]
    assert client.get_orders() == [{"id": "paper-order"}]
    assert fake.orders_filter is not None
    assert client.get_portfolio_history() == {"equity": [100_000]}


def test_sdk_errors_are_wrapped_without_leaking_details() -> None:
    class FailingClient(FakeTradingClient):
        def get_account(self) -> dict[str, str]:
            raise RuntimeError("transport failure")

    with pytest.raises(AlpacaClientError, match="Unable to retrieve Alpaca account"):
        AlpacaPaperClient(FailingClient()).get_account()
