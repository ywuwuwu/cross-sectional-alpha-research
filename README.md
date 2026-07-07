# Quant Factor Report Reproducer

A research automation project for reproducing quant factor research reports using local data, reusable factor code, backtesting, visualization, and audit documentation.

This project was designed to turn unstructured factor research reports into reproducible local research workflows. It extracts factor intuition, formulas, data requirements, portfolio-construction assumptions, and performance metrics, then maps them to an existing Python factor-research framework.

The project is a quant research engineering workflow for factor implementation, local-data validation, and reproducible backtesting.

---

## Motivation

Professional factor research reports often contain valuable ideas, but reproducing them is time-consuming because the analyst must manually identify:

- factor intuition
- factor formula
- required data fields
- universe and sample-period assumptions
- signal construction
- ranking and grouping logic
- neutralization or risk adjustment
- portfolio construction
- transaction costs
- benchmark assumptions
- performance metrics

In practice, the original report dataset is often unavailable or proprietary. This project therefore separates **formula-level reproduction** from **performance-level reproduction**.

When the original report dataset is unavailable, the objective is not exact return replication; the objective is transparent factor-logic implementation and local-data validation.

---

## Core Contribution

This project contributes:

1. A reusable Codex skill for factor research report reproduction.
2. A Python factor-research framework for strategy implementation and local backtesting.
3. A local-data reproduction protocol for cases where the original research-report data is unavailable.
4. A structured audit trail including data mapping, assumption logs, validation reports, and final reproduction reports.
5. A public-safe project structure that excludes proprietary data and copyrighted source reports.

---

## System Workflow

```text
Research Report
      ↓
Factor Intuition Extraction
      ↓
Formula and Assumption Mapping
      ↓
Local Data Availability Check
      ↓
Data Requirement Mapping
      ↓
Factor Strategy Implementation
      ↓
Signal Generation
      ↓
Portfolio Construction
      ↓
Backtest Execution
      ↓
Visualization
      ↓
Validation and Final Report
```

## Implemented Strategy Reproductions

This repository includes several local-data reproductions of factor research ideas. The original source reports are not redistributed. Each strategy is implemented as a public-safe local reproduction using the available data pipeline and backtesting framework.


| Strategy                      | Source Idea                                      | Implementation File                                                                                                 | Reproduction Status             | Main Purpose                                                                                                                   |
| ----------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| UTR Strategy                  | Volume-stability / turnover-rate factor research | `factor_mining/utr_strategy.py`                                                                                     | Local-data reproduction         | Reproduces a turnover-based signal and evaluates its cross-sectional predictive power                                          |
| UBL Strategy                  | Volume-stability turnover factor variant         | `factor_mining/ubl_strategy.py`                                                                                     | Local-data reproduction         | Tests a report-derived extension of UBL factor using the local daily data and portfolio framework                              |
| Paper UBL Strategy            | Paper-style UBL implementation                   | `factor_mining/PaperUBL_Strategy.py`                                                                                | Local-data reproduction         | Keeps a closer implementation of the report formula for comparison against the adapted local version                           |
| CPV Strategy                  | CPV price-volume autocorrelation factor research | `factor_mining/cpv_strategy.py`                                                                                     | Local-data reproduction         | Reproduces a price-volume correlation factor and evaluates its group returns, IC, RankIC, and long-short behavior              |
| CTR Strategy                  | Turnover-sliced CTR factor research              | `factor_mining/ctr_strategy.py`                                                                                     | Local-data reproduction         | Tests whether turnover segmentation improves or changes the behavior of a CTR-style factor                                     |
| Volume Momentum Strategy      | Volume-corrected momentum strategy               | `factor_mining/volume_momentum_strategy.py`                                                                         | Partial local-data reproduction | Implements the `mom_1430_smart` logic using daily turnover and 5-minute intraday proxies instead of the original 1-minute data |
| Factor Segmentation Framework | Factor slicing and decomposition methodology     | `factor_mining/signal_generator.py`, `factor_mining/portfolio_manager.py`, `factor_mining/performance_evaluator.py` | Framework reproduction          | Provides reusable grouping, ranking, portfolio construction, and evaluation utilities for factor reproduction                  |


These strategies should be interpreted as **local-data validations**, not exact replications of the original reports. Exact performance comparison is only valid when universe, sample period, data frequency, filters, transaction costs, and portfolio construction rules match the original report.

## Public Case Studies

The repository publishes curated examples instead of the full raw `reports/` directory.

| Item | Location | Purpose |
|---|---|---|
| PaperUBL sample report | `examples/sample_outputs/paper_ubl/report.md` | Public sample output with metrics and figures |
| PaperUBL case study | `docs/case_studies/PaperUBL.md` | Current public flagship reproduction example |
| UBL improvement track | `docs/case_studies/UBL.md` | Documents the next stronger UBL research direction without overclaiming unfinished results |
| Strategy comparison | `docs/case_studies/strategy_comparison.md` | Explains which strategy results are publishable now and which remain experimental |
| Report references | `docs/report_references.md` | Documents public references and internal report handling policy |

The current public sample focuses on `PaperUBL`. A stronger modified `UBL` strategy is planned as a later flagship case study after additional validation, drawdown reduction, transaction-cost testing, and walk-forward checks.

## Reproduction Modes

The project supports four reproduction statuses.


| Status                           | Meaning                                                                                                   |
| -------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Exact reproduction               | Local data and assumptions match the report closely enough for direct performance comparison.             |
| Local-data reproduction          | The factor logic is implemented and tested on available local data, but exact report data is unavailable. |
| Partial local-data reproduction  | Some factor components are implemented, but required data or assumptions are incomplete.                  |
| Implementation-only reproduction | The factor logic is mapped to code or pseudocode, but a valid backtest cannot be run.                     |


## Repository Structure

```
.
├── .agents/skills/factor-research-report-reproducer/
│   ├── SKILL.md
│   ├── assets/
│   └── references/
├── factor_mining/
│   ├── data_loader.py
│   ├── factor_calculator.py
│   ├── signal_generator.py
│   ├── portfolio_manager.py
│   ├── performance_evaluator.py
│   ├── strategy_base.py
│   ├── cpv_strategy.py
│   ├── ctr_strategy.py
│   ├── ideal_reversal_strategy.py
│   ├── PaperUBL_Strategy.py
│   ├── ubl_strategy.py
│   ├── utr_strategy.py
│   └── volume_momentum_strategy.py
├── run_research_backtest.py
├── visualizer.py
├── config/
├── docs/
├── examples/
├── reports/
└── tests/
```

## Main Components

factor_mining/

Contains the core factor-research modules:

- data loading  
- factor calculation  
- signal generation  
- portfolio construction  
- strategy definitions  
- performance evaluation

`run_research_backtest.py`

Canonical entry point for running local factor backtests where supported.

`visualizer.py`

Visualization utilities for plotting strategy results.

`.agents/skills/factor-research-report-reproducer/SKILL.md`

Codex skill that guides the reproduction workflow. It instructs Codex to:

- read a factor research report  
- extract factor intuition and formula  
- inspect local data availability  
- map report data requirements to local data  
- reuse the existing factor framework  
- run the existing backtest pipeline where possible  
- generate plots and validation reports  
- clearly distinguish exact reproduction from local-data reproduction

## Local Data Policy

This public repository does not include raw market data or source research reports.

The original private/local project may use data sources such as:

```
data/data_daily/
data/data_ret/
data/data_industry/
data/data_barra/
data/data_ud_new/
data_5m/
data.pkl
date.pkl
```

These files are intentionally excluded from GitHub.

To run the project locally, copy:
`config/data_paths.example.yaml`
to:
`config/data_paths.yaml`
and update the paths to point to your private local data.

## Expected Outputs

Each reproduction run should produce a dedicated folder under:

`reports/<factor_name>/`

Expected files include:

```
data_availability_report.md
data_mapping.csv
assumption_log.md
implementation_plan.md
validation_report.md
final_reproduction_report.md
figures/
metrics.csv
backtest_results.csv
```

Generated `reports/` outputs are ignored by default to avoid publishing private data-derived results.

For GitHub, publish only cleaned sample outputs such as:

```
examples/sample_outputs/paper_ubl/
docs/case_studies/
docs/report_references.md
```

Do not publish raw full `reports/` folders until smoke tests, failed experiments, private paths, and experimental strategy labels have been reviewed.

## Using the Codex Skill

From the project root, start Codex and call the skill explicitly:

```
Use $factor-research-report-reproducer to reproduce the CPV factor from my local research report.

First inspect the report and repository. Then create the data mapping, assumption log, and implementation plan under reports/cpv_reproduction/. Do not modify code or run the backtest until I approve the plan.
```

A full workflow prompt may look like:

```
Use $factor-research-report-reproducer to reproduce a factor research report.

Please:
1. Extract the factor intuition, formula, universe, sample period, rebalance rule, grouping method, benchmark, and reported metrics.
2. Inspect factor_mining/data_loader.py and map the report data requirements to local datasets.
3. Reuse factor_mining modules where possible.
4. Use run_research_backtest.py for the backtest if possible.
5. Use visualizer.py for plots if possible.
6. Save outputs under reports/<factor_name>/.
7. Clearly label the reproduction status.
8. Do not claim exact performance replication unless local data and report data match.
```

