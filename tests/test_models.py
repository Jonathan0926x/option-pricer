import math

import pytest

from option_pricer import OptionContract


def test_contract_is_immutable_and_allows_negative_rate_and_yield() -> None:
    contract = OptionContract(100, 100, -0.01, 0.2, 1, "call", -0.02)

    assert contract.rate == -0.01
    assert contract.dividend_yield == -0.02
    with pytest.raises((AttributeError, TypeError)):
        contract.spot = 101  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("spot", 0, "spot must be greater than zero"),
        ("spot", -1, "spot must be greater than zero"),
        ("strike", 0, "strike must be greater than zero"),
        ("time_years", -0.1, "time_years must be zero or greater"),
        ("volatility", -0.1, "volatility must be zero or greater"),
        ("rate", math.inf, "rate must be finite"),
        ("dividend_yield", math.nan, "dividend_yield must be finite"),
        ("spot", "100", "spot must be a finite real number"),
        ("strike", True, "strike must be a finite real number"),
    ],
)
def test_invalid_contract_values(field: str, value: object, message: str) -> None:
    values = {
        "spot": 100.0,
        "strike": 100.0,
        "rate": 0.05,
        "volatility": 0.2,
        "time_years": 1.0,
        "option_type": "call",
        "dividend_yield": 0.0,
    }
    values[field] = value

    with pytest.raises((TypeError, ValueError), match=message):
        OptionContract(**values)  # type: ignore[arg-type]


def test_invalid_option_type_is_rejected() -> None:
    with pytest.raises(ValueError, match="option_type must be 'call' or 'put'"):
        OptionContract(100, 100, 0.05, 0.2, 1, "CALL")  # type: ignore[arg-type]
