# Public Release Scope

## Included In The Public Repository

- a small formula-agnostic Python package for score validation, portfolio
  accounting, metrics, and visualization;
- an anonymous synthetic example and focused tests;
- an audited builder and renderer for aggregate evidence;
- research methodology and portfolio-accounting definitions;
- UBL, PaperUBL, and UBL plus LOWVOL case studies;
- aggregate return, turnover, cost, bootstrap, and walk-forward data;
- six portfolio-comparison figures;
- candidate decisions, limitations, and report-reproduction templates.

## Retained Locally

- raw daily and intraday market data;
- security identifiers, private weights, and trade ledgers;
- exact private UBL formulas and factor values;
- strategy constructors, family registries, and parameter defaults;
- the local factor adapter and backtest engine;
- the strategy-aware runner and visualizer;
- exploratory notebooks, parameter scans, and internal tests;
- full report snapshots and intermediate plots;
- lifecycle mappings and private data-path configuration.

The public package starts from precomputed, oriented `alpha_score` values. It
demonstrates research mechanics but does not reproduce the private
security-level strategy engine.

## Evidence Boundary

The public evidence builder verifies the private snapshot manifest, clean source
commit, clean public curation commit, configuration hash, dependency-lock hash,
and every curated input before writing. The public manifest stores those hashes
without local filesystem paths.

This supports claim-to-artifact tracing for the released aggregate evidence. It
does not make the omitted formulas, holdings, raw data, or private engine
publicly reproducible.

## Release Pipeline

Start with committed private research code and a clean private worktree.
Generate a new immutable private snapshot, then run the public build only while
the public repository is also clean:

```bash
git status --short

PRIVATE_SNAPSHOT=/path/to/immutable/ubl_lowvol_snapshot
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
git commit -m "Regenerate evidence from clean research snapshot"
git tag -a v0.2.0 -m "Reproducible public evidence release"
git push origin main
git push origin v0.2.0
```

Review every staged Python, CSV, JSON, Markdown, and image file before
committing. The release manifest must record
`source_worktree_was_dirty: false`.
