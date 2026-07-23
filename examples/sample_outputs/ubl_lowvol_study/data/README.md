# Published Portfolio Tables

These aggregate tables contain the numerical inputs used in the published UBL
and LOWVOL result figures.

- `date` is the common portfolio return date.
- `split` is `train`, `validation`, or `research_holdout`; the final label refers
  to the observed chronological holdout, which has now been viewed.
- Return fields are decimal daily returns.
- Turnover uses the full-turnover convention on a gross-2 book.
- Costs are decimal return deductions.
- Sharpe fields are annualized with a 0% cash hurdle.
- Max drawdown fields are positive decimal losses.

The tables do not include stock identifiers, holdings, factor values,
report-derived factor implementations, or licensed market data.
