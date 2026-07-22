# UBL Family Research Track

## Purpose

UBL is treated as a family of short-horizon candle-rejection signals rather
than one formula and one backtest. The research objective is to determine
whether related UBL definitions contain stable cross-sectional information that
can be converted into a cost-aware portfolio.

Exact private formulas and security-level factor values are not published. The
public record focuses on timing, direction, candidate selection, portfolio
construction, and economic validation.

## Research Sequence

1. Reconstruct a paper-style UBL reference.
2. Define one oriented `alpha_score` convention.
3. Correct IC and group diagnostics to use next-period returns.
4. Sweep a small preregistered set of horizons and rebalance offsets.
5. Decompose long and short legs.
6. Prune redundant family members using score, IC, return, holding, and drawdown
   correlations.
7. Test incremental alpha relative to PaperUBL.
8. Combine selected security weights before costs.
9. Diagnose turnover and freeze one no-trade policy.
10. Add only a preregistered diversifier that improves portfolio economics.

## Direction And Timing

All active UBL variants emit:

```text
raw_factor_value
alpha_score
```

Higher `alpha_score` always means higher expected return. Portfolio code never
inverts a signal. For the selected family, lower raw UBL pressure is oriented
to a higher alpha score.

Complete date-`t` OHLCV inputs are observed after the close. The resulting
portfolio is entered at the next tradable VWAP and evaluated against a later
exit benchmark. The old same-file daily IC/group diagnostics were withdrawn and
are not part of the public evidence.

## Selected Family

The frozen top-level UBL sleeve contains:

| Component | Role | Internal risk budget |
|---|---|---:|
| PaperUBL 3D | Lead implementation | 60% |
| UBL_M20 3D | Slower challenger | 20% |
| UBL_M5 5D | Specialist | 20% |

Related M10 and other windows remain in the private evidence library as
redundant, diagnostic, or watchlist candidates. They were not deleted.

## Family-Level Rationale

Closely related horizons can share information while differing in implementation
noise and turnover. The family process asks two separate questions:

- Does a candidate rank returns on its own?
- Does it retain incremental residual information after the lead candidate?

Candidates with very high score and return correlation are not automatically
mixed. Redundant candidates are retained for audit but removed from active
complexity.

## Portfolio Implementation

The selected family:

- combines security-level sleeve weights;
- scales sleeves with training-only volatility;
- normalizes to long +1 and short -1;
- applies a frozen 7.5 bps security-weight-change band;
- calculates transaction costs after aggregate trade netting.

This implementation replaced top-N long-only return as the primary evidence.
Dollar-neutral long/short results, cost tolerance, and timing robustness are the
main tests.

## Portfolio Role

UBL remains the principal signal sleeve. The public analysis emphasizes timing,
candidate selection, and implementation rather than a standalone Sharpe target.
The selected multi-factor result is documented in
[the combined-portfolio case study](ubl_lowvol_portfolio.md).
