"""Tests for safe account-status formatting and provider-normalization."""

from decimal import Decimal

from killjoy.agent.models import AccountSnapshot, PositionSnapshot
from killjoy.alpaca.client import AlpacaPaperClient
from killjoy.alpaca.status import format_connection_status, get_connection_status


def test_status_format_includes_required_paper_fields() -> None:
    output = format_connection_status(
        AccountSnapshot(status="ACTIVE", buying_power=Decimal("100000"), portfolio_value=Decimal("100500")),
        [PositionSnapshot(symbol="SPY", qty="1")],
    )
    assert "Alpaca: CONNECTED" in output
    assert "Paper Trading: TRUE" in output
    assert "Open Positions: 1" in output


def test_status_converts_mocked_alpaca_data() -> None:
    class FakeClient:
        def get_account(self): return {"status": "ACTIVE", "buying_power": "100000", "portfolio_value": "100500"}
        def get_all_positions(self): return [{"symbol": "SPY", "qty": "2"}]

    account, positions = get_connection_status(AlpacaPaperClient(FakeClient()))
    assert account.status == "ACTIVE"
    assert positions[0].quantity == Decimal("2")
