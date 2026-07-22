---
name: factor-research-report-reproducer
description: Use when reconstructing a Chinese or English quant factor report: extract formulas and assumptions, define point-in-time timing, map available data, choose an exact/local/partial reproduction mode, specify implementation and validation, and produce an auditable report without inventing missing math.
---

# Factor Research Report Reproducer

Use this skill to structure a factor-report reconstruction. It is independent of
the private UBL implementation and does not require the local backtest engine.

When the original report data is unavailable, the objective is transparent
factor-logic reconstruction and local-data validation, not exact return
replication.

## Operating Modes

### Public Sample Package

Use `src/alpha_research/` for formula-agnostic timing validation,
portfolio accounting, metrics, and report generation from precomputed oriented
scores. The synthetic example demonstrates the interface without reconstructing
a private strategy.

### Local Adapter

If the user supplies a private data loader or backtest adapter, inspect its API
and timing before using it. Do not assume a particular folder, class hierarchy,
or command exists merely because an older project used one.

## Required Workflow

1. Extract the economic hypothesis.
2. Record the explicit formula, notation, windows, direction, and ambiguities.
3. Separate report formula, inferred formula, local implementation, and proxy.
4. Map every required field to an observed data source and timestamp.
5. Choose exact, local-data, partial, or implementation-only reproduction.
6. Freeze direction, timing, universe, rebalance, costs, and selection gates.
7. Require `latest_factor_input < entry < exit`.
8. Orient the signal so higher `alpha_score` always means higher expected
   return.
9. Evaluate Pearson IC and Spearman RankIC separately.
10. Report group monotonicity, long/short legs, turnover, costs, drawdown, and
    coverage.
11. Use chronological validation, offset tests, and robustness checks before
    carrying a candidate forward.
12. Document mismatches, candidate decisions, unresolved items, and reporting
    limits.

## Public Project Map

- Sample runner: `src/alpha_research/runner.py`
- Portfolio accounting: `src/alpha_research/portfolio.py`
- Metrics: `src/alpha_research/metrics.py`
- Visualization: `src/alpha_research/visualization.py`
- Synthetic example: `examples/run_sample_package.py`
- Methodology contract: `docs/methodology.md`
- Combined-portfolio study:
  `docs/case_studies/ubl_lowvol_portfolio.md`
- Aggregate evidence:
  `examples/sample_outputs/ubl_lowvol_study/data/`

A supplied local adapter may add factor construction and security-level
backtesting. Keep adapter-specific paths in local reports rather than public
templates.

## Required Artifacts

Write local outputs under an ignored research directory:

- `data_availability_report.md`
- `data_mapping.csv`
- `assumption_log.md`
- `reproduction_summary.md`
- `final_reproduction_report.md`
- metric and figure files when execution is possible

## References

- Public repository layout: `references/repository_map.md`
- Reproduction modes and data inspection:
  `references/local_data_reproduction_policy.md`
- Analytical frameworks: `references/analytical_frameworks.md`
- Evaluation rubric: `references/evaluation_rubric.md`
- Machine-readable output contract: `references/output_schema.json`

## Assets

- `assets/final_report_template.md`
- `assets/reproduction_summary_template.md`
- `assets/data_mapping_template.csv`
- `assets/assumption_log_template.md`

## Guardrails

- Do not invent missing formulas.
- Do not choose sign using the final evaluation sample.
- Do not align a close-derived signal with a return that begins before entry.
- Do not call RankIC simply IC.
- Do not omit full-turnover and gross-exposure conventions.
- Do not publish copyrighted reports, proprietary data, security holdings, or
  private formulas.
- Do not claim exact reproduction unless every material data and implementation
  assumption matches.
