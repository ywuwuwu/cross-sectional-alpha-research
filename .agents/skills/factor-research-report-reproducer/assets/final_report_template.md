# Factor Research Reproduction Report: {{factor_name}}

## Summary

- Source report: {{source_report}}
- Reproduction mode: {{exact_or_local}}
- Strategy file: {{strategy_file}}
- Backtest command: `{{command}}`
- Conclusion: {{conclusion}}

## Report Formula

{{report_formula}}

## Local Implementation

{{implemented_formula}}

## Data Availability

Link:

- `data_availability_report.md`
- `data_mapping.csv`

Key local limitations:

{{data_limitations}}

## Assumptions

{{assumptions}}

## Backtest Setup

| Item | Value |
|---|---|
| Start date | {{start_date}} |
| End date | {{end_date}} |
| Universe | {{universe}} |
| Rebalance | {{rebalance_freq}} |
| Groups | {{n_groups}} |
| Top-N | {{top_n}} |
| Costs | {{costs}} |
| Neutralization | {{neutralization}} |

## Results

| Metric | Value |
|---|---:|
| Total return | {{total_return}} |
| Annual return | {{annual_return}} |
| Sharpe | {{sharpe_ratio}} |
| Max drawdown | {{max_drawdown}} |
| IC mean | {{ic_mean}} |
| IC std | {{ic_std}} |
| IR | {{ir}} |
| IC win rate | {{ic_win_rate}} |

## Layering Evidence

Stable layering: {{stable_layering_yes_no}}

Required artifacts:

- `group_cumulative_returns.png`
- `group_mean_returns.png`
- `group_long_short_returns.png`

Interpretation:

{{layering_interpretation}}

## Differences From Original Report

{{differences}}

## Next Steps

{{next_steps}}
