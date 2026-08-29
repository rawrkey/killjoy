"""Portfolio correlation — real rolling-return correlation analysis.

Replaces hardcoded correlation groups with actual correlation computation.
Uses historical returns to compute pairwise correlations.
"""

from __future__ import annotations

import logging
import statistics
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


def compute_returns(prices: list[float]) -> list[float]:
    """Compute simple returns from price series."""
    if len(prices) < 2:
        return []
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] != 0:
            returns.append((prices[i] - prices[i - 1]) / prices[i - 1])
    return returns


def compute_correlation(series_a: list[float], series_b: list[float]) -> float:
    """Compute Pearson correlation between two return series."""
    min_len = min(len(series_a), len(series_b))
    if min_len < 3:
        return 0.0

    a = series_a[-min_len:]
    b = series_b[-min_len:]

    mean_a = statistics.mean(a)
    mean_b = statistics.mean(b)

    if statistics.stdev(a) == 0 or statistics.stdev(b) == 0:
        return 0.0

    # Pearson correlation
    n = len(a)
    sum_ab = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    sum_a2 = sum((a[i] - mean_a) ** 2 for i in range(n))
    sum_b2 = sum((b[i] - mean_b) ** 2 for i in range(n))

    denom = (sum_a2 * sum_b2) ** 0.5
    if denom == 0:
        return 0.0

    return sum_ab / denom


class PortfolioCorrelation:
    """Compute and track correlations between portfolio positions."""

    def __init__(self) -> None:
        self._price_history: dict[str, list[float]] = {}
        self._correlation_cache: dict[tuple[str, str], float] = {}
        self._cache_dirty = True

    def update_prices(self, symbol: str, prices: list[float]) -> None:
        """Update price history for a symbol."""
        self._price_history[symbol] = prices
        self._cache_dirty = True

    def add_price(self, symbol: str, price: float) -> None:
        """Append a single price point."""
        self._price_history.setdefault(symbol, []).append(price)
        # Keep last 60 data points (roughly 3 months of daily data)
        if len(self._price_history[symbol]) > 60:
            self._price_history[symbol] = self._price_history[symbol][-60:]
        self._cache_dirty = True

    def compute_all_correlations(self) -> dict[tuple[str, str], float]:
        """Compute pairwise correlations for all symbols with data."""
        if not self._cache_dirty:
            return self._correlation_cache

        symbols = list(self._price_history.keys())
        self._correlation_cache = {}

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                sym_a = symbols[i]
                sym_b = symbols[j]
                returns_a = compute_returns(self._price_history[sym_a])
                returns_b = compute_returns(self._price_history[sym_b])
                corr = compute_correlation(returns_a, returns_b)
                self._correlation_cache[(sym_a, sym_b)] = corr

        self._cache_dirty = False
        return self._correlation_cache

    def get_correlation(self, sym_a: str, sym_b: str) -> float:
        """Get correlation between two symbols."""
        if sym_a == sym_b:
            return 1.0

        # Check cache
        key = (min(sym_a, sym_b), max(sym_a, sym_b))
        if key in self._correlation_cache:
            return self._correlation_cache[key]

        # Compute on demand
        returns_a = compute_returns(self._price_history.get(sym_a, []))
        returns_b = compute_returns(self._price_history.get(sym_b, []))
        corr = compute_correlation(returns_a, returns_b)
        self._correlation_cache[key] = corr
        return corr

    def get_high_correlation_pairs(
        self, threshold: float = 0.7
    ) -> list[tuple[str, str, float]]:
        """Find all pairs with correlation above threshold."""
        all_corr = self.compute_all_correlations()
        return [
            (sym_a, sym_b, corr)
            for (sym_a, sym_b), corr in all_corr.items()
            if abs(corr) >= threshold
        ]

    def get_portfolio_correlation_risk(
        self, symbols: list[str]
    ) -> dict[str, Any]:
        """Assess correlation risk for a set of portfolio symbols."""
        if len(symbols) < 2:
            return {"risk_level": "low", "high_corr_pairs": [], "avg_correlation": 0}

        pairs = []
        correlations = []

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                corr = self.get_correlation(symbols[i], symbols[j])
                correlations.append(corr)
                if abs(corr) >= 0.7:
                    pairs.append((symbols[i], symbols[j], round(corr, 3)))

        avg_corr = statistics.mean(correlations) if correlations else 0

        # Risk assessment
        high_corr_count = len(pairs)
        if high_corr_count >= 3 or avg_corr > 0.8:
            risk_level = "high"
        elif high_corr_count >= 1 or avg_corr > 0.5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "avg_correlation": round(avg_corr, 3),
            "high_corr_pairs": pairs,
            "symbols_analyzed": len(symbols),
        }

    def get_correlation_matrix(self, symbols: list[str]) -> dict[str, dict[str, float]]:
        """Get correlation matrix for dashboard display."""
        matrix: dict[str, dict[str, float]] = {}
        for sym_a in symbols:
            matrix[sym_a] = {}
            for sym_b in symbols:
                if sym_a == sym_b:
                    matrix[sym_a][sym_b] = 1.0
                else:
                    matrix[sym_a][sym_b] = round(self.get_correlation(sym_a, sym_b), 3)
        return matrix
