"""Command-line interface for model-based price comparisons."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from option_pricer import black_scholes_price, monte_carlo_price
from option_pricer.models import OptionContract

_DEFAULT_COUNTS = (1_000, 10_000, 100_000, 1_000_000)


def _positive_simulations(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 2:
        raise argparse.ArgumentTypeError("must be at least 2")
    return parsed


def _counts(value: str) -> tuple[int, ...]:
    try:
        counts = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "use comma-separated integers, such as 1000,10000,100000"
        ) from exc
    if not counts or any(count < 2 for count in counts):
        raise argparse.ArgumentTypeError("every simulation count must be at least 2")
    if tuple(sorted(set(counts))) != counts:
        raise argparse.ArgumentTypeError(
            "simulation counts must be unique and in ascending order"
        )
    return counts


def _add_contract_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--type", dest="option_type", choices=("call", "put"), required=True
    )
    parser.add_argument("--spot", type=float, required=True, help="spot price")
    parser.add_argument("--strike", type=float, required=True, help="strike price")
    parser.add_argument(
        "--rate", type=float, required=True, help="annual continuously compounded rate"
    )
    parser.add_argument(
        "--volatility", type=float, required=True, help="annualized volatility"
    )
    parser.add_argument(
        "--time", type=float, required=True, help="time to expiration in years"
    )
    parser.add_argument(
        "--dividend-yield",
        type=float,
        default=0.0,
        help="annual continuous dividend yield (default: 0)",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser, also exposed for CLI tests."""
    parser = argparse.ArgumentParser(
        prog="option-pricer",
        description="Compare Black–Scholes–Merton and risk-neutral Monte Carlo prices.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    price_parser = subparsers.add_parser("price", help="price one contract")
    _add_contract_arguments(price_parser)
    price_parser.add_argument(
        "--simulations", type=_positive_simulations, default=100_000
    )
    price_parser.add_argument("--seed", type=int, default=7)

    convergence_parser = subparsers.add_parser(
        "convergence", help="show estimates at increasing simulation counts"
    )
    _add_contract_arguments(convergence_parser)
    convergence_parser.add_argument(
        "--counts",
        type=_counts,
        default=_DEFAULT_COUNTS,
        help="ascending comma-separated counts (default: 1000,10000,100000,1000000)",
    )
    convergence_parser.add_argument("--seed", type=int, default=7)
    return parser


def _contract_from_args(args: argparse.Namespace) -> OptionContract:
    return OptionContract(
        spot=args.spot,
        strike=args.strike,
        rate=args.rate,
        volatility=args.volatility,
        time_years=args.time,
        option_type=args.option_type,
        dividend_yield=args.dividend_yield,
    )


def _format_contract(contract: OptionContract) -> str:
    return (
        f"type={contract.option_type}, spot={contract.spot:g}, "
        f"strike={contract.strike:g}, rate={contract.rate:g}, "
        f"volatility={contract.volatility:g}, time={contract.time_years:g} years, "
        f"dividend_yield={contract.dividend_yield:g}"
    )


def _price_report(contract: OptionContract, simulations: int, seed: int) -> str:
    analytic = black_scholes_price(contract)
    result = monte_carlo_price(contract, simulations=simulations, seed=seed)
    low, high = result.confidence_interval
    return "\n".join(
        (
            f"Contract: {_format_contract(contract)}",
            f"Analytical BSM price: ${analytic:.6f}",
            f"Monte Carlo estimate: ${result.price:.6f}",
            f"Absolute difference: ${abs(result.price - analytic):.6f}",
            f"Monte Carlo standard error: ${result.standard_error:.6f}",
            f"Approximate 95% interval: [${low:.6f}, ${high:.6f}]",
            f"Simulations: {result.simulations:,}; seed: {result.seed}",
            "The analytical value is the model reference; "
            "the simulation estimate is noisy.",
        )
    )


def _convergence_report(
    contract: OptionContract, counts: tuple[int, ...], seed: int
) -> str:
    analytic = black_scholes_price(contract)
    rows = [
        f"Contract: {_format_contract(contract)}",
        f"Analytical BSM reference: ${analytic:.6f}",
        f"Seed: {seed} (each run restarts from the same seed)",
        "Simulations   Estimate       Std. error",
    ]
    for simulations in counts:
        result = monte_carlo_price(contract, simulations=simulations, seed=seed)
        rows.append(
            f"{simulations:>11,}   ${result.price:>10.6f}   "
            f"${result.standard_error:.6f}"
        )
    rows.append("Standard error typically shrinks in proportion to 1 / sqrt(N).")
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        contract = _contract_from_args(args)
        if args.command == "price":
            print(_price_report(contract, args.simulations, args.seed))
        else:
            print(_convergence_report(contract, args.counts, args.seed))
    except (TypeError, ValueError, OverflowError) as exc:
        parser.error(str(exc))
    return 0
