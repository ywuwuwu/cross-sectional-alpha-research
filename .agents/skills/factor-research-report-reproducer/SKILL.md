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

2. Mathematical Logic Extraction and Code Mapping:
   - Extract and summarize the mathematical formulas in the research report.
   - Identify factor formula, notation and variable definitions, rolling windows, ranking or grouping logic, z-scoring or standardization, neutralization if used, turnover / volume / return transformations, portfolio construction math, IC / RankIC / long-short return calculations, and parameter choices such as lookback window, rebalance frequency, group count, or threshold.
   - If the report is in Chinese, preserve the original factor name where useful, but explain the math in clear English.
   - Distinguish explicit formula from the report, inferred formula, local implementation formula, and missing or ambiguous formula.
   - Do not hallucinate missing math. If a report does not provide explicit formulas, say so.
   - Map each mathematical component to implementation files, class names, and function or method names, preferably in `factor_mining/`.

3. Inspect local code before assuming APIs:
   - `factor_mining/data_loader.py`
   - `factor_mining/strategy_base.py`
   - strategy examples in `factor_mining/*_strategy.py` and `factor_mining/PaperUBL_Strategy.py`
   - `factor_mining/backtest_engine_strategy.py`
   - `run_research_backtest.py`
   - `visualizer.py`
   - `factor_mining/README.md`

4. Create required artifacts before implementation or backtest:
   - `reports/<factor_name>/data_availability_report.md`
   - `reports/<factor_name>/data_mapping.csv`
   - `reports/<factor_name>/reproduction_summary.md`

5. Choose reproduction mode:
   - **Exact reproduction**: only when original universe, sample period, fields, filters, adjustment, costs, neutralization, grouping, and portfolio rules are locally available.
   - **Local-data reproduction**: default when original data is unavailable, proprietary, unclear, or incomplete.

6. Implement or modify a strategy:
   - Put strategy code in `factor_mining/`.
   - Inherit `Strategy` from `factor_mining/strategy_base.py`.
   - Implement `calculate_factor(date, data_loader, **kwargs)` returning `code`, `date`, `factor_value`.
   - Implement `generate_signal(factor_df, top_n)` with correct ranking direction.
   - Reuse existing loaders, filters, neutralization patterns, and caching from local strategies.

7. Run backtests with the existing pipeline:
   - Prefer `python -B run_research_backtest.py --strategy <name> ...`
   - Reuse `visualizer.py` for plots and result tables.
   - Do not create a new engine unless impossible.

8. Validate at five levels:
   - formula-level reproduction
   - signal-level reproduction
   - portfolio-construction reproduction
   - performance-level reproduction
   - local-data validation

9. Final outputs must include:
   - `reports/<factor_name>/final_reproduction_report.md`
   - `reports/<factor_name>/reproduction_summary.md`
   - The final report should be broader and performance-focused.
   - `reproduction_summary.md` should be concise and focused on math -> financial meaning -> local implementation.
   - Both reports must document assumptions, mismatches, local data limits, and whether results show stable layering/group separation.

## Reference Navigation

- Repository modules and local schema: `references/repository_map.md`
- Reproduction modes and safe data inspection: `references/local_data_reproduction_policy.md`
- Factor research frameworks and layer tests: `references/analytical_frameworks.md`
- Evaluation checklist: `references/evaluation_rubric.md`
- Machine-readable output contract: `references/output_schema.json`

## Assets

Use these templates when producing deliverables:

- `assets/final_report_template.md`
- `assets/reproduction_summary_template.md`
- `assets/data_mapping_template.csv`
- `assets/assumption_log_template.md`

## Key Local Practices

- Save outputs under `reports/<factor_name>/`.
- Never claim exact report replication unless exact data availability has been verified.
- For mentor-style reproduction, stable grouped factor layering is often the decisive evidence: plot group cumulative curves, group mean returns, and long-short returns.
- Treat `factor_mining/` as strategy/framework source. Keep runner, visualizer, and reports outside it.
- Do not invent formulas that are not in the report.
- If a formula is inferred from prose or code, label it as inferred.
- If local implementation differs from the report formula, explain the difference.
- If local data requires proxies, explain how the proxy changes the math.
- Prefer mapping formulas to existing files in `factor_mining/`.
- Use file paths, class names, and function names for code mapping.
- Do not claim exact mathematical reproduction if key inputs are unavailable.
- Keep `reproduction_summary.md` concise enough for a quant researcher to review quickly.
