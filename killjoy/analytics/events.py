"""Event/audit log — persists every decision stage for reconstructability.

Every trading decision can be reconstructed from the event log.
Events are stored as JSON lines for efficient append and querying.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

EVENTS_DIR = Path("data") / "events"


class EventLog:
    """Append-only event log for decision traceability."""

    def __init__(self, log_dir: Path | None = None) -> None:
        self._dir = log_dir or EVENTS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event_type: str,
        run_id: str,
        symbol: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        """Append an event to the log.

        Event types:
        - analysis_started / analysis_completed
        - proposal_created
        - kill_started / kill_completed
        - debate_started / debate_completed
        - portfolio_checked
        - risk_checked
        - order_submitted / order_filled / order_failed
        - position_opened / position_updated / position_closed
        - postmortem_completed
        - rejection_recorded
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "run_id": run_id,
            "symbol": symbol,
            "data": data or {},
        }

        # Append to daily event file
        day = datetime.utcnow().strftime("%Y-%m-%d")
        filepath = self._dir / f"events_{day}.jsonl"

        try:
            with open(filepath, "a") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except Exception as e:
            logger.warning("Failed to write event: %s", e)

    def get_events(
        self,
        run_id: str | None = None,
        event_type: str | None = None,
        symbol: str | None = None,
        date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query events with optional filters."""
        events = []

        # Determine which files to read
        if date:
            files = [self._dir / f"events_{date}.jsonl"]
        else:
            files = sorted(self._dir.glob("events_*.jsonl"))

        for filepath in files:
            if not filepath.exists():
                continue
            try:
                for line in filepath.read_text().splitlines():
                    if not line.strip():
                        continue
                    event = json.loads(line)
                    if run_id and event.get("run_id") != run_id:
                        continue
                    if event_type and event.get("event_type") != event_type:
                        continue
                    if symbol and event.get("symbol") != symbol:
                        continue
                    events.append(event)
            except Exception as e:
                logger.warning("Failed to read events from %s: %s", filepath, e)

        return events

    def get_run_timeline(self, run_id: str) -> list[dict[str, Any]]:
        """Get the full timeline for a specific run."""
        return self.get_events(run_id=run_id)

    def get_summary(self, date: str | None = None) -> dict[str, Any]:
        """Get event summary for a date or all time."""
        events = self.get_events(date=date)
        type_counts: dict[str, int] = {}
        for e in events:
            t = e.get("event_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        run_ids = list(set(e.get("run_id", "") for e in events if e.get("run_id")))

        return {
            "total_events": len(events),
            "event_types": type_counts,
            "unique_runs": len(run_ids),
            "date": date or "all",
        }
