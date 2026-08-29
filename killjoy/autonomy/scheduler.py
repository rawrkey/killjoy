"""Autonomous scheduler — runs the full KILLJOY pipeline on a loop."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Any

from killjoy.agent.analyst import analyze_market
from killjoy.agent.kill_agent import kill_test
from killjoy.agent.models import (
    AccountSnapshot,
    PositionSnapshot,
    StrategyType,
    TradeProposal,
    TradeJournalEntry,
)
from killjoy.agent.portfolio_agent import check_portfolio_fit
from killjoy.agent.strategy_agent import generate_proposals
from killjoy.alpaca.market_data import MarketDataClient, DEFAULT_UNIVERSE
from killjoy.alpaca.options_data import OptionsDataClient
from killjoy.database.repository import TradeJournal
from killjoy.execution.executor import Executor
from killjoy.options.contracts import filter_by_dte
from killjoy.portfolio.manager import PortfolioManager
from killjoy.risk.engine import evaluate_risk

logger = logging.getLogger(__name__)


class KilljoyScheduler:
    """Autonomous trading scheduler — the main KILLJOY loop."""

    def __init__(
        self,
        market_data: MarketDataClient,
        options_data: OptionsDataClient,
        executor: Executor | None,
        portfolio: PortfolioManager,
        journal: TradeJournal,
        universe: list[str] | None = None,
        scan_interval: int = 300,
        dry_run: bool = False,
    ) -> None:
        self._market_data = market_data
        self._options_data = options_data
        self._executor = executor
        self._portfolio = portfolio
        self._journal = journal
        self._universe = universe or DEFAULT_UNIVERSE
        self._scan_interval = scan_interval
        self._dry_run = dry_run
        self._running = False

    def run_once(self) -> dict[str, Any]:
        """Execute one complete scan cycle. Returns summary."""
        logger.info("=== KILLJOY Scan Cycle: %s ===", datetime.utcnow().isoformat())
        results: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "universe": self._universe,
            "proposals_generated": 0,
            "proposals_killed": 0,
            "proposals_risk_rejected": 0,
            "orders_submitted": 0,
            "positions_monitored": 0,
        }

        # 1. Monitor existing positions
        open_trades = self._journal.get_open_trades()
        results["positions_monitored"] = len(open_trades)

        # 2. Scan each underlying
        for symbol in self._universe:
            try:
                self._scan_symbol(symbol, results)
            except Exception as e:
                logger.warning("Error scanning %s: %s", symbol, e)

        logger.info(
            "Scan complete: %d proposals, %d killed, %d risk-rejected, %d submitted",
            results["proposals_generated"],
            results["proposals_killed"],
            results["proposals_risk_rejected"],
            results["orders_submitted"],
        )
        return results

    def _scan_symbol(self, symbol: str, results: dict) -> None:
        """Scan a single symbol for opportunities."""
        # 1. Analyze market
        thesis = analyze_market(self._market_data, symbol)
        logger.info("Analysis for %s: %s (conf: %s)", symbol, thesis.regime.value, thesis.confidence)

        # 2. Get options chain
        from datetime import date, timedelta
        today = date.today()
        contracts = self._options_data.get_option_chain(
            underlying=symbol,
            expiration_date_gte=today,
            expiration_date_lte=today + timedelta(days=60),
        )

        if not contracts:
            logger.info("No options contracts found for %s", symbol)
            return

        # Filter by DTE
        contracts = filter_by_dte(contracts, min_dte=7, max_dte=45)
        if not contracts:
            logger.info("No contracts in DTE range for %s", symbol)
            return

        # 3. Generate proposals
        spot = thesis.current_price
        if spot <= 0:
            return

        proposals = generate_proposals(thesis, contracts, spot)
        results["proposals_generated"] += len(proposals)

        # 4. For each proposal, run kill test → portfolio → risk → execute
        for proposal in proposals[:2]:  # Limit to top 2 per symbol
            self._process_proposal(proposal, thesis, results)

    def _process_proposal(self, proposal: TradeProposal, thesis, results: dict) -> None:
        """Run the full pipeline for a single proposal."""
        logger.info(
            "Processing %s %s (R/R: %s, conf: %s)",
            proposal.underlying,
            proposal.strategy.value,
            proposal.reward_risk,
            proposal.confidence,
        )

        # Kill test
        kill_decision = kill_test(proposal, thesis, self._portfolio.get_portfolio_context())
        if not kill_decision.survives:
            logger.info("KILLED: %s — %s", proposal.underlying, kill_decision.kill_reasons)
            results["proposals_killed"] += 1
            return

        # Portfolio check
        portfolio_check = self._portfolio.evaluate_trade(proposal)
        if not portfolio_check.approved:
            logger.info("PORTFOLIO REJECT: %s — %s", proposal.underlying, portfolio_check.reasons)
            results["proposals_risk_rejected"] += 1
            return

        # Risk engine
        risk_decision = evaluate_risk(
            proposal,
            buying_power=self._portfolio.buying_power,
            current_positions=self._portfolio.position_count,
        )
        if not risk_decision.approved:
            logger.info("RISK REJECT: %s — %s", proposal.underlying, risk_decision.reasons)
            results["proposals_risk_rejected"] += 1
            return

        # Record in journal
        entry = TradeJournalEntry(
            underlying=proposal.underlying,
            strategy=proposal.strategy.value,
            legs=proposal.legs,
            thesis=proposal.thesis,
            confidence=proposal.confidence,
            kill_score=kill_decision.kill_score,
            kill_reasons=kill_decision.kill_reasons,
            risk_decision=risk_decision,
            result="open",
        )
        self._journal.record_entry(entry)

        # Execute
        if self._dry_run:
            logger.info("DRY RUN: Would execute %s %s", proposal.underlying, proposal.strategy.value)
            results["orders_submitted"] += 1
            return

        if self._executor:
            order_result = self._executor.execute_proposal(proposal)
            entry.order_result = order_result
            self._journal.record_entry(entry)
            if order_result.status != "failed":
                results["orders_submitted"] += 1
                logger.info("ORDER SUBMITTED: %s — %s", proposal.underlying, order_result.order_id)
            else:
                logger.warning("ORDER FAILED: %s — %s", proposal.underlying, order_result.error)

    def run_loop(self) -> None:
        """Run the autonomous loop indefinitely."""
        self._running = True
        logger.info(
            "KILLJOY autonomous loop starting (interval: %ds, dry_run: %s)",
            self._scan_interval,
            self._dry_run,
        )

        while self._running:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("Interrupted — shutting down")
                break
            except Exception as e:
                logger.error("Scan cycle error: %s", e)

            logger.info("Next scan in %d seconds...", self._scan_interval)
            time.sleep(self._scan_interval)

    def stop(self) -> None:
        self._running = False
