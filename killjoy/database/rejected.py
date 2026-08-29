"""Rejected trade persistence — 'Why Not Trade?' analytics."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from killjoy.agent.models import RejectedTrade

logger = logging.getLogger(__name__)

REJECTED_DIR = Path("data") / "rejected"


class RejectedTradeLog:
    """Persist rejected trade opportunities for analytics.

    Every analyzed opportunity that does NOT result in a trade is recorded here.
    This is a first-class KILLJOY feature for understanding what the system rejects.
    """

    def __init__(self, log_dir: Path | None = None) -> None:
        self._dir = log_dir or REJECTED_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def record_rejection(self, rejected: RejectedTrade) -> None:
        """Record a rejected trade opportunity."""
        filepath = self._dir / f"{rejected.id}.json"
        data = rejected.model_dump(mode="json")
        filepath.write_text(json.dumps(data, default=str, indent=2))
        logger.info(
            "Rejected trade recorded: %s %s (kill_score: %s, reason: %s)",
            rejected.underlying,
            rejected.proposed_strategy,
            rejected.kill_score,
            rejected.rejection_reason,
        )

    def get_all_rejections(self) -> list[RejectedTrade]:
        """Load all rejected trades from disk."""
        rejections = []
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                rejections.append(RejectedTrade(**data))
            except Exception as e:
                logger.warning("Failed to load rejected trade %s: %s", f, e)
        return rejections

    def get_analytics(self) -> dict:
        """Compute rejection analytics."""
        rejections = self.get_all_rejections()
        if not rejections:
            return {"total": 0, "top_rejection_reasons": {}, "avg_kill_score": 0}

        # Count rejection reasons
        reason_counts: dict[str, int] = {}
        for r in rejections:
            reason = r.rejection_reason or "unknown"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        # Sort by count
        top_reasons = dict(sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        # Average kill score
        avg_kill = sum(float(r.kill_score) for r in rejections) / len(rejections)

        # By strategy
        strategy_counts: dict[str, int] = {}
        for r in rejections:
            strat = r.proposed_strategy or "unknown"
            strategy_counts[strat] = strategy_counts.get(strat, 0) + 1

        return {
            "total": len(rejections),
            "top_rejection_reasons": top_reasons,
            "avg_kill_score": round(avg_kill, 3),
            "by_strategy": strategy_counts,
            "recent": [
                {
                    "id": r.id,
                    "timestamp": str(r.timestamp),
                    "underlying": r.underlying,
                    "strategy": r.proposed_strategy,
                    "kill_score": float(r.kill_score),
                    "reason": r.rejection_reason,
                }
                for r in sorted(rejections, key=lambda x: x.timestamp, reverse=True)[:10]
            ],
        }
