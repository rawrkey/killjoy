"""LLM-backed Strategy Agent — LLM reasons about strategy selection.

Architecture:
  1. Deterministic strategy candidates from existing strategy classes
  2. LLM evaluates and selects the best strategy with reasoning
  3. Schema validation ensures structured output
  4. Deterministic fallback when LLM unavailable
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from killjoy.agent.models import MarketThesis, StrategyType, TradeProposal
from killjoy.agent.strategy_agent import generate_proposals as deterministic_proposals

if TYPE_CHECKING:
    from killjoy.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class LLMStrategyOutput(BaseModel):
    """Structured LLM output for strategy selection."""
    selected_strategy: str = Field(description="Selected strategy type")
    reasoning: str = Field(description="Why this strategy was selected")
    confidence_adjustment: float = Field(default=0, ge=-0.3, le=0.3, description="Confidence adjustment based on analysis")
    risk_notes: str = Field(default="", description="Key risks for this strategy")
    alternative_considered: str = Field(default="", description="Alternative strategy considered and why rejected")
    adjustments: dict[str, str] = Field(default_factory=dict, description="Suggested adjustments to proposal parameters")


STRATEGY_SYSTEM_PROMPT = """You are KILLJOY's Strategy Agent. You evaluate options strategy proposals for a given market thesis.

Your job is to:
1. Evaluate each proposed strategy
2. Select the best one with clear reasoning
3. Note key risks and adjustments
4. Provide confidence assessment

Consider: regime alignment, risk/reward, liquidity, time decay, Greeks.

Be specific. Reference the actual proposals and market conditions.

You MUST respond with valid JSON matching this exact schema:
{
  "selected_strategy": "long_call",
  "reasoning": "why this strategy was selected",
  "confidence_adjustment": 0.05,
  "risk_notes": "key risks",
  "alternative_considered": "alternative strategy considered",
  "adjustments": {}
}"""

# Map string names back to StrategyType for validation
_STRATEGY_MAP = {s.value: s for s in StrategyType}


def generate_proposals_llm(
    thesis: MarketThesis,
    contracts: list,
    spot: Decimal,
    llm: LLMProvider,
) -> list[TradeProposal]:
    """Generate trade proposals with LLM-enhanced strategy selection.

    Falls back to deterministic proposals when LLM is unavailable.
    """
    # Step 1: Deterministic candidate generation
    candidates = deterministic_proposals(thesis, contracts, spot)

    if not candidates:
        return []

    # Step 2: LLM reasoning (if available)
    if not llm.is_available:
        logger.debug("LLM unavailable, using deterministic proposals")
        return candidates

    # Build context
    context = _build_strategy_context(thesis, candidates, spot)

    messages = [
        {"role": "system", "content": STRATEGY_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]

    output, response = llm.chat_structured(
        messages,
        schema=LLMStrategyOutput,
        temperature=0.3,
        max_tokens=1024,
    )

    if output is None:
        logger.warning("LLM strategy failed, using deterministic: %s", response.error)
        return candidates

    # Step 3: Apply LLM selection and adjustments
    return _apply_llm_strategy(candidates, output)


def _build_strategy_context(
    thesis: MarketThesis,
    candidates: list[TradeProposal],
    spot: Decimal,
) -> str:
    """Build context string for LLM strategy evaluation."""
    lines = [
        f"Market Analysis for {thesis.underlying}:",
        f"  Regime: {thesis.regime.value}",
        f"  Confidence: {thesis.confidence}",
        f"  Momentum: {thesis.momentum}%",
        f"  Spot Price: ${spot}",
        f"  Thesis: {thesis.thesis}",
        "",
        "Observations:",
    ]
    for obs in thesis.observations:
        lines.append(f"  - {obs}")

    lines.extend(["", "Risks:"])
    for risk in thesis.risks:
        lines.append(f"  - {risk}")

    lines.extend(["", "PROPOSED STRATEGIES (from deterministic analysis):"])
    for i, p in enumerate(candidates, 1):
        lines.extend([
            f"",
            f"Strategy {i}: {p.strategy.value}",
            f"  Underlying: {p.underlying}",
            f"  Legs: {len(p.legs)}",
            f"  Max Loss: ${p.max_loss}",
            f"  Max Profit: ${p.max_profit}",
            f"  Reward/Risk: {p.reward_risk}",
            f"  Confidence: {p.confidence}",
            f"  Thesis: {p.thesis}",
            f"  Expiration: {p.expiration}",
        ])
        for leg in p.legs:
            lines.append(f"    {leg.side.upper()} {leg.contract_symbol} (strike: {leg.strike}, delta: {leg.delta})")

    lines.extend([
        "",
        "Evaluate these strategies. Select the BEST one and explain why.",
        "Consider regime alignment, risk/reward, Greeks, and market context.",
        "Respond with valid JSON only.",
    ])

    return "\n".join(lines)


def _apply_llm_strategy(
    candidates: list[TradeProposal],
    llm_output: LLMStrategyOutput,
) -> list[TradeProposal]:
    """Apply LLM selection and adjustments to candidate proposals."""
    # Find the selected strategy
    selected = None
    for p in candidates:
        if p.strategy.value == llm_output.selected_strategy:
            selected = p
            break

    if selected is None:
        # If LLM selected something not in candidates, use first candidate
        logger.warning(
            "LLM selected %s but it's not in candidates, using best deterministic",
            llm_output.selected_strategy,
        )
        selected = candidates[0]

    # Apply confidence adjustment
    adj = Decimal(str(llm_output.confidence_adjustment))
    selected.confidence = max(Decimal("0"), min(Decimal("1"), selected.confidence + adj))

    # Enrich thesis with LLM reasoning
    if llm_output.reasoning:
        selected.thesis = f"{selected.thesis}\n\nStrategy reasoning: {llm_output.reasoning}"
    if llm_output.risk_notes:
        selected.metadata["llm_risk_notes"] = llm_output.risk_notes
    if llm_output.alternative_considered:
        selected.metadata["llm_alternative"] = llm_output.alternative_considered

    # Re-sort: selected strategy first, then by confidence * reward_risk
    result = [selected]
    for p in candidates:
        if p.id != selected.id:
            result.append(p)

    return result
