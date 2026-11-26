import pytest

from option_pricer.cli import main

_CONTRACT_ARGS = [
    "--type",
    "call",
    "--spot",
    "100",
    "--strike",
    "100",
    "--rate",
    "0.05",
    "--volatility",
    "0.20",
    "--time",
    "1",
]


def test_price_command_prints_comparison(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["price", *_CONTRACT_ARGS, "--simulations", "1000", "--seed", "7"])
    output = capsys.readouterr().out

    assert code == 0
    assert "Analytical BSM price: $10.450584" in output
    assert "Monte Carlo estimate:" in output
    assert "Absolute difference:" in output
    assert "Monte Carlo standard error:" in output
    assert "Approximate 95% interval:" in output
    assert "Simulations: 1,000; seed: 7" in output


def test_convergence_command_prints_all_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["convergence", *_CONTRACT_ARGS, "--counts", "100,300", "--seed", "7"])
    output = capsys.readouterr().out

    assert code == 0
    assert "Analytical BSM reference: $10.450584" in output
    assert "100" in output
    assert "300" in output
    assert "Std. error" in output


def test_invalid_contract_is_reported_as_cli_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as error:
        main(["price", *_CONTRACT_ARGS[:-1], "-1"])

    assert error.value.code == 2
    assert "time_years must be zero or greater" in capsys.readouterr().err
