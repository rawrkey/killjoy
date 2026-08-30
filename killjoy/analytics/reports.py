"""Cycle Reports — plain-English summaries of each trading cycle."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("data") / "reports"


class CycleReportBuilder:
    """Collects cycle data and builds a plain-English report."""

    def __init__(self) -> None:
        self._symbols: list[dict[str, Any]] = []
        self._closes: list[dict[str, Any]] = []
        self._summary: dict[str, Any] = {}

    def add_symbol_analysis(self, symbol: str, regime: str, confidence: float, price: float, thesis: str):
        self._symbols.append({
            "symbol": symbol,
            "regime": regime,
            "confidence": confidence,
            "price": price,
            "thesis": thesis,
            "proposals": [],
        })

    def add_proposal(self, symbol: str, strategy: str, kill_score: float, survives: bool,
                     kill_reasons: list[str], risk_approved: bool, risk_reasons: list[str],
                     portfolio_approved: bool, portfolio_reasons: list[str],
                     submitted: bool, order_id: str = ""):
        # Find the symbol entry
        entry = None
        for s in self._symbols:
            if s["symbol"] == symbol:
                entry = s
                break
        if entry is None:
            entry = {"symbol": symbol, "proposals": []}
            self._symbols.append(entry)

        # Determine what happened in plain English
        if submitted:
            outcome = "ORDER SUBMITTED"
        elif not portfolio_approved:
            outcome = "PORTFOLIO REJECTED"
        elif not risk_approved:
            outcome = "RISK REJECTED"
        elif not survives:
            outcome = "KILLED BY AGENT"
        else:
            outcome = "SUBMITTED"

        entry["proposals"].append({
            "strategy": strategy,
            "kill_score": kill_score,
            "survives": survives,
            "kill_reasons": kill_reasons,
            "risk_approved": risk_approved,
            "risk_reasons": risk_reasons,
            "portfolio_approved": portfolio_approved,
            "portfolio_reasons": portfolio_reasons,
            "outcome": outcome,
            "order_id": order_id,
        })

    def add_position_close(self, symbol: str, reason: str, pnl: float, strategy: str = ""):
        self._closes.append({
            "symbol": symbol,
            "reason": reason,
            "pnl": pnl,
            "strategy": strategy,
        })

    def set_summary(self, **kwargs):
        self._summary = kwargs

    def build(self) -> dict[str, Any]:
        """Build the full report dict."""
        # Compute simple stats
        total_proposals = sum(len(s["proposals"]) for s in self._symbols)
        killed = sum(1 for s in self._symbols for p in s["proposals"] if p["outcome"] == "KILLED BY AGENT")
        portfolio_rejected = sum(1 for s in self._symbols for p in s["proposals"] if p["outcome"] == "PORTFOLIO REJECTED")
        risk_rejected = sum(1 for s in self._symbols for p in s["proposals"] if p["outcome"] == "RISK REJECTED")
        submitted = sum(1 for s in self._symbols for p in s["proposals"] if "SUBMITTED" in p["outcome"])
        closed = len(self._closes)
        closed_pnl = sum(c["pnl"] for c in self._closes)

        # Build plain-English summary lines
        summary_lines = []

        if closed > 0:
            wins = sum(1 for c in self._closes if c["pnl"] > 0)
            losses = closed - wins
            summary_lines.append(f"Closed {closed} position(s): {wins} win(s), {losses} loss(es), ${closed_pnl:+.2f} total.")

        if submitted > 0:
            summary_lines.append(f"Submitted {submitted} order(s) to Alpaca.")
        elif total_proposals == 0:
            summary_lines.append("No trade opportunities found this cycle.")
        else:
            summary_lines.append(f"Analyzed {total_proposals} opportunity(ies). None survived all checks.")

        if killed > 0:
            summary_lines.append(f"Kill Agent rejected {killed} — they didn't survive adversarial testing.")

        if not summary_lines:
            summary_lines.append("Cycle completed. No action taken.")

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self._summary.get("mode", "paper"),
            "run_id": self._summary.get("run_id", ""),
            "llm": self._summary.get("llm", "deterministic"),
            "summary_text": " ".join(summary_lines),
            "stats": {
                "total_analyzed": total_proposals,
                "killed": killed,
                "portfolio_rejected": portfolio_rejected,
                "risk_rejected": risk_rejected,
                "orders_submitted": submitted,
                "positions_closed": closed,
                "closed_pnl": round(closed_pnl, 2),
            },
            "symbols": self._symbols,
            "closes": self._closes,
        }


def save_report(report: dict[str, Any]) -> Path:
    """Save report to disk and return path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = REPORTS_DIR / "latest.json"
    filepath.write_text(json.dumps(report, indent=2, default=str))
    # Also save timestamped copy
    ts = report["timestamp"].replace(":", "-").replace(".", "-")[:19]
    ts_path = REPORTS_DIR / f"report-{ts}.json"
    ts_path.write_text(json.dumps(report, indent=2, default=str))
    logger.info("Cycle report saved: %s", filepath)
    return filepath


def get_latest_report() -> dict[str, Any] | None:
    """Load the latest report from disk."""
    filepath = REPORTS_DIR / "latest.json"
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text())
    except Exception as e:
        logger.warning("Failed to load latest report: %s", e)
        return None


def get_all_reports() -> list[dict[str, Any]]:
    """Load all timestamped reports from disk, newest first."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for f in sorted(REPORTS_DIR.glob("report-*.json"), reverse=True):
        try:
            reports.append(json.loads(f.read_text()))
        except Exception:
            pass
    return reports
