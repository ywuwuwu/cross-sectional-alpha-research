# Local Data Reproduction Policy

## Two Modes

### Mode 1: Exact Reproduction

Use only if the original report's assumptions are available locally:

- universe
- sample period
- data frequency
- field definitions
- adjusted/unadjusted price convention
- return definition
- status filters
- listing-age filters
- neutralization fields
- benchmark/excess return rules
- transaction costs
- group/portfolio construction
- rebalance timing

If any of these are missing or uncertain, do not claim exact reproduction.

### Mode 2: Local-Data Reproduction

Default mode. Reproduce the formula and research logic, then validate it with local data.

Suggested status note:

> When the original report dataset is unavailable, the objective is not exact return replication; the objective is transparent factor-logic implementation and local-data validation.

## Data Inspection

Do:

- inspect code first
- list folders/files
- read small CSV samples with `nrows`
- use an existing loader or a bounded sample reader where possible
- report detected date ranges and columns

Use caution with:

- fully loading large folders
- unpacking `.zip` files unless necessary
- loading full `.pkl` files except lightweight calendar inspection
- assuming field meanings without checking source code and samples

## Required Data Artifacts

Before implementation/backtest create:

- `reports/<factor_name>/data_availability_report.md`
- `reports/<factor_name>/data_mapping.csv`

`data_availability_report.md` must include:

- available folders
- detected file types
- detected date range
- detected universe/ticker format if available
- detected frequency
- detected price fields
- detected volume/turnover fields
- return fields
- status/filter fields
- neutralization fields
- missing report-required fields
- exact-vs-local reproduction mode decision

`data_mapping.csv` must include:

- report requirement
- local source
- local field
- transformation
- availability status
- assumption/risk

## Result Labels

Use cautious labels:

- "formula-level reproduction"
- "local-data validation"
- "conceptual reproduction"
- "strict local reproduction"
- "not comparable due to data mismatch"

Do not say "matches the paper" unless exact data and setup have been verified.
