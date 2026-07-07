# Strategy Comparison

This page summarizes which strategy results are ready to publish publicly and which should remain experimental until they are improved.

The comparison is based on local-data diagnostics from the repository's backtest and report pipeline. It is not investment advice and is not an exact replication of any external report.

## Public Publishing Decision

| Strategy | Public status | Current interpretation |
|---|---|---|
| PaperUBL | Publish now | Positive Sharpe and positive IC; best current public sample because portfolio return, IC, and group behavior point in the same direction. |
| UBL | Work in progress | Strongest raw signal diagnostics, but implementation and portfolio conversion need improvement before publishing a flagship result. |
| Reversal | Experimental | Strong group long-short behavior, but weak top-N portfolio behavior; useful as a research candidate, not yet a public flagship. |
| CTR | Experimental / diagnostic | Good PnL in the local run, but alpha evidence is questionable because IC and long-short diagnostics do not fully support the portfolio result. |

## Why PaperUBL Is the First Public Sample

`PaperUBL` is the cleanest first public example because it shows a coherent factor-research workflow:

- factor implementation
- local-data backtest
- transaction-cost-aware portfolio evaluation
- IC analysis
- group return analysis
- saved figures
- generated report

The public sample is intentionally placed under:

```text
examples/sample_outputs/paper_ubl/
```

instead of publishing the full raw `reports/` directory.

## Why Raw Reports Are Not Published Yet

The full local `reports/` directory can contain:

- smoke tests
- failed or partial experiments
- debug runs
- private local paths
- private data-derived artifacts
- experimental strategies that need clearer labeling

Those outputs should remain local until each report is cleaned, labeled, and reviewed for public safety.

## Recommended Next Flagship Track

The most promising future flagship is a stronger modified UBL strategy, but only after it improves the link between signal quality and tradable portfolio quality.

The target standard for the next public UBL report should be:

- stronger Sharpe than the current PaperUBL sample
- lower drawdown
- positive IC and RankIC
- positive net long-short return after cost
- lower turnover or clear turnover justification
- walk-forward validation
- transaction-cost sweep
- correlation check against existing alpha families

## How To Read Negative Or Mixed Results

Mixed results are useful if they are clearly labeled. For example:

- A strategy with good PnL but weak IC may be exposed to unintended risk rather than true alpha.
- A strategy with strong IC but weak portfolio return may need better direction, neutralization, sizing, or trading rules.
- A strategy with strong group long-short but weak top-N performance may need broader portfolio construction or lower concentration.

The public repository should show that the research process can reject, diagnose, and improve factors, not only display positive results.
