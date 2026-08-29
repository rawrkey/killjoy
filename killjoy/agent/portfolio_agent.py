"""Portfolio Agent — evaluates trade fit against portfolio."""

from __future__ import annotations

import logging
from decimal import Decimal

from killjoy.agent.models import PortfolioCheck, TradeProposal

logger = logging.getLogger(__name__)

# Configurable defaults
MAX_SINGLE_UNDERLYING_EXPOSURE_PCT = Decimal("0.15")  # 15% of portfolio
MAX_TOTAL_OPTIONS_EXPOSURE_PCT = Decimal("0.30")  # 30% of portfolio
MAX_CORRELATED_EXPOSURE_PCT = Decimal("0.25")  # 25% in correlated names

# Simple correlation groups
CORRELATION_GROUPS = {
    "tech": {"AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"},
    "index": {"SPY", "QQQ", "IWM"},
}


def _get_correlation_group(symbol: str) -> str | None:
    for group, members in CORRELATION_GROUPS.items():
        if symbol in members:
            return group
    return None


def check_portfolio_fit(
    proposal: TradeProposal,
    positions: list,
    buying_power: Decimal,
    portfolio_value: Decimal,
) -> PortfolioCheck:
    """Evaluate whether a trade improves the portfolio."""
    reasons: list[str] = []
    approved = True

    # Check buying power
    if proposal.max_loss > buying_power:
        reasons.append(f"Max loss (${proposal.max_loss}) exceeds buying power (${buying_power})")
        approved = False

    # Check single-underlying concentration
    existing_exposure = Decimal("0")
    for pos in positions:
        sym = getattr(pos, "symbol", "") if hasattr(pos, "symbol") else pos.get("symbol", "")
        if proposal.underlying in str(sym):
            market_val = getattr(pos, "market_value", None)
            if market_val is None and isinstance(pos, dict):
                market_val = pos.get("market_value", 0)
            existing_exposure += Decimal(str(abs(float(market_val or 0))))

    if portfolio_value > 0:
        concentration = (existing_exposure + proposal.max_loss) / portfolio_value
        if concentration > MAX_SINGLE_UNDERLYING_EXPOSURE_PCT:
            reasons.append(
                f"Concentration in {proposal.underlying} would be {concentration:.1%} "
                f"(limit: {MAX_SINGLE_UNDERLYING_EXPOSURE_PCT:.0%})"
            )
            approved = False

    # Check total options exposure
    options_exposure = Decimal("0")
    for pos in positions:
        sym = str(getattr(pos, "symbol", "") if hasattr(pos, "symbol") else pos.get("symbol", ""))
        if sym and len(sym) > 4:  # rough heuristic for options
            market_val = getattr(pos, "market_value", None)
            if market_val is None and isinstance(pos, dict):
                market_val = pos.get("market_value", 0)
            options_exposure += Decimal(str(abs(float(market_val or 0))))

    if portfolio_value > 0:
        total_options_pct = (options_exposure + proposal.max_loss) / portfolio_value
        if total_options_pct > MAX_TOTAL_OPTIONS_EXPOSURE_PCT:
            reasons.append(
                f"Total options exposure would be {total_options_pct:.1%} "
                f"(limit: {MAX_TOTAL_OPTIONS_EXPOSURE_PCT:.0%})"
            )
            approved = False

    # Check correlated exposure
    corr_group = _get_correlation_group(proposal.underlying)
    if corr_group and portfolio_value > 0:
        corr_exposure = Decimal("0")
        for pos in positions:
            sym = str(getattr(pos, "symbol", "") if hasattr(pos, "symbol") else pos.get("symbol", ""))
            if _get_correlation_group(sym) == corr_group:
                market_val = getattr(pos, "market_value", None)
                if market_val is None and isinstance(pos, dict):
                    market_val = pos.get("market_value", 0)
                corr_exposure += Decimal(str(abs(float(market_val or 0))))
        corr_pct = (corr_exposure + proposal.max_loss) / portfolio_value
        if corr_pct > MAX_CORRELATED_EXPOSURE_PCT:
            reasons.append(
                f"Correlated group '{corr_group}' exposure would be {corr_pct:.1%} "
                f"(limit: {MAX_CORRELATED_EXPOSURE_PCT:.0%})"
            )

    if not reasons:
        reasons.append("Portfolio fit OK")

    logger.info(
        "Portfolio check for %s %s: %s",
        proposal.underlying,
        proposal.strategy.value,
        "APPROVED" if approved else "REJECTED",
    )

    return PortfolioCheck(
        approved=approved,
        reasons=reasons,
        total_options_exposure=options_exposure,
        buying_power_available=buying_power,
    )
