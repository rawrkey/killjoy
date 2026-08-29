"""Kill Agent — DETERMINISTIC BASELINE for adversarial trade testing.

This module provides the rule-based fallback for kill testing. It is called
internally by ``llm_kill.py`` for pre-screening before LLM adversarial analysis
and structured debate. The scheduler imports the LLM version, not this module
directly.

Fallback behavior: If no LLM provider is configured or available, the system
uses this module's 9 deterministic checks as the final kill decision.

Kill Score Semantics:
  0.0 - 0.2: KILL — Major red flags, trade should not proceed
  0.2 - 0.4: WEAK — Significant concerns, likely reject
  0.4 - 0.6: MARGINAL — Some concerns, proceed with caution
  0.6 - 0.8: DECENT — Minor concerns, acceptable
  0.8 - 1.0: STRONG — Few or no concerns, should proceed
"""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import KillDecision, MarketThesis, TradeProposal

logger = logging.getLogger(__name__)

# Threshold: kill_score below this = trade is rejected
KILL_THRESHOLD = Decimal("0.4")


def kill_test(
    proposal: TradeProposal,
    thesis: MarketThesis,
    portfolio_context: dict | None = None,
) -> KillDecision:
    """Adversarially test a trade proposal. Return a KillDecision.

    The kill agent actively tries to find reasons to reject the trade.
    """
    kill_reasons: list[str] = []
    score = Decimal("1.0")  # Start at 1.0 (safe), deduct for each issue

    # 1. Check confidence
    if proposal.confidence < Decimal("0.3"):
        kill_reasons.append(f"Low confidence: {proposal.confidence:.2f}")
        score -= Decimal("0.2")

    # 2. Check reward/risk
    if proposal.reward_risk < Decimal("1.0"):
        kill_reasons.append(f"Poor reward/risk ratio: {proposal.reward_risk:.2f}")
        score -= Decimal("0.2")
    elif proposal.reward_risk < Decimal("1.5"):
        kill_reasons.append(f"Marginal reward/risk: {proposal.reward_risk:.2f}")
        score -= Decimal("0.1")

    # 3. Check max loss relative to proposal
    if proposal.max_loss > Decimal("500"):
        kill_reasons.append(f"High max loss: ${proposal.max_loss:.0f}")
        score -= Decimal("0.15")

    # 4. Check thesis alignment
    if thesis.regime.value in ("strong_downtrend", "downtrend") and "Bullish" in proposal.thesis:
        kill_reasons.append("Bullish thesis in downtrend regime — contradictory")
        score -= Decimal("0.3")
    elif thesis.regime.value in ("strong_uptrend", "uptrend") and "Bearish" in proposal.thesis:
        kill_reasons.append("Bearish thesis in uptrend regime — contradictory")
        score -= Decimal("0.3")

    # 5. Check regime match for specific strategies
    if proposal.strategy.value == "iron_condor" and thesis.regime.value in ("high_volatility",):
        kill_reasons.append("Iron condor in high-volatility regime — dangerous")
        score -= Decimal("0.25")

    # 6. Check if thesis has risks
    if len(thesis.risks) > 2:
        kill_reasons.append(f"Multiple thesis risks identified: {len(thesis.risks)}")
        score -= Decimal("0.1")

    # 7. Check expiration timing
    from datetime import date
    days_to_exp = (proposal.expiration - date.today()).days
    if days_to_exp < 7:
        kill_reasons.append(f"Very short expiration: {days_to_exp} days")
        score -= Decimal("0.15")
    elif days_to_exp > 60:
        kill_reasons.append(f"Long-dated option: {days_to_exp} days")
        score -= Decimal("0.05")

    # 8. Check leg count for complexity
    if len(proposal.legs) > 4:
        kill_reasons.append(f"Complex multi-leg structure: {len(proposal.legs)} legs")
        score -= Decimal("0.1")

    # 9. Portfolio context checks
    if portfolio_context:
        existing = portfolio_context.get("existing_positions", [])
        underlying_count = sum(
            1 for p in existing if hasattr(p, "symbol") and proposal.underlying in str(getattr(p, "symbol", ""))
        )
        if underlying_count > 0:
            kill_reasons.append(f"Existing {proposal.underlying} position(s) in portfolio")
            score -= Decimal("0.15")

        buying_power = Decimal(str(portfolio_context.get("buying_power", 0)))
        if buying_power > 0 and proposal.max_loss > buying_power * Decimal("0.1"):
            kill_reasons.append(f"Max loss ({proposal.max_loss}) > 10% of buying power ({buying_power})")
            score -= Decimal("0.2")

    # Clamp score
    score = max(Decimal("0"), min(Decimal("1"), score))

    survives = score >= KILL_THRESHOLD

    analysis = (
        f"Kill score: {score:.2f} ({'SURVIVES' if survives else 'KILLED'}). "
        f"Found {len(kill_reasons)} issue(s)."
    )

    logger.info("Kill test: %s for %s %s", "PASS" if survives else "FAIL", proposal.underlying, proposal.strategy.value)

    return KillDecision(
        proposal_id=proposal.id,
        kill_score=score,
        kill_reasons=kill_reasons,
        survives=survives,
        confidence=Decimal("0.7"),
        analysis=analysis,
    )
