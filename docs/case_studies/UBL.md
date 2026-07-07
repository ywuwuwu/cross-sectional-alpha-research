# Case Study: UBL Improvement Track

## Overview

`UBL` is an active improvement track rather than the current public flagship result. The repository includes a local UBL implementation, but the stronger UBL version will be published later after additional validation and refinement.

For now, this page documents how UBL should be evaluated and improved without promoting an unfinished result.

## Current Public Position

| Item | Status |
|---|---|
| Strategy family | Volume-stability / price-shape alpha |
| Repository status | Implemented locally |
| Public report status | Withheld for now |
| Public claim | Work in progress |
| Current role | Candidate for further research and modification |

## Why UBL Is Still Interesting

UBL remains worth improving because early diagnostics suggest that the factor family can contain meaningful cross-sectional information. The current task is to convert that signal information into a more stable and tradable portfolio result.

In practical alpha research, this is a common gap:

```text
strong IC behavior
      does not automatically imply
strong net portfolio performance
```

The missing link is usually portfolio construction, signal direction, neutralization, turnover control, risk exposure, transaction cost, or regime sensitivity.

## Validation Checklist

Before publishing a stronger UBL case study, validate:

| Check | Purpose |
|---|---|
| Factor direction | Confirm whether high or low raw factor values should be bought |
| Point-in-time alignment | Ensure the signal uses only information available before trade time |
| Coverage | Verify enough stocks are available on each rebalance date |
| IC and RankIC | Measure cross-sectional predictive power |
| ICIR stability | Check whether IC is persistent, not one-regime luck |
| Group monotonicity | Confirm sorted groups behave consistently |
| Long-short return | Test economic spread between top and bottom groups |
| Top-N portfolio | Check whether the alpha survives actual portfolio construction |
| Turnover | Estimate how costly the strategy is to trade |
| Transaction-cost sweep | Test whether results survive realistic costs |
| Neutralization | Control industry, size, beta, and liquidity exposures |
| Train/test split | Avoid tuning entirely on the evaluation period |
| Correlation pruning | Avoid publishing a redundant version of an existing alpha |

## Improvement Directions

Good next experiments include:

- smoothed UBL ranks to reduce rebalance turnover
- industry-size neutralized UBL
- UBL combined with liquidity and volatility filters
- UBL direction testing across market regimes
- rolling ICIR selection between raw UBL and PaperUBL variants
- ensemble scoring with low-correlation reversal or liquidity signals
- risk-controlled long-short construction instead of pure top-N selection

## Publication Standard

Publish a full UBL case study only after it has:

- positive out-of-sample IC or RankIC
- sensible group monotonicity
- positive net long-short performance after cost
- acceptable drawdown
- documented training and testing periods
- clearly described limitations

This protects the project from overclaiming while keeping UBL visible as a high-potential research direction.
