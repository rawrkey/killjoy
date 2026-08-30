"""Agent Disagreement Scorer — measures uncertainty from multi-agent disagreement.

When agents disagree, the system is less certain. This module quantifies
that disagreement and uses it as an uncertainty signal.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from killjoy.agent.models import AgentDisagreement, AgentScore

logger = logging.getLogger(__name__)


def compute_disagreement(
    analyst_score: Decimal,
    analyst_stance: str,
    strategy_score: Decimal,
    strategy_stance: str,
    kill_score: Decimal,
    kill_stance: str,
    portfolio_approved: bool,
    risk_approved: bool,
) -> AgentDisagreement:
    """Compute disagreement index from all agent scores.

    Returns an AgentDisagreement with disagreement_index from 0 (full agreement)
    to 1 (maximum disagreement).
    """
    scores = [
        AgentScore(
            agent_name="analyst",
            confidence=analyst_score,
            stance=analyst_stance,
        ),
        AgentScore(
            agent_name="strategy",
            confidence=strategy_score,
            stance=strategy_stance,
        ),
        AgentScore(
            agent_name="kill_agent",
            confidence=kill_score,
            stance=kill_stance,
        ),
        AgentScore(
            agent_name="portfolio",
            confidence=Decimal("1") if portfolio_approved else Decimal("0"),
            stance="approve" if portfolio_approved else "reject",
        ),
        AgentScore(
            agent_name="risk_engine",
            confidence=Decimal("1") if risk_approved else Decimal("0"),
            stance="approve" if risk_approved else "reject",
        ),
    ]

    # Compute disagreement using standard deviation of confidence scores
    confidences = [s.confidence for s in scores]
    mean_conf = sum(confidences) / len(confidences)
    variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
    std_dev = variance ** Decimal("0.5")

    # Normalize to 0-1 range (max std dev is 0.5 for binary scores)
    disagreement_index = min(std_dev * 2, Decimal("1"))

    # Determine consensus
    stances = [s.stance for s in scores]
    unique_stances = set(stances)
    if len(unique_stances) == 1:
        consensus = "unanimous"
    elif len(unique_stances) == 2:
        # Check if it's majority
        from collections import Counter
        counts = Counter(stances)
        most_common = counts.most_common(1)[0][1]
        if most_common >= 3:
            consensus = "majority"
        else:
            consensus = "split"
    else:
        consensus = "contested"

    # Confidence impact: higher disagreement = bigger confidence reduction
    confidence_impact = disagreement_index * Decimal("0.3")

    return AgentDisagreement(
        agent_scores=scores,
        disagreement_index=round(disagreement_index, 4),
        consensus=consensus,
        confidence_impact=round(confidence_impact, 4),
    )


def disagreement_to_dict(da: AgentDisagreement) -> dict[str, Any]:
    """Convert AgentDisagreement to a JSON-serializable dict."""
    return {
        "proposal_id": da.proposal_id,
        "agent_scores": [
            {
                "agent_name": s.agent_name,
                "confidence": float(s.confidence),
                "stance": s.stance,
                "reasoning": s.reasoning,
            }
            for s in da.agent_scores
        ],
        "disagreement_index": float(da.disagreement_index),
        "consensus": da.consensus,
        "confidence_impact": float(da.confidence_impact),
    }
