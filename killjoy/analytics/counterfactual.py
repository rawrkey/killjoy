"""Counterfactual portfolio — tracks what rejected trades would have done.

This is the core differentiator for KILLJOY: proving that killing trades
actually improves results by maintaining a shadow portfolio of rejected trades.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from killjoy.agent.models import CounterfactualTrade, RejectedTrade

logger = logging.getLogger(__name__)

COUNTERFACTUAL_DIR = Path("data") / "counterfactual"


class CounterfactualPortfolio:
    """Track rejected trades and simulate their outcomes."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or COUNTERFACTUAL_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def record_rejection(self, rejected: RejectedTrade, receipt_id: str = "") -> CounterfactualTrade:
        """Record a rejected trade for counterfactual tracking."""
        ct = CounterfactualTrade(
            receipt_id=receipt_id,
            underlying=rejected.underlying,
            strategy=rejected.proposed_strategy,
            thesis=rejected.thesis,
            kill_score=rejected.kill_score,
            rejection_reason=rejected.rejection_reason,
        )
        self._persist(ct)
        logger.info("Counterfactual recorded: %s %s (kill_score: %s)", ct.underlying, ct.strategy, ct.kill_score)
        return ct

    def evaluate_all(self, price_getter: Any) -> dict[str, Any]:
        """Evaluate all pending counterfactual trades.

        price_getter: callable(symbol) -> Decimal (current price)
        Returns summary of evaluations.
        """
        trades = self._load_all()
        pending = [t for t in trades if not t.evaluated]
        evaluated_count = 0
        wins = 0
        losses = 0

        for ct in pending:
            try:
                current_price = price_getter(ct.underlying)
                if current_price <= 0:
                    continue

                ct.current_price = current_price
                ct.evaluation_date = datetime.now(timezone.utc)

                # Simple P&L estimation based on strategy type
                # For spreads, we approximate using the entry price estimate
                if ct.entry_price_estimate > 0:
                    price_change_pct = (current_price - ct.entry_price_estimate) / ct.entry_price_estimate

                    # Directional strategies: profit if price moves in expected direction
                    if ct.strategy in ("long_call", "bull_call_spread"):
                        ct.simulated_pnl = price_change_pct * ct.entry_price_estimate * 100
                    elif ct.strategy in ("long_put", "bear_put_spread"):
                        ct.simulated_pnl = -price_change_pct * ct.entry_price_estimate * 100
                    elif ct.strategy == "iron_condor":
                        # Iron condor profits from low movement
                        ct.simulated_pnl = -abs(price_change_pct) * ct.entry_price_estimate * 50
                    else:
                        ct.simulated_pnl = Decimal("0")

                    if ct.simulated_pnl > 0:
                        ct.simulated_result = "would_win"
                        wins += 1
                    elif ct.simulated_pnl < 0:
                        ct.simulated_result = "would_loss"
                        losses += 1
                    else:
                        ct.simulated_result = "would_breakeven"

                ct.evaluated = True
                self._persist(ct)
                evaluated_count += 1

            except Exception as e:
                logger.debug("Failed to evaluate counterfactual %s: %s", ct.id, e)

        return {
            "total_trades": len(trades),
            "pending_evaluation": len(pending) - evaluated_count,
            "evaluated": evaluated_count,
            "total_evaluated": sum(1 for t in trades if t.evaluated),
            "would_win": sum(1 for t in trades if t.simulated_result == "would_win"),
            "would_loss": sum(1 for t in trades if t.simulated_result == "would_loss"),
        }

    def get_summary(self) -> dict[str, Any]:
        """Get counterfactual portfolio summary."""
        trades = self._load_all()
        evaluated = [t for t in trades if t.evaluated]

        if not evaluated:
            return {
                "total_trades": len(trades),
                "evaluated": 0,
                "simulated_pnl": 0,
                "win_rate": 0,
                "would_win": 0,
                "would_loss": 0,
                "would_breakeven": 0,
                "avg_kill_score": 0,
                "recent": [],
            }

        total_pnl = sum(float(t.simulated_pnl or 0) for t in evaluated)
        wins = sum(1 for t in evaluated if t.simulated_result == "would_win")
        losses = sum(1 for t in evaluated if t.simulated_result == "would_loss")
        breakeven = sum(1 for t in evaluated if t.simulated_result == "would_breakeven")
        avg_kill = sum(float(t.kill_score) for t in evaluated) / len(evaluated)

        return {
            "total_trades": len(trades),
            "evaluated": len(evaluated),
            "simulated_pnl": round(total_pnl, 2),
            "win_rate": round(wins / len(evaluated), 4) if evaluated else 0,
            "would_win": wins,
            "would_loss": losses,
            "would_breakeven": breakeven,
            "avg_kill_score": round(avg_kill, 3),
            "recent": [
                {
                    "id": t.id,
                    "underlying": t.underlying,
                    "strategy": t.strategy,
                    "kill_score": float(t.kill_score),
                    "simulated_pnl": float(t.simulated_pnl or 0),
                    "simulated_result": t.simulated_result,
                    "rejection_reason": t.rejection_reason,
                    "timestamp": str(t.timestamp),
                }
                for t in sorted(evaluated, key=lambda x: x.timestamp, reverse=True)[:10]
            ],
        }

    def get_all_trades(self) -> list[CounterfactualTrade]:
        return self._load_all()

    def _persist(self, ct: CounterfactualTrade) -> None:
        filepath = self._dir / f"{ct.id}.json"
        data = ct.model_dump(mode="json")
        filepath.write_text(json.dumps(data, default=str, indent=2))

    def _load_all(self) -> list[CounterfactualTrade]:
        trades = []
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                trades.append(CounterfactualTrade(**data))
            except Exception as e:
                logger.debug("Failed to load counterfactual %s: %s", f, e)
        return trades
