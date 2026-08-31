"""LLM-backed Kill Agent — genuine adversarial testing with structured debate.

This is the defining feature of KILLJOY. The Kill Agent:

  1. Receives comprehensive trade context
  2. Tries to DISPROVE the trade with structured objections
  3. Engages in adversarial debate with the Strategy Agent
  4. Produces a dynamic Kill Score based on severity and confidence of objections

Architecture:
  1. Deterministic pre-screening (fast rejection of obvious failures)
  2. LLM adversarial reasoning (deep analysis)
  3. Adversarial debate (Trader vs Kill Agent)
  4. Dynamic Kill Score computation
  5. Schema validation
  6. Deterministic fallback

Kill Score Semantics (consistent everywhere):
  0.00 - 0.20: KILL — Major red flags, trade should not proceed
  0.20 - 0.40: WEAK — Significant concerns, rejected by threshold
  0.40 - 0.60: MARGINAL — Some concerns, passes threshold but risky
  0.60 - 0.80: DECENT — Minor concerns, acceptable
  0.80 - 1.00: STRONG — Few or no concerns, should proceed

Threshold: 0.55 — trades below this score are killed.

The final execution decision remains deterministic.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from killjoy.agent.kill_agent import kill_test as deterministic_kill
from killjoy.agent.models import (
    KillDecision,
    KillObjection,
    MarketThesis,
    TradeProposal,
)

if TYPE_CHECKING:
    from killjoy.llm.provider import LLMProvider

logger = logging.getLogger(__name__)

KILL_THRESHOLD = Decimal("0.55")


class LLMKillOutput(BaseModel):
    """Structured LLM output for kill decision."""
    kill_score: float = Field(ge=0, le=1, description="0=trade is dangerous, 1=trade is safe")
    survives: bool = Field(description="Whether the trade should proceed")
    confidence: float = Field(ge=0, le=1, description="Confidence in the kill decision")
    objections: list[dict] = Field(default_factory=list, description="List of {category, severity, reasoning, counterfactual}")
    critical_failures: list[str] = Field(default_factory=list, description="Fatal issues that should kill the trade")
    counterfactual: str = Field(default="", description="What would need to change for this trade to survive")
    recommendation: str = Field(default="", description="kill, marginal, or approve")
    analysis: str = Field(default="", description="Overall analysis")


KILL_SYSTEM_PROMPT = """You are KILLJOY's Kill Agent. Your EXPLICIT OBJECTIVE is to DISPROVE every trade proposal.

You are NOT a cheerleader. You are a skeptical risk analyst whose job is to find reasons to REJECT trades.

For every proposal, you must:
1. Identify specific weaknesses in the thesis
2. Challenge assumptions about market direction
3. Question timing and expiration choices
4. Assess IV risk and options structure
5. Evaluate reward/risk honestly
6. Check portfolio conflicts
7. Look for event risk, liquidity risk, regime mismatch

Your objections must be structured with:
- category: thesis_weakness, timing_risk, iv_risk, event_risk, liquidity_risk, poor_reward_risk, portfolio_correlation, concentration, market_regime_mismatch, unfavorable_structure, asymmetric_downside, missing_confirmation
- severity: 0.0 (minor) to 1.0 (critical)
- reasoning: Detailed explanation
- counterfactual: What would need to be true for this objection to not apply

Be genuinely adversarial. The best Kill Agent catches real problems.
If a trade is actually good, say so — but make it prove itself.

Kill Score calculation:
- Start at 0.5 (neutral)
- Each objection reduces score by its severity * 0.1 to 0.3
- Critical failures reduce by 0.3 to 0.5
- Good risk/reward adds 0.05 to 0.1
- Strong thesis alignment adds 0.05 to 0.1

You must respond with valid JSON matching the schema provided."""

DEBATE_KILL_PROMPT = """You are KILLJOY's Kill Agent in round {round} of an adversarial debate.

The Trader has responded to your objections. Your job is to:
1. Evaluate their defense honestly
2. Identify any remaining weaknesses
3. Acknowledge valid counterarguments
4. Maintain your adversarial stance — don't fold easily
5. Update your kill score based on the defense

Be rigorous. A good debate improves the final decision.
If the Trader convincingly addresses your concerns, adjust your score upward.
If they dodge or give weak responses, maintain or increase your kill score.

You must respond with valid JSON matching the schema provided."""

TRADER_DEBATE_PROMPT = """You are KILLJOY's Trader/Strategy Agent defending your trade proposal.

The Kill Agent has raised objections. Your job is to:
1. Address each objection specifically
2. Provide counterarguments with evidence
3. Acknowledge genuine risks but explain why they're acceptable
4. Defend your thesis with conviction
5. Be honest — if an objection is valid, concede it

This is an adversarial debate. Be specific and quantitative.
Vague defenses like "the trend looks strong" are not acceptable.
Reference actual data: momentum, volume, IV, Greeks, reward/risk.

You must respond with valid JSON matching the schema provided."""


class TraderDefense(BaseModel):
    """Trader's defense in the adversarial debate."""
    responses: list[dict] = Field(default_factory=list, description="Response to each objection: {objection_category, response, concession: bool}")
    overall_defense: str = Field(description="Overall defense of the trade")
    conceded_points: list[str] = Field(default_factory=list, description="Points conceded to Kill Agent")
    adjusted_confidence: float = Field(ge=0, le=1, description="Updated confidence after hearing objections")


def kill_test_llm(
    proposal: TradeProposal,
    thesis: MarketThesis,
    portfolio_context: dict | None = None,
    llm: LLMProvider | None = None,
) -> KillDecision:
    """Run adversarial kill test with LLM reasoning and debate.

    Falls back to deterministic kill test when LLM is unavailable.
    """
    # Step 1: Deterministic pre-screening
    deterministic_result = deterministic_kill(proposal, thesis, portfolio_context)

    # If deterministic already kills it hard, don't waste LLM tokens
    if deterministic_result.kill_score < Decimal("0.2"):
        logger.info("Deterministic pre-screen killed %s %s (score: %s)", proposal.underlying, proposal.strategy.value, deterministic_result.kill_score)
        return KillDecision(
            proposal_id=proposal.id,
            kill_score=deterministic_result.kill_score,
            survives=False,
            confidence=Decimal("0.9"),
            critical_failures=deterministic_result.kill_reasons,
            analysis=f"Deterministic pre-screen rejected: {'; '.join(deterministic_result.kill_reasons)}",
            kill_reasons=deterministic_result.kill_reasons,
            recommendation="kill",
        )

    # Step 2: LLM adversarial analysis
    if llm is None or not llm.is_available:
        logger.debug("LLM unavailable for kill test, using deterministic")
        return _enrich_with_model_fields(deterministic_result)

    # Build comprehensive context for kill agent
    context = _build_kill_context(proposal, thesis, portfolio_context)

    messages = [
        {"role": "system", "content": KILL_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]

    output, response = llm.chat_structured(
        messages,
        schema=LLMKillOutput,
        temperature=0.4,
        max_tokens=1024,
    )

    if output is None:
        logger.warning("LLM kill failed, using deterministic: %s", response.error)
        return _enrich_with_model_fields(deterministic_result)

    # Step 3: Skip debate for speed (cron timeout = 30s)
    debate_transcript = []

    # Step 4: Compute final kill score
    final_kill_score = _compute_kill_score(output, debate_transcript)

    # Step 5: Convert objections to KillObjection objects
    objections = _parse_objections(output.objections)
    survives = final_kill_score >= KILL_THRESHOLD

    return KillDecision(
        proposal_id=proposal.id,
        kill_score=final_kill_score,
        survives=survives,
        confidence=Decimal(str(output.confidence)),
        objections=objections,
        critical_failures=output.critical_failures,
        counterfactual=output.counterfactual,
        recommendation=output.recommendation or ("approve" if survives else "kill"),
        analysis=output.analysis,
        debate_transcript=debate_transcript,
        kill_reasons=[f"[{o.category}] {o.reasoning}" for o in objections],
    )


def _build_kill_context(
    proposal: TradeProposal,
    thesis: MarketThesis,
    portfolio_context: dict | None,
) -> str:
    """Build comprehensive context for the Kill Agent."""
    lines = [
        "=== TRADE PROPOSAL TO DISPROVE ===",
        "",
        f"Underlying: {proposal.underlying}",
        f"Strategy: {proposal.strategy.value}",
        f"Thesis: {proposal.thesis}",
        f"Confidence: {proposal.confidence}",
        f"Expiration: {proposal.expiration}",
        f"Max Loss: ${proposal.max_loss}",
        f"Max Profit: ${proposal.max_profit}",
        f"Reward/Risk: {proposal.reward_risk}",
        f"Legs: {len(proposal.legs)}",
        "",
    ]

    for i, leg in enumerate(proposal.legs, 1):
        lines.extend([
            f"Leg {i}: {leg.side.upper()} {leg.contract_symbol}",
            f"  Strike: {leg.strike}, Delta: {leg.delta}",
            f"  Bid: {leg.bid}, Ask: {leg.ask}, Mid: {leg.mid}",
            "",
        ])

    lines.extend([
        "=== MARKET CONTEXT ===",
        f"Regime: {thesis.regime.value}",
        f"Current Price: ${thesis.current_price}",
        f"Momentum: {thesis.momentum}%",
        f"Volume Signal: {thesis.volume_signal}",
        f"IV Rank: {thesis.iv_rank}",
        "",
        "Observations:",
    ])
    for obs in thesis.observations:
        lines.append(f"  - {obs}")

    lines.extend(["", "Risks:"])
    for risk in thesis.risks:
        lines.append(f"  - {risk}")

    if portfolio_context:
        lines.extend([
            "",
            "=== PORTFOLIO CONTEXT ===",
            f"Buying Power: ${portfolio_context.get('buying_power', 0)}",
            f"Portfolio Value: ${portfolio_context.get('portfolio_value', 0)}",
            f"Open Positions: {portfolio_context.get('position_count', 0)}",
        ])
        existing = portfolio_context.get("existing_positions", [])
        if existing:
            lines.append("Existing positions:")
            for pos in existing[:5]:
                sym = getattr(pos, "symbol", "") if hasattr(pos, "symbol") else pos.get("symbol", "")
                pnl = getattr(pos, "unrealized_pl", 0) if hasattr(pos, "unrealized_pl") else 0
                lines.append(f"  - {sym}: P&L ${pnl}")

    lines.extend([
        "",
        "=== YOUR TASK ===",
        "Try to DISPROVE this trade. Find every weakness.",
        "Be genuinely adversarial. The trade must earn your approval.",
        "Respond with valid JSON only.",
    ])

    return "\n".join(lines)


def _run_debate(
    proposal: TradeProposal,
    thesis: MarketThesis,
    kill_output: LLMKillOutput,
    llm: LLMProvider,
    max_rounds: int = 2,
) -> list[dict[str, str]]:
    """Run adversarial debate between Trader and Kill Agent.

    Returns debate transcript as list of {role, content} messages.
    """
    transcript: list[dict[str, str]] = []

    # Initial kill agent statement
    if kill_output.objections:
        initial_objections = "; ".join(
            f"[{o.get('category', 'unknown')}] {o.get('reasoning', '')}"
            for o in kill_output.objections[:5]
        )
        transcript.append({
            "role": "kill_agent",
            "content": f"KILL AGENT OBJECTIONS:\n{initial_objections}\n\nKill Score: {kill_output.kill_score}\nRecommendation: {kill_output.recommendation}",
        })

    # Trader defense
    trader_messages = [
        {"role": "system", "content": TRADER_DEBATE_PROMPT},
        {"role": "user", "content": _build_trader_defense_context(proposal, thesis, kill_output)},
    ]

    trader_output, _ = llm.chat_structured(
        trader_messages,
        schema=TraderDefense,
        temperature=0.3,
        max_tokens=512,
    )

    if trader_output:
        transcript.append({
            "role": "trader",
            "content": f"TRADER DEFENSE:\n{trader_output.overall_defense}\n\nConceded: {', '.join(trader_output.conceded_points) if trader_output.conceded_points else 'None'}",
        })

        # Kill Agent response (1 more round)
        for round_num in range(2, max_rounds + 1):
            kill_messages = [
                {"role": "system", "content": DEBATE_KILL_PROMPT.format(round=round_num)},
                {"role": "user", "content": _build_kill_response_context(kill_output, trader_output, proposal)},
            ]

            kill_response, _ = llm.chat_structured(
                kill_messages,
                schema=LLMKillOutput,
                temperature=0.4,
                max_tokens=512,
            )

            if kill_response:
                transcript.append({
                    "role": "kill_agent",
                    "content": f"KILL AGENT (Round {round_num}):\n{kill_response.analysis}\n\nUpdated Kill Score: {kill_response.kill_score}",
                })
                # Update kill output with latest score
                kill_output.kill_score = kill_response.kill_score
                kill_output.confidence = kill_response.confidence
                break

    return transcript


def _build_trader_defense_context(
    proposal: TradeProposal,
    thesis: MarketThesis,
    kill_output: LLMKillOutput,
) -> str:
    """Build context for the Trader's defense."""
    lines = [
        "=== YOUR TRADE PROPOSAL ===",
        f"Underlying: {proposal.underlying}",
        f"Strategy: {proposal.strategy.value}",
        f"Thesis: {proposal.thesis}",
        f"Reward/Risk: {proposal.reward_risk}",
        f"Max Loss: ${proposal.max_loss}",
        f"Max Profit: ${proposal.max_profit}",
        "",
        "=== MARKET CONTEXT ===",
        f"Regime: {thesis.regime.value}",
        f"Momentum: {thesis.momentum}%",
        f"Current Price: ${thesis.current_price}",
        "",
        "=== KILL AGENT OBJECTIONS ===",
    ]

    for i, obj in enumerate(kill_output.objections, 1):
        lines.extend([
            f"Objection {i} [{obj.get('category', 'unknown')}] (severity: {obj.get('severity', '?')}):",
            f"  {obj.get('reasoning', '')}",
            f"  Counterfactual: {obj.get('counterfactual', '')}",
            "",
        ])

    if kill_output.critical_failures:
        lines.extend(["CRITICAL FAILURES:"] + [f"  - {f}" for f in kill_output.critical_failures])

    lines.extend([
        "",
        "Defend your trade. Address each objection specifically.",
        "Be quantitative. Reference actual data.",
        "Concede points that are genuinely valid.",
        "Respond with valid JSON only.",
    ])

    return "\n".join(lines)


def _build_kill_response_context(
    kill_output: LLMKillOutput,
    trader_output: TraderDefense,
    proposal: TradeProposal,
) -> str:
    """Build context for the Kill Agent's response to Trader's defense."""
    lines = [
        "=== TRADER'S DEFENSE ===",
        trader_output.overall_defense,
        "",
        "=== TRADER'S RESPONSES TO OBJECTIONS ===",
    ]

    for resp in trader_output.responses:
        lines.extend([
            f"[{resp.get('objection_category', 'unknown')}]",
            f"  Response: {resp.get('response', '')}",
            f"  Conceded: {resp.get('concession', False)}",
            "",
        ])

    if trader_output.conceded_points:
        lines.extend(["CONCEDED POINTS:"] + [f"  - {p}" for p in trader_output.conceded_points])

    lines.extend([
        "",
        "=== YOUR ASSESSMENT ===",
        f"Your original kill score: {kill_output.kill_score}",
        f"Your original recommendation: {kill_output.recommendation}",
        "",
        "Evaluate the Trader's defense. Update your kill score.",
        "If they addressed your concerns, adjust upward.",
        "If they dodged or gave weak responses, maintain or increase your score.",
        "Respond with valid JSON only.",
    ])

    return "\n".join(lines)


def _compute_kill_score(
    llm_output: LLMKillOutput,
    debate_transcript: list[dict[str, str]],
) -> Decimal:
    """Compute the final kill score from LLM output and debate.

    The LLM provides an initial score. The debate may adjust it.
    We apply deterministic bounds to prevent extreme scores.
    """
    score = Decimal(str(llm_output.kill_score))

    # Apply deterministic bounds
    # If there are critical failures, cap the score
    if llm_output.critical_failures:
        max_score = Decimal("0.3")  # Critical failures cap at 0.3
        score = min(score, max_score)

    # If there are many high-severity objections, cap the score
    high_severity_count = sum(
        1 for o in llm_output.objections
        if o.get("severity", 0) and Decimal(str(o["severity"])) > Decimal("0.7")
    )
    if high_severity_count >= 3:
        score = min(score, Decimal("0.3"))
    elif high_severity_count >= 2:
        score = min(score, Decimal("0.5"))

    # Ensure score is in valid range
    score = max(Decimal("0"), min(Decimal("1"), score))

    return score


def _parse_objections(raw_objections: list[dict]) -> list[KillObjection]:
    """Parse raw LLM objection dicts into KillObjection objects."""
    objections = []
    for raw in raw_objections:
        try:
            objections.append(KillObjection(
                category=raw.get("category", "unknown"),
                severity=Decimal(str(raw.get("severity", 0.5))),
                reasoning=raw.get("reasoning", ""),
                counterfactual=raw.get("counterfactual", ""),
            ))
        except Exception as e:
            logger.debug("Failed to parse objection: %s", e)
    return objections


def _enrich_with_model_fields(result: KillDecision) -> KillDecision:
    """Enrich a deterministic KillDecision with new model fields."""
    # Convert kill_reasons to objections if empty
    if not result.objections and result.kill_reasons:
        objections = []
        for reason in result.kill_reasons:
            objections.append(KillObjection(
                category="deterministic_check",
                severity=Decimal("0.5"),
                reasoning=reason,
            ))
        result.objections = objections
    return result
