"""Market Analyst agent — analyzes market conditions and generates thesis."""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import MarketRegime, MarketThesis
from killjoy.alpaca.market_data import MarketDataClient

logger = logging.getLogger(__name__)


def _compute_regime(change_pct: Decimal, volume_ratio: Decimal) -> MarketRegime:
    """Determine market regime from price change and volume."""
    if change_pct > Decimal("2"):
        return MarketRegime.STRONG_UPTREND
    elif change_pct > Decimal("0.5"):
        return MarketRegime.UPTREND
    elif change_pct < Decimal("-2"):
        return MarketRegime.STRONG_DOWNTREND
    elif change_pct < Decimal("-0.5"):
        return MarketRegime.DOWNTREND
    else:
        return MarketRegime.SIDEWAYS


def analyze_market(
    market_data: MarketDataClient,
    underlying: str,
) -> MarketThesis:
    """Analyze market conditions for an underlying and return a structured thesis."""
    snapshot = market_data.get_snapshot(underlying)
    bars = market_data.get_bars(underlying, limit=20)

    price = snapshot.get("last_trade", snapshot.get("close", Decimal("0")))
    change_pct = snapshot.get("change_pct", Decimal("0"))
    volume = snapshot.get("volume", 0)

    # Compute simple metrics from bars
    trend_strength = Decimal("0")
    momentum = Decimal("0")
    iv_rank = Decimal("50")  # default neutral

    if len(bars) >= 5:
        closes = [b["close"] for b in bars[-20:]]
        if len(closes) >= 2:
            momentum = (closes[-1] - closes[0]) / closes[0] * 100

        # Simple trend: recent bars vs earlier
        recent_avg = sum(closes[-5:]) / 5
        earlier_avg = sum(closes[-10:-5]) / 5 if len(closes) >= 10 else sum(closes[:-5]) / max(len(closes) - 5, 1)
        if earlier_avg > 0:
            trend_strength = (recent_avg - earlier_avg) / earlier_avg * 100

    # Volume analysis
    avg_volume = sum(b["volume"] for b in bars[-20:]) / max(len(bars[-20:]), 1) if bars else 1
    volume_ratio = Decimal(str(volume)) / Decimal(str(max(avg_volume, 1))) if avg_volume > 0 else Decimal("1")

    regime = _compute_regime(change_pct, volume_ratio)

    # Volatility analysis
    if len(bars) >= 5:
        returns = []
        for i in range(1, len(bars)):
            prev = bars[i - 1]["close"]
            if prev > 0:
                returns.append(float((bars[i]["close"] - prev) / prev))
        if returns:
            import statistics
            vol = statistics.stdev(returns) * 100 if len(returns) > 1 else 0
            if vol > 3:
                regime = MarketRegime.HIGH_VOLATILITY
            elif vol < 0.5:
                regime = MarketRegime.LOW_VOLATILITY

    observations = []
    risks = []

    if momentum > 3:
        observations.append(f"Strong positive momentum: {momentum:.1f}%")
    elif momentum < -3:
        observations.append(f"Strong negative momentum: {momentum:.1f}%")

    if volume_ratio > 1.5:
        observations.append(f"Above-average volume ({volume_ratio:.1f}x)")
    elif volume_ratio < 0.5:
        observations.append(f"Below-average volume ({volume_ratio:.1f}x)")

    if change_pct > 1:
        observations.append(f"Up {change_pct:.1f}% today")
    elif change_pct < -1:
        observations.append(f"Down {change_pct:.1f}% today")

    if regime in (MarketRegime.HIGH_VOLATILITY, MarketRegime.STRONG_UPTREND, MarketRegime.STRONG_DOWNTREND):
        risks.append(f"Elevated volatility/momentum regime: {regime.value}")

    confidence = Decimal("0.5")
    if abs(momentum) > 5:
        confidence = Decimal("0.7")
    if abs(momentum) > 10:
        confidence = Decimal("0.8")

    thesis_text = f"{underlying} in {regime.value} regime. Momentum: {momentum:.1f}%, Change: {change_pct:.1f}%"

    return MarketThesis(
        underlying=underlying,
        regime=regime,
        confidence=confidence,
        thesis=thesis_text,
        observations=observations,
        risks=risks,
        current_price=price,
        iv_rank=iv_rank,
        trend_strength=trend_strength,
        momentum=momentum,
        volume_signal="high" if volume_ratio > 1.5 else ("low" if volume_ratio < 0.5 else "normal"),
    )
