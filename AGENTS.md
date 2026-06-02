# Repository Guidance

This is a quant factor research reproduction repository.

## Core Rules

- Reuse `factor_mining/` modules for strategy, data loading, portfolio, and evaluation.
- Reuse `run_research_backtest.py` for research backtests whenever possible.
- Reuse `visualizer.py` for plots, group-layering evidence, and report artifacts.
- Do not create a new backtesting engine unless the existing one cannot support the task.
- Do not overwrite raw data.
- Do not modify notebooks unless explicitly asked.
- Implement new factor strategies inside `factor_mining/` as `Strategy` subclasses.
- Keep runner, visualizer, reports, and skill assets outside `factor_mining/` unless they are strategy/framework source.

## Data Policy

- Inspect local data safely: code first, folder listings, small CSV samples, loader methods.
- Do not fully load large `.zip`, `.pkl`, or entire data folders unless necessary.
- Do not assume field names, ticker formats, adjustment methods, return definitions, or date coverage without checking.
- Document all assumptions.
Local data may exist in:

- `data/data_barra/`
- `data/data_daily/`
- `data/data_industry/`
- `data/data_ret/`
- `data/data_ud_new/`
- `data/date.pkl`
- `data_5m/`
- `data.pkl`

## Reproduction Policy

- Distinguish exact reproduction from local-data reproduction.
- Exact reproduction requires local availability of the report's universe, sample period, fields, filters, neutralization, portfolio construction, costs, and rebalance rules.
- If original report data is unavailable, reproduce factor logic and validate with local data transparently.
- Do not claim local results exactly match a report unless exact data availability is verified.

## Required Outputs

Save outputs under `reports/<factor_name>/` or the runner's `reports/<strategy>_<timestamp>/` directory.

Before implementing/running a reproduction, create:

- `reports/<factor_name>/data_availability_report.md`
- `reports/<factor_name>/data_mapping.csv`

Final reproduction reports should include:

- implemented formula
- data mapping
- assumptions
- backtest command
- metrics
- IC/IR
- group/layering plots
- reasons local results may differ from the original report

## Mentor Standard

For factor report reproduction, stable group layering is decisive evidence. Show:

- group cumulative returns
- group mean returns
- long-short group returns
- IC direction and IR
- whether layering is stable and directionally consistent
