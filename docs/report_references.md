# Research Sources

External research reports informed factor hypotheses during local development.
Copyrighted reports and licensed datasets are not redistributed.

The public repository separates the research into three parts:

| Part | Public content | Interpretation |
|---|---|---|
| Research background | High-level factor intuition and timing | Local implementation, not an exact paper replication |
| Portfolio mechanics | Compact strategy-agnostic package, focused tests, and synthetic example | Runs without report-derived factors or licensed data |
| Portfolio results | Aggregate return paths, metrics, and plots | Summary of the research run using non-redistributed data |

## Published Files

| Item | Location |
|---|---|
| Portfolio case study | `docs/case_studies/ubl_lowvol_portfolio.md` |
| Methodology | `docs/methodology.md` |
| UBL family path | `docs/case_studies/UBL.md` |
| PaperUBL reconstruction | `docs/case_studies/PaperUBL.md` |
| Candidate results | `docs/candidate_outcomes.md` |
| Aggregate result tables | `examples/sample_outputs/ubl_lowvol_study/data/` |
| Publication plots | `examples/sample_outputs/ubl_lowvol_study/plots/` |

## Reporting Scope

The repository reports the selected blend relative to the pre-specified UBL
baseline under the documented model. It does not establish exact reproduction,
production readiness, proprietary-data availability, live execution, or future
profitability.

Summary statements about the observed chronological holdout should also report the
walk-forward, delay, cost, and data limitations.
