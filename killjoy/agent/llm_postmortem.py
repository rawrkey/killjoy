"""LLM-backed Postmortem Agent — deep trade analysis with learning.

Architecture:
  1. Deterministic outcome extraction (P&L, win/loss, kill accuracy)
  2. LLM reasons about what happened, why, and what to learn
  3. Schema validation
  4. Bounded parameter recommendations
  5. Deterministic fallback
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from killjoy.agent.models import Postmortem, TradeJournalEntry
from killjoy.agent.postmortem_agent import run_postmortem as deterministic_postmortem

if TYPE_CHECKING:
    from killjoy.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class LLMPostmortemOutput(BaseModel):
    """Structured LLM output for trade postmortem."""
    thesis_correct: bool | None = Field(default=None, description="Was the original thesis correct?")
    thesis_analysis: str = Field(default="", description="Analysis of thesis correctness")
    execution_quality: str = Field(default="", description="Was the execution good? Entry/exit timing, etc.")
    kill_agent_accuracy: bool | None = Field(default=None, description="Was the Kill Agent's assessment accurate?")
    kill_agent_analysis: str = Field(default="", description="Analysis of Kill Agent performance")
    what_actually_happened: str = Field(default="", description="What actually happened in the market")
    root_cause: str = Field(default="", description="Root cause of win/loss")
    improvements: list[str] = Field(default_factory=list, description="Specific improvements for future trades")
    lessons: list[str] = Field(default_factory=list, description="Lessons learned")
    parameter_recommendations: dict[str, str] = Field(default_factory=dict, description="Bounded parameter recommendations")
    grade: str = Field(default="", description="Trade grade: A, B, C, D, F")


POSTMORTEM_SYSTEM_PROMPT = """You are KILLJOY's Postmortem Agent. You analyze completed trades to extract insights and improve future performance.

For each trade, you must:
1. Analyze whether the original thesis was correct
2. Evaluate execution quality (entry, exit, timing)
3. Assess whether the Kill Agent's assessment was accurate
4. Identify what actually happened vs what was expected
5. Determine root cause of the outcome
6. Extract specific, actionable improvements
7. Generate bounded parameter recommendations

Be honest and specific. Reference actual data:
- Original thesis and market context
- Kill Agent's objections and score
- Entry/exit prices and timing
- Realized P&L
- What the market actually did

Do NOT be vague. "Do better next time" is not an acceptable lesson.
Every lesson must be specific and implementable.

Parameter recommendations must be BOUNDED:
- Preferred DTE range (e.g., 14-30 days)
- Preferred IV regime (e.g., 30-50 IV rank)
- Minimum reward/risk (e.g., 1.5)
- Strategy preference adjustment
- Confidence threshold adjustment

You must respond with valid JSON matching the schema provided."""


def run_postmortem_llm(
    entry: TradeJournalEntry,
    llm: LLMProvider | None = None,
) -> Postmortem:
    """Run postmortem analysis with LLM reasoning.

    Falls back to deterministic postmortem when LLM is unavailable.
    """
    # Step 1: Deterministic baseline
    deterministic_result = deterministic_postmortem(entry)

    # Step 2: LLM reasoning (if available)
    if llm is None or not llm.is_available:
        logger.debug("LLM unavailable for postmortem, using deterministic")
        return deterministic_result

    # Build context
    context = _build_postmortem_context(entry)

    messages = [
        {"role": "system", "content": POSTMORTEM_SYSTEM_PROMPT},
        {"role": "user", "content": context},
    ]

    output, response = llm.chat_structured(
        messages,
        schema=LLMPostmortemOutput,
        temperature=0.3,
        max_tokens=2048,
    )

    if output is None:
        logger.warning("LLM postmortem failed, using deterministic: %s", response.error)
        return deterministic_result

    # Step 3: Merge LLM analysis with deterministic results
    return _merge_postmortem(deterministic_result, output)


def _build_postmortem_context(entry: TradeJournalEntry) -> str:
    """Build context string for LLM postmortem analysis."""
    lines = [
        "=== TRADE POSTMORTEM ANALYSIS ===",
        "",
        f"Trade ID: {entry.trade_id}",
        f"Underlying: {entry.underlying}",
        f"Strategy: {entry.strategy}",
        f"Original Thesis: {entry.thesis}",
        f"Confidence at Entry: {entry.confidence}",
        f"Kill Score at Entry: {entry.kill_score}",
        "",
        "Kill Agent Objections:",
    ]

    for reason in entry.kill_reasons:
        lines.append(f"  - {reason}")

    lines.extend([
        "",
        f"Realized P&L: ${entry.realized_pnl}",
        f"Result: {entry.result}",
        "",
    ])

    if entry.legs:
        lines.append("Legs:")
        for leg in entry.legs:
            lines.append(f"  {leg.side.upper()} {leg.contract_symbol} (strike: {leg.strike})")

    if entry.risk_decision:
        lines.extend([
            "Risk Decision:",
            f"  Approved: {entry.risk_decision.approved}",
            f"  Failed checks: {len(entry.risk_decision.failed_checks)}",
        ])

    lines.extend([
        "",
        "=== YOUR TASK ===",
        "Analyze this trade in depth. Be specific and honest.",
        "What happened? Was the thesis correct? Was the Kill Agent right?",
        "What should change for future trades?",
        "Respond with valid JSON only.",
    ])

    return "\n".join(lines)


def _merge_postmortem(
    deterministic: Postmortem,
    llm_output: LLMPostmortemOutput,
) -> Postmortem:
    """Merge LLM analysis with deterministic results."""
    # Use LLM's thesis correctness if provided
    thesis_correct = llm_output.thesis_correct if llm_output.thesis_correct is not None else deterministic.thesis_correct

    # Use LLM's kill agent accuracy if provided
    kill_accurate = llm_output.kill_agent_accuracy if llm_output.kill_agent_accuracy is not None else deterministic.kill_agent_accurate

    # Merge improvements and lessons
    improvements = list(deterministic.improvements)
    for imp in llm_output.improvements:
        if imp not in improvements:
            improvements.append(imp)

    lessons = list(deterministic.lessons)
    for lesson in llm_output.lessons:
        if lesson not in lessons:
            lessons.append(lesson)

    # Build LLM analysis string
    llm_analysis_parts = []
    if llm_output.thesis_analysis:
        llm_analysis_parts.append(f"Thesis: {llm_output.thesis_analysis}")
    if llm_output.execution_quality:
        llm_analysis_parts.append(f"Execution: {llm_output.execution_quality}")
    if llm_output.what_actually_happened:
        llm_analysis_parts.append(f"Market: {llm_output.what_actually_happened}")
    if llm_output.root_cause:
        llm_analysis_parts.append(f"Root cause: {llm_output.root_cause}")
    if llm_output.grade:
        llm_analysis_parts.append(f"Grade: {llm_output.grade}")

    # Add parameter recommendations to lessons
    if llm_output.parameter_recommendations:
        for param, value in llm_output.parameter_recommendations.items():
            lessons.append(f"Parameter: {param} -> {value}")

    return Postmortem(
        trade_id=deterministic.trade_id,
        underlying=deterministic.underlying,
        strategy=deterministic.strategy,
        original_thesis=deterministic.original_thesis,
        actual_outcome=deterministic.actual_outcome,
        thesis_correct=thesis_correct,
        win_loss=deterministic.win_loss,
        realized_pnl=deterministic.realized_pnl,
        kill_agent_accurate=kill_accurate,
        improvements=improvements,
        lessons=lessons,
        llm_analysis="\n".join(llm_analysis_parts),
    )
