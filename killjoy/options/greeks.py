"""Greeks computation and handling."""

from __future__ import annotations

import math
from decimal import Decimal

from killjoy.agent.models import OptionContract, OptionType


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def normal_pdf(x: float) -> float:
    """Standard normal probability density function."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def compute_greeks(
    spot: float,
    strike: float,
    time_to_expiry: float,
    rate: float,
    iv: float,
    option_type: OptionType,
) -> dict[str, float]:
    """Compute Black-Scholes Greeks.

    Args:
        spot: Current underlying price
        strike: Option strike price
        time_to_expiry: Time to expiration in years
        rate: Risk-free interest rate (annualized)
        iv: Implied volatility (annualized)
        option_type: CALL or PUT

    Returns:
        Dict with delta, gamma, theta, vega, rho
    """
    if iv <= 0 or time_to_expiry <= 0 or spot <= 0 or strike <= 0:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}

    sqrt_t = math.sqrt(time_to_expiry)
    d1 = (math.log(spot / strike) + (rate + 0.5 * iv**2) * time_to_expiry) / (iv * sqrt_t)
    d2 = d1 - iv * sqrt_t

    nd1 = normal_cdf(d1)
    nd2 = normal_cdf(d2)
    pdf_d1 = normal_pdf(d1)

    if option_type == OptionType.CALL:
        delta = nd1
    else:
        delta = nd1 - 1

    gamma = pdf_d1 / (spot * iv * sqrt_t)

    vega = spot * pdf_d1 * sqrt_t / 100  # per 1% IV change

    if option_type == OptionType.CALL:
        theta = (-(spot * pdf_d1 * iv) / (2 * sqrt_t) - rate * strike * math.exp(-rate * time_to_expiry) * nd2) / 365
    else:
        theta = (-(spot * pdf_d1 * iv) / (2 * sqrt_t) + rate * strike * math.exp(-rate * time_to_expiry) * normal_cdf(-d2)) / 365

    return {
        "delta": round(delta, 6),
        "gamma": round(gamma, 6),
        "theta": round(theta, 6),
        "vega": round(vega, 6),
    }


def enrich_with_greeks(contract: OptionContract, spot: float, rate: float = 0.05) -> OptionContract:
    """Enrich an OptionContract with computed Greeks if IV is available."""
    if contract.implied_volatility <= 0 or spot <= 0:
        return contract

    from datetime import date
    tte = max((contract.expiration - date.today()).days / 365.0, 1 / 365.0)

    greeks = compute_greeks(
        spot=spot,
        strike=float(contract.strike),
        time_to_expiry=tte,
        rate=rate,
        iv=float(contract.implied_volatility),
        option_type=contract.option_type,
    )

    contract.delta = Decimal(str(greeks["delta"]))
    contract.gamma = Decimal(str(greeks["gamma"]))
    contract.theta = Decimal(str(greeks["theta"]))
    contract.vega = Decimal(str(greeks["vega"]))
    return contract
