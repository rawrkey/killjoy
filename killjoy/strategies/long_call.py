"""Long Call strategy."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import MarketThesis, OptionContract, StrategyType, TradeProposal
from killjoy.options.contracts import select_strike
from killjoy.strategies.base import StrategyBase


class LongCallStrategy(StrategyBase):
    strategy_type = StrategyType.LONG_CALL

    def build_proposal(self, thesis, contracts, spot):
        if thesis.regime.value in ("strong_downtrend", "downtrend"):
            return None

        exp = self._select_expiration(contracts)
        if not exp:
            return None

        exp_contracts = [c for c in contracts if c.expiration == exp]
        calls = self._get_liquid_calls(exp_contracts)
        if not calls:
            return None

        # Pick slightly OTM call (delta ~0.3-0.4)
        target_delta = Decimal("0.35")
        call = select_strike(calls, target_delta=target_delta)
        if not call:
            return None

        debit = call.mid if call.mid > 0 else call.ask
        max_loss = debit * 100
        max_profit = Decimal("999")  # theoretically unlimited

        leg = self._build_leg(call, "buy")
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
            thesis=f"Bullish: {thesis.thesis}",
            metadata={"spot": float(spot), "iv": float(call.implied_volatility)},
        )
