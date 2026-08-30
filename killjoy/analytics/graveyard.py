"""Strategy Graveyard — tracks strategy variants, kills, and resurrections.

Every strategy variant gets tracked. When performance degrades, it's killed.
When conditions change, it can be resurrected with new parameters.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from killjoy.agent.models import StrategyGrave

logger = logging.getLogger(__name__)

GRAVEYARD_DIR = Path("data") / "graveyard"


class StrategyGraveyard:
    """Manage strategy lifecycle: active → killed → (optionally) resurrected."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or GRAVEYARD_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def get_all(self) -> list[StrategyGrave]:
        """Load all strategy graves."""
        graves = []
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                graves.append(StrategyGrave(**data))
            except Exception as e:
                logger.debug("Failed to load grave %s: %s", f, e)
        return graves

    def get_active(self) -> list[StrategyGrave]:
        return [g for g in self.get_all() if g.status == "active"]

    def get_killed(self) -> list[StrategyGrave]:
        return [g for g in self.get_all() if g.status == "killed"]

    def get_resurrected(self) -> list[StrategyGrave]:
        return [g for g in self.get_all() if g.status == "resurrected"]

    def record_trade(self, strategy_type: str, won: bool, pnl: float) -> None:
        """Record a trade outcome for a strategy variant."""
        graves = self.get_all()
        # Find or create the active grave for this strategy
        grave = None
        for g in graves:
            if g.strategy_type == strategy_type and g.status == "active":
                grave = g
                break

        if grave is None:
            grave = StrategyGrave(strategy_type=strategy_type)
            graves.append(grave)

        grave.total_trades += 1
        if won:
            grave.win_count += 1
        else:
            grave.loss_count += 1
        grave.total_pnl += Decimal(str(pnl))
        grave.win_rate = grave.win_count / grave.total_trades if grave.total_trades > 0 else Decimal("0")
        grave.avg_pnl = grave.total_pnl / grave.total_trades if grave.total_trades > 0 else Decimal("0")

        self._persist(grave)
        logger.info("Strategy %s recorded: trade=%d, win_rate=%.2f", strategy_type, grave.total_trades, grave.win_rate)

    def kill_strategy(self, strategy_type: str, reason: str) -> StrategyGrave | None:
        """Kill an active strategy variant."""
        graves = self.get_all()
        for g in graves:
            if g.strategy_type == strategy_type and g.status == "active":
                g.status = "killed"
                g.kill_reason = reason
                g.killed_at = datetime.now(timezone.utc)
                self._persist(g)
                logger.info("Strategy KILLED: %s — %s", strategy_type, reason)
                return g
        return None

    def resurrect_strategy(self, strategy_type: str, new_params: dict[str, Any] | None = None) -> StrategyGrave:
        """Resurrect a killed strategy with potentially new parameters."""
        graves = self.get_all()

        # Find the latest killed version
        killed = [g for g in graves if g.strategy_type == strategy_type and g.status == "killed"]
        if not killed:
            # No killed strategy to resurrect, create fresh
            grave = StrategyGrave(strategy_type=strategy_type, status="active")
        else:
            latest = max(killed, key=lambda g: g.version)
            latest.version += 1
            latest.status = "resurrected"
            latest.resurrected_at = datetime.now(timezone.utc)
            latest.resurrection_attempt += 1
            # Reset stats for the new version
            latest.total_trades = 0
            latest.win_count = 0
            latest.loss_count = 0
            latest.total_pnl = Decimal("0")
            latest.win_rate = Decimal("0")
            latest.avg_pnl = Decimal("0")
            latest.kill_reason = ""
            latest.killed_at = None
            if new_params:
                latest.metadata["resurrection_params"] = new_params
            grave = latest

        graves.append(grave) if grave not in graves else None
        self._persist(grave)
        logger.info("Strategy RESURRECTED: %s v%d", strategy_type, grave.version)
        return grave

    def evaluate_resurrection_candidates(self, min_trades: int = 5, min_win_rate: float = 0.4) -> list[dict[str, Any]]:
        """Evaluate whether killed strategies deserve resurrection."""
        killed = self.get_killed()
        candidates = []

        for grave in killed:
            # A strategy is a resurrection candidate if:
            # 1. It had enough trades to be statistically meaningful
            # 2. Its win rate was close to the threshold
            # 3. Market conditions may have changed
            if grave.total_trades >= min_trades:
                near_threshold = float(grave.win_rate) >= (min_win_rate - 0.1)
                if near_threshold:
                    candidates.append({
                        "strategy_type": grave.strategy_type,
                        "version": grave.version,
                        "total_trades": grave.total_trades,
                        "win_rate": float(grave.win_rate),
                        "total_pnl": float(grave.total_pnl),
                        "kill_reason": grave.kill_reason,
                        "resurrection_readiness": "high" if float(grave.win_rate) >= min_win_rate else "medium",
                    })

        return sorted(candidates, key=lambda x: x["win_rate"], reverse=True)

    def get_graveyard_summary(self) -> dict[str, Any]:
        """Get full graveyard summary."""
        all_graves = self.get_all()
        active = self.get_active()
        killed = self.get_killed()
        resurrected = self.get_resurrected()

        by_strategy: dict[str, list[dict]] = {}
        for g in all_graves:
            if g.strategy_type not in by_strategy:
                by_strategy[g.strategy_type] = []
            by_strategy[g.strategy_type].append({
                "version": g.version,
                "status": g.status,
                "total_trades": g.total_trades,
                "win_rate": float(g.win_rate),
                "total_pnl": float(g.total_pnl),
                "kill_reason": g.kill_reason,
            })

        return {
            "total_variants": len(all_graves),
            "active": len(active),
            "killed": len(killed),
            "resurrected": len(resurrected),
            "by_strategy": by_strategy,
            "resurrection_candidates": self.evaluate_resurrection_candidates(),
            "graves": [
                {
                    "id": g.id,
                    "strategy_type": g.strategy_type,
                    "version": g.version,
                    "status": g.status,
                    "total_trades": g.total_trades,
                    "win_rate": float(g.win_rate),
                    "total_pnl": float(g.total_pnl),
                    "kill_reason": g.kill_reason,
                    "created_at": str(g.created_at),
                    "killed_at": str(g.killed_at) if g.killed_at else None,
                    "resurrected_at": str(g.resurrected_at) if g.resurrected_at else None,
                }
                for g in sorted(all_graves, key=lambda x: x.created_at, reverse=True)
            ],
        }

    def _persist(self, grave: StrategyGrave) -> None:
        filepath = self._dir / f"{grave.id}.json"
        data = grave.model_dump(mode="json")
        filepath.write_text(json.dumps(data, default=str, indent=2))
