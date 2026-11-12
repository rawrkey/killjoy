"""Tests for Agensi-ready features: Zero-Config Sandbox, On-Demand Symbol CLI, and Cash-Secured Puts."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from killjoy.agent.models import MarketRegime, MarketThesis, OptionContract, OptionType, StrategyType
from killjoy.alpaca.market_data import MarketDataClient
from killjoy.alpaca.options_data import OptionsDataClient
from killjoy.config.settings import Settings
from killjoy.strategies.cash_secured_put import CashSecuredPutStrategy


def test_sandbox_market_data():
    """Verify MarketDataClient works seamlessly without Alpaca credentials."""
    settings = Settings(alpaca_api_key=None, alpaca_secret_key=None)
    client = MarketDataClient(settings)
    
    quote = client.get_latest_quote("NVDA")
    assert quote["symbol"] == "NVDA"
    assert quote["mid"] > Decimal("0")
    
    snapshot = client.get_snapshot("AAPL")
    assert snapshot["symbol"] == "AAPL"
    assert snapshot["close"] > Decimal("0")
    
    bars = client.get_bars("SPY", limit=10)
    assert len(bars) == 10
    assert bars[0]["close"] > Decimal("0")


def test_sandbox_options_data():
    """Verify OptionsDataClient generates valid synthetic OCC chains in sandbox mode."""
    settings = Settings(alpaca_api_key=None, alpaca_secret_key=None)
    client = OptionsDataClient(settings)
    
    chain = client.get_option_chain("TSLA")
    assert len(chain) > 0
    assert any(c.option_type == OptionType.CALL for c in chain)
    assert any(c.option_type == OptionType.PUT for c in chain)
    
    for c in chain[:5]:
        assert c.underlying == "TSLA"
        assert c.strike > Decimal("0")
        assert c.mid > Decimal("0")
        assert c.open_interest >= 500


def test_cash_secured_put_strategy():
    """Verify Cash-Secured Put strategy builds valid defined-risk proposals."""
    strategy = CashSecuredPutStrategy()
    today = date.today()
    exp = today + timedelta(days=30)
    spot = Decimal("140.00")

    thesis = MarketThesis(
        underlying="NVDA",
        regime=MarketRegime.UPTREND,
        confidence=Decimal("0.80"),
        current_price=spot,
        thesis="Bullish momentum",
    )

    contracts = [
        OptionContract(
            symbol=f"NVDA{exp.strftime('%y%m%d')}P00130000",
            underlying="NVDA",
            strike=Decimal("130.00"),
            expiration=exp,
            option_type=OptionType.PUT,
            bid=Decimal("2.40"),
            ask=Decimal("2.60"),
            mid=Decimal("2.50"),
            delta=Decimal("-0.25"),
            implied_volatility=Decimal("0.30"),
            open_interest=2000,
            volume=500,
        ),
        OptionContract(
            symbol=f"NVDA{exp.strftime('%y%m%d')}P00125000",
            underlying="NVDA",
            strike=Decimal("125.00"),
            expiration=exp,
            option_type=OptionType.PUT,
            bid=Decimal("1.40"),
            ask=Decimal("1.60"),
            mid=Decimal("1.50"),
            delta=Decimal("-0.15"),
            implied_volatility=Decimal("0.32"),
            open_interest=3000,
            volume=800,
        ),
    ]

    proposal = strategy.build_proposal(thesis, contracts, spot)
    assert proposal is not None
    assert proposal.strategy == StrategyType.CASH_SECURED_PUT
    assert proposal.max_profit == Decimal("250.00")
    assert proposal.legs[0].side == "sell"
    assert proposal.legs[0].strike == Decimal("130.00")


def test_cash_secured_put_rejected_in_strong_downtrend():
    """Verify Cash-Secured Put refuses to sell puts into steep market collapses."""
    strategy = CashSecuredPutStrategy()
    today = date.today()
    exp = today + timedelta(days=30)
    spot = Decimal("140.00")

    thesis = MarketThesis(
        underlying="NVDA",
        regime=MarketRegime.STRONG_DOWNTREND,
        confidence=Decimal("0.90"),
        current_price=spot,
        thesis="Severe crash",
    )

    proposal = strategy.build_proposal(thesis, [], spot)
    assert proposal is None
