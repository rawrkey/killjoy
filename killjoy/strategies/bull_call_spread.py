"""Bull Call Spread strategy."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import MarketThesis, OptionContract, StrategyType, TradeProposal
from killjoy.strategies.base import StrategyBase


class BullCallSpreadStrategy(StrategyBase):
    strategy_type = StrategyType.BULL_CALL_SPREAD

    def build_proposal(self, thesis, contracts, spot):
        if thesis.regime.value in ("strong_downtrend", "downtrend"):
            return None

        exp = self._select_expiration(contracts)
        if not exp:
            return None

        exp_contracts = [c for c in contracts if c.expiration == exp]
        calls = self._get_liquid_calls(exp_contracts)
        if len(calls) < 2:
            return None

        # Buy ATM/slightly ITM call, sell OTM call
        calls_sorted = sorted(calls, key=lambda c: c.strike)
        long_call = None
        short_call = None

        for c in calls_sorted:
            if c.strike <= spot and long_call is None:
                long_call = c
            elif c.strike > spot and short_call is None:
                short_call = c

        if not long_call or not short_call:
            # Fallback: use first two
            if len(calls_sorted) >= 2:
                long_call = calls_sorted[0]
                short_call = calls_sorted[-1]
            else:
                return None

        long_debit = long_call.mid if long_call.mid > 0 else long_call.ask
        short_credit = short_call.mid if short_call.mid > 0 else short_call.bid
        width = short_call.strike - long_call.strike

        net_debit = (long_debit - short_credit) * 100
        max_loss = net_debit
        max_profit = (width * 100) - net_debit

        long_leg = self._build_leg(long_call, "buy")
        short_leg = self._build_leg(short_call, "sell")

        reward_risk = max_profit / max_loss if max_loss > 0 else Decimal("0")

        return TradeProposal(
            underlying=thesis.underlying,
            strategy=self.strategy_type,
            legs=[long_leg, short_leg],
            expiration=exp,
            max_loss=max_loss,
            max_profit=max_profit,
            reward_risk=reward_risk,
            confidence=thesis.confidence * Decimal("0.85"),
            thesis=f"Moderately bullish: {thesis.thesis}",
            metadata={
                "spot": float(spot),
                "width": float(width),
                "net_debit": float(net_debit),
            },
        )
