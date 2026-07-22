# Portfolio Data Dictionary

These files contain aggregate portfolio results for the predefined UBL and
LOWVOL comparison.

- `date` is the common portfolio return date.
- `split` is `train`, `validation`, or `research_holdout`.
- Return fields are decimal daily returns.
- Turnover uses the full-turnover convention on a gross-2 book.
- Costs are decimal return deductions.
- Sharpe fields are annualized with a zero hurdle.
- Max drawdown fields are positive decimal losses.

The files omit stock identifiers, holdings, factor values, raw market data, and
private strategy code.
