# Research Sources

External research reports informed factor hypotheses during local development.
Copyrighted reports and licensed datasets are not redistributed.

The public repository separates the research into three parts:

| Part | Public content | Interpretation |
|---|---|---|
| Research background | High-level factor intuition and timing | Local implementation, not an exact paper replication |
| Portfolio mechanics | Small generic package, focused tests, and synthetic example | Runs without private strategies or data |
| Portfolio results | Aggregate return paths, metrics, and plots | Summary of the private-data research run |

## Published Files

| Item | Location |
|---|---|
| Portfolio case study | `docs/case_studies/ubl_lowvol_portfolio.md` |
| Methodology contract | `docs/methodology.md` |
| UBL family path | `docs/case_studies/UBL.md` |
| PaperUBL reconstruction | `docs/case_studies/PaperUBL.md` |
| Candidate outcomes | `docs/candidate_outcomes.md` |
| Aggregate result tables | `examples/sample_outputs/ubl_lowvol_study/data/` |
| Publication plots | `examples/sample_outputs/ubl_lowvol_study/plots/` |

## Reporting Scope

The repository reports the selected blend relative to the predefined UBL
baseline under the documented model. It does not establish exact reproduction,
production readiness, proprietary-data availability, live execution, or future
profitability.

Summary statements about the research-holdout comparison should also report the
walk-forward, delay, cost, and data limitations.
