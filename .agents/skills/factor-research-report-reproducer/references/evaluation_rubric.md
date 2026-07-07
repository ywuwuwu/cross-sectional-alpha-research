# Evaluation Rubric

Use this rubric to classify a factor reproduction. Score local-data reproductions on a 100-point scale.

## Local-Data Reproduction Scorecard

### Thesis Extraction: 0-10

- 0: report thesis not identified
- 3: broad intuition extracted but missing factor motivation
- 6: thesis, target anomaly, and expected return direction explained
- 10: thesis, mechanism, universe, period, benchmark, and published metrics clearly summarized

### Mathematical Logic and Code Mapping: 0-15

- 0: formulas and math are not extracted
- 3: formulas are partially listed but notation or meaning is unclear
- 6: formulas and notation are explained, but code mapping is incomplete
- 10: formulas, notation, financial meaning, and local approximations are clearly separated
- 15: formulas are accurately extracted, notation is explained, financial meaning is clear, and each mathematical component is mapped to implementation files/classes/functions with local approximations labeled

Evaluate whether:

- formulas are extracted accurately
- notation is explained
- financial meaning is clear
- formulas are mapped to implementation files, classes, and functions
- local approximations are clearly labeled

### Formula Reproduction: 0-20

- 0: no implemented formula
- 5: conceptual implementation only
- 10: main formula implemented with material approximations documented
- 15: report formula implemented with local fields and minor approximations
- 20: formula implemented exactly and manually spot-checked

### Data Mapping: 0-15

- 0: no mapping
- 4: informal mapping only
- 8: `data_mapping.csv` exists but gaps are incomplete
- 12: mapping and availability report document fields, coverage, and gaps
- 15: mapping includes schema samples, exact-vs-local decision, and expected impact of proxies

### Backtest Execution: 0-15

- 0: no run
- 4: smoke run only
- 8: local backtest completes with basic metrics
- 12: local backtest completes with IC and grouped returns
- 15: run uses existing runner, visualizer plots, costs/turnover, and documented command/config

### Performance Evaluation: 0-10

- 0: no metrics
- 3: basic return metrics only
- 6: IC/IR and group metrics included
- 8: layering stability and direction discussed
- 10: results compared to paper with fair mismatch caveats

### Difference Attribution: 0-10

- 0: no explanation of mismatch
- 3: generic caveats only
- 6: data, formula, universe, and timing differences identified
- 10: differences are tied to expected performance impact and exact/local reproduction label

### Code Reuse Quality: 0-5

- 0: standalone or duplicated framework
- 2: partly reuses local modules
- 4: reuses `factor_mining`, `run_research_backtest.py`, and `visualizer.py`
- 5: cleanly follows existing strategy interfaces and avoids unnecessary framework changes

Total: 0-100

## Legacy Layer Checks

Use these checks as supporting evidence when assigning the score:

### Formula

- Formula-level reproduction is required before claiming local-data validation.
- If a formula is inferred from prose, label it as inferred.
- If a formula is locally approximated, explain what input or operation changed.

### Data Mapping

- `data_availability_report.md` and `data_mapping.csv` must exist before implementation or backtest.
- Missing inputs must be tied to reproduction label.

### Signal

- Ranking direction must be documented.
- Direction should be checked against IC and/or group layering where possible.

### Portfolio/Grouping

- Group cumulative returns, group mean returns, and long-short returns should be generated through `visualizer.py` when possible.
- If long-short direction differs from the factor's economic direction, explain it.

### Performance

- IC/IR, grouped returns, turnover, costs, and drawdown should be presented when available.
- Never claim exact performance replication unless the report data and local data match.

## Reproduction Labels

- **Exact report reproduction**: all layers score high and original data/setup are locally available.
- **Strict local reproduction**: exact formula and local-data backtest, but original data/setup unavailable.
- **Partial local-data reproduction**: core idea implemented with documented proxies, approximations, or limited data.
- **Implementation-only reproduction**: formula/code exists but backtest or validation is missing/incomplete.
- **Prototype only**: smoke test or short-period test without stable layering.

## Minimum Output

- `data_availability_report.md`
- `data_mapping.csv`
- `reproduction_summary.md`
- `final_reproduction_report.md` or runner-generated `report.md` plus a final summary
- strategy source file in `factor_mining/`
- backtest run directory under `reports/<factor_name>/`
- `summary.csv`
- `group_cumulative_returns.png`
- `group_mean_returns.png`
- `group_long_short_returns.png`
- IC/IR metrics
- clear conclusion: stable layering yes/no
