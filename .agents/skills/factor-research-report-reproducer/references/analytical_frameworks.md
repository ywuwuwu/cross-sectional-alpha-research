# Analytical Frameworks

## Five Reproduction Layers

1. Formula-level reproduction
   - Extract exact mathematical definition.
   - Check windows, normalization, clipping, z-score, neutralization, direction.

2. Signal-level reproduction
   - Convert factor values into rankings/selections correctly.
   - Verify ascending vs descending.
   - Confirm filters and missing-value handling.

3. Portfolio-construction reproduction
   - Match groups, top-N, long-short, equal/value weight, rebalance timing, costs.

4. Performance-level reproduction
   - Compare IC/RankIC, ICIR/IR, group layering, long-short, drawdown, turnover.

5. Local-data validation
   - Explain data limitations and why local results may differ.

## Group Return Diagnostics

Interpretation: sort stocks by factor value, split into groups, and show stable separation in future returns.

Review:

- group cumulative return curves separate
- group mean returns are monotonic or directionally ordered
- long-short group curve is stable
- IC sign agrees with the group direction
- result is robust over a sufficiently long period

Use `n_groups=10` when matching papers that show 10 groups. Use 5 groups only for quick tests or when the paper uses 5 groups.

## Direction Checks

For every factor, record:

- Does the report sort low-to-high or high-to-low?
- Which group is expected to outperform?
- Does local IC sign match that direction?
- Does the oriented `alpha_score` match the predefined direction?
- Is long-short defined high-minus-low or low-minus-high?

## Common Factor Operations

- winsorization / outlier clipping
- cross-sectional z-score
- rolling mean/std
- size neutralization (`desize`)
- industry neutralization
- Barra style neutralization
- rank transformation
- quantile grouping
- monthly rebalance

## Report-to-Code Checklist

For each formula component:

- write report formula verbatim
- write local implementation formula
- list required fields
- list local fields used
- list transformation differences
- write a small manual validation plan for one date and a few tickers
