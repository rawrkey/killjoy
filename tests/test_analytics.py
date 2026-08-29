"""Tests for analytics, events, correlation, and params modules."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from killjoy.agent.models import TradeJournalEntry
from killjoy.analytics.performance import PerformanceAnalytics
from killjoy.analytics.events import EventLog
from killjoy.analytics.correlation import (
    compute_returns,
    compute_correlation,
    PortfolioCorrelation,
)
from killjoy.analytics.params import ParameterManager


# ---------------------------------------------------------------------------
# Performance Analytics Tests
# ---------------------------------------------------------------------------

class TestPerformanceAnalytics:
    def _make_entry(self, pnl: float, result: str = "win", strategy: str = "long_call", underlying: str = "SPY", kill_score: float = 0.8, confidence: float = 0.6) -> TradeJournalEntry:
        return TradeJournalEntry(
            trade_id=f"t-{pnl}",
            underlying=underlying,
            strategy=strategy,
            result=result,
            realized_pnl=Decimal(str(pnl)),
            kill_score=Decimal(str(kill_score)),
            confidence=Decimal(str(confidence)),
        )

    def test_empty_analytics(self):
        a = PerformanceAnalytics([])
        s = a.summary()
        assert s["total_trades"] == 0
        assert s["note"] == "No trades yet"

    def test_win_rate(self):
        entries = [
            self._make_entry(100, "win"),
            self._make_entry(200, "win"),
            self._make_entry(-50, "loss"),
        ]
        a = PerformanceAnalytics(entries)
        s = a.summary()
        assert s["win_rate"] == pytest.approx(2 / 3, abs=0.01)
        assert s["win_count"] == 2
        assert s["loss_count"] == 1

    def test_pnl(self):
        entries = [
            self._make_entry(100, "win"),
            self._make_entry(-50, "loss"),
        ]
        a = PerformanceAnalytics(entries)
        s = a.summary()
        assert s["realized_pnl"] == 50.0

    def test_by_strategy(self):
        entries = [
            self._make_entry(100, "win", strategy="long_call"),
            self._make_entry(-50, "loss", strategy="long_put"),
        ]
        a = PerformanceAnalytics(entries)
        s = a.summary()
        assert "long_call" in s["by_strategy"]
        assert "long_put" in s["by_strategy"]
        assert s["by_strategy"]["long_call"]["total_pnl"] == 100.0

    def test_kill_score_attribution(self):
        entries = [
            self._make_entry(100, "win", kill_score=0.1),
            self._make_entry(-50, "loss", kill_score=0.9),
        ]
        a = PerformanceAnalytics(entries)
        s = a.summary()
        assert "0.0-0.2" in s["kill_score_attribution"]
        assert "0.8-1.0" in s["kill_score_attribution"]


# ---------------------------------------------------------------------------
# Event Log Tests
# ---------------------------------------------------------------------------

class TestEventLog:
    def test_log_and_retrieve(self, tmp_path):
        el = EventLog(log_dir=tmp_path)
        el.log("analysis_started", "run-001", symbol="SPY")
        el.log("kill_completed", "run-001", symbol="SPY", data={"kill_score": 0.5})

        events = el.get_events(run_id="run-001")
        assert len(events) == 2
        assert events[0]["event_type"] == "analysis_started"

    def test_filter_by_type(self, tmp_path):
        el = EventLog(log_dir=tmp_path)
        el.log("analysis_started", "run-001")
        el.log("kill_completed", "run-001")
        el.log("analysis_completed", "run-001")

        events = el.get_events(event_type="kill_completed")
        assert len(events) == 1

    def test_summary(self, tmp_path):
        el = EventLog(log_dir=tmp_path)
        el.log("analysis_started", "run-001")
        el.log("kill_completed", "run-001")
        el.log("analysis_completed", "run-001")

        summary = el.get_summary()
        assert summary["total_events"] == 3
        assert summary["unique_runs"] == 1


# ---------------------------------------------------------------------------
# Correlation Tests
# ---------------------------------------------------------------------------

class TestCorrelation:
    def test_compute_returns(self):
        prices = [100, 102, 101, 105]
        returns = compute_returns(prices)
        assert len(returns) == 3
        assert returns[0] == pytest.approx(0.02, abs=0.001)

    def test_compute_correlation_identical(self):
        series = [0.01, 0.02, -0.01, 0.03]
        corr = compute_correlation(series, series)
        assert corr == pytest.approx(1.0, abs=0.001)

    def test_compute_correlation_opposite(self):
        a = [0.01, 0.02, 0.03]
        b = [-0.01, -0.02, -0.03]
        corr = compute_correlation(a, b)
        assert corr == pytest.approx(-1.0, abs=0.001)

    def test_portfolio_correlation(self):
        pc = PortfolioCorrelation()
        pc.update_prices("SPY", [100, 102, 101, 105, 107])
        pc.update_prices("QQQ", [100, 101, 103, 106, 108])

        corr = pc.get_correlation("SPY", "QQQ")
        assert isinstance(corr, float)
        assert -1 <= corr <= 1

    def test_same_symbol_correlation(self):
        pc = PortfolioCorrelation()
        corr = pc.get_correlation("SPY", "SPY")
        assert corr == 1.0


# ---------------------------------------------------------------------------
# Parameter Manager Tests
# ---------------------------------------------------------------------------

class TestParameterManager:
    def test_default_params(self, tmp_path):
        pm = ParameterManager(params_dir=tmp_path)
        assert pm.get("min_dte") == 7
        assert pm.get("min_reward_risk") == 1.0

    def test_recommend_and_apply(self, tmp_path):
        pm = ParameterManager(params_dir=tmp_path)
        rec = pm.recommend(
            "min_dte", 14,
            reason="Testing",
            evidence="Test data",
            confidence=0.8,
        )
        assert rec.parameter == "min_dte"

        applied = pm.apply_recommendation(rec, min_confidence=0.6)
        assert applied is True
        assert pm.get("min_dte") == 14

    def test_reject_out_of_bounds(self, tmp_path):
        pm = ParameterManager(params_dir=tmp_path)
        with pytest.raises(ValueError, match="outside bounds"):
            pm.recommend("min_dte", 200, reason="Test", evidence="Test")

    def test_reject_low_confidence(self, tmp_path):
        pm = ParameterManager(params_dir=tmp_path)
        rec = pm.recommend(
            "min_dte", 14,
            reason="Testing",
            evidence="Test data",
            confidence=0.3,
        )
        applied = pm.apply_recommendation(rec, min_confidence=0.6)
        assert applied is False
        assert pm.get("min_dte") == 7  # unchanged

    def test_revert(self, tmp_path):
        pm = ParameterManager(params_dir=tmp_path)
        rec = pm.recommend("min_dte", 14, reason="Test", evidence="Test", confidence=0.9)
        pm.apply_recommendation(rec, min_confidence=0.5)
        assert pm.get("min_dte") == 14

        pm.revert_last()
        assert pm.get("min_dte") == 7
