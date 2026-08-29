"""Trade journal and persistence layer."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from killjoy.agent.models import Postmortem, TradeJournalEntry

logger = logging.getLogger(__name__)

JOURNAL_DIR = Path("data") / "journal"


class TradeJournal:
    """Persist trade lifecycle data to JSON files."""

    def __init__(self, journal_dir: Path | None = None) -> None:
        self._dir = journal_dir or JOURNAL_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, TradeJournalEntry] = {}

    def record_entry(self, entry: TradeJournalEntry) -> None:
        """Record a new trade journal entry."""
        self._entries[entry.trade_id] = entry
        self._persist(entry)
        logger.info("Journal entry recorded: %s", entry.trade_id)

    def record_exit(
        self,
        trade_id: str,
        realized_pnl: float,
        result: str,
        exit_order_id: str = "",
    ) -> None:
        """Record trade exit."""
        if trade_id in self._entries:
            entry = self._entries[trade_id]
            entry.realized_pnl = realized_pnl
            entry.result = result
            self._persist(entry)
            logger.info("Trade %s closed: %s ($%.2f)", trade_id, result, realized_pnl)

    def record_postmortem(self, trade_id: str, postmortem: Postmortem) -> None:
        """Attach a postmortem to a trade."""
        if trade_id in self._entries:
            self._entries[trade_id].postmortem = postmortem
            self._persist(self._entries[trade_id])
            logger.info("Postmortem recorded for %s", trade_id)

    def get_entry(self, trade_id: str) -> TradeJournalEntry | None:
        return self._entries.get(trade_id)

    def get_all_entries(self) -> list[TradeJournalEntry]:
        """Load all entries from disk."""
        entries = []
        for f in self._dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                entries.append(TradeJournalEntry(**data))
            except Exception as e:
                logger.warning("Failed to load journal entry %s: %s", f, e)
        return entries

    def get_open_trades(self) -> list[TradeJournalEntry]:
        return [e for e in self.get_all_entries() if e.result in ("", "open")]

    def _persist(self, entry: TradeJournalEntry) -> None:
        """Write entry to disk."""
        filepath = self._dir / f"{entry.trade_id}.json"
        data = entry.model_dump(mode="json")
        # Convert datetime objects to strings for JSON serialization
        filepath.write_text(json.dumps(data, default=str, indent=2))
