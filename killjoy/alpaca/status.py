"""Convert read-only Alpaca responses into a safe connection status report."""

from __future__ import annotations

from typing import Any

from killjoy.agent.models import AccountSnapshot, PositionSnapshot
from killjoy.alpaca.client import AlpacaPaperClient


def _value(source: Any, name: str) -> Any:
    return source.get(name) if isinstance(source, dict) else getattr(source, name)


def get_connection_status(client: AlpacaPaperClient) -> tuple[AccountSnapshot, list[PositionSnapshot]]:
    """Read account/positions and return provider-neutral values without trading."""
    account = client.get_account()
    positions = client.get_positions()
    return (
        AccountSnapshot(
            status=_value(account, "status"),
            buying_power=_value(account, "buying_power"),
            portfolio_value=_value(account, "portfolio_value"),
        ),
        [PositionSnapshot(symbol=_value(item, "symbol"), qty=_value(item, "qty")) for item in positions],
    )


def format_connection_status(account: AccountSnapshot, positions: list[PositionSnapshot]) -> str:
    """Format the Phase 1 paper-account status banner."""
    return "\n".join(
        [
            "KILLJOY",
            "Alpaca: CONNECTED",
            "Paper Trading: TRUE",
            f"Account: {account.status}",
            f"Buying Power: {account.buying_power}",
            f"Portfolio Value: {account.portfolio_value}",
            f"Open Positions: {len(positions)}",
        ]
    )
