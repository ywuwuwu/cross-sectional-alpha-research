# Repository Map

This repository is a quant factor research reproduction workspace rooted at:

`/home/yashuo/rc/quant-materials/11.量化研报精读与因子复现`

## Local Data

Observed data folders:

- `data/data_daily/`: daily OHLCV-style CSV files.
  - observed columns: `date`, `code`, `open`, `close`, `low`, `high`, `volume`, `money`, `turnover_ratio`
  - observed ticker format: `000001.XSHE`, `600000.XSHG`
- `data/data_ret/`: forward return CSV files.
  - observed columns: `code`, `date`, `1vwap_pct`, `5vwap_pct`, `10vwap_pct`, `15vwap_pct`
  - backtest engine uses `1vwap_pct` for daily portfolio return and IC.
- `data/data_ud_new/`: trading status/limit CSV files.
  - observed columns: `date`, `code`, `open`, `pre_close`, `high_limit`, `low_limit`, `paused`, `zt`, `dt`
- `data/data_barra/`: Barra exposure CSV files.
  - observed columns: `code`, `size`, `beta`, `momentum`, `residual_volatility`, `non_linear_size`, `book_to_price_ratio`, `liquidity`, `earnings_yield`, `growth`, `leverage`
- `data/data_industry/`: industry classification CSV files.
  - observed columns: `code`, `industry`
- `data/date.pkl`: trading calendar. Observed full pickle range includes 2014-01-02 to 2024-12-20, but `DataLoader` filters to dates with `data_daily` files.
- `data_5m/`: 5-minute bar CSV files.
  - observed columns: `code`, `datetime`, `open`, `close`, `high`, `low`, `volume`, `money`, `date`

Always inspect current files before assuming columns or coverage.

## Core Framework

`factor_mining/data_loader.py`

- `DataLoader(data_dir='./data')`
- loads `date.pkl`, filters dates where `data_daily/<date>.csv` exists
- `get_all_dates()`
- `get_daily_data(date)`
- `get_daily_returns(date)`
- `get_daily_status(date)`

`factor_mining/strategy_base.py`

- Abstract `Strategy` requires:
  - `calculate_factor(date, data_loader, **kwargs) -> DataFrame`
  - `generate_signal(factor_df, top_n=10) -> list`
- Factor DataFrame must contain `code`, `date`, `factor_value`.
- Includes example `MomentumStrategy` and `ReversalStrategy`.

`factor_mining/backtest_engine_strategy.py`

- Main engine: `BacktestEngine`
- Runs date loop, computes factors, IC, group returns, portfolio returns.
- Uses pending signal execution to avoid same-day lookahead.
- Supports `rebalance_freq`: integer, `month_start`/`m`, `month_end`/`month_last`.
- `n_groups > 1` computes grouped factor returns and long-short group returns.

`factor_mining/portfolio_manager.py`

- Equal-weight long-only portfolio manager.
- Tracks current holdings, weight drift, turnover, commission, slippage, stamp duty.

`factor_mining/performance_evaluator.py`

- Computes total return, annual return, annual volatility, Sharpe, Calmar, max drawdown, win rate.
- `calculate_ic` defaults to Spearman rank IC.
- `calculate_ic_ir` returns `ic_mean`, `ic_std`, `ir`, `ic_win_rate`.

`run_research_backtest.py`

- Canonical CLI runner.
- Strategy registry includes: `ubl`, `paper_ubl`, `PaperUBL_Strategy`, `utr`, `ideal_reversal`, `ideal`, `cpv`, `momentum`, `reversal`.
- Supports `--strategy-param KEY=VALUE` and `--grid-param KEY=V1,V2`.
- Outputs to `reports/<strategy>_<timestamp>/`.

`visualizer.py`

- Canonical plotting/report helper.
- Saves key metrics, drawdown, rolling metrics, group pivot, group cumulative returns, group means.
- Plots performance overview, rolling metrics, group cumulative returns, group mean returns, group long-short returns, IC series, IC distribution.

## Existing Strategies and Report Mapping

- `PaperUBL_Strategy.py` / `PaperUBLStrategy`: strict UBL formula from `模块1：威廉指标.pdf`.
- `ubl_strategy.py` / `UBLStrategy`: expanded conceptual UBL using U/B/L/WR/TREND.
- `utr_strategy.py` / `UTRStrategy`: turnover stability/rank strategy related to `模块2：量稳换手率.pdf`.
- `cpv_strategy.py` / `CPVStrategy`: 5-minute close-volume correlation strategy related to `模块3：CPV价量自相关性.pdf`.
- `ideal_reversal_strategy.py` / `IdealReversalStrategy`: factor-cutting ideal reversal strategy related to `模块4：因子切割论.pdf`.

Unimplemented PDFs observed:

- `模块4：成交量对动量因子的修正.pdf`
- `模块4：换手率切割刀 CTR 因子.pdf`

## Recommended Commands

Run a strategy:

```bash
python -B run_research_backtest.py --strategy paper_ubl --n-groups 10 --top-n 50 --rebalance-freq month_start
```

Run a parameter grid:

```bash
python -B run_research_backtest.py --strategy utr \
  --grid-param turnover_window=10,20,40 \
  --grid-param top_n=30,50,100
```
