# Public Release Scope

## Included In The Public Repository

- a small formula-agnostic Python package for score validation, portfolio
  accounting, metrics, and visualization;
- an anonymous synthetic example and focused tests;
- a renderer for the committed aggregate evidence;
- research methodology and portfolio-accounting definitions;
- UBL, PaperUBL, and UBL plus LOWVOL case studies;
- frozen aggregate return, turnover, cost, bootstrap, and walk-forward data;
- six portfolio-comparison figures;
- candidate decisions, limitations, and report-reproduction templates.

## Retained Locally

- raw daily and intraday market data;
- security identifiers, private weights, and trade ledgers;
- exact private UBL formulas and factor values;
- strategy constructors, family registries, and parameter defaults;
- the local factor adapter and backtest engine;
- the original strategy-aware runner and visualizer;
- exploratory notebooks, parameter scans, and internal tests;
- full report snapshots and intermediate plots;
- lifecycle mappings and private data-path configuration.

The public package starts from precomputed, oriented `alpha_score` values.
It demonstrates research mechanics but does not reproduce the private
security-level strategy engine.

## Publication Checks

Before pushing:

```bash
git status --short
git diff --cached --name-status
git diff --cached --check
git grep --cached -n "$HOME"
python -m pytest -q tests/test_sample_package.py
python examples/run_sample_package.py
python examples/render_public_results.py
```

Review every staged Python, CSV, JSON, Markdown, and image file before
committing.
