# Public Repository Map

## Sample Package

- `src/alpha_research/runner.py`: point-in-time panel validation,
  quantile long/short execution, IC diagnostics, and a weight ledger.
- `src/alpha_research/portfolio.py`: dollar-neutral normalization,
  sleeve combination, turnover, costs, and PnL accounting.
- `src/alpha_research/metrics.py`: Sharpe, drawdown, performance
  summaries, and paired moving-block bootstrap.
- `src/alpha_research/visualization.py`: generic comparison plots and
  `Visualizer.save_report()`.
- `examples/run_sample_package.py`: anonymous point-in-time synthetic
  example.
- `examples/render_public_results.py`: renderer for committed aggregate
  evidence.
- `tests/test_sample_package.py`: timing, accounting, report, evidence,
  and privacy checks.

The package accepts precomputed oriented scores. It does not contain alpha
formulas or strategy factories.

## Research Documentation

- `README.md`: project summary, package example, portfolio comparison,
  and review order.
- `docs/methodology.md`: timing, direction, cost, and metric contracts.
- `docs/case_studies/UBL.md`: UBL family selection and implementation
  logic.
- `docs/case_studies/PaperUBL.md`: paper-style reference
  reconstruction.
- `docs/case_studies/ubl_lowvol_portfolio.md`: combined-portfolio
  analysis.
- `docs/candidate_outcomes.md`: candidate decisions and timing
  revisions.
- `docs/public_release_scope.md`: public/private boundary.
- `docs/report_references.md`: source and evidence policy.

## Aggregate Evidence

`examples/sample_outputs/ubl_lowvol_study/data/` contains:

- split-level portfolio metrics;
- same-date aggregate returns, turnover, and costs;
- transaction-cost sensitivity;
- fixed-rule walk-forward folds;
- paired bootstrap summaries and Sharpe differences;
- PnL concentration;
- evidence identifiers and checksums.

`examples/sample_outputs/ubl_lowvol_study/plots/` contains six selected
portfolio-comparison figures.

## Local Implementation Boundary

The private workspace may contain data loaders, factor formulas, strategy
registries, backtest engines, and full report archives. They are outside the
sample package.

Before using a local adapter:

1. inspect its input and output schema;
2. verify its timestamp convention;
3. test one anonymous score panel;
4. record the exact command and code version locally;
5. review all generated artifacts before publication.
