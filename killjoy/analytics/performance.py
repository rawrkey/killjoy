"""Performance analytics — P&L tracking, win rate, drawdown, attribution.

Computes metrics from ACTUAL paper-trading data in the trade journal.
No fabricated results.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from killjoy.agent.models import TradeJournalEntry

logger = logging.getLogger(__name__)


class PerformanceAnalytics:
    """Compute performance metrics from trade journal data."""

    def __init__(self, entries: list[TradeJournalEntry]) -> None:
        self._entries = entries
        self._closed = [e for e in entries if e.result in ("win", "loss", "breakeven", "closed")]
        self._open = [e for e in entries if e.result in ("", "open")]

    def summary(self) -> dict[str, Any]:
        """Compute full performance summary."""
        if not self._entries:
            return self._empty_summary()

        realized_pnl = sum(float(e.realized_pnl) for e in self._closed)
        wins = [e for e in self._closed if float(e.realized_pnl) > 0]
        losses = [e for e in self._closed if float(e.realized_pnl) < 0]
        breakeven = [e for e in self._closed if float(e.realized_pnl) == 0]

        win_count = len(wins)
        loss_count = len(losses)
        total_closed = len(self._closed)

        win_rate = win_count / total_closed if total_closed > 0 else 0
        avg_win = sum(float(e.realized_pnl) for e in wins) / win_count if win_count > 0 else 0
        avg_loss = sum(float(e.realized_pnl) for e in losses) / loss_count if loss_count > 0 else 0

        gross_profit = sum(float(e.realized_pnl) for e in wins)
        gross_loss = abs(sum(float(e.realized_pnl) for e in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0

        # Max drawdown from equity curve
        max_dd, max_dd_pct = self._compute_max_drawdown()

        # By strategy
        by_strategy = self._by_strategy()

        # By underlying
        by_underlying = self._by_underlying()

        # Kill Score attribution
        kill_score_buckets = self._kill_score_attribution()

        # Confidence calibration
        confidence_calibration = self._confidence_calibration()

        return {
            "total_trades": len(self._entries),
            "open_trades": len(self._open),
            "closed_trades": total_closed,
            "realized_pnl": round(realized_pnl, 2),
            "win_count": win_count,
            "loss_count": loss_count,
            "breakeven_count": len(breakeven),
            "win_rate": round(win_rate, 4),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "inf",
            "max_drawdown": round(max_dd, 2),
            "max_drawdown_pct": round(max_dd_pct, 4),
            "by_strategy": by_strategy,
            "by_underlying": by_underlying,
            "kill_score_attribution": kill_score_buckets,
            "confidence_calibration": confidence_calibration,
        }

    def _compute_max_drawdown(self) -> tuple[float, float]:
        """Compute max drawdown from closed trade P&L series."""
        if not self._closed:
            return 0.0, 0.0

        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        max_dd_pct = 0.0

        for entry in sorted(self._closed, key=lambda e: e.timestamp):
            equity += float(entry.realized_pnl)
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
            if peak > 0:
                dd_pct = dd / peak
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct

        return max_dd, max_dd_pct

    def _by_strategy(self) -> dict[str, dict[str, Any]]:
        """Compute P&L by strategy."""
        strategies: dict[str, list[TradeJournalEntry]] = {}
        for e in self._closed:
            strat = e.strategy or "unknown"
            strategies.setdefault(strat, []).append(e)

        result = {}
        for strat, entries in strategies.items():
            pnls = [float(e.realized_pnl) for e in entries]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]
            result[strat] = {
                "count": len(entries),
                "total_pnl": round(sum(pnls), 2),
                "win_rate": round(len(wins) / len(entries), 4) if entries else 0,
                "avg_pnl": round(sum(pnls) / len(entries), 2) if entries else 0,
            }
        return result

    def _by_underlying(self) -> dict[str, dict[str, Any]]:
        """Compute P&L by underlying."""
        underlyings: dict[str, list[TradeJournalEntry]] = {}
        for e in self._closed:
            sym = e.underlying or "unknown"
            underlyings.setdefault(sym, []).append(e)

        result = {}
        for sym, entries in underlyings.items():
            pnls = [float(e.realized_pnl) for e in entries]
            wins = [p for p in pnls if p > 0]
            result[sym] = {
                "count": len(entries),
                "total_pnl": round(sum(pnls), 2),
                "win_rate": round(len(wins) / len(entries), 4) if entries else 0,
            }
        return result

    def _kill_score_attribution(self) -> dict[str, dict[str, Any]]:
        """Compute win rate by Kill Score bucket."""
        buckets = {
            "0.0-0.2": [],
            "0.2-0.4": [],
            "0.4-0.6": [],
            "0.6-0.8": [],
            "0.8-1.0": [],
        }

        for e in self._closed:
            ks = float(e.kill_score)
            if ks < 0.2:
                buckets["0.0-0.2"].append(e)
            elif ks < 0.4:
                buckets["0.2-0.4"].append(e)
            elif ks < 0.6:
                buckets["0.4-0.6"].append(e)
            elif ks < 0.8:
                buckets["0.6-0.8"].append(e)
            else:
                buckets["0.8-1.0"].append(e)

        result = {}
        for bucket, entries in buckets.items():
            if not entries:
                result[bucket] = {"count": 0, "win_rate": 0, "avg_pnl": 0}
                continue
            pnls = [float(e.realized_pnl) for e in entries]
            wins = [p for p in pnls if p > 0]
            result[bucket] = {
                "count": len(entries),
                "win_rate": round(len(wins) / len(entries), 4),
                "avg_pnl": round(sum(pnls) / len(entries), 2),
            }
        return result

    def _confidence_calibration(self) -> dict[str, Any]:
        """Track predicted confidence vs actual outcome."""
        if not self._closed:
            return {"buckets": {}, "note": "No closed trades yet"}

        buckets: dict[str, list[TradeJournalEntry]] = {
            "0.0-0.3": [],
            "0.3-0.5": [],
            "0.5-0.7": [],
            "0.7-1.0": [],
        }

        for e in self._closed:
            conf = float(e.confidence)
            if conf < 0.3:
                buckets["0.0-0.3"].append(e)
            elif conf < 0.5:
                buckets["0.3-0.5"].append(e)
            elif conf < 0.7:
                buckets["0.5-0.7"].append(e)
            else:
                buckets["0.7-1.0"].append(e)

        result = {}
        for bucket, entries in buckets.items():
            if not entries:
                result[bucket] = {"count": 0, "win_rate": 0, "avg_confidence": 0}
                continue
            pnls = [float(e.realized_pnl) for e in entries]
            wins = [p for p in pnls if p > 0]
            avg_conf = sum(float(e.confidence) for e in entries) / len(entries)
            result[bucket] = {
                "count": len(entries),
                "win_rate": round(len(wins) / len(entries), 4),
                "avg_confidence": round(avg_conf, 4),
            }
        return result

    def _empty_summary(self) -> dict[str, Any]:
        return {
            "total_trades": 0,
            "open_trades": 0,
            "closed_trades": 0,
            "realized_pnl": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "max_drawdown_pct": 0,
            "by_strategy": {},
            "by_underlying": {},
            "kill_score_attribution": {},
            "confidence_calibration": {},
            "note": "No trades yet",
        }
