# Evaluation Rubric

Use this rubric to classify a factor reproduction.

## A. Formula

- 0: formula not extracted
- 1: intuition extracted but formula incomplete
- 2: formula implemented with material differences
- 3: exact formula implemented, local fields mapped
- 4: exact formula plus manual spot checks

## B. Data Mapping

- 0: no mapping
- 1: informal mapping only
- 2: `data_mapping.csv` exists but gaps unclear
- 3: mapping and availability report document all fields and gaps
- 4: mapping includes manual schema samples and exact-vs-local mode decision

## C. Signal

- 0: no signal
- 1: top-N works but direction unknown
- 2: direction documented
- 3: direction verified against IC/group layering
- 4: direction tested with ablation or manual examples

## D. Portfolio/Grouping

- 0: no backtest
- 1: long-only top-N only
- 2: groups computed
- 3: group cumulative, mean, and long-short plotted
- 4: grouping matches paper and stability is discussed

## E. Performance

- 0: no metrics
- 1: basic return metrics only
- 2: IC/IR included
- 3: IC/IR plus group layering and turnover/costs
- 4: compared to paper with mismatch explanations

## Reproduction Labels

- **Exact report reproduction**: all layers score 3+ and original data/setup are locally available.
- **Strict local reproduction**: exact formula and local-data backtest, but original data/setup unavailable.
- **Conceptual local reproduction**: factor idea implemented with modified formula/setup.
- **Prototype only**: smoke test or short-period test without stable layering.

## Minimum Mentor-Ready Output

- `data_availability_report.md`
- `data_mapping.csv`
- strategy source file in `factor_mining/`
- backtest run directory under `reports/<factor_name>/`
- `summary.csv`
- `report.md`
- `group_cumulative_returns.png`
- `group_mean_returns.png`
- `group_long_short_returns.png`
- IC/IR metrics
- clear conclusion: stable layering yes/no
