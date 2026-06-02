# Case Study: VolumeMomentumStrategy

## Overview

`VolumeMomentumStrategy` is a partial local-data reproduction of a volume-corrected momentum strategy inspired by the BigQuant research note:

```text
https://bigquant.com/wiki/doc/b15vA5ca1d
```

The goal of this case study is not to redistribute or copy the original report. Instead, this document summarizes the factor logic, maps the required data to the available local dataset, documents the necessary approximations, and explains how the strategy is validated within the local backtesting framework.

This is a **factor-logic validation project**, not an exact performance replication.

---

## Reproduction Status

**Status:** Partial local-data reproduction

**Strategy:** `VolumeMomentumStrategy`

**Default target factor:** `mom_1430_smart`

**Expected output directory:**

```text
reports/volume_momentum_reproduction/
```

---

## Research Motivation

Simple price momentum often mixes several different return components. A stock's past return may come from overnight price movement, intraday trading pressure, liquidity-driven movement, or short-term reversal noise.

The source idea argues that volume and turnover can help distinguish different information environments inside the momentum signal. Instead of treating all past returns equally, the strategy adjusts momentum by using turnover-based information buckets and intraday timing information.

The core hypothesis is:

> Momentum is more informative when conditioned on where the return occurs and how trading activity is distributed across time.

This motivates a factor that separates overnight and intraday return components, then corrects them using turnover or volume proxies.

---

## Simplified Paper Logic

The implemented strategy follows this simplified logic:

1. Split 20-day momentum into intraday and overnight components.

2. Use turnover or volume information to divide each stock's recent 20 observations into low-information and high-information buckets.

3. Combine low-turnover reversal and high-turnover momentum or reversal components after cross-sectional z-scoring.

4. For the final smart factor, `mom_1430_smart`, use:

   * previous-day 14:30-15:00 turnover for the overnight component
   * smart AM/PM intraday turnover for the intraday component

The resulting factor is designed to be a volume-corrected version of momentum rather than a plain past-return signal.

---

## Target Factor

The default target factor is:

```text
mom_1430_smart
```

Conceptually, this factor combines:

```text
overnight momentum/reversal component
+
intraday momentum/reversal component
```

with turnover-based correction.

The implementation should treat `mom_1430_smart` as the main strategy signal unless another target factor is explicitly specified.

---

## Local Data Limitation

The original research logic requires a richer dataset than the public-safe local reproduction can provide.

The original report logic relies on:

* 1-minute intraday bars
* opening auction turnover
* exact intraday turnover
* full A-share universe
* 2014-2023 sample period
* monthly group tests
* original report-specific filters and assumptions

The local repository has:

* daily `turnover_ratio`
* 5-minute bars
* limited 5-minute data coverage, mainly around 2021
* local stock universe and local data filters
* local backtesting and visualization framework

Therefore, this strategy uses **5-minute proxies** for intraday timing and turnover behavior.

The local result should be interpreted as:

```text
factor-logic validation with local proxies
```

not:

```text
exact replication of the original report's published backtest
```

---

## Data Availability and Substitution

| Component                | Original Requirement            | Local Substitute                                | Match Quality              | Expected Impact                                               |
| ------------------------ | ------------------------------- | ----------------------------------------------- | -------------------------- | ------------------------------------------------------------- |
| Universe                 | Full A-share universe           | Local available stock universe                  | Low / Medium               | Performance may differ due to universe mismatch               |
| Sample period            | 2014-2023                       | Local 5-minute data, mainly 2021                | Low                        | Regime and sample-period mismatch may strongly affect results |
| Intraday frequency       | 1-minute bars                   | 5-minute bars                                   | Medium                     | Intraday timing is approximated, not exact                    |
| Opening auction turnover | Exact auction turnover          | Not available or approximated                   | Low                        | Opening-related component may be missing or noisy             |
| Intraday turnover        | Exact intraday turnover         | 5-minute turnover or volume proxy               | Medium                     | Turnover bucket assignment may differ                         |
| Daily turnover           | Daily turnover ratio            | Local `turnover_ratio`                          | High if field is available | Supports fallback and validation logic                        |
| 14:30-15:00 turnover     | Exact late-session turnover     | Aggregated 5-minute proxy from 14:30 to close   | Medium                     | Late-session signal is approximate                            |
| AM/PM turnover           | Exact AM/PM turnover            | Aggregated 5-minute AM/PM proxy                 | Medium                     | Intraday split is approximate                                 |
| Group tests              | Monthly group tests             | Existing local backtest framework               | Medium                     | Portfolio construction may not exactly match report           |
| Transaction costs        | Report-specific cost assumption | Repository default or explicit local assumption | Low / Medium               | Net performance may not be comparable                         |

---

## Implementation Mapping

| Component                  | Repository Location                         |
| -------------------------- | ------------------------------------------- |
| Strategy class             | `factor_mining/volume_momentum_strategy.py` |
| Base strategy interface    | `factor_mining/strategy_base.py`            |
| Data loading               | `factor_mining/data_loader.py`              |
| Factor calculation support | `factor_mining/factor_calculator.py`        |
| Signal generation          | `factor_mining/signal_generator.py`         |
| Portfolio construction     | `factor_mining/portfolio_manager.py`        |
| Performance evaluation     | `factor_mining/performance_evaluator.py`    |
| Backtest entry point       | `run_research_backtest.py`                  |
| Visualization              | `visualizer.py`                             |
| Output folder              | `reports/volume_momentum_reproduction/`     |

The implementation should reuse the existing framework as much as possible. A new backtesting engine should not be created unless the current framework cannot support the required workflow.

---

## Factor Construction Outline

A simplified local implementation should follow this structure:

```text
1. Load daily and 5-minute local data.
2. Construct 20-day return components.
3. Separate overnight and intraday momentum proxies.
4. Aggregate 5-minute turnover or volume into relevant time windows.
5. Build low-turnover and high-turnover buckets.
6. Compute component-level momentum or reversal signals.
7. Cross-sectionally z-score components.
8. Combine components into mom_1430_smart.
9. Rank stocks by the final factor.
10. Run local long-short or group backtest.
```

The implementation should explicitly log every proxy and approximation.

---

## Validation Focus

Because this is not an exact data reproduction, validation should focus on whether the factor logic is implemented correctly and behaves reasonably on local data.

Recommended validation checks:

| Check                           | Purpose                                                          |
| ------------------------------- | ---------------------------------------------------------------- |
| Factor coverage                 | Ensure the signal exists for enough stocks and dates             |
| Missing-value ratio             | Detect unusable factor construction                              |
| Cross-sectional distribution    | Check whether the factor has meaningful dispersion               |
| Correlation with plain momentum | Verify that the factor is not merely simple momentum             |
| Turnover-bucket behavior        | Check whether low/high turnover buckets produce distinct signals |
| IC and RankIC                   | Evaluate cross-sectional predictive power                        |
| Group returns                   | Check monotonicity across factor groups                          |
| Long-short performance          | Evaluate economic relevance                                      |
| Turnover                        | Measure trading intensity                                        |
| Drawdown                        | Evaluate downside behavior                                       |

The most important diagnostic is not whether the local Sharpe exactly matches the original report, but whether the strategy produces interpretable signal behavior under the local proxy construction.

---

## Expected Output Artifacts

A completed local reproduction should create:

```text
reports/volume_momentum_reproduction/
├── data_availability_report.md
├── data_mapping.csv
├── assumption_log.md
├── implementation_plan.md
├── validation_report.md
├── final_reproduction_report.md
├── metrics.csv
├── backtest_results.csv
└── figures/
```

The `assumption_log.md` should clearly distinguish:

* report assumptions
* local implementation assumptions
* inferred assumptions
* missing assumptions
* manual review items

---

## Interpretation of Results

The local backtest should be interpreted carefully.

If the strategy performs well locally, the result suggests that the volume-corrected momentum logic may be robust enough to survive approximate 5-minute proxy construction.

If the strategy performs poorly locally, the result does not necessarily reject the original paper idea, because the implementation differs from the original in several important ways:

* 5-minute bars instead of 1-minute bars
* limited sample period
* different universe
* unavailable opening auction turnover
* approximate intraday turnover
* possibly different rebalance and grouping rules

Therefore, the key conclusion should focus on factor behavior, implementation validity, and difference attribution rather than exact performance comparison.

---

## Limitations

This reproduction has several important limitations:

1. The original report's exact data is not available.
2. The original report uses 1-minute bars, while the local implementation uses 5-minute proxies.
3. Opening auction turnover is unavailable or only approximated.
4. Full 2014-2023 A-share coverage is unavailable in the local 5-minute data.
5. Monthly group tests may not exactly match the original report's testing framework.
6. Transaction-cost assumptions may differ.
7. Local universe filters may differ from the original report.
8. The implementation validates factor logic, not exact report performance.

---

## Future Improvements

To move from partial local-data reproduction toward closer reproduction, the next steps are:

1. Add full 1-minute intraday bars.
2. Add opening auction turnover.
3. Extend local data coverage to the original 2014-2023 sample period.
4. Match the original report's universe and stock filters.
5. Reproduce the original monthly group test methodology.
6. Compare simple momentum, volume-corrected momentum, and `mom_1430_smart` side by side.
7. Add robustness checks by year, industry, market-cap bucket, and liquidity bucket.
8. Add transaction-cost sensitivity analysis.
9. Add correlation analysis against existing reproduced factors.
10. Add a sanitized public example using synthetic intraday data.

---

## Summary

`VolumeMomentumStrategy` is a public-safe case study showing how a research-report factor idea can be converted into a local, auditable factor implementation.

The main contribution is not exact report replication. The contribution is the structured workflow:

```text
research idea
→ factor formula
→ local data mapping
→ proxy construction
→ backtest implementation
→ validation
→ limitation analysis
```

This is the realistic workflow a quant researcher follows when translating an external factor idea into an internal research environment.

