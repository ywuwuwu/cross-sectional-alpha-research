# Public Release Scope

## Included In The Public Repository

- a compact, strategy-agnostic reference package for score validation,
  portfolio accounting, metrics, and visualization;
- an anonymous synthetic example and focused tests;
- a builder and renderer for aggregate result files;
- research methodology and portfolio-accounting definitions;
- UBL, PaperUBL, and UBL plus LOWVOL case studies;
- aggregate return, turnover, cost, bootstrap, and walk-forward data;
- six portfolio-comparison figures;
- candidate results, limitations, and report-reproduction templates.

## Retained Locally

- raw daily and intraday market data;
- security identifiers, private weights, and trade ledgers;
- report-derived factor implementations, licensed data, and factor values;
- strategy constructors, family registries, and parameter defaults;
- the local factor adapter and backtest engine;
- the strategy-aware runner and visualizer;
- exploratory notebooks, parameter scans, and internal tests;
- full report snapshots and intermediate plots;
- lifecycle mappings and private data-path configuration;
- local source-version and output-hash records.

The public package starts from precomputed, oriented `alpha_score` values. It
demonstrates research mechanics but does not reproduce the internal
security-level research engine.

## Result Boundary

Before copying aggregate results, the release builder checks the versioned
private snapshot, source state, configuration, dependency lock, and curated
inputs. The detailed build record remains local.

The published tables and figures can be inspected and regenerated from the
included aggregate CSVs. They do not make the omitted factor implementations,
holdings, licensed data, or internal engine reproducible.

## Release Pipeline

Start with committed private research code and a clean private worktree.
Generate a new versioned private snapshot, then run the public build only while
the public repository is also clean:

```bash
git status --short

PRIVATE_SNAPSHOT=/path/to/ubl_lowvol_snapshot
python tools/build_public_evidence.py --source "$PRIVATE_SNAPSHOT"

python -m pytest -q tests/test_sample_package.py
python examples/run_sample_package.py
python examples/render_public_results.py

git status --short
git diff --check
git grep -n "$HOME" -- .
git add README.md docs examples tools tests .gitignore pyproject.toml
git diff --cached --name-status
git diff --cached --check
git commit -m "Update published research results"
git tag -a vX.Y.Z -m "Research result release vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Review every staged Python, CSV, JSON, Markdown, and image file before
committing. The generated local build record is ignored by Git and should not
be staged.
