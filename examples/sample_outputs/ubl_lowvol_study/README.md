# UBL Plus LOWVOL Portfolio Output

This folder contains portfolio-level evidence for the frozen UBL plus LOWVOL
comparison. It contains no stock identifiers, holdings, raw prices, factor
values, local paths, exact private UBL formulas, or private strategy code.

## Research-Holdout Comparison

| Metric | UBL only | 80% UBL / 20% LOWVOL |
|---|---:|---:|
| Observations | 133 | 133 |
| Net return | 2.10% | 4.87% |
| Net Sharpe 0rf | 0.60 | 1.36 |
| Net max drawdown | 4.82% | 4.05% |
| Average full turnover | 0.532 | 0.462 |
| Break-even cost | 13.12 bps | 17.93 bps |

The comparison uses a 10 bps per dollar traded cost model on full turnover and
a gross-2 dollar-neutral book.

## Figure Set

### Net NAV With Chronological Splits

![Net NAV](plots/01_net_nav_comparison.png)

### Drawdown

![Drawdown](plots/02_drawdown_comparison.png)

### Transaction-Cost Frontier

![Cost frontier](plots/03_transaction_cost_frontier.png)

### Paired Holdout Bootstrap

![Bootstrap](plots/04_paired_bootstrap_sharpe_difference.png)

### Fixed-Rule Walk-Forward Folds

![Walk-forward](plots/05_walk_forward_fold_returns.png)

### PnL Concentration

![Concentration](plots/06_pnl_concentration.png)

## Data Dictionary

| File | Content |
|---|---|
| `headline_metrics.csv` | Train, validation, holdout, and all-sample standardized metrics |
| `portfolio_returns.csv` | Same-date aggregate returns, turnover, and cost for UBL and the blend |
| `cost_sensitivity.csv` | Full-common-sample 5/10/15/20 bps results |
| `walk_forward_folds.csv` | Four paired fixed-rule fold outcomes |
| `bootstrap_method_summary.csv` | Frozen holdout frequencies for four block schemes |
| `bootstrap_sharpe_differences.csv` | 5,000 paired 5-day moving-block Sharpe differences |
| `pnl_concentration.csv` | Full-common top-five-day PnL concentration |
| `robustness_summary.csv` | Compact robustness values used in the project README |
| `evidence_manifest.json` | Source snapshot ID, exclusions, and SHA-256 checksums |

## Regenerate Figures

From the repository root:

```bash
pip install -e ".[plots]"
python examples/render_public_results.py
```

## Evidence Review

The CSV files are the aggregate inputs for the committed figures.
`data/evidence_manifest.json` records hashes for every released table and
figure, the clean private source commit and tree, configuration and dependency
hashes, and the clean public curation commit.

The aggregate files do not make the private security-level strategy
independently reproducible. The holdout has been viewed, paired walk-forward
Sharpe is -0.07, only 2/4 folds are positive, and an additional execution day
reduces full-sample Sharpe to 0.46.

See the [combined-portfolio case study](../../../docs/case_studies/ubl_lowvol_portfolio.md).
