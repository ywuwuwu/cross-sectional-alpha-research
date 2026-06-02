# Reproduction Summary: <Factor Name>

## 1. Reproduction Status

- Status:
- Source idea:
- Implementation file:
- Output directory:
- Exact reproduction / local-data reproduction / partial reproduction / implementation-only reproduction:

## 2. Research Report Thesis

Briefly summarize the report's factor intuition and why the factor may predict returns.

## 3. Mathematical Logic from the Report

### 3.1 Core Formula

Write the report's main formula in readable Markdown / LaTeX-style notation.

If the exact formula is unavailable, label the formula as inferred or locally approximated.

### 3.2 Notation

| Symbol / Variable | Meaning | Data Requirement | Local Proxy |
|---|---|---|---|

### 3.3 Formula Steps

| Step | Mathematical Operation | Financial Meaning | Implementation Mapping |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |

## 4. Financial Meaning of the Math

Explain what each mathematical component is trying to capture financially.

Examples:
- return reversal
- price-volume interaction
- turnover stability
- intraday information flow
- volume-corrected momentum
- liquidity effect
- crowding / trading pressure
- information diffusion
- risk adjustment

## 5. Math-to-Code Mapping

| Mathematical Component | Report Logic | Local Implementation | Code Location | Notes |
|---|---|---|---|---|
| Factor raw input |  |  | `factor_mining/...` |  |
| Rolling window |  |  | `factor_mining/...` |  |
| Standardization |  |  | `factor_mining/...` |  |
| Signal ranking |  |  | `factor_mining/...` |  |
| Portfolio construction |  |  | `factor_mining/...` |  |
| Performance evaluation |  |  | `factor_mining/...` |  |

Use file paths, class names, and function/method names. Include line numbers only if they are stable and easy to verify.

## 6. Local Data Substitution

Explain how the mathematical formula is adapted to local data.

| Report Requirement | Local Data / Proxy | Match Quality | Expected Impact |
|---|---|---|---|

## 7. Implementation Pseudocode

Provide concise pseudocode showing how the formula becomes a signal.

```python
# pseudocode only
```

## 8. Validation Checks

List the checks used to verify that the mathematical implementation behaves correctly.

Examples:

- factor coverage
- missing-value ratio
- cross-sectional dispersion
- correlation with baseline factor
- IC / RankIC
- group return monotonicity
- long-short return
- turnover
- drawdown

## 9. Key Limitations

Explain which parts of the math are exact, approximated, inferred, or missing.

## 10. Bottom Line

One short paragraph explaining what was successfully reproduced and what should be manually reviewed.
