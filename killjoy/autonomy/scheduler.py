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
import re
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from killjoy.agent.llm_analyst import analyze_market_llm
from killjoy.agent.llm_kill import kill_test_llm

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
from killjoy.analytics.counterfactual import CounterfactualPortfolio
from killjoy.analytics.disagreement import compute_disagreement, disagreement_to_dict
from killjoy.analytics.events import EventLog
from killjoy.analytics.graveyard import StrategyGraveyard
from killjoy.analytics.receipts import DecisionReceiptManager
from killjoy.analytics.reports import CycleReportBuilder, save_report
from killjoy.database.rejected import RejectedTradeLog
from killjoy.database.repository import TradeJournal
from killjoy.execution.executor import Executor
from killjoy.llm.provider import LLMProvider
from killjoy.options.contracts import filter_by_dte
from killjoy.portfolio.manager import PortfolioManager
from killjoy.risk.engine import evaluate_risk

logger = logging.getLogger(__name__)


def _extract_underlying(option_symbol: str) -> str:
    """Extract root underlying from an OCC option symbol.

    Example: AAPL261002P00305000 -> AAPL, NVDA261002C00230000 -> NVDA
    """
    m = re.match(r"^([A-Z]+)\d{6}[CP]\d+", option_symbol)
    return m.group(1) if m else option_symbol


class KilljoyScheduler:
    """Autonomous trading scheduler — the main KILLJOY loop.

    Integrates LLM-backed agents with deterministic safety controls.
    """
    _run_lock = threading.Lock()  # Prevent concurrent cron executions

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
        self._event_log = EventLog()
        self._counterfactual = CounterfactualPortfolio()
        self._graveyard = StrategyGraveyard()
        self._receipts = DecisionReceiptManager()
        self._report = CycleReportBuilder()
        self._run_counter = 0

    def run_once(self) -> dict[str, Any]:
        """Execute one complete scan cycle. Returns summary."""
        if not KilljoyScheduler._run_lock.acquire(blocking=False):
            logger.warning("Another cycle already running — skipping")
            return {"skipped": True, "reason": "concurrent_execution"}
        try:
            return self._run_once_inner()
        finally:
            KilljoyScheduler._run_lock.release()

    def _run_once_inner(self) -> dict[str, Any]:
        """Internal scan cycle execution."""
        self._run_counter += 1
        self._report = CycleReportBuilder()
        run_id = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{self._run_counter:05d}"

        logger.info("=== KILLJOY Scan Cycle: RUN %s ===", run_id)
        self._event_log.log("analysis_started", run_id)
        results: dict[str, Any] = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
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

        # 1. Monitor existing positions — evaluate for exit
        open_trades = self._journal.get_open_trades()
        results["positions_monitored"] = len(open_trades)
        results["positions_closed"] = 0
        self._report.set_positions_checked(len(open_trades))

        # 1a. EOD strategy: sell profitable positions before close
        eod_closed_symbols: set[str] = set()
        try:
            from datetime import timedelta as _td
            try:
                from zoneinfo import ZoneInfo
                et = datetime.now(ZoneInfo("America/New_York"))
            except Exception:
                # Fallback: use UTC and manually compute Eastern time
                utc_now = datetime.now(timezone.utc)
                # Approximate EST/EDT: EST = UTC-5, EDT = UTC-4
                # DST starts 2nd Sunday of March, ends 1st Sunday of November
                month, day, weekday = utc_now.month, utc_now.day, utc_now.weekday()
                is_dst = (
                    (month > 3 or (month == 3 and day >= 8 and weekday == 6))
                    and (month < 11 or (month == 11 and day < 8 and weekday != 6))
                )
                offset_hours = -4 if is_dst else -5
                et = utc_now + _td(hours=offset_hours)
            market_close = et.replace(hour=16, minute=0, second=0, microsecond=0)
            minutes_to_close = (market_close - et).total_seconds() / 60

            if 0 <= minutes_to_close <= 5:
                # Near market close — EOD logic
                total_pnl = sum(
                    float(getattr(p, "unrealized_pl", 0) or 0)
                    for p in self._portfolio._positions
                )
                logger.info("EOD: %.0f min to close, total P&L: $%.2f", minutes_to_close, total_pnl)

                for pos_snap in list(self._portfolio._positions):
                    sym_pnl = float(getattr(pos_snap, "unrealized_pl", 0) or 0)
                    should_close = (total_pnl > 0) and (sym_pnl > 0)
                    if should_close:
                        logger.info("EOD CLOSE %s: P&L $%.2f (portfolio: $%.2f)", pos_snap.symbol, sym_pnl, total_pnl)
                        if not self._dry_run and self._executor:
                            order_result = self._executor.close_position(pos_snap.symbol)
                            if order_result.status != "failed":
                                # Find matching journal entry and record exit
                                matched = False
                                for trade in open_trades:
                                    if trade.underlying == _extract_underlying(pos_snap.symbol):
                                        self._journal.record_exit(trade.trade_id, sym_pnl, "closed_eod", order_result.order_id)
                                        matched = True
                                        break
                                if not matched:
                                    logger.warning("EOD: no journal match for %s — exit not recorded", pos_snap.symbol)
                                results["positions_closed"] += 1
                                eod_closed_symbols.add(_extract_underlying(pos_snap.symbol))
                                self._event_log.log("eod_close", run_id, symbol=pos_snap.symbol, data={
                                    "pnl": sym_pnl,
                                    "portfolio_pnl": total_pnl,
                                })
                        else:
                            logger.info("EOD DRY RUN: Would close %s", pos_snap.symbol)
                            results["positions_closed"] += 1
                            eod_closed_symbols.add(_extract_underlying(pos_snap.symbol))
        except Exception as e:
            logger.debug("EOD check skipped: %s", e)

        for trade in open_trades:
            try:
                symbol = trade.underlying
                if not symbol:
                    continue

                # Skip positions already closed by EOD
                if symbol in eod_closed_symbols:
                    continue

                # Find matching position from portfolio
                pos_snap = None
                for p in self._portfolio._positions:
                    if _extract_underlying(p.symbol) == symbol:
                        pos_snap = p
                        break

                if pos_snap is None:
                    continue

                from killjoy.monitoring.position_monitor import evaluate_position
                # Pass high_water_mark and days_held from journal
                hwm = trade.high_water_mark
                days_held = trade.days_held
                action, reason = evaluate_position(pos_snap, high_water_mark=hwm, days_held=days_held)

                # Update high water mark and days held in journal
                current_pnl = Decimal(str(pos_snap.unrealized_pl))
                if current_pnl > hwm:
                    hwm = current_pnl
                trade_id = trade.trade_id
                if trade_id:
                    from datetime import datetime as dt
                    entry_time = trade.timestamp
                    if entry_time:
                        try:
                            if isinstance(entry_time, str):
                                entry_dt = dt.fromisoformat(entry_time.replace("Z", "+00:00"))
                            else:
                                entry_dt = entry_time
                            days_held = (dt.now(timezone.utc) - entry_dt).days
                        except (ValueError, TypeError):
                            days_held = 0
                    self._journal.update_entry(trade_id, high_water_mark=hwm, days_held=days_held)

                if action == "exit":
                    logger.info("AUTO-SELL %s: %s", symbol, reason)
                    self._event_log.log("exit_signal", run_id, symbol=symbol, data={"reason": reason})

                    if not self._dry_run and self._executor:
                        order_result = self._executor.close_position(pos_snap.symbol)
                        if order_result.status != "failed":
                            # Record exit in journal
                            realized_pnl = float(pos_snap.unrealized_pl)
                            self._journal.record_exit(trade.trade_id, realized_pnl, "closed", order_result.order_id)
                            results["positions_closed"] += 1
                            # Update graveyard with actual outcome
                            strategy_type = trade.strategy or "unknown"
                            self._graveyard.record_trade(
                                strategy_type,
                                won=realized_pnl > 0,
                                pnl=realized_pnl,
                            )
                            self._event_log.log("position_closed", run_id, symbol=symbol, data={
                                "pnl": realized_pnl,
                                "reason": reason,
                                "order_id": order_result.order_id,
                            })
                            logger.info("CLOSED %s: P&L $%.2f — %s", symbol, realized_pnl, reason)
                            self._report.add_position_close(
                                symbol, reason, realized_pnl,
                                strategy=trade.strategy,
                            )
                    else:
                        logger.info("DRY RUN: Would close %s — %s", symbol, reason)
                        results["positions_closed"] += 1
            except Exception as e:
                logger.warning("Error evaluating position: %s", e)

        # 2. Scan each underlying (3 symbols max for speed)
        for i, symbol in enumerate(self._universe[:3]):
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
        self._event_log.log("analysis_completed", run_id, data=results)

        # Save report
        self._report.set_summary(
            mode="dry_run" if self._dry_run else "live",
            run_id=run_id,
            llm="active" if (self._llm and self._llm.is_available) else "deterministic",
        )
        try:
            save_report(self._report.build())
        except Exception as e:
            logger.warning("Failed to save cycle report: %s", e)

        return results

    def _scan_symbol(self, symbol: str, results: dict) -> None:
        """Scan a single symbol for opportunities."""
        run_id = results.get("run_id", "")
        # 1. LLM-enhanced market analysis
        self._event_log.log("analysis_started", run_id, symbol=symbol)
        thesis = analyze_market_llm(self._market_data, symbol, self._llm)
        logger.info(
            "ANALYST %s: %s (conf: %s) [%s]",
            symbol,
            thesis.regime.value,
            thesis.confidence,
            thesis.source.upper(),
        )
        self._report.add_symbol_analysis(
            symbol=symbol,
            regime=thesis.regime.value,
            confidence=float(thesis.confidence),
            price=float(thesis.current_price),
            thesis=thesis.thesis or "",
            observations=thesis.observations or [],
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

        # 3. Proposal generation (deterministic — fast, no LLM)
        spot = thesis.current_price
        if spot <= 0:
            return

        from killjoy.agent.strategy_agent import generate_proposals
        proposals = generate_proposals(thesis, contracts, spot)
        results["proposals_generated"] += len(proposals)

        # 4. For each proposal, run kill test -> portfolio -> risk -> execute
        for proposal in proposals[:1]:  # Limit to top 1 per symbol for speed
            self._process_proposal(proposal, thesis, results)

    def _process_proposal(self, proposal: TradeProposal, thesis, results: dict) -> None:
        """Run the full pipeline for a single proposal."""
        run_id = results.get("run_id", "")
        logger.info(
            "Processing %s %s (R/R: %s, conf: %s)",
            proposal.underlying,
            proposal.strategy.value,
            proposal.reward_risk,
            proposal.confidence,
        )
        self._event_log.log("proposal_created", run_id, symbol=proposal.underlying, data={
            "strategy": proposal.strategy.value,
            "reward_risk": float(proposal.reward_risk),
            "confidence": float(proposal.confidence),
        })

        # Kill test (LLM adversarial)
        self._event_log.log("kill_started", run_id, symbol=proposal.underlying)
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
        self._event_log.log("kill_completed", run_id, symbol=proposal.underlying, data={
            "kill_score": float(kill_decision.kill_score),
            "survives": kill_decision.survives,
            "objections_count": len(kill_decision.objections),
            "critical_count": len(kill_decision.critical_failures),
            "debate_rounds": len(kill_decision.debate_transcript),
        })

        # Kill check — if killed, reject and move on
        if not kill_decision.survives:
            self._record_rejection(
                proposal, thesis, kill_decision,
                rejection_reason="kill_agent",
                results=results,
            )
            logger.info("KILLED: %s %s (score: %.2f)", proposal.underlying, proposal.strategy.value, kill_decision.kill_score)
            results["proposals_killed"] += 1
            return

        # Portfolio check
        portfolio_check = self._portfolio.evaluate_trade(proposal)
        self._event_log.log("portfolio_checked", run_id, symbol=proposal.underlying, data={
            "approved": portfolio_check.approved,
            "reasons": portfolio_check.reasons,
        })
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
        # Compute daily P&L from journal
        daily_pnl = Decimal("0")
        try:
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            for entry in self._journal.get_all_entries():
                entry_ts = entry.timestamp
                if isinstance(entry_ts, str):
                    entry_ts = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
                if entry_ts.strftime("%Y-%m-%d") == today_str:
                    daily_pnl += entry.realized_pnl
        except Exception:
            pass

        risk_decision = evaluate_risk(
            proposal,
            buying_power=self._portfolio.buying_power,
            daily_pnl=daily_pnl,
            current_positions=self._portfolio.position_count,
        )
        self._event_log.log("risk_checked", run_id, symbol=proposal.underlying, data={
            "approved": risk_decision.approved,
            "failed_checks": len(risk_decision.failed_checks),
        })
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

        # Compute agent disagreement
        disagreement = compute_disagreement(
            analyst_score=thesis.confidence,
            analyst_stance="bullish" if "up" in thesis.regime.value else "bearish" if "down" in thesis.regime.value else "neutral",
            strategy_score=proposal.confidence,
            strategy_stance="bullish" if proposal.strategy in (StrategyType.LONG_CALL, StrategyType.BULL_CALL_SPREAD) else "bearish" if proposal.strategy in (StrategyType.LONG_PUT, StrategyType.BEAR_PUT_SPREAD) else "neutral",
            kill_score=Decimal("1") - kill_decision.kill_score,
            kill_stance="approve" if kill_decision.survives else "reject",
            portfolio_approved=portfolio_check.approved,
            risk_approved=risk_decision.approved,
        )

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

        # Generate decision receipt
        agent_scores = {
            "analyst": thesis.confidence,
            "strategy": proposal.confidence,
            "kill_agent": Decimal("1") - kill_decision.kill_score,
            "disagreement": disagreement.disagreement_index,
        }
        receipt = self._receipts.create_receipt(
            proposal=proposal,
            thesis=thesis,
            kill_decision=kill_decision,
            risk_decision=risk_decision,
            portfolio_approved=portfolio_check.approved,
            portfolio_reasons=portfolio_check.reasons,
            agent_scores=agent_scores,
        )

        # Track for report
        submitted = False
        order_id = ""

        # Execute
        if self._dry_run:
            logger.info("DRY RUN: Would execute %s %s", proposal.underlying, proposal.strategy.value)
            results["orders_submitted"] += 1
            submitted = True
        elif self._executor:
            order_result = self._executor.execute_proposal(proposal, self._portfolio.buying_power)
            entry.order_result = order_result
            self._journal.record_entry(entry)
            if order_result.status != "failed":
                results["orders_submitted"] += 1
                submitted = True
                order_id = order_result.order_id
                # Record in graveyard (outcome pending until close)
                self._graveyard.record_trade(
                    proposal.strategy.value,
                    won=False,
                    pnl=0,
                )
                # Update receipt with order ID
                self._receipts.update_outcome(receipt.receipt_id, 0, "open")
                self._event_log.log("order_submitted", run_id, symbol=proposal.underlying, data={
                    "order_id": order_result.order_id,
                    "status": order_result.status,
                })
                logger.info("ORDER SUBMITTED: %s — %s", proposal.underlying, order_result.order_id)
            else:
                self._event_log.log("order_failed", run_id, symbol=proposal.underlying, data={
                    "error": order_result.error,
                })
                logger.warning("ORDER FAILED: %s — %s", proposal.underlying, order_result.error)

        # Add to report
        self._report.add_proposal(
            symbol=proposal.underlying,
            strategy=proposal.strategy.value,
            analyst_score=float(thesis.confidence),
            analyst_stance=thesis.regime.value,
            analyst_thesis=thesis.thesis or "",
            kill_score=float(kill_decision.kill_score),
            survives=kill_decision.survives,
            kill_reasons=kill_decision.kill_reasons,
            kill_objections=kill_decision.objections,
            kill_critical=kill_decision.critical_failures,
            debate_rounds=len(kill_decision.debate_transcript),
            portfolio_approved=portfolio_check.approved,
            portfolio_reasons=portfolio_check.reasons,
            risk_approved=risk_decision.approved,
            risk_reasons=risk_decision.reasons,
            risk_checks=[{"name": c.name, "passed": c.passed, "reason": c.reason} for c in risk_decision.checks],
            submitted=submitted,
            order_id=order_id,
        )

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
        """Record a rejected trade opportunity for analytics and counterfactual tracking."""
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

            # Record in counterfactual portfolio
            self._counterfactual.record_rejection(rejected)

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
