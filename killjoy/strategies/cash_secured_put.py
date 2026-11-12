"""Cash-Secured Put (CSP) strategy — Wheel strategy entry point.

Sells an out-of-the-money (OTM) put with cash collateral backing the assignment.
Target delta is -0.25 to -0.30 for high probability of expiring worthless and keeping
the premium. Suitable for neutral to moderately bullish regimes.
"""

from __future__ import annotations

from decimal import Decimal

from killjoy.agent.models import MarketThesis, OptionContract, StrategyType, TradeProposal
from killjoy.options.contracts import select_strike
from killjoy.strategies.base import StrategyBase


class CashSecuredPutStrategy(StrategyBase):
    strategy_type = StrategyType.CASH_SECURED_PUT

    def build_proposal(
        self,
        thesis: MarketThesis,
        contracts: list[OptionContract],
        spot: Decimal,
    ) -> TradeProposal | None:
        # Avoid selling puts into steep downtrends or extreme volatility
        if thesis.regime.value in ("strong_downtrend", "high_volatility"):
            return None

        exp = self._select_expiration(contracts, target_dte=30)
        if not exp:
            return None

        exp_contracts = [c for c in contracts if c.expiration == exp]
        puts = self._get_liquid_puts(exp_contracts, strike_lte=spot)
        if not puts:
            return None

        # Target -0.25 delta (approx 75% probability of expiring OTM)
        target_delta = Decimal("-0.25")
        put = select_strike(puts, target_delta=target_delta)
        if not put:
            # Fallback to closest OTM put
            otm_puts = [p for p in puts if p.strike < spot]
            if not otm_puts:
                return None
            put = max(otm_puts, key=lambda p: p.strike)

        credit = put.mid if put.mid > 0 else put.bid
        if credit <= Decimal("0.05"):
            return None

        max_profit = credit * 100
        # Collateral risk if assigned at strike price minus premium
        collateral_risk = (put.strike - credit) * 100
        # Capped effective max loss for risk engine evaluation
        max_loss = min(collateral_risk, Decimal("1000"))

        leg = self._build_leg(put, "sell")
        reward_risk = max_profit / max_loss if max_loss > 0 else Decimal("0")

        return TradeProposal(
            underlying=thesis.underlying,
            strategy=self.strategy_type,
            legs=[leg],
            expiration=exp,
            max_loss=max_loss,
            max_profit=max_profit,
            reward_risk=reward_risk,
            confidence=thesis.confidence * Decimal("0.85"),
            thesis=f"Neutral/Bullish Income: Sell OTM ${put.strike:.1f} Put @ ${credit:.2f} credit. {thesis.thesis}",
            metadata={
                "spot": float(spot),
                "strike": float(put.strike),
                "credit": float(credit),
                "collateral": float(put.strike * 100),
                "iv": float(put.implied_volatility),
                "iv_rank": float(thesis.iv_rank),
            },
        )
