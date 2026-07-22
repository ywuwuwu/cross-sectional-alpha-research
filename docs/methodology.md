# Methodology

This document defines the public research contract behind the predefined UBL
plus LOWVOL_60 comparison. It is designed to prevent timing, sign, metric, and
transaction-cost conventions from changing between experiments.

## Point-in-Time Timing

For a daily UBL observation:

```text
date t close:
    observe complete OHLCV inputs
    calculate raw factor
    orient it into alpha_score

next tradable date:
    enter at the specified VWAP benchmark

following tradable date:
    realize the next-period VWAP-to-VWAP return
```

The required ordering is:

```text
latest_factor_input_timestamp < entry_timestamp < exit_timestamp
```

A return row is valid only when it records `factor_date`, `entry_price_date`,
and `exit_price_date` and satisfies this inequality. Same-period ranking and
return evaluation is not used.

LOWVOL_60 uses 60 prior daily returns and a 20-trading-day holding horizon with
20 staggered offsets. Warm-up observations may construct a score but may not
enter the evaluation return sample.

## Direction Contract

Every strategy stores:

```text
raw_factor_value
alpha_score
```

The public invariant is:

```text
higher alpha_score = higher expected return
```

The portfolio layer never decides whether to invert a factor. It always forms
the long side from the highest oriented scores and the short side from the
lowest. Reversed signals are explicit direction-control tests, not hidden engine
settings.

## Universe And Tradability

The research universe required:

- at least 60 rows of history for the common UBL universe;
- valid OHLCV observations;
- entry-date tradability;
- next-tradable-date VWAP execution;
- a terminal-event rule;
- average daily value traded of at least CNY 5 million.

Security-level inputs and membership are private and are not published. The
aggregate public files contain no ticker identifiers.

## Chronological Splits

| Split | Contract dates | Effective common observations |
|---|---|---:|
| Train | 2020-01-02 to 2020-12-30 | 180 |
| Validation | 2021-01-04 to 2021-06-29 | 111 |
| Research holdout | 2021-07-01 to 2022-01-21 | 133 |

The effective common sample begins after required history is available. Training
fits volatility scales. Validation chooses among preregistered implementation
rules. The holdout was evaluated once for the combined-portfolio comparison,
but it has now been viewed and cannot be reused for further selection.

## Portfolio Construction

The selected UBL family uses internal risk budgets:

```text
PaperUBL 3D = 0.60
UBL_M20 3D = 0.20
UBL_M5 5D = 0.20
```

It is treated as one top-level sleeve after its internal 7.5 bps
security-weight-change band.

The selected family blend is:

```text
UBL risk budget       = 0.80
LOWVOL_60 risk budget = 0.20
```

For each sleeve `j`, use training-only gross return volatility `sigma_j`:

```text
raw combined weight = sum_j(risk_budget_j * sleeve_weight_j / sigma_j)
```

Then:

1. sum security weights across sleeves;
2. normalize long gross to +1 and short gross to -1;
3. apply the common 7.5 bps security-weight-change band;
4. enforce lifecycle and tradability rules;
5. calculate turnover on final aggregate weights;
6. charge transaction costs once on aggregate trades.

This order captures trade netting. Averaging standalone net-return series does
not.

## Turnover And Costs

For date `t`:

```text
full_turnover_t    = sum_i(abs(w_i,t - w_i,t-1))
one_way_turnover_t = 0.5 * full_turnover_t
transaction_cost_t = full_turnover_t * cost_bps / 10,000
net_return_t       = gross_return_t - transaction_cost_t
```

The book has gross exposure 2, so an initial fully invested long/short book has
full turnover 2. A value such as 0.462 means 46.2% of one unit of capital traded
under the full-turnover convention, not 0.462%.

The base model is 10 bps per dollar traded. Sensitivities use 5, 10, 15, and 20
bps. Borrow fees, financing, and nonlinear market impact are not included.

Break-even cost is:

```text
mean(gross_return) / mean(full_turnover) * 10,000
```

## Metrics

- **Net total return:** compounded product of `1 + net_return` minus one.
- **Net Sharpe 0rf:** `sqrt(252) * mean(net_return) / std(net_return)`.
- **Net max drawdown:** deepest peak-to-trough decline in compounded net NAV.
- **Pearson IC:** cross-sectional Pearson correlation of score and forward return.
- **RankIC:** cross-sectional Spearman rank correlation.
- **Raw RankICIR:** mean RankIC divided by RankIC standard deviation.
- **Annualized RankICIR:** raw RankICIR times the square root of observations per
  year.

Pearson IC and RankIC are never labeled interchangeably. Financing-adjusted
Sharpe is unavailable because borrow and financing are not modeled.

## Robustness Tests

The selected UBL plus LOWVOL portfolio was evaluated with:

- 5/10/15/20 bps cost sensitivity;
- four paired fixed-rule walk-forward folds;
- moving-block bootstrap lengths 3, 5, and 10;
- stationary bootstrap with expected block length 5;
- 5,000 paired resamples per bootstrap method;
- top-five-day PnL concentration;
- one-additional-day execution delay;
- leave-one-sleeve-out comparisons;
- beta, size, liquidity, and industry exposure checks.

Paired bootstrap indices are applied to UBL and the blend on the same dates.
Reported frequencies are properties of the observed sample and resampling
scheme, not probabilities of future success.

## Reproducibility Scope

Before writing aggregate files, `tools/build_public_evidence.py` checks the
versioned private snapshot and stops if either the private or public worktree
has uncommitted changes. A detailed record of source versions and output hashes
is retained locally rather than published.

The committed aggregate CSVs are the numerical inputs for every public table
and figure, so `examples/render_public_results.py` can regenerate the figures
without private data.

The public sample package can validate generic score timing, portfolio
accounting, metrics, and report generation on synthetic or user-supplied
oriented scores. It does not construct the private factors or reproduce the
security-level backtest because raw market data, holdings, private factor
values, exact UBL formulas, and the local adapter engine are excluded.
