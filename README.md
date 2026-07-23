# Cross-Sectional Alpha Research: UBL + Low-Volatility Case Study

This repository contains two complementary components:

1. A documented China A-share portfolio case study supported by aggregate
   result tables and figures.
2. A compact, strategy-agnostic reference package for point-in-time validation,
   portfolio accounting, transaction costs, paired block-bootstrap comparisons,
   and report generation.

The public package begins with precomputed, directionally oriented factor
scores. Report-derived factor implementations, licensed market data, and
the internal security-level research engine are not redistributed.

Reported results are simulated research results, not live performance or
investment advice.

![Net NAV comparison](examples/sample_outputs/ubl_lowvol_study/plots/01_net_nav_comparison.png)

## Research Question

Can a slower low-volatility sleeve improve the UBL family's Sharpe, drawdown,
turnover, and transaction-cost tolerance without replacing the underlying UBL
signal? The study compares the UBL family with a fixed 80% UBL / 20% LOWVOL_60
risk allocation.

## Observed Chronological Holdout

The chronological holdout contains 133 daily observations and has now been
viewed. It should be treated as observed evidence rather than an untouched
out-of-sample test.

On this period, the blend achieved annualized net Sharpe of 1.36 at a 0% cash
hurdle, compared with 0.60 for UBL alone. Net return increased from 2.10% to
4.87%, max drawdown declined from 4.82% to 4.05%, turnover declined, and the
estimated break-even transaction cost increased from 13.12 to 17.93 bps.

| Metric | UBL only | UBL + LOWVOL |
|---|---:|---:|
| Annualized net Sharpe, 0% cash hurdle | 0.60 | 1.36 |
| Net return | 2.10% | 4.87% |
| Max drawdown | 4.82% | 4.05% |
| Average full turnover | 0.532 | 0.462 |
| Break-even transaction cost | 13.12 bps | 17.93 bps |
| Fraction of paired bootstrap resamples with $\Delta \mathrm{Sharpe} > 0$ | - | 95.2% |

Turnover is `sum(abs(w_t - w_t-1))` for a dollar-neutral portfolio normalized
to long gross +1 and short gross -1.

## Interpretation And Robustness

The observed improvement is broader than Sharpe alone: the blend also had a
shallower drawdown, lower average turnover, and a larger estimated
transaction-cost margin. The paired-bootstrap result is an observed-sample
resampling frequency, not a probability of future profitability.

| Additional result | Observed value |
|---|---:|
| Validation annualized net Sharpe | 1.69 |
| Full-common-sample annualized net Sharpe | 1.64 |
| Full-common-sample net Sharpe at 15 bps | 0.71 |
| Paired walk-forward annualized net Sharpe | -0.07 |
| Positive walk-forward folds | 2 / 4 |
| One-additional-day execution-delay Sharpe | 0.46 |

The result remains uneven through time. Paired walk-forward Sharpe is slightly
negative, only two of four folds are positive, and one additional execution day
materially weakens performance. These limits make unchanged-rule testing on new
data more important than further tuning on the viewed sample.

![Paired walk-forward folds](examples/sample_outputs/ubl_lowvol_study/plots/05_walk_forward_fold_returns.png)

## Portfolio Design

The UBL sleeve combines PaperUBL 3D, UBL_M20 3D, and UBL_M5 5D with internal
risk budgets of 60%, 20%, and 20%.

At the top level, UBL receives 80% of risk and LOWVOL_60 receives 20%.
Security-level weights are combined before turnover and transaction costs are
calculated, so crossing between sleeves is reflected in the reported results.

## Compact Reference Package

The public code is a compact, strategy-agnostic reference package for analyzing
precomputed, directionally oriented factor scores.

It supports:

- point-in-time timestamp validation and IC/RankIC analysis;
- dollar-neutral portfolio accounting and security-level weight ledgers;
- turnover, transaction-cost, Sharpe, and drawdown calculations;
- paired moving-block bootstrap comparisons and report figures.

A higher `alpha_score` always represents a higher expected return. The runner
requires:

```text
latest_factor_input_timestamp < entry_timestamp < exit_timestamp
```

It then records:

- previous, target, and executed security weights;
- weight changes and full/one-way turnover;
- gross PnL, security-level cost, and net PnL contributions;
- Pearson IC and Spearman RankIC;
- exposure, Sharpe, drawdown, and break-even cost.

Report-derived factor implementations, licensed data, universe selection,
strategy parameters, borrow modeling, and live execution are not redistributed.

## Run The Public Example

Python 3.10 or newer is recommended.

```bash
cd cross-sectional-alpha-research
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q tests/test_sample_package.py
```

Run the anonymous synthetic example:

```bash
python examples/run_sample_package.py
```

It writes a synthetic input panel, daily results, a security-level weight
ledger, summary JSON, four plots, and `report.md` under
`outputs/sample_package/`. The generated performance is a mechanics
check, not an empirical claim.

Regenerate the six committed portfolio figures from the public aggregate
CSVs:

```bash
python examples/render_public_results.py
```

## Input Schema

The generic runner expects one row per factor date and asset:

| Column                          | Meaning                              |
| ------------------------------- | ------------------------------------ |
| `factor_date`                   | Date associated with the score       |
| `latest_factor_input_timestamp` | Latest information used by the score |
| `entry_timestamp`               | Simulated execution timestamp        |
| `exit_timestamp`                | Return-measurement endpoint          |
| `asset`                         | Anonymous or public asset identifier |
| `alpha_score`                   | Oriented score; higher means better  |
| `forward_return`                | Realized return strictly after entry |

## API Example

```python
import pandas as pd

from alpha_research import (
    BacktestConfig,
    Visualizer,
    run_cross_sectional_backtest,
)

panel = pd.read_csv(
    "oriented_scores_and_returns.csv",
    parse_dates=[
        "factor_date",
        "latest_factor_input_timestamp",
        "entry_timestamp",
        "exit_timestamp",
    ],
)

result = run_cross_sectional_backtest(
    panel,
    BacktestConfig(
        long_fraction=0.20,
        short_fraction=0.20,
        cost_bps=10.0,
        band_bps=5.0,
    ),
)

Visualizer(result).save_report("outputs/example_report")
```

## Detailed Portfolio Construction

**UBL family sleeve**

| Component   | Internal risk budget |
| ----------- | -------------------- |
| PaperUBL 3D | 60%                  |
| UBL_M20 3D  | 20%                  |
| UBL_M5 5D   | 20%                  |

The UBL family first applies the 7.5 bps security-weight-change band selected on
validation data, and is then treated as one top-level sleeve.

**Top-level blend**

| Sleeve     | Risk budget |
| ---------- | ----------- |
| UBL family | 80%         |
| LOWVOL_60  | 20%         |

Each sleeve is divided by training-only realized portfolio volatility. Security
weights are combined, normalized to long +1 / short -1, passed through a common
7.5 bps no-trade band, and charged costs on final aggregate trades. Standalone
net-return series are not averaged.

## Methodology Summary

- **Signal timing:** complete data at date `t` is used only for a
  portfolio entered at the next tradable VWAP.
- **Direction:** every factor emits an oriented `alpha_score`.
- **Portfolio:** market-neutral long/short, net exposure 0, gross exposure 2.
- **Costs:** base 10 bps per dollar traded, applied to full turnover; 5/10/15/20
  bps sensitivity is reported.
- **Sample periods:** train 2020, validation first half of 2021, and the viewed
  chronological holdout from July 2021 through January 2022.
- **Selection:** budgets, LOWVOL_60 window, UBL family composition, and no-trade
  rule were set using training and validation before the holdout comparison.
- **Robustness:** paired same-date resampling, fixed-rule walk-forward folds,
  cost stress, PnL concentration, delay sensitivity, and exposure checks.

See [methodology.md](docs/methodology.md) for definitions and the
[point-in-time timing details](docs/methodology.md#point-in-time-timing).

## Additional Results

### Transaction-Cost Frontier

![Transaction-cost frontier](examples/sample_outputs/ubl_lowvol_study/plots/03_transaction_cost_frontier.png)

The blend remains positive at 15 bps on the full common sample, while both
portfolios are negative at 20 bps.

### Paired Bootstrap Comparison

![Paired bootstrap Sharpe difference](examples/sample_outputs/ubl_lowvol_study/plots/04_paired_bootstrap_sharpe_difference.png)

The plot shows the 5-day moving-block specification with 5,000 resamples. The
reported 95.2% is the mean frequency across four pre-specified block schemes.
It is an observed-sample resampling frequency, not a probability of future
profitability.

The full figure set and data dictionary are in the
[portfolio output bundle](examples/sample_outputs/ubl_lowvol_study/README.md).

## Published Results And Code Boundary

The committed aggregate CSVs are the inputs to every published table and
figure. Run `python examples/render_public_results.py` to regenerate the six
figures without private data.

The aggregate files do not include security-level holdings, licensed market
data, or report-derived factor implementations. They support review of the
reported portfolio results, but do not permit an independent rerun of the
internal security-level strategy.

## Detailed Analysis

- [UBL + LOWVOL portfolio](docs/case_studies/ubl_lowvol_portfolio.md)
- [UBL factor family](docs/case_studies/UBL.md)
- [PaperUBL reconstruction](docs/case_studies/PaperUBL.md)
- [Candidate results](docs/candidate_outcomes.md)

## Interpretation Limits

- The chronological holdout has now been viewed and cannot be reused for
  selection.
- Its 133 observations cover a short and regime-specific period.
- Paired walk-forward performance is negative with only 2/4 positive folds.
- LOWVOL_60 varies substantially by period: validation Sharpe is near zero,
  while Sharpe in the observed holdout is higher.
- An additional day of execution delay cuts the selected full-sample Sharpe to
  0.46.
- Borrow availability, financing, market impact, and short-sale constraints are
  not modeled.
- The adjusted-price source and pre-2020 LOWVOL_60 warm-up inputs were not
  independently verified.
- The reference package illustrates portfolio mechanics; excluded factor
  implementations and data are required to recreate the reported returns.

The most informative next evidence would be unchanged-rule replication on new
data with independently checked corporate-action adjustments, borrow
assumptions, and execution constraints.

## Related Factor Result

Two conventional medium-term momentum definitions were evaluated with a
pre-specified positive direction and were not selected. Both had negative
validation RankIC and negative gross and net returns. The pre-specified sign was
retained throughout evaluation. Details are in
[candidate_outcomes.md](docs/candidate_outcomes.md).

## Report-Reproduction Template

The optional
[factor research report reproducer](.agents/skills/factor-research-report-reproducer/SKILL.md)
supports structured literature review and report drafting. It is separate from
the internal security-level research engine.

## License

Code, documentation, and released artifacts are covered by the
[MIT License](LICENSE). Published metrics are research artifacts and carry no
warranty of investment performance.
