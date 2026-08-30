"""Kill Precision Analytics — measures whether killing trades actually helps.

Tracks correct kills vs false kills by comparing:
- Trades that were killed and would have lost (correct kill)
- Trades that were killed but would have won (false kill)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from killjoy.agent.models import CounterfactualTrade, TradeJournalEntry

logger = logging.getLogger(__name__)


class KillPrecisionAnalytics:
    """Compute kill agent precision from counterfactual data."""

    def __init__(
        self,
        counterfactuals: list[CounterfactualTrade],
        journal_entries: list[TradeJournalEntry] | None = None,
    ) -> None:
        self._counterfactuals = counterfactuals
        self._journal = journal_entries or []

    def summary(self) -> dict[str, Any]:
        """Compute kill precision metrics."""
        evaluated = [ct for ct in self._counterfactuals if ct.evaluated]

        if not evaluated:
            return self._empty_summary()

        correct_kills = 0
        false_kills = 0
        correct_executes = 0
        false_executes = 0

        for ct in evaluated:
            if ct.simulated_result == "would_loss":
                correct_kills += 1  # KILLJOY was right to kill it
            elif ct.simulated_result == "would_win":
                false_kills += 1  # KILLJOY wrongly killed a winner

        # Count executed trades
        for entry in self._journal:
            if entry.result in ("win", "loss", "breakeven", "closed"):
                if float(entry.realized_pnl) > 0:
                    correct_executes += 1
                elif float(entry.realized_pnl) < 0:
                    false_executes += 1

        total_kills = correct_kills + false_kills
        total_executes = correct_executes + false_executes

        precision = correct_kills / total_kills if total_kills > 0 else 0
        execute_quality = correct_executes / total_executes if total_executes > 0 else 0

        # Kill score distribution for killed trades
        kill_score_dist = self._kill_score_distribution(evaluated)

        # False kill analysis
        false_kill_analysis = self._false_kill_analysis(evaluated)

        return {
            "correct_kills": correct_kills,
            "false_kills": false_kills,
            "total_kills": total_kills,
            "kill_precision": round(precision, 4),
            "correct_executes": correct_executes,
            "false_executes": false_executes,
            "total_executes": total_executes,
            "execute_quality": round(execute_quality, 4),
            "kill_score_distribution": kill_score_dist,
            "false_kill_analysis": false_kill_analysis,
            "net_value_added": self._compute_net_value(evaluated),
        }

    def _kill_score_distribution(self, evaluated: list[CounterfactualTrade]) -> dict[str, dict[str, Any]]:
        """Break down precision by kill score buckets."""
        buckets: dict[str, list[CounterfactualTrade]] = {
            "0.0-0.2": [],
            "0.2-0.4": [],
            "0.4-0.6": [],
            "0.6-0.8": [],
            "0.8-1.0": [],
        }

        for ct in evaluated:
            ks = float(ct.kill_score)
            if ks < 0.2:
                buckets["0.0-0.2"].append(ct)
            elif ks < 0.4:
                buckets["0.2-0.4"].append(ct)
            elif ks < 0.6:
                buckets["0.4-0.6"].append(ct)
            elif ks < 0.8:
                buckets["0.6-0.8"].append(ct)
            else:
                buckets["0.8-1.0"].append(ct)

        result = {}
        for bucket, trades in buckets.items():
            if not trades:
                result[bucket] = {"count": 0, "precision": 0, "would_win": 0, "would_loss": 0}
                continue
            correct = sum(1 for t in trades if t.simulated_result == "would_loss")
            false = sum(1 for t in trades if t.simulated_result == "would_win")
            result[bucket] = {
                "count": len(trades),
                "precision": round(correct / len(trades), 4) if trades else 0,
                "would_win": false,
                "would_loss": correct,
            }
        return result

    def _false_kill_analysis(self, evaluated: list[CounterfactualTrade]) -> list[dict[str, Any]]:
        """Analyze false kills — trades that were killed but would have won."""
        false_kills = [ct for ct in evaluated if ct.simulated_result == "would_win"]
        return [
            {
                "underlying": ct.underlying,
                "strategy": ct.strategy,
                "kill_score": float(ct.kill_score),
                "would_pnl": float(ct.simulated_pnl or 0),
                "rejection_reason": ct.rejection_reason,
            }
            for ct in sorted(false_kills, key=lambda x: float(x.simulated_pnl or 0), reverse=True)[:10]
        ]

    def _compute_net_value(self, evaluated: list[CounterfactualTrade]) -> float:
        """Compute net value added by killing trades.

        Positive = killing trades saved money (correct kills outperformed false kills)
        Negative = killing trades cost money (false kills were expensive)
        """
        correct_value = sum(
            abs(float(ct.simulated_pnl or 0))
            for ct in evaluated
            if ct.simulated_result == "would_loss"
        )
        false_value = sum(
            float(ct.simulated_pnl or 0)
            for ct in evaluated
            if ct.simulated_result == "would_win"
        )
        return round(correct_value - false_value, 2)

    def _empty_summary(self) -> dict[str, Any]:
        return {
            "correct_kills": 0,
            "false_kills": 0,
            "total_kills": 0,
            "kill_precision": 0,
            "correct_executes": 0,
            "false_executes": 0,
            "total_executes": 0,
            "execute_quality": 0,
            "kill_score_distribution": {},
            "false_kill_analysis": [],
            "net_value_added": 0,
            "note": "No evaluated counterfactuals yet",
        }
