# PaperUBL Reconstruction

## Role

PaperUBL is the lead paper-style member of the UBL family. It preserves the
economic idea of a candle-rejection signal as a common reference implementation.
Source reports, report-derived factor implementations, licensed data, and
security-level values are not redistributed.

This is a local-data reconstruction, not an exact replication of an external
paper's reported performance.

## Portfolio Role

PaperUBL remained the family lead because it was more distinct than several
standard-window UBL variants and served as the reference implementation during
family selection. The selected UBL sleeve assigns it a 60% internal risk budget.

Its role is defined within the family portfolio; standalone production use was
not evaluated.

## Methodology Corrections

An early historical sample mixed correctly lagged top-N portfolio accounting
with invalid pre-fix IC and daily group diagnostics. Those diagnostic plots were
withdrawn from the public release.

The corrected timing requires:

```text
complete factor inputs at t
    -> oriented alpha_score at t
    -> entry at next tradable VWAP
    -> return measured after entry
```

PaperUBL is evaluated with the same sign, timing, turnover, and cost definitions
as every other family member.

## Interpretation

This study is a local-data reconstruction. It does not establish:

- exact paper replication;
- access to the source report's original universe;
- identical corporate-action adjustments;
- live short availability;
- audited production performance.

Within the selected family, PaperUBL provides the reference signal for
redundancy and incremental-alpha tests and contributes to the selected UBL sleeve
used in the
[UBL plus LOWVOL case study](ubl_lowvol_portfolio.md).
