"""Deterministic risk engine — final veto authority.

These are configurable engineering defaults, NOT universal trading truths.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import RiskCheck, RiskDecision, TradeProposal

logger = logging.getLogger(__name__)

# ─── Configurable Risk Limits ────────────────────────────────────────────────
MAX_RISK_PER_TRADE = Decimal("500")         # max dollars at risk per trade
MAX_DAILY_LOSS = Decimal("1000")            # max daily portfolio loss
MAX_OPTIONS_EXPOSURE = Decimal("10000")     # max total options exposure
MAX_SINGLE_UNDERLYING_EXPOSURE = Decimal("3000")
MIN_REWARD_RISK = Decimal("1.5")            # minimum reward/risk ratio (was 1.0)
MIN_BUYING_POWER = Decimal("500")           # minimum buying power required
MAX_POSITIONS = 10                          # max concurrent positions
MIN_CONFIDENCE = Decimal("0.4")             # minimum proposal confidence (was 0.3)
MAX_IV_RANK = Decimal("70")                 # don't buy options when IV rank > 70%


def evaluate_risk(
    proposal: TradeProposal,
    buying_power: Decimal = Decimal("100000"),
    daily_pnl: Decimal = Decimal("0"),
    total_options_exposure: Decimal = Decimal("0"),
    current_positions: int = 0,
) -> RiskDecision:
    """Run the proposal through deterministic risk gates.

    Returns a RiskDecision with pass/fail for each check.
    The risk engine has FINAL VETO AUTHORITY.
    """
    checks: list[RiskCheck] = []
    metrics: dict = {
        "max_loss": float(proposal.max_loss),
        "max_profit": float(proposal.max_profit),
        "reward_risk": float(proposal.reward_risk),
        "buying_power": float(buying_power),
        "daily_pnl": float(daily_pnl),
        "total_options_exposure": float(total_options_exposure),
        "current_positions": current_positions,
    }

    # 1. Max risk per trade
    checks.append(RiskCheck(
        name="max_risk_per_trade",
        passed=proposal.max_loss <= MAX_RISK_PER_TRADE,
        value=float(proposal.max_loss),
        limit=float(MAX_RISK_PER_TRADE),
        reason=f"Max loss ${proposal.max_loss:.0f} {'OK' if proposal.max_loss <= MAX_RISK_PER_TRADE else '> limit ' + str(MAX_RISK_PER_TRADE)}",
    ))

    # 2. Daily loss limit
    remaining_daily = MAX_DAILY_LOSS + daily_pnl  # daily_pnl is negative when losing
    checks.append(RiskCheck(
        name="daily_loss_limit",
        passed=daily_pnl > -MAX_DAILY_LOSS,
        value=float(daily_pnl),
        limit=float(-MAX_DAILY_LOSS),
        reason=f"Daily P&L ${daily_pnl:.0f} {'OK' if daily_pnl > -MAX_DAILY_LOSS else 'exceeds daily loss limit'}",
    ))

    # 3. Total options exposure
    new_exposure = total_options_exposure + proposal.max_loss
    checks.append(RiskCheck(
        name="total_options_exposure",
        passed=new_exposure <= MAX_OPTIONS_EXPOSURE,
        value=float(new_exposure),
        limit=float(MAX_OPTIONS_EXPOSURE),
        reason=f"New exposure ${new_exposure:.0f} {'OK' if new_exposure <= MAX_OPTIONS_EXPOSURE else '> limit'}",
    ))

    # 4. Single underlying exposure
    checks.append(RiskCheck(
        name="single_underlying_exposure",
        passed=proposal.max_loss <= MAX_SINGLE_UNDERLYING_EXPOSURE,
        value=float(proposal.max_loss),
        limit=float(MAX_SINGLE_UNDERLYING_EXPOSURE),
        reason=f"Underlying risk ${proposal.max_loss:.0f} {'OK' if proposal.max_loss <= MAX_SINGLE_UNDERLYING_EXPOSURE else '> limit'}",
    ))

    # 5. Reward/risk ratio
    checks.append(RiskCheck(
        name="reward_risk_ratio",
        passed=proposal.reward_risk >= MIN_REWARD_RISK,
        value=float(proposal.reward_risk),
        limit=float(MIN_REWARD_RISK),
        reason=f"R/R {proposal.reward_risk:.2f} {'OK' if proposal.reward_risk >= MIN_REWARD_RISK else '< minimum ' + str(MIN_REWARD_RISK)}",
    ))

    # 6. Buying power
    checks.append(RiskCheck(
        name="buying_power",
        passed=buying_power >= MIN_BUYING_POWER + proposal.max_loss,
        value=float(buying_power),
        limit=float(MIN_BUYING_POWER + proposal.max_loss),
        reason=f"Buying power ${buying_power:.0f} {'OK' if buying_power >= MIN_BUYING_POWER + proposal.max_loss else 'insufficient'}",
    ))

    # 7. Position count
    checks.append(RiskCheck(
        name="max_positions",
        passed=current_positions < MAX_POSITIONS,
        value=current_positions,
        limit=MAX_POSITIONS,
        reason=f"Positions {current_positions} {'OK' if current_positions < MAX_POSITIONS else 'at maximum'}",
    ))

    # 8. Confidence
    checks.append(RiskCheck(
        name="min_confidence",
        passed=proposal.confidence >= MIN_CONFIDENCE,
        value=float(proposal.confidence),
        limit=float(MIN_CONFIDENCE),
        reason=f"Confidence {proposal.confidence:.2f} {'OK' if proposal.confidence >= MIN_CONFIDENCE else '< minimum ' + str(MIN_CONFIDENCE)}",
    ))

    # 9. IV Rank check — don't buy options when IV is high (overpaying for premium)
    iv_rank = Decimal(str(proposal.metadata.get("iv_rank", 50)) if proposal.metadata else 50)
    if proposal.legs and proposal.legs[0].side == "buy":
        checks.append(RiskCheck(
            name="iv_rank_check",
            passed=iv_rank <= MAX_IV_RANK,
            value=float(iv_rank),
            limit=float(MAX_IV_RANK),
            reason=f"IV rank {iv_rank:.0f}% {'OK' if iv_rank <= MAX_IV_RANK else '> ' + str(MAX_IV_RANK) + '% — overpaying for premium'}",
        ))

    failed = [c for c in checks if not c.passed]
    approved = len(failed) == 0
    reasons = [c.reason for c in failed]

    if not approved:
        logger.warning(
            "Risk REJECTED %s %s: %s",
            proposal.underlying,
            proposal.strategy.value,
            "; ".join(reasons),
        )
    else:
        logger.info(
            "Risk APPROVED %s %s (R/R: %s, Max loss: $%s)",
            proposal.underlying,
            proposal.strategy.value,
            proposal.reward_risk,
            proposal.max_loss,
        )

    return RiskDecision(
        proposal_id=proposal.id,
        approved=approved,
        checks=checks,
        failed_checks=failed,
        reasons=reasons,
        metrics=metrics,
    )
