# Research Sources And Evidence Policy

External research reports informed factor hypotheses during local development.
Copyrighted reports and licensed datasets are not redistributed.

The public repository distinguishes three evidence layers:

| Layer | Public content | Interpretation |
|---|---|---|
| Formula reconstruction | High-level factor intuition and timing | Local implementation, not exact paper replication |
| Portfolio mechanics | Small generic package, focused tests, and synthetic example | Reproducible without private strategies or data |
| Empirical result | Aggregate return paths, metrics, and plots | Verifiable public summary of a private-data run |

## Public Evidence Index

| Item | Location |
|---|---|
| Portfolio case study | `docs/case_studies/ubl_lowvol_portfolio.md` |
| Methodology contract | `docs/methodology.md` |
| UBL family path | `docs/case_studies/UBL.md` |
| PaperUBL reconstruction | `docs/case_studies/PaperUBL.md` |
| Candidate outcomes | `docs/candidate_outcomes.md` |
| Aggregate evidence | `examples/sample_outputs/ubl_lowvol_study/data/` |
| Publication plots | `examples/sample_outputs/ubl_lowvol_study/plots/` |
| Evidence checksums | `examples/sample_outputs/ubl_lowvol_study/data/evidence_manifest.json` |

## Reporting Scope

The repository reports the selected blend relative to the frozen UBL baseline
under the documented model. It does not establish exact reproduction,
production readiness, proprietary-data availability, live execution, or future
profitability.

Summary statements about the research-holdout comparison should also report the
walk-forward, delay, cost, and data-provenance limitations.
