# Option Pricer

An educational Python package that prices the same European call or put in two
independent ways: the Black–Scholes–Merton (BSM) analytical formula and a
risk-neutral Monte Carlo simulation. The project makes the model assumptions
and simulation uncertainty visible, and uses no runtime dependencies.

These are model-based prices under the stated assumptions. They are not
guaranteed market prices, a forecast, or investment advice, and they do not
establish a profitable trading opportunity.

## Features

- Immutable, shared `OptionContract` inputs for both pricing methods.
- Direct BSM implementation with the standard normal CDF calculated using
  Python's built-in `math.erf`.
- Risk-neutral simulation of terminal prices with a reproducible integer seed.
- Monte Carlo estimate, sample standard error, and approximate 95% interval.
- CLI comparison and convergence table, including a one-million-draw run.
- Zero runtime dependencies; `pytest` and `ruff` are development tools.

## Install

From a clone of this repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

The project requires Python 3.11 or newer. The package can also be used without
installing development tools with `python -m pip install -e .`.

## Canonical example

Both methods use the same contract:

| Input | Value |
| --- | ---: |
| Spot `S` | 100 |
| Strike `K` | 100 |
| Annual continuously compounded rate `r` | 0.05 |
| Annualized volatility `sigma` | 0.20 |
| Time to expiration `T` | 1 year |
| Continuous dividend yield `q` | 0 |

The analytical values are approximately **$10.4506** for the call and **$5.5735**
for the put. With 100,000 Monte Carlo simulations and seed 7, this project
prints:

| Type | Analytical BSM | Monte Carlo | Absolute difference | Std. error | Approx. 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| Call | $10.450584 | $10.475415 | $0.024832 | $0.046512 | [$10.384254, $10.566576] |
| Put | $5.573526 | $5.551960 | $0.021566 | $0.027311 | [$5.498431, $5.605489] |

These are the verified outputs for 100,000 simulations and seed 7. The CLI
also reports the count and seed. Monte Carlo is noisy; the analytical result is
the reference price under the model assumptions. A larger simulation count
usually reduces standard error approximately in proportion to `1 / sqrt(N)`,
but each larger run is not guaranteed to land closer to the analytical value.

## Price a call or put

From the repository root, the exact call command is:

```bash
python -m option_pricer price \
  --type call \
  --spot 100 \
  --strike 100 \
  --rate 0.05 \
  --volatility 0.20 \
  --time 1 \
  --dividend-yield 0 \
  --simulations 100000 \
  --seed 7
```

Change `--type call` to `--type put` for the corresponding put. The report
includes contract inputs, both prices, absolute difference, Monte Carlo standard
error and 95% interval, simulation count, and seed. Invalid values produce an
actionable command-line error.

The Python API is also available:

```python
from option_pricer import OptionContract, black_scholes_price, monte_carlo_price

contract = OptionContract(
    spot=100.0,
    strike=100.0,
    rate=0.05,
    volatility=0.20,
    time_years=1.0,
    option_type="call",
    dividend_yield=0.0,
)

analytic = black_scholes_price(contract)
simulation = monte_carlo_price(contract, simulations=100_000, seed=7)
print(analytic, simulation.price, simulation.standard_error)
```

## Convergence

To print estimates at 1,000, 10,000, 100,000, and 1,000,000 simulations for
the canonical call, run:

```bash
python -m option_pricer convergence \
  --type call \
  --spot 100 \
  --strike 100 \
  --rate 0.05 \
  --volatility 0.20 \
  --time 1 \
  --dividend-yield 0 \
  --seed 7
```

Use `--type put` for the put or pass custom ascending counts, for example
`--counts 1000,5000,20000`. Each row starts from the same seed, so lower-count
runs use the same initial sequence as larger runs in the same Python version.
The interval shown by `price` is an approximate normal interval; it summarizes
sampling uncertainty and does not cover model error or input uncertainty.

With the canonical inputs and seed 7, the verified convergence output is:

| Simulations | Call estimate | Call std. error | Put estimate | Put std. error |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | $10.640244 | $0.455112 | $5.263524 | $0.278344 |
| 10,000 | $10.496073 | $0.146425 | $5.539810 | $0.086305 |
| 100,000 | $10.475415 | $0.046512 | $5.551960 | $0.027311 |
| 1,000,000 | $10.454477 | $0.014710 | $5.565897 | $0.008648 |

The million-draw estimates are within one reported standard error of their
analytical references for this seed. That is an observed result for this run,
not a guarantee for other seeds or larger runs.

## Model and formulas

The first release covers European options, which can be exercised only at
expiration. Its assumptions are:

- Constant volatility and interest rate over the option's life.
- Geometric Brownian motion under the risk-neutral measure.
- A continuously compounded annual risk-free rate `r` and continuous annual
  dividend yield `q`.
- No transaction costs, taxes, bid–ask spread, or early exercise.
- No calibration to current market data.

Rates, volatility, dividend yield, and time must use consistent annual units:
enter a 5% rate as `0.05`, volatility of 20% as `0.20`, and one year as `1.0`.
Spot and strike must be finite and positive. Volatility and time must be finite
and nonnegative. Finite negative rates and dividend yields are allowed. The
option type is `call` or `put`; dividend yield defaults to zero.

For `T > 0` and `sigma > 0`:

```text
d1 = [ln(S / K) + (r - q + sigma² / 2) T] / (sigma sqrt(T))
d2 = d1 - sigma sqrt(T)

Call = S exp(-q T) N(d1) - K exp(-r T) N(d2)
Put  = K exp(-r T) N(-d2) - S exp(-q T) N(-d1)
N(x) = [1 + erf(x / sqrt(2))] / 2
```

At expiration, the price is intrinsic value. At zero volatility, the terminal
price is deterministic under the risk-neutral drift and the payoff is
discounted directly.

Monte Carlo draws `Z ~ N(0, 1)` and simulates:

```text
S_T = S exp((r - q - sigma² / 2) T + sigma sqrt(T) Z)
```

The option payoff at expiration is discounted by `exp(-r T)`, and the
simulation estimate is the mean discounted payoff. Welford's online algorithm
computes sample variance without storing each payoff. Standard error is sample
standard deviation divided by the square root of the simulation count. The
approximate 95% interval is estimate ± 1.95996 standard errors. Sampling error
typically falls as `1 / sqrt(N)`; this does not mean every larger run is closer
to the analytical value.

The simulator draws terminal prices directly because a European payoff depends
only on the expiration price. Simulating full paths is a natural later
extension for path-dependent contracts such as barrier or Asian options.

## Tests and lint

```bash
python -m pytest
ruff check .
ruff format --check .
```

The tests cover input validation, CDF symmetry, canonical prices, put–call
parity, expiration and zero-volatility limits, bounds and monotonicity,
reproducibility, standard-error and confidence-interval calculations,
statistically scaled Monte Carlo accuracy, and CLI reports. The routine suite
does not run one million simulations.

GitHub Actions runs the test suite, Ruff lint, and Ruff formatting checks on
pushes and pull requests.

## Limitations and possible extensions

This educational implementation does not support American exercise, implied
volatility solving, Greeks, live market data, stochastic volatility, jumps, or
path-dependent payoffs. It does not calibrate or validate inputs against market
quotes. Possible later work includes path-dependent contracts, variance
reduction, and comparison with an independent implementation for tests only.

## Historical reference

Fischer Black and Myron Scholes, “The Pricing of Options and Corporate
Liabilities,” *Journal of Political Economy* 81(3), 637–654 (1973),
[doi:10.1086/260062](https://doi.org/10.1086/260062).
