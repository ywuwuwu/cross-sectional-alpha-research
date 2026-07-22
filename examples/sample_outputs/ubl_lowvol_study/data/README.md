# Portfolio-Level Evidence Schema

These files are portfolio-level derivatives of the frozen UBL plus LOWVOL
comparison.

- `date` is the common portfolio return date.
- `split` is `train`, `validation`, or `research_holdout`.
- Return fields are decimal daily returns.
- Turnover uses the full-turnover convention on a gross-2 book.
- Costs are decimal return deductions.
- Sharpe fields are annualized with a zero hurdle.
- Max drawdown fields are positive decimal losses.

The files omit stock identifiers, holdings, factor values, raw market data, and
private strategy code. `evidence_manifest.json` records SHA-256 hashes for
every released CSV and figure, plus the clean private source commit and tree,
configuration and dependency hashes, and clean public builder commit.
