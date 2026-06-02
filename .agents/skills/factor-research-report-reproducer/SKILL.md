---
name: factor-research-report-reproducer
description: Use when reproducing Chinese or English quant factor research reports in this repository: extract factor formulas, map required data to local data folders, implement Strategy subclasses in factor_mining, run the existing backtest pipeline, generate plots/reports, and distinguish exact reproduction from local-data validation.
---

# Factor Research Report Reproducer

Use this skill to convert a factor research report into a local, testable strategy using this repository's existing factor mining framework. This is not a generic paper summarizer.

When the original report dataset is unavailable, the objective is not exact return replication; the objective is transparent factor-logic implementation and local-data validation.

## Required Workflow

1. Inspect the report and extract:
   - factor intuition
   - formula
   - frequency and window parameters
   - universe and filters
   - ranking direction
   - rebalance timing
   - grouping/long-short rules
   - neutralization rules
   - benchmark/cost assumptions

2. Inspect local code before assuming APIs:
   - `factor_mining/data_loader.py`
   - `factor_mining/strategy_base.py`
   - strategy examples in `factor_mining/*_strategy.py` and `factor_mining/PaperUBL_Strategy.py`
   - `factor_mining/backtest_engine_strategy.py`
   - `run_research_backtest.py`
   - `visualizer.py`
   - `factor_mining/README.md`

3. Create data mapping artifacts before implementation or backtest:
   - `reports/<factor_name>/data_availability_report.md`
   - `reports/<factor_name>/data_mapping.csv`

4. Choose reproduction mode:
   - **Exact reproduction**: only when original universe, sample period, fields, filters, adjustment, costs, neutralization, grouping, and portfolio rules are locally available.
   - **Local-data reproduction**: default when original data is unavailable, proprietary, unclear, or incomplete.

5. Implement or modify a strategy:
   - Put strategy code in `factor_mining/`.
   - Inherit `Strategy` from `factor_mining/strategy_base.py`.
   - Implement `calculate_factor(date, data_loader, **kwargs)` returning `code`, `date`, `factor_value`.
   - Implement `generate_signal(factor_df, top_n)` with correct ranking direction.
   - Reuse existing loaders, filters, neutralization patterns, and caching from local strategies.

6. Run backtests with the existing pipeline:
   - Prefer `python -B run_research_backtest.py --strategy <name> ...`
   - Reuse `visualizer.py` for plots and result tables.
   - Do not create a new engine unless impossible.

7. Validate at five levels:
   - formula-level reproduction
   - signal-level reproduction
   - portfolio-construction reproduction
   - performance-level reproduction
   - local-data validation

8. Final report must document assumptions, mismatches, local data limits, and whether results show stable layering/group separation.

## Reference Navigation

- Repository modules and local schema: `references/repository_map.md`
- Reproduction modes and safe data inspection: `references/local_data_reproduction_policy.md`
- Factor research frameworks and layer tests: `references/analytical_frameworks.md`
- Evaluation checklist: `references/evaluation_rubric.md`
- Machine-readable output contract: `references/output_schema.json`

## Assets

Use these templates when producing deliverables:

- `assets/final_report_template.md`
- `assets/data_mapping_template.csv`
- `assets/assumption_log_template.md`

## Key Local Practices

- Save outputs under `reports/<factor_name>/`.
- Never claim exact report replication unless exact data availability has been verified.
- For mentor-style reproduction, stable grouped factor layering is often the decisive evidence: plot group cumulative curves, group mean returns, and long-short returns.
- Treat `factor_mining/` as strategy/framework source. Keep runner, visualizer, and reports outside it.
