"""Typed, provider-neutral models used across KILLJOY."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Account / Position snapshots
# ---------------------------------------------------------------------------

class AccountSnapshot(BaseModel):
    status: str
    buying_power: Decimal
    portfolio_value: Decimal
    equity: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    day_trade_count: int = 0


class PositionSnapshot(BaseModel):
    symbol: str
    quantity: Decimal = Field(alias="qty")
    side: str = ""
    avg_entry_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")
    unrealized_pl: Decimal = Decimal("0")
    unrealized_plpc: Decimal = Decimal("0")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class OptionContract(BaseModel):
    symbol: str
    underlying: str
    strike: Decimal
    expiration: date
    option_type: OptionType
    bid: Decimal = Decimal("0")
    ask: Decimal = Decimal("0")
    mid: Decimal = Decimal("0")
    last: Decimal = Decimal("0")
    volume: int = 0
    open_interest: int = 0
    implied_volatility: Decimal = Decimal("0")
    delta: Decimal = Decimal("0")
    gamma: Decimal = Decimal("0")
    theta: Decimal = Decimal("0")
    vega: Decimal = Decimal("0")


class OptionLeg(BaseModel):
    contract_symbol: str
    option_type: OptionType
    strike: Decimal
    expiration: date
    side: str  # "buy" or "sell"
    quantity: int = 1
    bid: Decimal = Decimal("0")
    ask: Decimal = Decimal("0")
    mid: Decimal = Decimal("0")
    delta: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Strategy / Trade
# ---------------------------------------------------------------------------

class StrategyType(str, Enum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    IRON_CONDOR = "iron_condor"


class MarketRegime(str, Enum):
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    SIDEWAYS = "sideways"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class MarketThesis(BaseModel):
    underlying: str
    regime: MarketRegime
    confidence: Decimal = Field(ge=0, le=1, default=Decimal("0.5"))
    thesis: str = ""
    observations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    current_price: Decimal = Decimal("0")
    iv_rank: Decimal = Decimal("0")
    trend_strength: Decimal = Decimal("0")
    momentum: Decimal = Decimal("0")
    volume_signal: str = "neutral"


class TradeProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    underlying: str
    strategy: StrategyType
    legs: list[OptionLeg]
    expiration: date
    max_loss: Decimal
    max_profit: Decimal
    reward_risk: Decimal = Decimal("0")
    confidence: Decimal = Field(ge=0, le=1, default=Decimal("0.5"))
    thesis: str = ""
    kill_score: Decimal = Field(ge=0, le=1, default=Decimal("0"))
    kill_reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Kill Agent
# ---------------------------------------------------------------------------

class KillObjection(BaseModel):
    """A structured objection raised by the Kill Agent."""
    category: str = Field(description="thesis_weakness, timing_risk, iv_risk, event_risk, liquidity_risk, poor_reward_risk, portfolio_correlation, concentration, market_regime_mismatch, unfavorable_structure, asymmetric_downside, missing_confirmation")
    severity: Decimal = Field(ge=0, le=1, description="0=minor concern, 1=critical failure")
    reasoning: str = Field(description="Detailed explanation of this objection")
    counterfactual: str = Field(default="", description="What would need to be true for this objection to not apply")


class KillDecision(BaseModel):
    """Structured output from the Kill Agent.

    Kill Score Semantics (consistent everywhere):
      0.00 - 0.20: KILL — Major red flags, trade should not proceed
      0.20 - 0.40: WEAK — Significant concerns, likely reject
      0.40 - 0.60: MARGINAL — Some concerns, proceed with caution
      0.60 - 0.80: DECENT — Minor concerns, acceptable
      0.80 - 1.00: STRONG — Few or no concerns, should proceed

    Survival Score = 1 - Kill Score (exposed for dashboard/analytics)
    """
    proposal_id: str
    kill_score: Decimal = Field(ge=0, le=1, description="0=trade is dangerous, 1=trade is safe")
    survives: bool = False
    confidence: Decimal = Field(ge=0, le=1, default=Decimal("0.5"))
    objections: list[KillObjection] = Field(default_factory=list)
    critical_failures: list[str] = Field(default_factory=list)
    counterfactual: str = Field(default="", description="What would need to change for this trade to survive")
    recommendation: str = Field(default="", description="kill, marginal, or approve")
    analysis: str = ""
    debate_transcript: list[dict[str, str]] = Field(default_factory=list, description="Adversarial debate transcript")
    # Legacy field for backward compatibility
    kill_reasons: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------

class RiskCheck(BaseModel):
    name: str
    passed: bool
    value: Any = None
    limit: Any = None
    reason: str = ""


class RiskDecision(BaseModel):
    proposal_id: str
    approved: bool
    checks: list[RiskCheck] = Field(default_factory=list)
    failed_checks: list[RiskCheck] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

class OrderResult(BaseModel):
    order_id: str = ""
    client_order_id: str = ""
    status: str = "pending"
    filled_avg_price: Decimal = Decimal("0")
    filled_qty: Decimal = Decimal("0")
    symbol: str = ""
    side: str = ""
    type: str = ""
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    error: str = ""


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------

class PortfolioCheck(BaseModel):
    approved: bool
    reasons: list[str] = Field(default_factory=list)
    concentration: dict[str, Decimal] = Field(default_factory=dict)
    total_options_exposure: Decimal = Decimal("0")
    buying_power_available: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Postmortem
# ---------------------------------------------------------------------------

class Postmortem(BaseModel):
    trade_id: str
    underlying: str
    strategy: str
    original_thesis: str = ""
    actual_outcome: str = ""
    thesis_correct: bool | None = None
    win_loss: str = ""  # "win", "loss", "breakeven"
    realized_pnl: Decimal = Decimal("0")
    kill_agent_accurate: bool | None = None
    improvements: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    llm_analysis: str = Field(default="", description="LLM-generated postmortem analysis")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Rejected Trade ("Why Not Trade?")
# ---------------------------------------------------------------------------

class RejectedTrade(BaseModel):
    """Persisted record of a rejected trade opportunity."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    underlying: str = ""
    thesis: str = ""
    proposed_strategy: str = ""
    kill_score: Decimal = Decimal("0")
    survives: bool = False
    objections: list[KillObjection] = Field(default_factory=list)
    critical_failures: list[str] = Field(default_factory=list)
    risk_failures: list[str] = Field(default_factory=list)
    portfolio_failures: list[str] = Field(default_factory=list)
    rejection_reason: str = ""
    debate_transcript: list[dict[str, str]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Trade Journal Entry
# ---------------------------------------------------------------------------

class TradeJournalEntry(BaseModel):
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    underlying: str = ""
    strategy: str = ""
    legs: list[OptionLeg] = Field(default_factory=list)
    thesis: str = ""
    confidence: Decimal = Decimal("0")
    kill_score: Decimal = Decimal("0")
    kill_reasons: list[str] = Field(default_factory=list)
    risk_decision: RiskDecision | None = None
    order_result: OrderResult | None = None
    exit_order: OrderResult | None = None
    realized_pnl: Decimal = Decimal("0")
    result: str = ""  # "open", "win", "loss", "breakeven", "closed"
    postmortem: Postmortem | None = None


# ---------------------------------------------------------------------------
# Decision Receipt
# ---------------------------------------------------------------------------

class DecisionReceipt(BaseModel):
    """Machine-readable audit trail for every trade decision."""
    receipt_id: str = Field(default_factory=lambda: f"KJ-{str(uuid.uuid4())[:8].upper()}")
    trade_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    underlying: str = ""
    strategy: str = ""
    thesis: str = ""
    confidence: Decimal = Decimal("0")
    kill_score: Decimal = Decimal("0")
    survives_kill: bool = False
    portfolio_check: bool = False
    risk_check: bool = False
    final_decision: str = ""  # "EXECUTE", "KILLED", "PORTFOLIO_REJECTED", "RISK_REJECTED"
    kill_reasons: list[str] = Field(default_factory=list)
    counterfactual: str = ""
    portfolio_reasons: list[str] = Field(default_factory=list)
    risk_reasons: list[str] = Field(default_factory=list)
    order_id: str = ""
    alpaca_status: str = ""
    agent_scores: dict[str, Decimal] = Field(default_factory=dict)
    debate_rounds: int = 0
    mcp_tools_used: list[str] = Field(default_factory=list)
    outcome_pnl: Decimal | None = None
    outcome_result: str = ""


# ---------------------------------------------------------------------------
# Counterfactual Trade
# ---------------------------------------------------------------------------

class CounterfactualTrade(BaseModel):
    """Tracks what would have happened if a rejected trade had been executed."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    receipt_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    underlying: str = ""
    strategy: str = ""
    thesis: str = ""
    kill_score: Decimal = Decimal("0")
    rejection_reason: str = ""
    entry_price_estimate: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")
    simulated_pnl: Decimal | None = None
    simulated_result: str = ""  # "would_win", "would_loss", "would_breakeven", "pending"
    evaluation_date: datetime | None = None
    evaluated: bool = False


# ---------------------------------------------------------------------------
# Strategy Grave
# ---------------------------------------------------------------------------

class StrategyGrave(BaseModel):
    """Tracks a strategy variant that has been killed or is active."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    strategy_type: str = ""
    version: int = 1
    status: str = "active"  # "active", "killed", "resurrected"
    kill_reason: str = ""
    total_trades: int = 0
    win_count: int = 0
    loss_count: int = 0
    total_pnl: Decimal = Decimal("0")
    win_rate: Decimal = Decimal("0")
    avg_pnl: Decimal = Decimal("0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    killed_at: datetime | None = None
    resurrected_at: datetime | None = None
    resurrection_attempt: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Agent Disagreement
# ---------------------------------------------------------------------------

class AgentScore(BaseModel):
    """Individual agent's confidence/stance for a proposal."""
    agent_name: str = ""
    confidence: Decimal = Decimal("0")
    stance: str = ""  # "bullish", "bearish", "neutral"
    reasoning: str = ""


class AgentDisagreement(BaseModel):
    """Measures uncertainty from disagreement between agents."""
    proposal_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    agent_scores: list[AgentScore] = Field(default_factory=list)
    disagreement_index: Decimal = Field(default=Decimal("0"), description="0=full agreement, 1=maximum disagreement")
    consensus: str = ""  # "unanimous", "majority", "split", "contested"
    confidence_impact: Decimal = Field(default=Decimal("0"), description="How much disagreement reduces overall confidence")
