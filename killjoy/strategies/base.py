"""Strategy base class and interfaces."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal

from killjoy.agent.models import (
    MarketThesis,
    OptionContract,
    OptionLeg,
    StrategyType,
    TradeProposal,
)
from killjoy.options.contracts import filter_by_dte, filter_by_moneyness, select_strike
from killjoy.options.liquidity import filter_liquid

logger = logging.getLogger(__name__)


class StrategyBase(ABC):
    """Base class for all option strategies."""

    strategy_type: StrategyType

    @abstractmethod
    def build_proposal(
        self,
        thesis: MarketThesis,
        contracts: list[OptionContract],
        spot: Decimal,
    ) -> TradeProposal | None:
        """Build a trade proposal from a thesis and available contracts."""
        ...

    def _select_expiration(self, contracts: list[OptionContract], target_dte: int = 30) -> date | None:
        """Select the best expiration date."""
        filtered = filter_by_dte(contracts, min_dte=max(target_dte - 10, 7), max_dte=target_dte + 10)
        if not filtered:
            return None
        expirations = sorted(set(c.expiration for c in filtered))
        today = date.today()
        return min(expirations, key=lambda e: abs((e - today).days - target_dte))

    def _get_liquid_calls(
        self, contracts: list[OptionContract], strike_gte: Decimal | None = None
    ) -> list[OptionContract]:
        calls = [c for c in contracts if c.option_type.value == "call"]
        if strike_gte:
            calls = [c for c in calls if c.strike >= strike_gte]
        return filter_liquid(calls)

    def _get_liquid_puts(
        self, contracts: list[OptionContract], strike_lte: Decimal | None = None
    ) -> list[OptionContract]:
        puts = [c for c in contracts if c.option_type.value == "put"]
        if strike_lte:
            puts = [c for c in puts if c.strike <= strike_lte]
        return filter_liquid(puts)

    def _build_leg(self, contract: OptionContract, side: str, qty: int = 1) -> OptionLeg:
        return OptionLeg(
            contract_symbol=contract.symbol,
            option_type=contract.option_type,
            strike=contract.strike,
            expiration=contract.expiration,
            side=side,
            quantity=qty,
            bid=contract.bid,
            ask=contract.ask,
            mid=contract.mid,
            delta=contract.delta,
        )
