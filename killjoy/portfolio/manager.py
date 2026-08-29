"""Portfolio manager — evaluates portfolio state for trade decisions."""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import AccountSnapshot, PortfolioCheck, PositionSnapshot, TradeProposal
from killjoy.agent.portfolio_agent import check_portfolio_fit

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages portfolio state and evaluates trade fit."""

    def __init__(self) -> None:
        self._positions: list[PositionSnapshot] = []
        self._account: AccountSnapshot | None = None

    def update(self, account: AccountSnapshot, positions: list[PositionSnapshot]) -> None:
        """Update portfolio state from Alpaca data."""
        self._account = account
        self._positions = positions
        logger.info(
            "Portfolio updated: %d positions, buying power $%s",
            len(positions),
            account.buying_power,
        )

    def evaluate_trade(self, proposal: TradeProposal) -> PortfolioCheck:
        """Evaluate whether a trade fits the portfolio."""
        if not self._account:
            return PortfolioCheck(
                approved=False,
                reasons=["Portfolio state not initialized"],
            )

        return check_portfolio_fit(
            proposal=proposal,
            positions=self._positions,
            buying_power=self._account.buying_power,
            portfolio_value=self._account.portfolio_value,
        )

    @property
    def position_count(self) -> int:
        return len(self._positions)

    @property
    def buying_power(self) -> Decimal:
        return self._account.buying_power if self._account else Decimal("0")

    @property
    def portfolio_value(self) -> Decimal:
        return self._account.portfolio_value if self._account else Decimal("0")

    @property
    def positions(self) -> list[PositionSnapshot]:
        return self._positions

    def get_portfolio_context(self) -> dict:
        """Get portfolio context for the kill agent."""
        return {
            "existing_positions": self._positions,
            "buying_power": float(self.buying_power),
            "portfolio_value": float(self.portfolio_value),
            "position_count": self.position_count,
        }
