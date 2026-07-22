# Factor Research Reproduction Report: {{factor_name}}

## Summary

- Source report: {{source_report}}
- Reproduction mode: {{exact_or_local}}
- Strategy file: {{strategy_file}}
- Backtest command: `{{command}}`
- Current interpretation: {{conclusion}}

## Report Formula

{{report_formula}}


## Formula And Implementation Mapping

See:

```text
reports/<factor_name>/reproduction_summary.md
```

This summary records the formula, economic interpretation, local-data substitutions, and implementation mapping.

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

## Observed Results

| Metric | Value |
|---|---:|
| Total return | {{total_return}} |
| Annual return | {{annual_return}} |
| Sharpe | {{sharpe_ratio}} |
| Max drawdown | {{max_drawdown}} |
| Pearson IC mean | {{ic_mean}} |
| RankIC mean | {{rankic_mean}} |
| RankICIR | {{rankic_ir}} |
| IC win rate | {{ic_win_rate}} |

## Group Return Diagnostics

Group ordering: {{stable_layering_yes_no}}

Figures:

- `group_cumulative_returns.png`
- `group_mean_returns.png`
- `group_long_short_returns.png`

Interpretation:

{{layering_interpretation}}

## Differences From Original Report

{{differences}}

## Open Questions And Next Test

{{next_steps}}
