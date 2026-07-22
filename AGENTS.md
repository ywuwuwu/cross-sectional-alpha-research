# Repository Guidance

This repository documents a frozen cross-sectional UBL plus low-volatility
study and includes a small formula-agnostic research package.

## Research Contract

- Keep exact private UBL formulas, raw data, security weights, and local adapters
  out of tracked files.
- Preserve the timing invariant: factor inputs before entry, entry before exit.
- Public inputs must use an oriented score where higher means better.
- Combine security weights before calculating turnover and costs.
- Report full and one-way turnover and state gross exposure.
- Do not change a reported metric without a new frozen evidence snapshot.
- Do not optimize on the viewed research holdout.

## Public Code

- The package under `src/alpha_research/` is intentionally small and
  formula-agnostic.
- It may consume precomputed `alpha_score` values, but it must not construct
  or approximate private strategies.
- Public code may cover validation, portfolio accounting, metrics,
  visualization, and synthetic examples.
- Do not add private strategy imports, parameter defaults, family registries, or
  local data assumptions.
- Public examples must run entirely on synthetic or committed aggregate data.

## Evidence

- Portfolio-level data:
  `examples/sample_outputs/ubl_lowvol_study/data/`.
- Combined-portfolio analysis:
  `docs/case_studies/ubl_lowvol_portfolio.md`.
- Every reported improvement must remain paired with walk-forward, delay, cost,
  and data-provenance results.

## Optional Skill

The report-reproduction skill under `.agents/skills/` structures formula,
assumption, timing, and data-mapping reviews. It must not assume a private
adapter is available in a public clone.
