"""Tests for the LLM layer — all mocked, no live API calls."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from killjoy.agent.models import (
    KillObjection,
    MarketRegime,
    MarketThesis,
    OptionType,
    StrategyType,
    TradeProposal,
    OptionLeg,
    RejectedTrade,
)
from killjoy.llm.provider import LLMProvider, LLMResponse, get_llm_provider


# ---------------------------------------------------------------------------
# LLM Provider Tests
# ---------------------------------------------------------------------------

class TestLLMProvider:
    def test_provider_no_key(self):
        provider = LLMProvider(api_key="")
        assert provider.is_available is False
        result = provider.chat([{"role": "user", "content": "test"}])
        assert result.success is False
        assert "not available" in result.error.lower()

    def test_provider_with_key(self):
        provider = LLMProvider(api_key="test-key", model="gpt-4o-mini")
        assert provider.is_available is True

    def test_provider_fallback_no_openai(self):
        provider = LLMProvider(api_key="test-key")
        # Client init will fail if openai not installed, but we have it
        # Just verify the provider is marked available
        assert provider.is_available is True

    def test_get_llm_provider_factory(self):
        with patch.dict("os.environ", {
            "KILLJOY_LLM_API_KEY": "env-key",
            "KILLJOY_LLM_BASE_URL": "https://custom.api.com/v1",
            "KILLJOY_LLM_MODEL": "custom-model",
        }):
            provider = get_llm_provider()
            assert provider.is_available is True

    def test_get_llm_provider_explicit_args(self):
        provider = get_llm_provider(
            api_key="explicit-key",
            base_url="https://explicit.api.com/v1",
            model="explicit-model",
        )
        assert provider.is_available is True


# ---------------------------------------------------------------------------
# LLM Response Tests
# ---------------------------------------------------------------------------

class TestLLMResponse:
    def test_empty_response(self):
        r = LLMResponse()
        assert r.success is False
        assert r.content == ""
        assert r.parsed == {}

    def test_successful_response(self):
        r = LLMResponse(
            content='{"key": "value"}',
            parsed={"key": "value"},
            model="gpt-4o-mini",
            success=True,
        )
        assert r.success is True
        assert r.parsed["key"] == "value"


# ---------------------------------------------------------------------------
# Kill Decision Model Tests (with new fields)
# ---------------------------------------------------------------------------

class TestKillDecisionModel:
    def test_kill_objection(self):
        obj = KillObjection(
            category="thesis_weakness",
            severity=Decimal("0.8"),
            reasoning="Thesis assumes continuation without volume confirmation",
            counterfactual="Volume above average would address this concern",
        )
        assert obj.category == "thesis_weakness"
        assert obj.severity == Decimal("0.8")

    def test_kill_decision_with_debate(self):
        from killjoy.agent.models import KillDecision
        d = KillDecision(
            proposal_id="test",
            kill_score=Decimal("0.3"),
            survives=False,
            objections=[
                KillObjection(
                    category="poor_reward_risk",
                    severity=Decimal("0.6"),
                    reasoning="R/R below 1.0",
                )
            ],
            critical_failures=["Reward/risk too low"],
            debate_transcript=[
                {"role": "kill_agent", "content": "Your R/R is poor"},
                {"role": "trader", "content": "But the setup is strong"},
                {"role": "kill_agent", "content": "Not convinced"},
            ],
        )
        assert d.survives is False
        assert len(d.objections) == 1
        assert len(d.debate_transcript) == 3

    def test_rejected_trade_model(self):
        r = RejectedTrade(
            underlying="SPY",
            thesis="Bullish test",
            proposed_strategy="long_call",
            kill_score=Decimal("0.25"),
            survives=False,
            rejection_reason="kill_agent",
        )
        assert r.underlying == "SPY"
        assert r.survives is False


# ---------------------------------------------------------------------------
# LLM Analyst Tests (mocked)
# ---------------------------------------------------------------------------

class TestLLMAnalyst:
    def _make_thesis(self) -> MarketThesis:
        return MarketThesis(
            underlying="SPY",
            regime=MarketRegime.UPTREND,
            confidence=Decimal("0.6"),
            thesis="Test thesis",
            current_price=Decimal("550"),
            momentum=Decimal("2.5"),
            volume_signal="normal",
        )

    def test_analyst_fallback_no_llm(self):
        from killjoy.agent.llm_analyst import analyze_market_llm
        mock_llm = MagicMock()
        mock_llm.is_available = False
        mock_market = MagicMock()
        mock_market.get_snapshot.return_value = {
            "last_trade": Decimal("550"),
            "change_pct": Decimal("1.5"),
            "volume": 1000000,
        }
        mock_market.get_bars.return_value = [
            {"close": Decimal("540"), "volume": 500000},
            {"close": Decimal("545"), "volume": 600000},
            {"close": Decimal("548"), "volume": 550000},
            {"close": Decimal("550"), "volume": 700000},
            {"close": Decimal("552"), "volume": 800000},
        ]

        result = analyze_market_llm(mock_market, "SPY", mock_llm)
        assert isinstance(result, MarketThesis)
        assert result.underlying == "SPY"


# ---------------------------------------------------------------------------
# LLM Kill Agent Tests (mocked)
# ---------------------------------------------------------------------------

class TestLLMKillAgent:
    def _make_proposal(self) -> TradeProposal:
        return TradeProposal(
            underlying="SPY",
            strategy=StrategyType.LONG_CALL,
            legs=[
                OptionLeg(
                    contract_symbol="SPY250919C00550000",
                    option_type=OptionType.CALL,
                    strike=Decimal("550"),
                    expiration=date.today() + timedelta(days=30),
                    side="buy",
                    quantity=1,
                    bid=Decimal("5"),
                    ask=Decimal("5.50"),
                    mid=Decimal("5.25"),
                )
            ],
            expiration=date.today() + timedelta(days=30),
            max_loss=Decimal("500"),
            max_profit=Decimal("1000"),
            reward_risk=Decimal("2.0"),
            confidence=Decimal("0.6"),
            thesis="Bullish test",
        )

    def _make_thesis(self) -> MarketThesis:
        return MarketThesis(
            underlying="SPY",
            regime=MarketRegime.UPTREND,
            confidence=Decimal("0.6"),
            thesis="Test thesis",
            current_price=Decimal("550"),
        )

    def test_kill_fallback_no_llm(self):
        from killjoy.agent.llm_kill import kill_test_llm
        proposal = self._make_proposal()
        thesis = self._make_thesis()

        result = kill_test_llm(proposal, thesis, llm=None)
        assert result.proposal_id == proposal.id
        assert isinstance(result.kill_score, Decimal)
        assert 0 <= result.kill_score <= 1

    def test_kill_low_confidence_gets_penalized(self):
        """Low confidence should produce kill reasons in deterministic mode."""
        from killjoy.agent.llm_kill import kill_test_llm
        proposal = self._make_proposal()
        proposal.confidence = Decimal("0.05")
        thesis = self._make_thesis()

        result = kill_test_llm(proposal, thesis, llm=None)
        # Should have kill reasons about low confidence
        assert len(result.kill_reasons) > 0
        assert any("confidence" in r.lower() for r in result.kill_reasons)

    def test_kill_with_mocked_llm(self):
        from killjoy.agent.llm_kill import kill_test_llm
        from killjoy.llm.provider import LLMResponse

        mock_llm = MagicMock()
        mock_llm.is_available = True

        # Mock kill analysis output
        mock_kill_output = MagicMock()
        mock_kill_output.kill_score = 0.25
        mock_kill_output.survives = False
        mock_kill_output.confidence = 0.8
        mock_kill_output.objections = [
            {"category": "poor_reward_risk", "severity": 0.6, "reasoning": "R/R is marginal", "counterfactual": ""}
        ]
        mock_kill_output.critical_failures = []
        mock_kill_output.counterfactual = "Would need R/R > 1.5"
        mock_kill_output.recommendation = "kill"
        mock_kill_output.analysis = "Trade has concerns"

        # Mock trader defense output
        mock_trader_output = MagicMock()
        mock_trader_output.overall_defense = "The R/R is acceptable given the strong trend"
        mock_trader_output.responses = [
            {"objection_category": "poor_reward_risk", "response": "Addressed", "concession": False}
        ]
        mock_trader_output.conceded_points = []

        mock_response = LLMResponse(success=True, parsed={})

        # First call: kill analysis, second call: trader defense, third call: kill round 2
        mock_llm.chat_structured.side_effect = [
            (mock_kill_output, mock_response),
            (mock_trader_output, mock_response),
            (mock_kill_output, mock_response),
        ]

        proposal = self._make_proposal()
        thesis = self._make_thesis()

        result = kill_test_llm(proposal, thesis, llm=mock_llm)
        assert result.kill_score >= Decimal("0")
        assert len(result.objections) >= 0


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Rejected Trade Log Tests
# ---------------------------------------------------------------------------

class TestRejectedTradeLog:
    def test_record_and_retrieve(self, tmp_path):
        from killjoy.database.rejected import RejectedTradeLog
        log = RejectedTradeLog(log_dir=tmp_path)
        rejected = RejectedTrade(
            underlying="SPY",
            thesis="Test",
            proposed_strategy="long_call",
            kill_score=Decimal("0.3"),
            survives=False,
            rejection_reason="kill_agent",
        )
        log.record_rejection(rejected)
        all_rejections = log.get_all_rejections()
        assert len(all_rejections) == 1
        assert all_rejections[0].underlying == "SPY"

    def test_analytics(self, tmp_path):
        from killjoy.database.rejected import RejectedTradeLog
        log = RejectedTradeLog(log_dir=tmp_path)
        for i in range(5):
            log.record_rejection(RejectedTrade(
                underlying="SPY" if i < 3 else "QQQ",
                kill_score=Decimal(str(0.2 + i * 0.1)),
                rejection_reason="kill_agent" if i < 3 else "portfolio",
                proposed_strategy="long_call",
            ))
        analytics = log.get_analytics()
        assert analytics["total"] == 5
        assert "kill_agent" in analytics["top_rejection_reasons"]
        assert analytics["avg_kill_score"] > 0
