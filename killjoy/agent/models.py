"""Typed, provider-neutral models used across KILLJOY."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class AccountSnapshot(BaseModel):
    status: str
    buying_power: Decimal
    portfolio_value: Decimal


class PositionSnapshot(BaseModel):
    symbol: str
    quantity: Decimal = Field(alias="qty")

    model_config = {"populate_by_name": True}
