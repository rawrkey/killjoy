"""LLM-backed Market Analyst — deterministic features + LLM reasoning.

Architecture:
  1. Deterministic feature extraction (price, volume, momentum, regime)
  2. LLM reasons on extracted features to produce thesis
  3. Schema validation ensures structured output
  4. Deterministic fallback when LLM unavailable

The LLM enhances analysis with contextual reasoning that rules cannot capture.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from killjoy.agent.analyst import analyze_market as deterministic_analyze
from killjoy.agent.models import MarketRegime, MarketThesis

if TYPE_CHECKING:
    from killjoy.alpaca.market_data import MarketDataClient
    from killjoy.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class LLMAnalystOutput(BaseModel):
    """Structured LLM output for market analysis."""
    regime: str = Field(description="Market regime: strong_uptrend, uptrend, sideways, downtrend, strong_downtrend, high_volatility, low_volatility")
    confidence: float = Field(ge=0, le=1, description="Confidence in the analysis")
    thesis: str = Field(description="Market thesis explanation")
    observations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    options_context: str = Field(default="", description="Options-specific market context")
    sentiment_signal: str = Field(default="neutral", description="bullish, bearish, neutral")
    key_levels: str = Field(default="", description="Key support/resistance levels mentioned")


ANALYST_SYSTEM_PROMPT = """You are KILLJOY's Market Analyst agent. You analyze stock market conditions and generate actionable trading theses.

You receive deterministic market features extracted from real market data. Your job is to:
1. Interpret the features in market context
2. Identify the dominant regime and its implications
3. Assess options-specific factors (IV, skew, term structure implications)
4. Generate a clear thesis with supporting observations and risks
5. Provide sentiment signal

Be specific and quantitative. Reference the actual numbers provided.
Do NOT make up data. Only reason about the features you receive.
Keep your analysis focused and actionable for options trading.

You must respond with valid JSON matching the schema provided."""


def analyze_market_llm(
    market_data: MarketDataClient,
    underlying: str,
    llm: LLMProvider,
) -> MarketThesis:
    """Analyze market with LLM-enhanced reasoning.

    Falls back to deterministic analysis when LLM is unavailable.
    """
    # Step 1: Deterministic feature extraction
    features = deterministic_analyze(market_data, underlying)

    # Step 2: LLM reasoning (if available)
    if not llm.is_available:
        logger.debug("LLM unavailable for %s, using deterministic analysis", underlying)
        return features

    # Build context from deterministic features
    feature_context = _build_feature_context(underlying, features)

    messages = [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": feature_context},
    ]

    output, response = llm.chat_structured(
        messages,
        schema=LLMAnalystOutput,
        temperature=0.3,
        max_tokens=512,
    )

    if output is None:
        logger.warning("LLM analyst failed for %s, using deterministic: %s", underlying, response.error)
        return features

    # Step 3: Merge LLM reasoning with deterministic features
    return _merge_analysis(features, output)


def _build_feature_context(underlying: str, features: MarketThesis) -> str:
    """Build a context string from deterministic features for the LLM."""
    return f"""Analyze market conditions for {underlying}:

DETERMINISTIC FEATURES (from real market data):
- Current Price: ${features.current_price}
- Regime: {features.regime.value}
- Confidence: {features.confidence}
- Momentum: {features.momentum}%
- Trend Strength: {features.trend_strength}%
- Volume Signal: {features.volume_signal}
- IV Rank (estimated): {features.iv_rank}

OBSERVATIONS:
{chr(10).join(f"  - {obs}" for obs in features.observations) if features.observations else "  None"}

IDENTIFIED RISKS:
{chr(10).join(f"  - {risk}" for risk in features.risks) if features.risks else "  None"}

Based on these features, provide your analysis. Consider:
1. Is the regime assessment correct? Any nuances?
2. What does the momentum and volume suggest about near-term direction?
3. What options strategies would be most appropriate?
4. What are the key risks for options traders?
5. What is your overall sentiment signal?

Respond with valid JSON only."""


def _merge_analysis(deterministic: MarketThesis, llm_output: LLMAnalystOutput) -> MarketThesis:
    """Merge LLM reasoning with deterministic features.

    Deterministic features are primary for quantitative values.
    LLM enhances with qualitative reasoning and context.
    """
    # Use deterministic regime but allow LLM to suggest refinement
    regime = deterministic.regime
    try:
        llm_regime = MarketRegime(llm_output.regime)
        # Only override if LLM has higher confidence
        if llm_output.confidence > float(deterministic.confidence):
            regime = llm_regime
    except (ValueError, KeyError):
        pass

    # Merge observations: deterministic first, then LLM additions
    observations = list(deterministic.observations)
    if llm_output.options_context:
        observations.append(f"Options context: {llm_output.options_context}")
    if llm_output.key_levels:
        observations.append(f"Key levels: {llm_output.key_levels}")

    # Merge risks
    risks = list(deterministic.risks)
    for risk in llm_output.risks:
        if risk not in risks:
            risks.append(risk)

    # Use LLM thesis if provided, otherwise enhance deterministic
    thesis = llm_output.thesis if llm_output.thesis else deterministic.thesis
    if llm_output.sentiment_signal != "neutral":
        thesis = f"[{llm_output.sentiment_signal.upper()}] {thesis}"

    # Use the higher confidence
    confidence = max(deterministic.confidence, Decimal(str(llm_output.confidence)))

    return MarketThesis(
        underlying=deterministic.underlying,
        regime=regime,
        confidence=confidence,
        thesis=thesis,
        observations=observations,
        risks=risks,
        current_price=deterministic.current_price,
        iv_rank=deterministic.iv_rank,
        trend_strength=deterministic.trend_strength,
        momentum=deterministic.momentum,
        volume_signal=deterministic.volume_signal,
    )
