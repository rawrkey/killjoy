"""Bear Put Spread strategy."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import MarketThesis, OptionContract, StrategyType, TradeProposal
from killjoy.strategies.base import StrategyBase


class BearPutSpreadStrategy(StrategyBase):
    strategy_type = StrategyType.BEAR_PUT_SPREAD

    def build_proposal(self, thesis, contracts, spot):
        if thesis.regime.value in ("strong_uptrend", "uptrend"):
            return None

        exp = self._select_expiration(contracts)
        if not exp:
            return None

        exp_contracts = [c for c in contracts if c.expiration == exp]
        puts = self._get_liquid_puts(exp_contracts)
        if len(puts) < 2:
            return None

        puts_sorted = sorted(puts, key=lambda c: c.strike, reverse=True)
        long_put = None
        short_put = None

        for c in puts_sorted:
            if c.strike >= spot and long_put is None:
                long_put = c
            elif c.strike < spot and short_put is None:
                short_put = c

        if not long_put or not short_put:
            if len(puts_sorted) >= 2:
                long_put = puts_sorted[0]
                short_put = puts_sorted[-1]
            else:
                return None

        long_debit = long_put.mid if long_put.mid > 0 else long_put.ask
        short_credit = short_put.mid if short_put.mid > 0 else short_put.bid
        width = long_put.strike - short_put.strike

        net_debit = (long_debit - short_credit) * 100
        max_loss = net_debit
        max_profit = (width * 100) - net_debit

        long_leg = self._build_leg(long_put, "buy")
        short_leg = self._build_leg(short_put, "sell")

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
            thesis=f"Moderately bearish: {thesis.thesis}",
            metadata={
                "spot": float(spot),
                "width": float(width),
                "net_debit": float(net_debit),
                "iv_rank": float(thesis.iv_rank),
            },
        )
