"""Postmortem Agent — analyzes completed trades."""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import Postmortem, TradeJournalEntry

logger = logging.getLogger(__name__)


def run_postmortem(entry: TradeJournalEntry) -> Postmortem:
    """Analyze a completed trade and generate insights."""
    improvements: list[str] = []
    lessons: list[str] = []

    # Determine win/loss
    realized = entry.realized_pnl
    if realized > 0:
        win_loss = "win"
    elif realized < 0:
        win_loss = "loss"
    else:
        win_loss = "breakeven"

    # Evaluate kill agent accuracy
    kill_accurate = None
    if entry.kill_score > Decimal("0.6") and win_loss == "loss":
        kill_accurate = False
        lessons.append("Kill agent gave high score but trade lost — review kill criteria")
    elif entry.kill_score < Decimal("0.4") and win_loss == "win":
        kill_accurate = False
        lessons.append("Kill agent gave low score but trade won — may be too aggressive")
    elif (entry.kill_score > Decimal("0.6") and win_loss == "win") or \
         (entry.kill_score < Decimal("0.4") and win_loss == "loss"):
        kill_accurate = True

    # Generate improvements
    if abs(realized) > Decimal("500"):
        if win_loss == "loss":
            improvements.append("Consider tighter stop-loss for large losses")
        else:
            lessons.append("Good position sizing on winning trade")

    if entry.legs and len(entry.legs) > 2:
        if win_loss == "loss":
            improvements.append("Multi-leg strategies may have added unnecessary complexity")

    if not entry.thesis:
        improvements.append("Trade lacked a clear thesis — always document reasoning")

    return Postmortem(
        trade_id=entry.trade_id,
        underlying=entry.underlying,
        strategy=entry.strategy,
        original_thesis=entry.thesis,
        actual_outcome=f"{win_loss} (${realized:.2f})",
        thesis_correct=None,  # Would need human/LLM review
        win_loss=win_loss,
        realized_pnl=realized,
        kill_agent_accurate=kill_accurate,
        improvements=improvements,
        lessons=lessons,
    )
