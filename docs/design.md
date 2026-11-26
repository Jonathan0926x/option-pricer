# Design notes

## Public API and modules

- `models.py` defines immutable `OptionContract` and the `OptionType` literal.
  The contract is the only input accepted by either pricing method, which keeps
  the validated terms identical between analytical and simulated prices.
- `black_scholes.py` implements the standard normal CDF with `math.erf` and the
  dividend-adjusted Black–Scholes–Merton formula. It has no pricing-library
  dependency.
- `monte_carlo.py` simulates risk-neutral terminal prices and returns a frozen
  `MonteCarloResult` containing the estimate, sample standard error, normal
  approximation interval, count, and seed.
- `cli.py` presents one-contract comparisons (`price`) and estimates over
  increasing sample counts (`convergence`).

The main Python interface is:

```python
from option_pricer import OptionContract, black_scholes_price, monte_carlo_price

contract = OptionContract(100, 100, 0.05, 0.20, 1, "call")
analytic = black_scholes_price(contract)
simulation = monte_carlo_price(contract, simulations=100_000, seed=7)
```

The results share price units with spot and strike. Rates, volatility, yield,
and time use annual units: for example, 5% is `0.05` and one year is `1.0`.

## Validation and numerical edges

Spot and strike must be finite positive real numbers. Time and volatility must
be finite and nonnegative. Rate and continuous dividend yield may be any finite
real values, including negative ones. Booleans, non-real values, NaN, and
infinities are rejected. Option type must be exactly `"call"` or `"put"`.
Simulation count must be an integer of at least two, since sample standard
error needs at least two observations; the seed must be an integer.

At expiration, both methods return intrinsic value. At zero volatility, the
terminal price is deterministic under the risk-neutral drift, so both methods
discount its payoff directly and Monte Carlo reports zero sampling error. For
positive time and volatility the analytical method uses `d1` and `d2` and
`N(x) = (1 + erf(x / sqrt(2))) / 2`.

## Risk-neutral simulation

Under geometric Brownian motion with continuous dividend yield `q`, the
risk-neutral terminal spot is

```text
S_T = S exp((r - q - sigma² / 2) T + sigma sqrt(T) Z),  Z ~ N(0, 1).
```

For each independent draw, the pricer evaluates the call or put payoff at
`S_T`, multiplies it by `exp(-r T)`, then averages the discounted payoffs. It
does not call the analytical pricer. Welford's one-pass method accumulates the
mean and sample variance without keeping every simulated payoff in memory.
The reported standard error is the sample standard deviation divided by the
square root of the simulation count; the interval is estimate ± 1.95996
standard errors. This is an approximate interval, especially for small samples
or highly skewed payoff distributions.

Python's `random.Random(seed).gauss` is used so a run can be repeated with the
same Python random-number implementation. Every convergence row restarts with
the same seed; consequently, smaller counts use the same initial random draws
as larger counts in a given Python version. Monte Carlo sampling error usually
shrinks at roughly `1 / sqrt(N)`, but a particular larger estimate can be
farther from the analytical reference than a smaller estimate.

## Why simulate only the terminal price?

A European option's payoff depends only on the underlying price at expiration.
The model gives a direct distribution for `S_T`, so intermediate prices do not
change the payoff or discounted estimator. Full paths are useful for later
extensions such as barrier or Asian options, whose payoffs depend on what
happens before expiration.

## Tests

The pytest suite checks shared-input validation, normal-CDF symmetry, known
canonical prices, put–call parity, expiration and zero-volatility limits,
price bounds and monotonicity, deterministic seeded output, standard-error and
interval calculations, Monte Carlo accuracy against the analytical reference
using a tolerance scaled to observed standard error, and CLI output/errors.
The routine suite does not run the one-million-draw convergence row.

## Scope and references

The first release covers European calls and puts under constant volatility and
interest rate, geometric Brownian motion under the risk-neutral measure, and a
continuous dividend yield. It does not calibrate to market data or include
transaction costs, taxes, bid–ask spreads, or early exercise. The original
historical reference is Fischer Black and Myron Scholes, “The Pricing of
Options and Corporate Liabilities,” *Journal of Political Economy* 81(3),
637–654 (1973), [doi:10.1086/260062](https://doi.org/10.1086/260062).
