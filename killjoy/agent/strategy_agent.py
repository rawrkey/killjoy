"""Strategy Agent — DETERMINISTIC BASELINE for trade proposal generation.

This module provides the rule-based fallback for strategy selection. It is called
internally by ``llm_strategy.py`` to generate candidate proposals before LLM
reasoning selects the best one. The scheduler imports the LLM version, not this
module directly.

Fallback behavior: If no LLM provider is configured or available, the system
returns all ranked proposals from this module unchanged.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import MarketThesis, StrategyType, TradeProposal
from killjoy.strategies.bull_call_spread import BullCallSpreadStrategy
from killjoy.strategies.bear_put_spread import BearPutSpreadStrategy
from killjoy.strategies.iron_condor import IronCondorStrategy
from killjoy.strategies.long_call import LongCallStrategy
from killjoy.strategies.long_put import LongPutStrategy

logger = logging.getLogger(__name__)

STRATEGIES = [
    LongCallStrategy(),
    LongPutStrategy(),
    BullCallSpreadStrategy(),
    BearPutSpreadStrategy(),
    IronCondorStrategy(),
]


def generate_proposals(
    thesis: MarketThesis,
    contracts: list,
    spot: Decimal,
) -> list[TradeProposal]:
    """Generate trade proposals from a thesis and available contracts."""
    proposals = []
    for strategy in STRATEGIES:
        try:
            proposal = strategy.build_proposal(thesis, contracts, spot)
            if proposal:
                proposals.append(proposal)
                logger.info(
                    "Generated %s proposal for %s (R/R: %s)",
                    proposal.strategy.value,
                    proposal.underlying,
                    proposal.reward_risk,
                )
        except Exception as e:
            logger.warning("Strategy %s failed: %s", strategy.strategy_type.value, e)

    # Sort by confidence * reward_risk
    proposals.sort(key=lambda p: p.confidence * p.reward_risk, reverse=True)
    return proposals
