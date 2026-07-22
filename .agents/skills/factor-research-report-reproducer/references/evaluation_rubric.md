# Factor Reproduction Evaluation Rubric

Score each section from 0 to 4 and explain every score.

## Formula Fidelity

- 4: explicit report formula, notation, direction, and windows are mapped exactly.
- 3: minor documented substitutions.
- 2: material proxies with defensible interpretation.
- 1: substantial ambiguity.
- 0: formula invented or not implemented.

## Data Fidelity

- 4: universe, frequency, fields, adjustment, and timestamps match.
- 3: limited documented differences.
- 2: local-data reproduction with material proxies.
- 1: severe coverage or provenance gaps.
- 0: data cannot support the hypothesis.

## Timing Integrity

- 4: row-level proof that latest input precedes entry and entry precedes exit.
- 3: correct design with incomplete row-level audit.
- 2: timing inferred from conventions.
- 1: ambiguous alignment.
- 0: leakage or same-period use.

## Signal Validation

- 4: Pearson IC, RankIC, ICIR, win rate, coverage, and monotonicity are stable.
- 3: most diagnostics support the signal.
- 2: mixed or horizon-specific evidence.
- 1: weak evidence.
- 0: sign or signal hypothesis fails.

## Portfolio Realism

- 4: explicit weights, net/gross exposure, turnover, costs, and constraints.
- 3: sound accounting with limited execution assumptions.
- 2: simplified but transparent implementation.
- 1: top-N or group evidence only.
- 0: no executable portfolio definition.

## Robustness

- 4: chronological validation, offsets, cost stress, and walk-forward support.
- 3: most checks support the result.
- 2: meaningful but mixed robustness.
- 1: one favorable sample or parameter.
- 0: result depends on tuning or leakage.

## Reporting Quality

- 4: formula, data mapping, assumptions, code mapping, metrics, candidate outcomes,
  and limitations are complete.
- 3: minor omissions.
- 2: useful but incomplete report.
- 1: summary metrics without an audit trail.
- 0: misleading or non-reproducible claims.

## Public Release Check

A public result fails regardless of score if it exposes proprietary data,
security holdings, licensed reports, private formulas, credentials, or local
filesystem paths.

## Minimum Deliverables

- data availability report;
- data mapping;
- assumption log;
- reproduction summary;
- final report;
- timing and direction contract;
- standardized metrics;
- selected figures;
- exact/local/partial status and reporting scope.
