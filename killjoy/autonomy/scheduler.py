"""Autonomous scheduler — runs the full KILLJOY pipeline with LLM agents.

Pipeline:
  1. Monitor existing positions
  2. Scan each underlying:
     a. LLM Market Analyst (deterministic features + LLM reasoning)
     b. LLM Strategy Agent (deterministic candidates + LLM selection)
     c. LLM Kill Agent (adversarial testing + debate)
     d. Portfolio Check
     e. Deterministic Risk Engine
     f. Execution (paper only)
  3. Record rejections ("Why Not Trade?")
  4. Log structured observability data
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from killjoy.agent.llm_analyst import analyze_market_llm
from killjoy.agent.llm_kill import kill_test_llm
from killjoy.agent.llm_strategy import generate_proposals_llm
from killjoy.agent.models import (
    AccountSnapshot,
    PositionSnapshot,
    RejectedTrade,
    StrategyType,
    TradeProposal,
    TradeJournalEntry,
)
from killjoy.agent.portfolio_agent import check_portfolio_fit
from killjoy.alpaca.market_data import MarketDataClient, DEFAULT_UNIVERSE
from killjoy.alpaca.options_data import OptionsDataClient
from killjoy.database.rejected import RejectedTradeLog
from killjoy.database.repository import TradeJournal
from killjoy.execution.executor import Executor
from killjoy.llm.provider import LLMProvider
from killjoy.options.contracts import filter_by_dte
from killjoy.portfolio.manager import PortfolioManager
from killjoy.risk.engine import evaluate_risk

logger = logging.getLogger(__name__)


class KilljoyScheduler:
    """Autonomous trading scheduler — the main KILLJOY loop.

    Integrates LLM-backed agents with deterministic safety controls.
    """

    def __init__(
        self,
        market_data: MarketDataClient,
        options_data: OptionsDataClient,
        executor: Executor | None,
        portfolio: PortfolioManager,
        journal: TradeJournal,
        llm: LLMProvider | None = None,
        universe: list[str] | None = None,
        scan_interval: int = 30,
        dry_run: bool = False,
    ) -> None:
        self._market_data = market_data
        self._options_data = options_data
        self._executor = executor
        self._portfolio = portfolio
        self._journal = journal
        self._llm = llm
        self._universe = universe or DEFAULT_UNIVERSE
        self._scan_interval = scan_interval
        self._dry_run = dry_run
        self._running = False
        self._rejected_log = RejectedTradeLog()
        self._run_counter = 0

    def run_once(self) -> dict[str, Any]:
        """Execute one complete scan cycle. Returns summary."""
        self._run_counter += 1
        run_id = f"{datetime.utcnow().strftime('%Y-%m-%d')}-{self._run_counter:05d}"

        logger.info("=== KILLJOY Scan Cycle: RUN %s ===", run_id)
        results: dict[str, Any] = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "universe": self._universe,
            "llm_available": self._llm.is_available if self._llm else False,
            "proposals_generated": 0,
            "proposals_killed": 0,
            "proposals_portfolio_rejected": 0,
            "proposals_risk_rejected": 0,
            "orders_submitted": 0,
            "positions_monitored": 0,
            "rejections_recorded": 0,
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
            "RUN %s complete: %d proposals, %d killed, %d portfolio-rejected, %d risk-rejected, %d submitted, %d rejections recorded",
            run_id,
            results["proposals_generated"],
            results["proposals_killed"],
            results["proposals_portfolio_rejected"],
            results["proposals_risk_rejected"],
            results["orders_submitted"],
            results["rejections_recorded"],
        )
        return results

    def _scan_symbol(self, symbol: str, results: dict) -> None:
        """Scan a single symbol for opportunities."""
        # 1. LLM-enhanced market analysis
        thesis = analyze_market_llm(self._market_data, symbol, self._llm)
        logger.info(
            "ANALYST %s: %s (conf: %s) [%s]",
            symbol,
            thesis.regime.value,
            thesis.confidence,
            "LLM" if (self._llm and self._llm.is_available) else "DETERMINISTIC",
        )

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

        # 3. LLM-enhanced proposal generation
        spot = thesis.current_price
        if spot <= 0:
            return

        proposals = generate_proposals_llm(thesis, contracts, spot, self._llm)
        results["proposals_generated"] += len(proposals)

        # 4. For each proposal, run kill test -> portfolio -> risk -> execute
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

        # Kill test (LLM adversarial)
        kill_decision = kill_test_llm(
            proposal,
            thesis,
            self._portfolio.get_portfolio_context(),
            self._llm,
        )
        logger.info(
            "KILL %s %s: score=%.2f survives=%s confidence=%s [%d objections, %d critical]",
            proposal.underlying,
            proposal.strategy.value,
            kill_decision.kill_score,
            kill_decision.survives,
            kill_decision.confidence,
            len(kill_decision.objections),
            len(kill_decision.critical_failures),
        )

        if not kill_decision.survives:
            self._record_rejection(
                proposal, thesis, kill_decision,
                rejection_reason="kill_agent",
                results=results,
            )
            results["proposals_killed"] += 1
            return

        # Portfolio check
        portfolio_check = self._portfolio.evaluate_trade(proposal)
        if not portfolio_check.approved:
            self._record_rejection(
                proposal, thesis, kill_decision,
                rejection_reason="portfolio",
                portfolio_failures=portfolio_check.reasons,
                results=results,
            )
            logger.info("PORTFOLIO REJECT: %s — %s", proposal.underlying, portfolio_check.reasons)
            results["proposals_portfolio_rejected"] += 1
            return

        # Risk engine (deterministic — final veto authority)
        risk_decision = evaluate_risk(
            proposal,
            buying_power=self._portfolio.buying_power,
            current_positions=self._portfolio.position_count,
        )
        if not risk_decision.approved:
            self._record_rejection(
                proposal, thesis, kill_decision,
                rejection_reason="risk_engine",
                risk_failures=risk_decision.reasons,
                results=results,
            )
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

    def _record_rejection(
        self,
        proposal: TradeProposal,
        thesis,
        kill_decision,
        rejection_reason: str,
        portfolio_failures: list[str] | None = None,
        risk_failures: list[str] | None = None,
        results: dict | None = None,
    ) -> None:
        """Record a rejected trade opportunity for analytics."""
        try:
            rejected = RejectedTrade(
                underlying=proposal.underlying,
                thesis=proposal.thesis,
                proposed_strategy=proposal.strategy.value,
                kill_score=kill_decision.kill_score,
                survives=kill_decision.survives,
                objections=kill_decision.objections,
                critical_failures=kill_decision.critical_failures,
                risk_failures=risk_failures or [],
                portfolio_failures=portfolio_failures or [],
                rejection_reason=rejection_reason,
                debate_transcript=kill_decision.debate_transcript,
            )
            self._rejected_log.record_rejection(rejected)
            if results is not None:
                results["rejections_recorded"] = results.get("rejections_recorded", 0) + 1
        except Exception as e:
            logger.warning("Failed to record rejection: %s", e)

    def run_loop(self) -> None:
        """Run the autonomous loop indefinitely."""
        self._running = True
        logger.info(
            "KILLJOY autonomous loop starting (interval: %ds, dry_run: %s, llm: %s)",
            self._scan_interval,
            self._dry_run,
            self._llm.is_available if self._llm else False,
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
