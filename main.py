"""Safe KILLJOY Phase 1 paper-account status command."""

from __future__ import annotations

from killjoy.alpaca.client import AlpacaClientError, AlpacaPaperClient
from killjoy.alpaca.status import format_connection_status, get_connection_status
from killjoy.config import MissingAlpacaCredentialsError, get_settings
from killjoy.config.logging import configure_logging


def run() -> int:
    configure_logging()
    settings = get_settings()
    if not settings.has_alpaca_credentials:
        print("KILLJOY\nAlpaca: NOT CONFIGURED\nPaper Trading: TRUE")
        print("Set paper credentials in an untracked .env to verify connectivity.")
        return 0
    try:
        client = AlpacaPaperClient.from_settings(settings)
        account, positions = get_connection_status(client)
    except (MissingAlpacaCredentialsError, AlpacaClientError) as exc:
        print(f"KILLJOY\nAlpaca: UNAVAILABLE\nPaper Trading: TRUE\nReason: {exc}")
        return 1
    print(format_connection_status(account, positions))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
