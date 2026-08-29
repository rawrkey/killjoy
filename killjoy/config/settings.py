"""Environment-backed application settings with paper-trading safeguards."""

from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingAlpacaCredentialsError(RuntimeError):
    """Raised when an operation needs Alpaca credentials that are not configured."""


class Settings(BaseSettings):
    """KILLJOY settings loaded from environment variables and an optional `.env` file.

    This foundation intentionally supports paper trading only. Supplying
    ``ALPACA_PAPER=false`` is rejected during configuration loading.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    alpaca_api_key: SecretStr | None = None
    alpaca_secret_key: SecretStr | None = None
    alpaca_paper: bool = True
    alpaca_paper_trade: bool = True
    alpaca_toolsets: str = "account,trading,assets,stock-data,options-data,news"

    # LLM provider configuration (OpenAI-compatible endpoints)
    killjoy_llm_api_key: SecretStr | None = None
    killjoy_llm_base_url: str = "https://api.openai.com/v1"
    killjoy_llm_model: str = "gpt-4o-mini"
    killjoy_llm_temperature: float = 0.3
    killjoy_llm_max_tokens: int = 2048

    @field_validator("alpaca_paper")
    @classmethod
    def require_paper_trading(cls, value: bool) -> bool:
        if not value:
            raise ValueError("KILLJOY supports paper trading only; ALPACA_PAPER must be true.")
        return value

    @field_validator("alpaca_paper_trade")
    @classmethod
    def require_mcp_paper_trading(cls, value: bool) -> bool:
        if not value:
            raise ValueError("KILLJOY supports paper trading only; ALPACA_PAPER_TRADE must be true.")
        return value

    @property
    def has_alpaca_credentials(self) -> bool:
        """Return whether both required Alpaca credentials are present and non-blank."""
        return bool(
            self.alpaca_api_key
            and self.alpaca_api_key.get_secret_value().strip()
            and self.alpaca_secret_key
            and self.alpaca_secret_key.get_secret_value().strip()
        )

    def require_alpaca_credentials(self) -> tuple[str, str]:
        """Return credentials for a client call, or raise a safe, actionable error."""
        if not self.has_alpaca_credentials:
            raise MissingAlpacaCredentialsError(
                "Alpaca paper-trading credentials are required. Set ALPACA_API_KEY and "
                "ALPACA_SECRET_KEY in your environment or an untracked .env file."
            )
        assert self.alpaca_api_key is not None
        assert self.alpaca_secret_key is not None
        return (
            self.alpaca_api_key.get_secret_value(),
            self.alpaca_secret_key.get_secret_value(),
        )


@lru_cache
def get_settings() -> Settings:
    """Return process-cached application settings."""
    return Settings()
