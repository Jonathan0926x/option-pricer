"""Risk-neutral Monte Carlo pricing for European terminal-payoff options."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from option_pricer.models import OptionContract

_NORMAL_95 = 1.959963984540054


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    """Monte Carlo estimate and uncertainty summary."""

    price: float
    standard_error: float
    confidence_interval: tuple[float, float]
    simulations: int
    seed: int


def monte_carlo_price(
    contract: OptionContract,
    simulations: int = 100_000,
    seed: int = 7,
) -> MonteCarloResult:
    """Estimate a European option price by simulating risk-neutral terminal spots.

    Each draw uses ``S_T = S exp((r - q - sigma²/2)T + sigma sqrt(T) Z)`` for
    ``Z ~ N(0, 1)``. The discounted payoff mean is the estimate. Welford's
    online algorithm computes sample variance without retaining the payoffs.
    A two-sided normal-approximation 95% interval is returned as estimate ±
    1.95996 standard errors. The same integer seed and simulation count produce
    repeatable output in the same Python random-number implementation.

    Sampling error typically scales approximately as ``1 / sqrt(simulations)``;
    an individual larger run is not guaranteed to be closer to the analytical
    value. At zero time or volatility the discounted payoff is deterministic,
    so the estimate is exact and the estimated standard error is zero.
    """
    if isinstance(simulations, bool) or not isinstance(simulations, int):
        raise TypeError("simulations must be an integer")
    if simulations < 2:
        raise ValueError("simulations must be at least 2 to estimate sample error")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    if contract.time_years == 0 or contract.volatility == 0:
        if contract.time_years == 0:
            terminal_spot = contract.spot
        else:
            terminal_spot = contract.spot * math.exp(
                (contract.rate - contract.dividend_yield) * contract.time_years
            )
        price = math.exp(-contract.rate * contract.time_years) * contract.payoff(
            terminal_spot
        )
        return MonteCarloResult(price, 0.0, (price, price), simulations, seed)

    rng = random.Random(seed)
    root_time = math.sqrt(contract.time_years)
    drift = (
        contract.rate - contract.dividend_yield - 0.5 * contract.volatility**2
    ) * contract.time_years
    diffusion = contract.volatility * root_time
    discount = math.exp(-contract.rate * contract.time_years)

    mean = 0.0
    squared_deviation_sum = 0.0
    for count in range(1, simulations + 1):
        normal_draw = rng.gauss(0.0, 1.0)
        terminal_spot = contract.spot * math.exp(drift + diffusion * normal_draw)
        discounted_payoff = discount * contract.payoff(terminal_spot)
        delta = discounted_payoff - mean
        mean += delta / count
        squared_deviation_sum += delta * (discounted_payoff - mean)

    sample_variance = squared_deviation_sum / (simulations - 1)
    standard_error = math.sqrt(sample_variance / simulations)
    half_width = _NORMAL_95 * standard_error
    return MonteCarloResult(
        price=mean,
        standard_error=standard_error,
        confidence_interval=(mean - half_width, mean + half_width),
        simulations=simulations,
        seed=seed,
    )
