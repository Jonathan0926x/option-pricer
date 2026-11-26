"""Black–Scholes–Merton European option pricing, implemented with ``math``."""

from __future__ import annotations

import math

from option_pricer.models import OptionContract


def normal_cdf(x: float) -> float:
    """Return the standard normal cumulative distribution ``N(x)``.

    The implementation uses only Python's built-in error function.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _deterministic_price(contract: OptionContract) -> float:
    """Price the discounted payoff when expiration value is deterministic."""
    if contract.time_years == 0:
        return contract.payoff(contract.spot)
    terminal_spot = contract.spot * math.exp(
        (contract.rate - contract.dividend_yield) * contract.time_years
    )
    discounted_payoff = math.exp(
        -contract.rate * contract.time_years
    ) * contract.payoff(terminal_spot)
    return discounted_payoff


def black_scholes_price(contract: OptionContract) -> float:
    """Price a European call or put with the Black–Scholes–Merton formula.

    ``contract`` supplies spot, strike, continuously compounded annual rate,
    annualized volatility, years to expiration, option type, and continuous
    annual dividend yield. The returned price is in the same currency units as
    spot and strike. At expiration and at zero volatility the deterministic
    discounted payoff is returned explicitly.
    """
    if contract.time_years == 0 or contract.volatility == 0:
        return _deterministic_price(contract)

    root_time = math.sqrt(contract.time_years)
    sigma_root_time = contract.volatility * root_time
    d1 = (
        math.log(contract.spot / contract.strike)
        + (contract.rate - contract.dividend_yield + 0.5 * contract.volatility**2)
        * contract.time_years
    ) / sigma_root_time
    d2 = d1 - sigma_root_time

    discounted_spot = contract.spot * math.exp(
        -contract.dividend_yield * contract.time_years
    )
    discounted_strike = contract.strike * math.exp(-contract.rate * contract.time_years)
    if contract.option_type == "call":
        return discounted_spot * normal_cdf(d1) - discounted_strike * normal_cdf(d2)
    return discounted_strike * normal_cdf(-d2) - discounted_spot * normal_cdf(-d1)
