"""Iron Condor strategy."""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import MarketThesis, OptionContract, StrategyType, TradeProposal
from killjoy.strategies.base import StrategyBase


class IronCondorStrategy(StrategyBase):
    strategy_type = StrategyType.IRON_CONDOR

    def build_proposal(self, thesis, contracts, spot):
        # Only suitable for sideways / low-vol regimes
        if thesis.regime.value in ("strong_uptrend", "strong_downtrend", "high_volatility"):
            return None

        exp = self._select_expiration(contracts)
        if not exp:
            return None

        exp_contracts = [c for c in contracts if c.expiration == exp]
        calls = sorted(
            [c for c in exp_contracts if c.option_type.value == "call" and c.strike > spot],
            key=lambda c: c.strike,
        )
        puts = sorted(
            [c for c in exp_contracts if c.option_type.value == "put" and c.strike < spot],
            key=lambda c: c.strike,
            reverse=True,
        )

        calls = [c for c in calls if c.volume > 5 and c.open_interest > 20]
        puts = [c for c in puts if c.volume > 5 and c.open_interest > 20]

        if len(calls) < 2 or len(puts) < 2:
            return None

        # Sell inner, buy outer
        short_call = calls[0]
        long_call = calls[1] if len(calls) > 1 else calls[0]
        short_put = puts[0]
        long_put = puts[1] if len(puts) > 1 else puts[0]

        # Net credit
        short_credit = (short_call.mid + short_put.mid) / 2
        long_debit = (long_call.mid + long_put.mid) / 2
        net_credit = (short_credit - long_debit) * 100

        # Widths
        call_width = (long_call.strike - short_call.strike) * 100
        put_width = (short_put.strike - long_put.strike) * 100
        max_width = max(call_width, put_width)

        max_loss = max_width - net_credit if net_credit > 0 else max_width
        max_profit = net_credit if net_credit > 0 else Decimal("0")

        legs = [
            self._build_leg(short_call, "sell"),
            self._build_leg(long_call, "buy"),
            self._build_leg(short_put, "sell"),
            self._build_leg(long_put, "buy"),
        ]

        reward_risk = max_profit / max_loss if max_loss > 0 else Decimal("0")

        return TradeProposal(
            underlying=thesis.underlying,
            strategy=self.strategy_type,
            legs=legs,
            expiration=exp,
            max_loss=max_loss,
            max_profit=max_profit,
            reward_risk=reward_risk,
            confidence=thesis.confidence * Decimal("0.7"),
            thesis=f"Neutral/range-bound: {thesis.thesis}",
            metadata={
                "spot": float(spot),
                "net_credit": float(net_credit),
                "call_width": float(call_width),
                "put_width": float(put_width),
            },
        )
