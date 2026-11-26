import math

import pytest

from option_pricer import OptionContract, black_scholes_price, normal_cdf


def canonical(option_type: str = "call", **overrides: float) -> OptionContract:
    values = {
        "spot": 100.0,
        "strike": 100.0,
        "rate": 0.05,
        "volatility": 0.20,
        "time_years": 1.0,
        "option_type": option_type,
        "dividend_yield": 0.0,
    }
    values.update(overrides)
    return OptionContract(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("x", [-8.0, -2.0, -0.25, 0.0, 0.25, 2.0, 8.0])
def test_normal_cdf_symmetry(x: float) -> None:
    assert normal_cdf(x) + normal_cdf(-x) == pytest.approx(1.0, abs=1e-15)


def test_canonical_call_and_put_prices() -> None:
    assert black_scholes_price(canonical("call")) == pytest.approx(
        10.45058357, abs=1e-7
    )
    assert black_scholes_price(canonical("put")) == pytest.approx(5.57352602, abs=1e-7)


def test_put_call_parity_with_continuous_dividend_yield() -> None:
    call = black_scholes_price(canonical("call", dividend_yield=0.02))
    put = black_scholes_price(canonical("put", dividend_yield=0.02))
    expected = 100 * math.exp(-0.02) - 100 * math.exp(-0.05)

    assert call - put == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    ("option_type", "spot", "strike", "expected"),
    [
        ("call", 110, 100, 10),
        ("call", 90, 100, 0),
        ("put", 90, 100, 10),
        ("put", 110, 100, 0),
    ],
)
def test_intrinsic_value_at_expiration(
    option_type: str, spot: float, strike: float, expected: float
) -> None:
    contract = OptionContract(spot, strike, 0.05, 0.2, 0.0, option_type)

    assert black_scholes_price(contract) == pytest.approx(expected)


def test_zero_volatility_uses_discounted_deterministic_payoff() -> None:
    contract = OptionContract(100, 110, 0.05, 0.0, 1.0, "put", 0.01)
    deterministic_terminal_spot = 100 * math.exp(0.04)
    expected = math.exp(-0.05) * (110 - deterministic_terminal_spot)

    assert black_scholes_price(contract) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("option_type", "lower", "upper"),
    [
        (
            "call",
            max(100 * math.exp(-0.02) - 105 * math.exp(-0.05), 0),
            100 * math.exp(-0.02),
        ),
        (
            "put",
            max(105 * math.exp(-0.05) - 100 * math.exp(-0.02), 0),
            105 * math.exp(-0.05),
        ),
    ],
)
def test_no_arbitrage_bounds_and_monotonicity(
    option_type: str, lower: float, upper: float
) -> None:
    base = black_scholes_price(
        OptionContract(100, 105, 0.05, 0.2, 1.0, option_type, 0.02)
    )
    higher_spot = black_scholes_price(
        OptionContract(101, 105, 0.05, 0.2, 1.0, option_type, 0.02)
    )
    higher_strike = black_scholes_price(
        OptionContract(100, 106, 0.05, 0.2, 1.0, option_type, 0.02)
    )

    assert lower <= base <= upper
    if option_type == "call":
        assert higher_spot > base
        assert higher_strike < base
    else:
        assert higher_spot < base
        assert higher_strike > base
