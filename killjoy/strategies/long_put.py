"""Long Put strategy."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import MarketThesis, OptionContract, StrategyType, TradeProposal
from killjoy.options.contracts import select_strike
from killjoy.strategies.base import StrategyBase


class LongPutStrategy(StrategyBase):
    strategy_type = StrategyType.LONG_PUT

    def build_proposal(self, thesis, contracts, spot):
        if thesis.regime.value in ("strong_uptrend", "uptrend"):
            return None

        exp = self._select_expiration(contracts)
        if not exp:
            return None

        exp_contracts = [c for c in contracts if c.expiration == exp]
        puts = self._get_liquid_puts(exp_contracts)
        if not puts:
            return None

        target_delta = Decimal("-0.35")
        put = select_strike(puts, target_delta=target_delta)
        if not put:
            return None

        debit = put.mid if put.mid > 0 else put.ask
        max_loss = debit * 100
        max_profit = put.strike * 100 - max_loss  # intrinsic at zero

        leg = self._build_leg(put, "buy")
        reward_risk = max_profit / max_loss if max_loss > 0 else Decimal("0")

        return TradeProposal(
            underlying=thesis.underlying,
            strategy=self.strategy_type,
            legs=[leg],
            expiration=exp,
            max_loss=max_loss,
            max_profit=max_profit,
            reward_risk=reward_risk,
            confidence=thesis.confidence * Decimal("0.8"),
            thesis=f"Bearish: {thesis.thesis}",
            metadata={"spot": float(spot), "iv": float(put.implied_volatility)},
        )
