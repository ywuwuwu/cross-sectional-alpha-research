# Case Study: PaperUBL

## Overview

`PaperUBL` is the current public sample case study for this repository. It is a local-data reproduction of a paper-style UBL factor implementation, evaluated through the repository's factor construction, portfolio, transaction-cost, IC, group-return, and visualization pipeline.

This page is intentionally public-safe:

- raw market data is not included
- source research reports are not redistributed
- private full `reports/` folders are not published
- only a curated sample output is included under `examples/sample_outputs/paper_ubl/`

The goal is to demonstrate the research engine and reporting workflow, not to claim exact replication of the original report.

## Public Sample Output

The curated public output is available here:

- [sample report](../../examples/sample_outputs/paper_ubl/report.md)
- [performance overview](../../examples/sample_outputs/paper_ubl/performance_overview.png)
- [rolling metrics](../../examples/sample_outputs/paper_ubl/rolling_metrics.png)
- [group cumulative returns](../../examples/sample_outputs/paper_ubl/group_cumulative_returns.png)
- [group mean returns](../../examples/sample_outputs/paper_ubl/group_mean_returns.png)
- [group long-short returns](../../examples/sample_outputs/paper_ubl/group_long_short_returns.png)
- [IC series](../../examples/sample_outputs/paper_ubl/ic_series.png)
- [IC distribution](../../examples/sample_outputs/paper_ubl/ic_distribution.png)

## Backtest Configuration

The public sample was generated with:

| Setting | Value |
|---|---|
| Strategy | `PaperUBL` |
| Period | 2020-01-02 to 2022-01-21 |
| Rebalance | Month start |
| Portfolio | Top 50 |
| Groups | 10 |
| Transaction cost | Enabled |
| IC calculation | Enabled |

## Key Local Results

| Metric | Value |
|---|---:|
| Total return | 24.52% |
| Annual return | 12.73% |
| Sharpe | 0.5321 |
| Max drawdown | 25.75% |
| IC mean | 0.0467 |
| ICIR | 0.5857 |
| IC win rate | 71.58% |
| Mean daily group long-short return | 0.51% |
| Average turnover | 99.39% |

These values are local-data diagnostics. They should be interpreted as evidence that the signal has positive cross-sectional information in this local test, not as a tradable production result.

## Research Interpretation

The useful part of this case study is the alignment between:

- positive top-portfolio return
- positive IC
- positive group long-short return
- monotonic group mean returns in the sample report

That combination makes `PaperUBL` a good public demonstration of the research workflow. It is still not a finished production alpha because turnover is high, drawdown is material, and robustness across longer samples, alternate universes, and cost assumptions still needs to be tested.

## Next Improvements

The next version should focus on:

- reducing turnover with slower signal decay or holding-period smoothing
- testing stronger neutralization and risk controls
- running train/test and walk-forward validation
- adding transaction-cost sweeps
- testing correlation against existing alpha families
- comparing raw UBL, PaperUBL, and modified UBL variants side by side

## Reproduction Notes

This is a local-data reproduction. Exact performance comparison with the original research source would require matching the original universe, sample period, factor formula details, filters, transaction-cost assumptions, and portfolio construction rules.
