# Candidate Results

This note compares the supporting factor candidates and timing diagnostics used
around the UBL portfolio. Interpretation is based on cross-sectional evidence,
standalone returns, common-date implementation, incremental information, and
portfolio contribution rather than a single Sharpe ratio.

All results use the point-in-time and metric conventions in
[methodology.md](methodology.md). LOWVOL results are promising, but remain
research evidence rather than audited trading performance.

## Summary

| Candidate | Research use | Outcome | Interpretation |
|---|---|---|---|
| LOWVOL_60 | Defensive sleeve in the selected 80/20 portfolio | Provisionally included | Improves UBL Sharpe, drawdown, turnover, cost tolerance, and concentration on common dates |
| LOWVOL_20 | Shorter-window robustness comparison | Retained for comparison | Stronger observed standalone statistics, but was not pre-specified as the primary sleeve |
| MOM_60_5 | Medium-term continuation test | Not included | Negative validation RankIC and negative gross return |
| MOM_120_20 | Longer continuation test | Not included | Negative validation RankIC and weak offset breadth |
| Early unlagged UBL diagnostics | Timing diagnostic | Superseded | Factor and return labels did not describe an executable same-period trade |

## Low-Volatility Candidates

### Pre-Specified Factor Definitions

The factor definitions and directions were set before evaluation:

- `LOWVOL_60` ranks stocks using a 60-day realized-volatility window and is the
  slower primary specification.
- `LOWVOL_20` uses a 20-day window and was pre-specified as a robustness comparison.
- Higher score always means lower realized volatility and higher expected
  return; the sign was not reversed after seeing results.
- Both candidates use a 20-trading-day holding horizon, 20 staggered offsets,
  next-tradable VWAP entry, a dollar-neutral gross-2 book, and a base cost of 10
  bps per dollar traded.
- Raw equal-offset portfolios are the standalone evidence. The inherited 7.5
  bps weight-change band is a fixed implementation sensitivity.

The local close-to-close series does not contain independently verified
corporate-action adjustment metadata, and no pre-2020 price history was
available for a true out-of-sample warm-up. Those constraints make the result
provisional.

### Cross-Sectional Evidence

| Candidate | Train RankIC | Validation RankIC | Viewed-holdout RankIC | Validation RankIC win rate | Validation HAC t-stat |
|---|---:|---:|---:|---:|---:|
| LOWVOL_60 | 0.1031 | 0.0721 | 0.1427 | 61.5% | 1.45 |
| LOWVOL_20 | 0.0941 | 0.1069 | 0.1619 | 74.0% | 2.05 |

Both pre-specified positive directions survive train and validation. The
validation decile ordering is also positive: the Spearman correlation between
decile number and average return is 0.588 for LOWVOL_60 and 0.770 for
LOWVOL_20. Adjacent deciles increase in 5/9 and 6/9 comparisons respectively.

The mechanically annualized RankICIR is intentionally not emphasized. Forward
20-day returns overlap, so the HAC statistic and executable staggered
portfolios are more informative than treating every daily IC as independent.
The holdout values are confirmation-only because that period has already been
viewed.

### Standalone Executable Evidence

The first comparison uses every available validation date for each raw
standalone sleeve.

| Candidate | Validation observations | Net return | Net Sharpe | Max DD | Full turnover | Break-even cost | Positive offsets |
|---|---:|---:|---:|---:|---:|---:|---:|
| LOWVOL_60 | 115 | 6.98% | 1.008 | 10.04% | 0.074 | 95.98 bps | 16 / 20 |
| LOWVOL_20 | 115 | 13.40% | 1.861 | 8.32% | 0.136 | 93.79 bps | 20 / 20 |

At 20 bps, LOWVOL_60 retains a 6.08% validation return and 0.892 net Sharpe;
LOWVOL_20 retains 11.64% and 1.643. Low turnover gives both raw sleeves a wide
standalone cost cushion in this simplified linear-cost model.

Excluding the best training offset barely changes validation results:
LOWVOL_60 net Sharpe is 1.002 and LOWVOL_20 is 1.824. Two fixed-rule
selection-period walk-forward folds are positive for each candidate, with
aggregate net returns of 33.66% and 31.64%. Those folds cover only 126 test
observations inside the train and validation era, so they are stability checks,
not a fresh out-of-sample result.

### Common-Date Reconciliation

The attractive full-validation result does not transfer uniformly to the dates
available to the selected UBL portfolio. The table below uses the same 7.5 bps
weight-change policy before and after restricting to the 111 UBL-common dates.

| Candidate | Full validation net return | Common-date net return | Common-date net Sharpe | Early four-date PnL share |
|---|---:|---:|---:|---:|
| LOWVOL_60 | 4.94% | 0.02% | 0.079 | 86.8% |
| LOWVOL_20 | 11.20% | 7.49% | 1.163 | 28.8% |

For LOWVOL_60, the four excluded dates from 2021-01-05 through 2021-01-08
compound to 4.75% and explain 86.8% of arithmetic validation PnL. This is the
main reason the final common-date report shows validation Sharpe near zero even
though the raw standalone table shows 1.008. Both values are correct, but they
answer different questions.

LOWVOL_20 is less dependent on those four dates. Its observed validation result
is stronger, which is useful robustness evidence and also a warning that the
low-volatility result is lookback-window sensitive.

### Independence And Economic Attribution

| Candidate | Mean score correlation with UBL | RankIC-series correlation | Return correlation | Long holding overlap | Short holding overlap | Annualized residual alpha | HAC t-stat |
|---|---:|---:|---:|---:|---:|---:|---:|
| LOWVOL_60 | -0.045 | -0.531 | -0.315 | 12.3% | 18.0% | 8.73% | 0.37 |
| LOWVOL_20 | 0.104 | -0.387 | -0.210 | 16.3% | 25.5% | 22.38% | 0.91 |

Both sleeves are distinct from UBL in scores, holdings, and common-policy
returns. However, neither LOWVOL-on-UBL residual alpha has a persuasive HAC
t-statistic in validation. Independence supports diversification, but does not
by itself prove a separate idiosyncratic alpha.

The raw LOWVOL_60 validation result is materially exposed to familiar defensive
characteristics. Its standardized long-minus-short beta and liquidity spreads
are -1.41 and -2.30. A single industry-and-size-neutral sensitivity reduces
validation RankIC from 0.072 to 0.040 and net Sharpe from 1.008 to 0.084.
Accordingly, LOWVOL_60 is better interpreted as a broad defensive or risk-premium
sleeve than as a clean stock-specific alpha.

### Contribution To The Selected UBL Portfolio

The selected portfolio comparison combines security-level weights using training-only
volatility scales and fixed 80% UBL / 20% LOWVOL_60 risk budgets. Turnover and
costs are calculated after aggregate trade netting.

| Sample | UBL net Sharpe | Blend net Sharpe | UBL max DD | Blend max DD | UBL full turnover | Blend full turnover |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 1.537 | 1.692 | 2.66% | 2.43% | 0.563 | 0.496 |
| Observed holdout | 0.597 | 1.358 | 4.82% | 4.05% | 0.532 | 0.462 |
| Full common sample | 1.143 | 1.644 | 5.47% | 4.30% | 0.552 | 0.482 |

On the viewed 133-observation holdout, net return rises from 2.10% to 4.87% and
break-even cost rises from 13.12 to 17.93 bps. Across four paired block
bootstrap schemes, the blend has higher Sharpe than UBL in 95.2% of resamples
from the observed holdout.

The portfolio evidence still has clear boundaries:

- paired walk-forward Sharpe remains -0.068 with only 2/4 positive folds;
- one additional execution day reduces full-common-sample Sharpe to 0.457;
- net Sharpe is 0.706 at 15 bps and turns negative at 20 bps;
- top-five-day PnL concentration improves from 60.9% to 43.9%, but remains
  material.

The fixed LOWVOL_20 robustness blend records net Sharpe of 1.807 in validation,
1.508 on the viewed holdout, and 1.655 on the full common sample. It also has
3/4 positive paired walk-forward folds. These observations support the broader
low-volatility diversification hypothesis, but promoting LOWVOL_20 after seeing
those results would convert a robustness check into post-result model
selection.

Detailed aggregate evidence is available in the
[UBL plus LOWVOL case study](case_studies/ubl_lowvol_portfolio.md) and the
[aggregate result bundle](../examples/sample_outputs/ubl_lowvol_study/README.md).

### LOWVOL Interpretation

`LOWVOL_60` remains the selected provisional research candidate because the
slower window and primary role were pre-specified before evaluation, and the 80/20
blend improves several documented UBL weaknesses after aggregate costs.
It is not classified as production-ready or as a stable standalone alpha.

`LOWVOL_20` remains an active robustness candidate with genuinely useful
results. It is not rejected, deleted, or relabeled as the selected sleeve. Its
stronger observed performance is evidence to carry into an unchanged-rule
replication rather than a reason to replace LOWVOL_60 inside the viewed sample.

Evidence needed before treating this result as more than provisional includes:

- verified adjusted prices and pre-2020 warm-up history;
- unchanged-rule evaluation on genuinely new data;
- broader positive walk-forward performance;
- explicit borrow, financing, market-impact, and execution evidence.

## Medium-Term Momentum

Two positive-direction momentum definitions were evaluated:

```text
MOM_60_5   = medium-term continuation excluding the latest 5 days
MOM_120_20 = longer continuation excluding the latest 20 days
```

The pre-specified positive direction was retained throughout evaluation.

| Candidate | Validation RankIC | Gross return | Net return | Net Sharpe | Positive offsets |
|---|---:|---:|---:|---:|---:|
| MOM_60_5 | -0.0720 | -15.23% | -16.98% | -1.66 | 0 / 10 |
| MOM_120_20 | -0.0315 | -3.20% | -4.36% | -0.44 | 1 / 20 |

Both factors had negative returns before the base 10 bps cost model. Their lower
correlation with UBL did not offset the negative standalone expected returns.

The fixed 80/20 UBL-plus-momentum comparison produced:

| Portfolio | Validation net Sharpe |
|---|---:|
| UBL baseline | 1.54 |
| UBL + MOM_60_5 | 0.90 |
| UBL + MOM_120_20 | 1.39 |

Neither blend exceeded the UBL baseline validation Sharpe. The current sample
does not support adding either momentum sleeve. A future test would require new
data or a distinct economic hypothesis; sign reversal or neighboring-window
searches after observing these results would be post hoc.

## Timing-Diagnostic Revision

Early UBL IC and group-return plots used factor and return files whose date
labels did not represent an executable same-period trade. Those plots remain in
the local methodology archive and are not included in the published results.

The corrected timing convention requires complete factor inputs before entry and
entry before exit. Historical extreme group NAV and unlagged IC values are
excluded from the README and portfolio case study.

## Interpretation Summary

- `LOWVOL_60`: provisional defensive candidate in the pre-specified 80/20
  research portfolio; confirmation requires new adjustment-verified data.
- `LOWVOL_20`: retained robustness candidate with strong observed evidence; not
  promoted after result inspection.
- `MOM_60_5`: not selected under the pre-specified positive direction.
- `MOM_120_20`: not selected under the pre-specified positive direction.
- Early unlagged UBL diagnostics: superseded by the point-in-time timing
  convention.
- No candidate sign was revised after evaluation.
- Low correlation alone was never treated as sufficient for inclusion.
