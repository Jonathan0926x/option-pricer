import math
import random

import pytest

from option_pricer import (
    OptionContract,
    black_scholes_price,
    monte_carlo_price,
)


def canonical(option_type: str) -> OptionContract:
    return OptionContract(100, 100, 0.05, 0.2, 1.0, option_type)


def test_same_seed_produces_same_result() -> None:
    first = monte_carlo_price(canonical("call"), simulations=10_000, seed=7)
    second = monte_carlo_price(canonical("call"), simulations=10_000, seed=7)

    assert first == second


@pytest.mark.parametrize("option_type", ["call", "put"])
def test_estimate_is_within_five_estimated_standard_errors(option_type: str) -> None:
    result = monte_carlo_price(canonical(option_type), simulations=100_000, seed=7)
    analytic = black_scholes_price(canonical(option_type))

    assert abs(result.price - analytic) <= 5 * result.standard_error


def test_standard_error_and_confidence_interval_match_sample() -> None:
    contract = canonical("call")
    simulations = 31
    seed = 42
    result = monte_carlo_price(contract, simulations=simulations, seed=seed)

    rng = random.Random(seed)
    payoffs = []
    for _ in range(simulations):
        z = rng.gauss(0.0, 1.0)
        terminal_spot = 100 * math.exp((0.05 - 0.2**2 / 2) + 0.2 * z)
        payoffs.append(math.exp(-0.05) * max(terminal_spot - 100, 0.0))
    sample_mean = sum(payoffs) / simulations
    sample_variance = sum((value - sample_mean) ** 2 for value in payoffs) / (
        simulations - 1
    )
    expected_se = math.sqrt(sample_variance / simulations)
    expected_half_width = 1.959963984540054 * expected_se

    assert result.simulations == simulations
    assert result.seed == seed
    assert result.price == pytest.approx(sample_mean, abs=1e-12)
    assert result.standard_error == pytest.approx(expected_se, abs=1e-12)
    assert result.confidence_interval == pytest.approx(
        (sample_mean - expected_half_width, sample_mean + expected_half_width),
        abs=1e-12,
    )


def test_deterministic_contract_has_zero_sampling_error() -> None:
    contract = OptionContract(100, 110, 0.05, 0.0, 1.0, "put")
    result = monte_carlo_price(contract, simulations=100, seed=7)

    assert result.price == pytest.approx(black_scholes_price(contract))
    assert result.standard_error == 0.0
    assert result.confidence_interval == (result.price, result.price)


@pytest.mark.parametrize("simulations", [0, 1])
def test_too_few_simulations_rejected(simulations: int) -> None:
    with pytest.raises(ValueError, match="simulations must be at least 2"):
        monte_carlo_price(canonical("call"), simulations=simulations)


def test_non_integer_simulation_count_and_seed_rejected() -> None:
    with pytest.raises(TypeError, match="simulations must be an integer"):
        monte_carlo_price(canonical("call"), simulations=2.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="seed must be an integer"):
        monte_carlo_price(canonical("call"), seed="7")  # type: ignore[arg-type]
