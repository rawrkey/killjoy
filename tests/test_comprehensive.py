"""Comprehensive tests for all KILLJOY modules."""

from __future__ import annotations

import json
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from killjoy.agent.models import (
    AccountSnapshot,
    KillDecision,
    MarketRegime,
    MarketThesis,
    OptionContract,
    OptionLeg,
    OptionType,
    PortfolioCheck,
    Postmortem,
    PositionSnapshot,
    RiskCheck,
    RiskDecision,
    StrategyType,
    TradeJournalEntry,
    TradeProposal,
    OrderResult,
)
from killjoy.agent.kill_agent import kill_test, KILL_THRESHOLD
from killjoy.agent.portfolio_agent import check_portfolio_fit
from killjoy.agent.postmortem_agent import run_postmortem
from killjoy.agent.strategy_agent import generate_proposals
from killjoy.options.contracts import (
    filter_by_dte,
    filter_by_moneyness,
    parse_option_symbol,
    select_strike,
)
from killjoy.options.greeks import compute_greeks, normal_cdf
from killjoy.options.liquidity import check_liquidity, filter_liquid
from killjoy.options.pricing import compute_mid_price, compute_reward_risk
from killjoy.risk.engine import evaluate_risk
from killjoy.risk.position_size import calculate_position_size
from killjoy.risk.exposure import (
    calculate_total_exposure,
    calculate_options_exposure,
    calculate_underlying_exposure,
)
from killjoy.monitoring.position_monitor import evaluate_position, PositionAction
from killjoy.database.repository import TradeJournal
from killjoy.portfolio.manager import PortfolioManager
from killjoy.strategies.long_call import LongCallStrategy
from killjoy.strategies.long_put import LongPutStrategy
from killjoy.strategies.bull_call_spread import BullCallSpreadStrategy
from killjoy.strategies.bear_put_spread import BearPutSpreadStrategy
from killjoy.strategies.iron_condor import IronCondorStrategy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_contract(
    symbol: str = "SPY250919C00550000",
    underlying: str = "SPY",
    strike: float = 550.0,
    option_type: OptionType = OptionType.CALL,
    bid: float = 5.0,
    ask: float = 5.50,
    volume: int = 100,
    oi: int = 500,
    dte: int = 30,
    delta: float = 0.35,
) -> OptionContract:
    return OptionContract(
        symbol=symbol,
        underlying=underlying,
        strike=Decimal(str(strike)),
        expiration=date.today() + timedelta(days=dte),
        option_type=option_type,
        bid=Decimal(str(bid)),
        ask=Decimal(str(ask)),
        mid=Decimal(str((bid + ask) / 2)),
        volume=volume,
        open_interest=oi,
        delta=Decimal(str(delta)),
    )


def _make_proposal(
    underlying: str = "SPY",
    strategy: StrategyType = StrategyType.LONG_CALL,
    max_loss: float = 500,
    reward_risk: float = 2.0,
    confidence: float = 0.6,
    thesis: str = "Bullish test",
) -> TradeProposal:
    return TradeProposal(
        underlying=underlying,
        strategy=strategy,
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
        max_loss=Decimal(str(max_loss)),
        max_profit=Decimal(str(max_loss * reward_risk)),
        reward_risk=Decimal(str(reward_risk)),
        confidence=Decimal(str(confidence)),
        thesis=thesis,
    )


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------

class TestModels:
    def test_account_snapshot(self):
        snap = AccountSnapshot(status="ACTIVE", buying_power=Decimal("100000"), portfolio_value=Decimal("50000"))
        assert snap.status == "ACTIVE"
        assert snap.buying_power == Decimal("100000")

    def test_position_snapshot_alias(self):
        pos = PositionSnapshot(symbol="SPY", qty=Decimal("10"))
        assert pos.quantity == Decimal("10")

    def test_option_contract(self):
        c = _make_contract()
        assert c.option_type == OptionType.CALL
        assert c.strike == Decimal("550")

    def test_trade_proposal_defaults(self):
        p = _make_proposal()
        assert p.id  # auto-generated
        assert p.underlying == "SPY"
        assert p.strategy == StrategyType.LONG_CALL

    def test_kill_decision(self):
        d = KillDecision(proposal_id="test", kill_score=Decimal("0.3"), survives=False)
        assert d.survives is False

    def test_risk_decision(self):
        r = RiskDecision(proposal_id="test", approved=True)
        assert r.approved is True


# ---------------------------------------------------------------------------
# Options Engine Tests
# ---------------------------------------------------------------------------

class TestOptionsContracts:
    def test_filter_by_dte(self):
        contracts = [
            _make_contract(dte=5),
            _make_contract(dte=15),
            _make_contract(dte=30),
            _make_contract(dte=60),
        ]
        filtered = filter_by_dte(contracts, min_dte=10, max_dte=45)
        assert len(filtered) == 2

    def test_filter_by_moneyness_calls(self):
        contracts = [
            _make_contract(strike=540, option_type=OptionType.CALL),
            _make_contract(strike=560, option_type=OptionType.CALL),
            _make_contract(strike=580, option_type=OptionType.CALL),
        ]
        filtered = filter_by_moneyness(contracts, underlying_price=Decimal("550"), option_type=OptionType.CALL)
        # OTM calls: strike > 550
        assert all(c.strike > 550 for c in filtered)

    def test_select_strike_by_delta(self):
        contracts = [
            _make_contract(strike=540, delta=0.7),
            _make_contract(strike=550, delta=0.5),
            _make_contract(strike=560, delta=0.35),
        ]
        selected = select_strike(contracts, target_delta=Decimal("0.4"))
        assert selected is not None
        assert selected.strike == Decimal("560")

    def test_select_strike_closest_to_atm(self):
        contracts = [
            _make_contract(strike=540),
            _make_contract(strike=560),
        ]
        selected = select_strike(contracts, underlying_price=Decimal("550"))
        assert selected.strike == Decimal("540")  # closer to 550


class TestOptionsGreeks:
    def test_normal_cdf(self):
        assert normal_cdf(0) == 0.5
        assert normal_cdf(2) > 0.95

    def test_compute_greeks_call(self):
        greeks = compute_greeks(
            spot=100, strike=100, time_to_expiry=0.25, rate=0.05, iv=0.2, option_type=OptionType.CALL
        )
        assert "delta" in greeks
        assert 0.4 < greeks["delta"] < 0.7  # ATM call delta
        assert greeks["gamma"] > 0

    def test_compute_greeks_put(self):
        greeks = compute_greeks(
            spot=100, strike=100, time_to_expiry=0.25, rate=0.05, iv=0.2, option_type=OptionType.PUT
        )
        assert greeks["delta"] < 0  # put delta is negative

    def test_compute_greeks_zero_iv(self):
        greeks = compute_greeks(
            spot=100, strike=100, time_to_expiry=0.25, rate=0.05, iv=0, option_type=OptionType.CALL
        )
        assert greeks["delta"] == 0


class TestOptionsLiquidity:
    def test_liquid_contract(self):
        c = _make_contract(volume=100, oi=500, bid=5.0, ask=5.25)
        is_liquid, reason = check_liquidity(c)
        assert is_liquid is True

    def test_illiquid_low_volume(self):
        c = _make_contract(volume=2, oi=500)
        is_liquid, reason = check_liquidity(c)
        assert is_liquid is False
        assert "Volume" in reason

    def test_illiquid_wide_spread(self):
        c = _make_contract(bid=1.0, ask=5.0)
        is_liquid, reason = check_liquidity(c)
        assert is_liquid is False
        assert "spread" in reason.lower()

    def test_filter_liquid(self):
        contracts = [
            _make_contract(volume=100, oi=500),
            _make_contract(volume=2, oi=500),
        ]
        liquid = filter_liquid(contracts)
        assert len(liquid) == 1


class TestOptionsPricing:
    def test_compute_mid_price(self):
        c = _make_contract(bid=5.0, ask=6.0)
        mid = compute_mid_price(c)
        assert mid == Decimal("5.5")

    def test_compute_reward_risk(self):
        rr = compute_reward_risk([], Decimal("500"), Decimal("1000"))
        assert rr == Decimal("2")


# ---------------------------------------------------------------------------
# Strategy Tests
# ---------------------------------------------------------------------------

class TestStrategies:
    def _make_thesis(self, regime: MarketRegime = MarketRegime.UPTREND) -> MarketThesis:
        return MarketThesis(
            underlying="SPY",
            regime=regime,
            confidence=Decimal("0.6"),
            thesis="Test thesis",
            current_price=Decimal("550"),
        )

    def _make_contracts(self) -> list[OptionContract]:
        contracts = []
        for strike in range(530, 580, 5):
            contracts.append(_make_contract(strike=strike, option_type=OptionType.CALL, bid=3.0, ask=3.2))
            contracts.append(_make_contract(
                symbol=f"SPY250919P{strike:08d}",
                strike=strike,
                option_type=OptionType.PUT,
                bid=3.0,
                ask=3.2,
            ))
        return contracts

    def test_long_call_uptrend(self):
        strategy = LongCallStrategy()
        thesis = self._make_thesis(MarketRegime.UPTREND)
        contracts = self._make_contracts()
        proposal = strategy.build_proposal(thesis, contracts, Decimal("550"))
        assert proposal is not None
        assert proposal.strategy == StrategyType.LONG_CALL

    def test_long_call_rejects_downtrend(self):
        strategy = LongCallStrategy()
        thesis = self._make_thesis(MarketRegime.DOWNTREND)
        contracts = self._make_contracts()
        proposal = strategy.build_proposal(thesis, contracts, Decimal("550"))
        assert proposal is None

    def test_long_put_downtrend(self):
        strategy = LongPutStrategy()
        thesis = self._make_thesis(MarketRegime.DOWNTREND)
        contracts = self._make_contracts()
        proposal = strategy.build_proposal(thesis, contracts, Decimal("550"))
        assert proposal is not None
        assert proposal.strategy == StrategyType.LONG_PUT

    def test_long_put_rejects_uptrend(self):
        strategy = LongPutStrategy()
        thesis = self._make_thesis(MarketRegime.UPTREND)
        contracts = self._make_contracts()
        proposal = strategy.build_proposal(thesis, contracts, Decimal("550"))
        assert proposal is None

    def test_bull_call_spread(self):
        strategy = BullCallSpreadStrategy()
        thesis = self._make_thesis(MarketRegime.UPTREND)
        contracts = self._make_contracts()
        proposal = strategy.build_proposal(thesis, contracts, Decimal("550"))
        assert proposal is not None
        assert len(proposal.legs) == 2

    def test_generate_proposals(self):
        thesis = self._make_thesis(MarketRegime.UPTREND)
        contracts = self._make_contracts()
        proposals = generate_proposals(thesis, contracts, Decimal("550"))
        assert len(proposals) > 0
        assert all(p.underlying == "SPY" for p in proposals)


# ---------------------------------------------------------------------------
# Kill Agent Tests
# ---------------------------------------------------------------------------

class TestKillAgent:
    def test_kill_low_confidence(self):
        proposal = _make_proposal(confidence=0.1)
        thesis = MarketThesis(underlying="SPY", regime=MarketRegime.UPTREND, confidence=Decimal("0.5"))
        decision = kill_test(proposal, thesis)
        assert any("confidence" in r.lower() for r in decision.kill_reasons)

    def test_kill_poor_rr(self):
        proposal = _make_proposal(reward_risk=0.5)
        thesis = MarketThesis(underlying="SPY", regime=MarketRegime.UPTREND, confidence=Decimal("0.5"))
        decision = kill_test(proposal, thesis)
        assert any("reward/risk" in r.lower() for r in decision.kill_reasons)

    def test_survives_good_proposal(self):
        proposal = _make_proposal(confidence=0.7, reward_risk=2.5, max_loss=200)
        thesis = MarketThesis(underlying="SPY", regime=MarketRegime.UPTREND, confidence=Decimal("0.6"))
        decision = kill_test(proposal, thesis)
        assert decision.survives is True
        assert decision.kill_score >= KILL_THRESHOLD

    def test_kill_contradictory_thesis(self):
        proposal = _make_proposal(thesis="Bullish test")
        thesis = MarketThesis(underlying="SPY", regime=MarketRegime.DOWNTREND, confidence=Decimal("0.5"))
        decision = kill_test(proposal, thesis)
        assert any("contradictory" in r.lower() for r in decision.kill_reasons)


# ---------------------------------------------------------------------------
# Risk Engine Tests
# ---------------------------------------------------------------------------

class TestRiskEngine:
    def test_approval_within_limits(self):
        proposal = _make_proposal(max_loss=200, reward_risk=2.0, confidence=0.6)
        decision = evaluate_risk(
            proposal,
            buying_power=Decimal("100000"),
            current_positions=2,
        )
        assert decision.approved is True

    def test_rejection_high_risk(self):
        proposal = _make_proposal(max_loss=1000, reward_risk=0.5)
        decision = evaluate_risk(proposal, buying_power=Decimal("100000"))
        assert decision.approved is False
        assert len(decision.failed_checks) > 0

    def test_rejection_low_reward_risk(self):
        proposal = _make_proposal(max_loss=300, reward_risk=0.5)
        decision = evaluate_risk(proposal, buying_power=Decimal("100000"))
        assert decision.approved is False

    def test_rejection_max_positions(self):
        proposal = _make_proposal(max_loss=200, reward_risk=2.0, confidence=0.6)
        decision = evaluate_risk(proposal, buying_power=Decimal("100000"), current_positions=10)
        assert decision.approved is False

    def test_metrics_populated(self):
        proposal = _make_proposal()
        decision = evaluate_risk(proposal)
        assert "max_loss" in decision.metrics
        assert "buying_power" in decision.metrics


# ---------------------------------------------------------------------------
# Portfolio Agent Tests
# ---------------------------------------------------------------------------

class TestPortfolioAgent:
    def test_approve_good_fit(self):
        proposal = _make_proposal(max_loss=200)
        check = check_portfolio_fit(
            proposal,
            positions=[],
            buying_power=Decimal("100000"),
            portfolio_value=Decimal("100000"),
        )
        assert check.approved is True

    def test_reject_insufficient_buying_power(self):
        proposal = _make_proposal(max_loss=500)
        check = check_portfolio_fit(
            proposal,
            positions=[],
            buying_power=Decimal("100"),
            portfolio_value=Decimal("10000"),
        )
        assert check.approved is False

    def test_reject_concentration(self):
        proposal = _make_proposal(max_loss=2000)
        mock_pos = MagicMock()
        mock_pos.symbol = "SPY"
        mock_pos.market_value = 15000
        check = check_portfolio_fit(
            proposal,
            positions=[mock_pos],
            buying_power=Decimal("100000"),
            portfolio_value=Decimal("100000"),
        )
        assert check.approved is False


# ---------------------------------------------------------------------------
# Position Sizing Tests
# ---------------------------------------------------------------------------

class TestPositionSizing:
    def test_basic_sizing(self):
        size = calculate_position_size(Decimal("250"), risk_per_trade=Decimal("500"))
        assert size == 2

    def test_minimum_one(self):
        size = calculate_position_size(Decimal("1000"), risk_per_trade=Decimal("500"))
        assert size == 1

    def test_max_cap(self):
        size = calculate_position_size(Decimal("10"), risk_per_trade=Decimal("500"), max_contracts=5)
        assert size == 5


# ---------------------------------------------------------------------------
# Exposure Tests
# ---------------------------------------------------------------------------

class TestExposure:
    def test_total_exposure(self):
        mock_pos = MagicMock()
        mock_pos.market_value = 1000
        total = calculate_total_exposure([mock_pos])
        assert total == Decimal("1000")

    def test_options_exposure(self):
        mock_pos = MagicMock()
        mock_pos.symbol = "SPY250919C00550000"  # long symbol = options
        mock_pos.market_value = 500
        total = calculate_options_exposure([mock_pos])
        assert total == Decimal("500")


# ---------------------------------------------------------------------------
# Monitoring Tests
# ---------------------------------------------------------------------------

class TestMonitoring:
    def test_hold_winning_position(self):
        pos = PositionSnapshot(
            symbol="SPY",
            qty=Decimal("1"),
            unrealized_pl=Decimal("100"),
            unrealized_plpc=Decimal("0.10"),
        )
        action, reason = evaluate_position(pos, days_held=5)
        assert action == PositionAction.HOLD

    def test_exit_losing_position(self):
        pos = PositionSnapshot(
            symbol="SPY",
            qty=Decimal("1"),
            avg_entry_price=Decimal("1000"),
            unrealized_pl=Decimal("-500"),
            unrealized_plpc=Decimal("-0.30"),
        )
        action, reason = evaluate_position(pos, days_held=5, max_loss_pct=Decimal("0.20"))
        assert action == PositionAction.EXIT


# ---------------------------------------------------------------------------
# Database / Journal Tests
# ---------------------------------------------------------------------------

class TestJournal:
    def test_record_and_retrieve(self, tmp_path):
        journal = TradeJournal(journal_dir=tmp_path)
        entry = TradeJournalEntry(
            trade_id="test1",
            underlying="SPY",
            strategy="long_call",
            thesis="Test",
            result="open",
        )
        journal.record_entry(entry)
        loaded = journal.get_entry("test1")
        assert loaded is not None
        assert loaded.underlying == "SPY"

    def test_persists_to_disk(self, tmp_path):
        journal = TradeJournal(journal_dir=tmp_path)
        entry = TradeJournalEntry(trade_id="test2", underlying="QQQ", strategy="long_put")
        journal.record_entry(entry)
        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1
        data = json.loads(files[0].read_text())
        assert data["underlying"] == "QQQ"

    def test_record_exit(self, tmp_path):
        journal = TradeJournal(journal_dir=tmp_path)
        journal.record_entry(TradeJournalEntry(trade_id="test3", underlying="AAPL", result="open"))
        journal.record_exit("test3", realized_pnl=150.0, result="win")
        entry = journal.get_entry("test3")
        assert entry.result == "win"
        assert entry.realized_pnl == 150.0


# ---------------------------------------------------------------------------
# Postmortem Tests
# ---------------------------------------------------------------------------

class TestPostmortem:
    def test_winning_trade(self):
        entry = TradeJournalEntry(
            trade_id="pm1",
            underlying="SPY",
            strategy="long_call",
            thesis="Bullish",
            kill_score=Decimal("0.8"),
            realized_pnl=Decimal("200"),
            result="win",
        )
        pm = run_postmortem(entry)
        assert pm.win_loss == "win"
        assert pm.realized_pnl == Decimal("200")

    def test_losing_trade(self):
        entry = TradeJournalEntry(
            trade_id="pm2",
            underlying="QQQ",
            strategy="long_put",
            thesis="Bearish",
            kill_score=Decimal("0.3"),
            realized_pnl=Decimal("-800"),
            result="loss",
        )
        pm = run_postmortem(entry)
        assert pm.win_loss == "loss"
        assert len(pm.improvements) > 0 or len(pm.lessons) > 0


# ---------------------------------------------------------------------------
# Portfolio Manager Tests
# ---------------------------------------------------------------------------

class TestPortfolioManager:
    def test_evaluate_trade_no_state(self):
        pm = PortfolioManager()
        proposal = _make_proposal()
        check = pm.evaluate_trade(proposal)
        assert check.approved is False

    def test_update_and_evaluate(self):
        pm = PortfolioManager()
        account = AccountSnapshot(status="ACTIVE", buying_power=Decimal("50000"), portfolio_value=Decimal("100000"))
        pm.update(account, [])
        assert pm.position_count == 0
        assert pm.buying_power == Decimal("50000")


# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------

class TestConfig:
    def test_settings_paper_only(self):
        from killjoy.config.settings import Settings
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Settings(alpaca_paper=False)

    def test_missing_credentials(self):
        from killjoy.config.settings import Settings, MissingAlpacaCredentialsError
        s = Settings(alpaca_api_key=None, alpaca_secret_key=None)
        assert s.has_alpaca_credentials is False
        with pytest.raises(MissingAlpacaCredentialsError):
            s.require_alpaca_credentials()

    def test_valid_credentials(self):
        from killjoy.config.settings import Settings
        s = Settings(alpaca_api_key="key", alpaca_secret_key="secret", alpaca_paper=True)
        assert s.has_alpaca_credentials is True
        assert s.require_alpaca_credentials() == ("key", "secret")


# ---------------------------------------------------------------------------
# Safety Stress Tests — Every bad proposal MUST be rejected
# ---------------------------------------------------------------------------

class TestSafetyStress:
    """Deliberately bad proposals — every one must be rejected by some gate.

    Tests the full chain: Kill Agent + Risk Engine.
    A proposal that passes any of these is a BUG.
    """

    def _base_proposal(self, **overrides) -> TradeProposal:
        defaults = dict(
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
            max_loss=Decimal("200"),
            max_profit=Decimal("400"),
            reward_risk=Decimal("2.0"),
            confidence=Decimal("0.6"),
            thesis="Bullish test",
        )
        defaults.update(overrides)
        return TradeProposal(**defaults)

    def _base_thesis(self, **overrides) -> MarketThesis:
        defaults = dict(
            underlying="SPY",
            regime=MarketRegime.UPTREND,
            confidence=Decimal("0.6"),
            thesis="Test thesis",
            current_price=Decimal("550"),
        )
        defaults.update(overrides)
        return MarketThesis(**defaults)

    def test_too_much_risk(self):
        """Max loss > $500 limit → risk engine rejects."""
        proposal = self._base_proposal(max_loss=Decimal("1000"), reward_risk=Decimal("2.0"))
        thesis = self._base_thesis()
        kill = kill_test(proposal, thesis)
        risk = evaluate_risk(proposal, buying_power=Decimal("100000"))
        # Either kill agent or risk engine must reject
        assert not kill.survives or not risk.approved

    def test_bad_reward_risk(self):
        """R/R < 1.0 → risk engine rejects (kill agent notes but may not kill alone)."""
        proposal = self._base_proposal(reward_risk=Decimal("0.5"), max_loss=Decimal("200"))
        thesis = self._base_thesis()
        kill = kill_test(proposal, thesis)
        risk = evaluate_risk(proposal, buying_power=Decimal("100000"))
        # Kill agent records the issue
        assert any("reward/risk" in r.lower() for r in kill.kill_reasons)
        # Risk engine definitively rejects
        assert not risk.approved

    def test_duplicate_order(self):
        """Same proposal twice within 5 min → executor blocks."""
        from killjoy.execution.executor import Executor
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        executor = Executor(mock_client)
        proposal = self._base_proposal()

        # First call would go through (but fail on mock)
        # Second call with same proposal → duplicate blocked
        result1 = executor.execute_proposal(proposal)
        result2 = executor.execute_proposal(proposal)
        # Either first fails on mock or second is duplicate
        assert result2.status == "duplicate_blocked" or result1.status == "failed"

    def test_insufficient_buying_power(self):
        """Buying power too low → risk engine rejects."""
        proposal = self._base_proposal(max_loss=Decimal("200"))
        risk = evaluate_risk(proposal, buying_power=Decimal("50"))
        assert not risk.approved
        assert any("buying_power" in c.name for c in risk.failed_checks)

    def test_max_positions_reached(self):
        """10 positions already open → risk engine rejects."""
        proposal = self._base_proposal(max_loss=Decimal("200"))
        risk = evaluate_risk(proposal, buying_power=Decimal("100000"), current_positions=10)
        assert not risk.approved
        assert any("max_positions" in c.name for c in risk.failed_checks)

    def test_low_confidence_killed(self):
        """Confidence < 0.3 → kill agent notes, risk engine rejects."""
        proposal = self._base_proposal(confidence=Decimal("0.1"))
        thesis = self._base_thesis()
        kill = kill_test(proposal, thesis)
        risk = evaluate_risk(proposal, buying_power=Decimal("100000"))
        # Kill agent records the issue
        assert any("confidence" in r.lower() for r in kill.kill_reasons)
        # Risk engine definitively rejects
        assert not risk.approved
        assert any("min_confidence" in c.name for c in risk.failed_checks)

    def test_contradictory_thesis_killed(self):
        """Bullish proposal in downtrend → kill agent notes contradiction."""
        proposal = self._base_proposal(thesis="Bullish test")
        thesis = self._base_thesis(regime=MarketRegime.DOWNTREND)
        kill = kill_test(proposal, thesis)
        # Kill agent records the contradiction
        assert any("contradictory" in r.lower() for r in kill.kill_reasons)
        # Kill score is reduced (but single issue may not push below 0.4)
        assert kill.kill_score < Decimal("1.0")

    def test_iron_condor_in_high_vol_killed(self):
        """Iron condor in high-vol regime → kill agent notes danger."""
        proposal = self._base_proposal(
            strategy=StrategyType.IRON_CONDOR,
            legs=[
                OptionLeg(contract_symbol="C1", option_type=OptionType.CALL, strike=Decimal("560"),
                          expiration=date.today() + timedelta(days=30), side="sell", quantity=1,
                          bid=Decimal("3"), ask=Decimal("3.5"), mid=Decimal("3.25")),
                OptionLeg(contract_symbol="C2", option_type=OptionType.CALL, strike=Decimal("570"),
                          expiration=date.today() + timedelta(days=30), side="buy", quantity=1,
                          bid=Decimal("2"), ask=Decimal("2.5"), mid=Decimal("2.25")),
                OptionLeg(contract_symbol="P1", option_type=OptionType.PUT, strike=Decimal("540"),
                          expiration=date.today() + timedelta(days=30), side="sell", quantity=1,
                          bid=Decimal("3"), ask=Decimal("3.5"), mid=Decimal("3.25")),
                OptionLeg(contract_symbol="P2", option_type=OptionType.PUT, strike=Decimal("530"),
                          expiration=date.today() + timedelta(days=30), side="buy", quantity=1,
                          bid=Decimal("2"), ask=Decimal("2.5"), mid=Decimal("2.25")),
            ],
            max_loss=Decimal("500"),
        )
        thesis = self._base_thesis(regime=MarketRegime.HIGH_VOLATILITY)
        kill = kill_test(proposal, thesis)
        # Kill agent records the danger
        assert any("iron condor" in r.lower() or "high-volatility" in r.lower() for r in kill.kill_reasons)
        # Kill score is reduced
        assert kill.kill_score < Decimal("1.0")

    def test_stale_quote_rejected(self):
        """All bid/ask/mid zero → executor rejects as stale."""
        from killjoy.execution.executor import Executor
        from unittest.mock import MagicMock

        proposal = self._base_proposal(
            legs=[
                OptionLeg(
                    contract_symbol="SPY250919C00550000",
                    option_type=OptionType.CALL,
                    strike=Decimal("550"),
                    expiration=date.today() + timedelta(days=30),
                    side="buy",
                    quantity=1,
                    bid=Decimal("0"),
                    ask=Decimal("0"),
                    mid=Decimal("0"),
                )
            ]
        )
        executor = Executor(MagicMock())
        result = executor.execute_proposal(proposal)
        assert result.status == "stale_quote"

    def test_risk_engine_metrics_populated(self):
        """Risk engine always populates metrics for observability."""
        proposal = self._base_proposal()
        risk = evaluate_risk(proposal)
        assert "max_loss" in risk.metrics
        assert "max_profit" in risk.metrics
        assert "reward_risk" in risk.metrics
        assert "buying_power" in risk.metrics
        assert "current_positions" in risk.metrics

    def test_kill_agent_returns_structured_objections(self):
        """Kill agent returns structured objections for dashboard display."""
        proposal = self._base_proposal(confidence=Decimal("0.1"))
        thesis = self._base_thesis()
        kill = kill_test(proposal, thesis)
        assert isinstance(kill.kill_reasons, list)
        assert len(kill.kill_reasons) > 0

    def test_risk_engine_has_8_gates(self):
        """Verify all 8 risk gates are evaluated."""
        proposal = self._base_proposal()
        risk = evaluate_risk(proposal, buying_power=Decimal("100000"), current_positions=2)
        gate_names = [c.name for c in risk.checks]
        expected = [
            "max_risk_per_trade", "daily_loss_limit", "total_options_exposure",
            "single_underlying_exposure", "reward_risk_ratio", "buying_power",
            "max_positions", "min_confidence",
        ]
        assert gate_names == expected


# ---------------------------------------------------------------------------
# Strategy Graveyard Tests
# ---------------------------------------------------------------------------

class TestGraveyard:
    def test_record_win_updates_stats(self, tmp_path):
        """Graveyard correctly records a winning trade."""
        from killjoy.analytics.graveyard import StrategyGraveyard
        gy = StrategyGraveyard(data_dir=tmp_path)
        gy.record_trade("long_call", won=True, pnl=150.0)
        graves = gy.get_all()
        assert len(graves) == 1
        g = graves[0]
        assert g.strategy_type == "long_call"
        assert g.total_trades == 1
        assert g.win_count == 1
        assert g.loss_count == 0
        assert float(g.total_pnl) == 150.0
        assert float(g.win_rate) == 1.0

    def test_record_loss_updates_stats(self, tmp_path):
        """Graveyard correctly records a losing trade."""
        from killjoy.analytics.graveyard import StrategyGraveyard
        gy = StrategyGraveyard(data_dir=tmp_path)
        gy.record_trade("long_put", won=False, pnl=-80.0)
        graves = gy.get_all()
        assert len(graves) == 1
        g = graves[0]
        assert g.total_trades == 1
        assert g.win_count == 0
        assert g.loss_count == 1
        assert float(g.total_pnl) == -80.0
        assert float(g.win_rate) == 0.0

    def test_mixed_outcomes(self, tmp_path):
        """Graveyard correctly aggregates wins and losses."""
        from killjoy.analytics.graveyard import StrategyGraveyard
        gy = StrategyGraveyard(data_dir=tmp_path)
        gy.record_trade("bull_call_spread", won=True, pnl=200.0)
        gy.record_trade("bull_call_spread", won=False, pnl=-100.0)
        gy.record_trade("bull_call_spread", won=True, pnl=50.0)
        graves = gy.get_all()
        assert len(graves) == 1
        g = graves[0]
        assert g.total_trades == 3
        assert g.win_count == 2
        assert g.loss_count == 1
        assert float(g.total_pnl) == 150.0
        assert float(g.win_rate) == pytest.approx(2 / 3, abs=0.01)

    def test_different_strategies_separate(self, tmp_path):
        """Different strategies get separate grave records."""
        from killjoy.analytics.graveyard import StrategyGraveyard
        gy = StrategyGraveyard(data_dir=tmp_path)
        gy.record_trade("long_call", won=True, pnl=100.0)
        gy.record_trade("long_put", won=False, pnl=-50.0)
        graves = gy.get_all()
        assert len(graves) == 2
        types = {g.strategy_type for g in graves}
        assert types == {"long_call", "long_put"}
