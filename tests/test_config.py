"""Tests for safe environment configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from killjoy.config.settings import MissingAlpacaCredentialsError, Settings


def test_settings_accept_paper_credentials() -> None:
    settings = Settings(
        alpaca_api_key="paper-key",
        alpaca_secret_key="paper-secret",
        alpaca_paper=True,
    )

    assert settings.alpaca_paper is True
    assert settings.has_alpaca_credentials is True
    assert settings.require_alpaca_credentials() == ("paper-key", "paper-secret")


def test_missing_credentials_raise_actionable_error() -> None:
    settings = Settings(
        alpaca_api_key=None,
        alpaca_secret_key=None,
    )

    assert settings.has_alpaca_credentials is False
    with pytest.raises(MissingAlpacaCredentialsError, match="ALPACA_API_KEY"):
        settings.require_alpaca_credentials()


def test_live_trading_setting_is_rejected() -> None:
    with pytest.raises(ValidationError, match="paper trading only"):
        Settings(alpaca_paper=False)
