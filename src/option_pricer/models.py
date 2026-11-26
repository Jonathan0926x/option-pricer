"""Shared, validated inputs for the pricing methods."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Literal

OptionType = Literal["call", "put"]


@dataclass(frozen=True, slots=True)
class OptionContract:
    """An immutable European option contract and its model inputs.

    Rates, volatility, dividend yield, and time are annualized and must use
    consistent units. For example, enter 5% as ``0.05`` and one year as ``1.0``.
    ``dividend_yield`` defaults to zero. Spot and strike use the same currency
    units; prices returned by this package use those same units.
    """

    spot: float
    strike: float
    rate: float
    volatility: float
    time_years: float
    option_type: OptionType
    dividend_yield: float = 0.0

    def __post_init__(self) -> None:
        """Reject invalid values once, before either pricing method can run."""
        for name in (
            "spot",
            "strike",
            "rate",
            "volatility",
            "time_years",
            "dividend_yield",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a finite real number")
            try:
                finite = math.isfinite(value)
            except OverflowError as exc:
                raise ValueError(f"{name} must be finite and representable") from exc
            if not finite:
                raise ValueError(f"{name} must be finite")

        if self.spot <= 0:
            raise ValueError("spot must be greater than zero")
        if self.strike <= 0:
            raise ValueError("strike must be greater than zero")
        if self.time_years < 0:
            raise ValueError("time_years must be zero or greater")
        if self.volatility < 0:
            raise ValueError("volatility must be zero or greater")
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")

    def payoff(self, terminal_spot: float) -> float:
        """Return the option's undiscounted payoff at expiration."""
        if self.option_type == "call":
            return max(terminal_spot - self.strike, 0.0)
        return max(self.strike - terminal_spot, 0.0)
