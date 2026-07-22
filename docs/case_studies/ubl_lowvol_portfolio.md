# Case Study: Frozen UBL Plus LOWVOL_60

## Portfolio Selection Status

The frozen 80% UBL / 20% LOWVOL_60 portfolio met 8 of 10 preregistered inclusion
checks, including every mandatory check, and was retained as the combined
research portfolio.

The portfolio remains a research specification. The sample is short, the
holdout has been viewed, paired walk-forward performance remains negative, and
borrow, impact, adjusted prices, and genuinely new data are unresolved.

## Research Question

Earlier UBL analysis identified a short-horizon cross-sectional signal with the
following implementation concerns:

- high transaction-cost sensitivity;
- time instability;
- concentration in a small number of profitable days;
- sensitivity to one additional day of execution delay;
- meaningful beta and liquidity exposure.

The combination test addressed one question:

> Does a frozen 20% risk allocation to a slower LOWVOL_60 sleeve improve several
> UBL weaknesses after security weights are combined and aggregate costs are
> charged?

Family budgets were held fixed throughout the comparison.

## Frozen Specification

| Layer | Rule |
|---|---|
| UBL internal family | PaperUBL 3D 60%, UBL_M20 3D 20%, UBL_M5 5D 20% |
| UBL internal control | 7.5 bps security-weight-change band |
| Defensive sleeve | LOWVOL_60, positive low-volatility direction |
| Top-level risk budget | UBL 80%, LOWVOL_60 20% |
| Scaling | Training-only sleeve volatility |
| Final book | Long +1, short -1, net 0, gross 2 |
| Final no-trade rule | Common 7.5 bps security-weight-change band |
| Base transaction cost | 10 bps per dollar traded on full turnover |
| Execution | Next-tradable VWAP |
| Selection | Fixed before combined-portfolio results |

Security weights are combined before turnover and costs. This captures trade
netting. Averaging standalone net-return series would not account for this.

## Research-Holdout Comparison

| Metric | UBL only | Selected blend | Change |
|---|---:|---:|---:|
| Observations | 133 | 133 | 0 |
| Net total return | 2.10% | 4.87% | +2.77 pp |
| Net Sharpe 0rf | 0.60 | 1.36 | +0.76 |
| Net max drawdown | 4.82% | 4.05% | -0.77 pp |
| Average full turnover | 0.532 | 0.462 | -0.070 |
| Average one-way turnover | 0.266 | 0.231 | -0.035 |
| Break-even cost | 13.12 bps | 17.93 bps | +4.82 bps |

![Net NAV](../../examples/sample_outputs/ubl_lowvol_study/plots/01_net_nav_comparison.png)

On the holdout, the blend has higher return and Sharpe and lower drawdown and
turnover. The 133 observations limit the precision and generality of the
comparison.

## Cost Frontier

| Cost | UBL net Sharpe | Blend net Sharpe |
|---:|---:|---:|
| 5 bps | 2.16 | 2.58 |
| 10 bps | 1.14 | 1.64 |
| 15 bps | 0.12 | 0.71 |
| 20 bps | -0.89 | -0.23 |

These are full-common-sample values, not holdout-only values.

![Cost frontier](../../examples/sample_outputs/ubl_lowvol_study/plots/03_transaction_cost_frontier.png)

The blend remains positive at 15 bps and turns negative at 20 bps. This places
the observed break-even cost between those two sensitivity points.

## Paired Bootstrap

Across the four frozen holdout schemes:

| Paired question | Mean observed frequency |
|---|---:|
| Combined Sharpe > UBL Sharpe | 95.2% |
| Combined max DD < UBL max DD | 86.2% |
| Combined turnover < UBL turnover | 100.0% |
| Combined net return > UBL net return | 95.0% |
| Combined Sharpe > 0 | 77.8% |
| UBL Sharpe > 0 | 62.1% |

![Paired bootstrap](../../examples/sample_outputs/ubl_lowvol_study/plots/04_paired_bootstrap_sharpe_difference.png)

The histogram displays the 5-day moving-block method. The four-method average
favors the blend within the observed sample; it does not estimate future
profitability.

## Walk-Forward Results

| Portfolio | Aggregate net return | Net Sharpe | Max DD | Positive folds |
|---|---:|---:|---:|---:|
| UBL only | -2.69% | -0.39 | 5.36% | 2 / 4 |
| Selected blend | -0.60% | -0.07 | 4.30% | 2 / 4 |

![Walk-forward folds](../../examples/sample_outputs/ubl_lowvol_study/plots/05_walk_forward_fold_returns.png)

The blend has a less negative aggregate return and smaller drawdown, but the
aggregate remains negative and only two folds are positive. Time stability is
unresolved.

## Drawdown And Concentration

Full-common-sample net max drawdown declines from 5.47% to 4.30%. Top-five-day
arithmetic PnL concentration declines from 60.9% to 43.9%.

![Drawdown](../../examples/sample_outputs/ubl_lowvol_study/plots/02_drawdown_comparison.png)

![PnL concentration](../../examples/sample_outputs/ubl_lowvol_study/plots/06_pnl_concentration.png)

The top-five-day share is lower for the blend, although 43.9% remains a material
concentration.

## Delay And Exposure Tests

On 421 matched full-sample dates:

| Portfolio | Base Sharpe | One-additional-day-delay Sharpe |
|---|---:|---:|
| UBL only | 1.15 | -0.07 |
| Selected blend | 1.65 | 0.46 |

The defensive sleeve reduces, but does not remove, timing sensitivity.

Average standardized exposures changed as follows:

| Exposure | UBL only | Selected blend |
|---|---:|---:|
| Beta | 0.281 | 0.160 |
| Liquidity | 0.215 | 0.028 |
| Size | -0.008 | -0.001 |
| Maximum absolute industry net weight | 0.044 | 0.042 |

The exposure changes are consistent with the intended defensive role of the
LOWVOL sleeve.

## Role Of LOWVOL_60

Standalone LOWVOL_60 had validation net Sharpe 0.08 and holdout net Sharpe 2.22.
The difference between periods is too large to treat LOWVOL_60 as a stable
standalone result. It is evaluated here as a fixed defensive sleeve relative to
UBL on the same dates.

LOWVOL_20 produced higher observed values in some tests but was
preregistered as robustness-only and remained in that role after evaluation.

## Interpretation

Within the observed sample, adding the frozen 20% LOWVOL_60 risk sleeve was
associated with higher holdout Sharpe, lower drawdown and turnover, greater
break-even cost, and lower PnL concentration relative to UBL alone.

The analysis does not establish:

- production readiness;
- a stable Sharpe above 1 across time;
- exact reproduction of an external paper;
- live tradability in A-shares;
- resilience to realistic borrow and impact costs;
- future performance probability of 95.2%.

The next planned evaluation is unchanged-rule replication on new,
adjustment-verified data with explicit borrow and execution modeling.

## Public Evidence

Every number above is available in
[the aggregate evidence bundle](../../examples/sample_outputs/ubl_lowvol_study/README.md).
No security identifiers or private factor values are required to regenerate the
plots.
