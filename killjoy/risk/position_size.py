"""Position sizing logic."""

from __future__ import annotations

from decimal import Decimal


def calculate_position_size(
    max_loss: Decimal,
    risk_per_trade: Decimal = Decimal("500"),
    max_contracts: int = 10,
) -> int:
    """Calculate number of contracts based on risk budget.

    Args:
        max_loss: Maximum loss per contract
        risk_per_trade: Total dollars willing to risk
        max_contracts: Maximum contracts allowed

    Returns:
        Number of contracts (minimum 1)
    """
    if max_loss <= 0:
        return 0
    contracts = int(risk_per_trade / max_loss)
    return max(1, min(contracts, max_contracts))
