"""
CTR strategy - Cutlets of Turnover Rate.

Partial local-data reproduction of 模块4：换手率切割刀 CTR 因子.pdf.

Report formula summary:
1. For each stock, look back 20 trading days.
2. Compute next-day overnight smart money:
       OvernightSmart_t = normalized(overnight_return_t) / overnight_turnover_t
3. Sort prior-day intraday turnover by next-day OvernightSmart from low to high.
4. Average the prior-day turnover of the four lowest OvernightSmart observations.
5. Desize the resulting factor.

Local-data limitation:
The report needs intraday turnover and overnight turnover. Local data has daily
turnover_ratio and 5-minute volume for 2021 only. This implementation uses
daily turnover_ratio as the intraday turnover proxy and estimates overnight
turnover from the first 5-minute bar when available; otherwise it falls back to
daily turnover_ratio. Therefore this is not exact performance replication.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from strategy_base import Strategy


class CTRStrategy(Strategy):
    def __init__(
        self,
        data_dir: str = './data',
        min5_dir: str = './data_5m',
        window: int = 20,
        cut_count: int = 4,
        min_avg_volume: float = 5e5,
        liquidity_window: int = 20,
        min_stock_count: int = 200,
        min_listed_days: int = 60,
        min_listed_coverage: float = 0.8,
        outlier_method: str = 'sigma',
        outlier_param: float = 3.0,
        neutralize_size: bool = True,
        neutralize_industry: bool = False,
        select_ascending: bool = True,
    ):
        super().__init__(name='CTR')
        self.data_dir = Path(data_dir)
        self.min5_dir = Path(min5_dir)
        self.window = window
        self.cut_count = cut_count
        self.min_avg_volume = min_avg_volume
        self.liquidity_window = liquidity_window
        self.min_stock_count = min_stock_count
        self.min_listed_days = min_listed_days
        self.min_listed_coverage = min_listed_coverage
        self.outlier_method = outlier_method
        self.outlier_param = outlier_param
        self.neutralize_size = neutralize_size
        self.neutralize_industry = neutralize_industry
        self.select_ascending = select_ascending

        self.trade_dates: Optional[List[str]] = None
        self.date_to_idx: Dict[str, int] = {}
        self.daily_cache: Dict[str, pd.DataFrame] = {}
        self.status_cache: Dict[str, pd.DataFrame] = {}
        self.barra_cache: Dict[str, pd.DataFrame] = {}
        self.industry_cache: Dict[str, pd.DataFrame] = {}
        self.min5_first_cache: Dict[str, pd.DataFrame] = {}
        self.stock_pool_cache: Dict[str, List[str]] = {}
        self.panel_cache: Dict[str, pd.DataFrame] = {}

    @staticmethod
    def _zscore(series: pd.Series) -> pd.Series:
        s = series.astype(float)
        std = s.std()
        if std == 0 or np.isnan(std):
            return s * 0.0
        return (s - s.mean()) / (std + 1e-8)

    def _clip_outliers(self, df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        if df.empty:
            return df
        method = (self.outlier_method or '').lower()
        for col in cols:
            if col not in df.columns:
                continue
            series = df[col].astype(float)
            if method == 'quantile':
                q = float(self.outlier_param)
                lower = series.quantile(q)
                upper = series.quantile(1 - q)
                df[col] = series.clip(lower=lower, upper=upper)
            else:
                n_sigma = float(self.outlier_param)
                mean = series.mean()
                std = series.std()
                if std == 0 or np.isnan(std):
                    continue
                df[col] = series.clip(lower=mean - n_sigma * std, upper=mean + n_sigma * std)
        return df

    def _ensure_trade_dates(self, data_loader) -> None:
        if self.trade_dates is None:
            self.trade_dates = data_loader.get_all_dates()
            self.date_to_idx = {d: i for i, d in enumerate(self.trade_dates)}

    def _get_daily(self, data_loader, date: str) -> pd.DataFrame:
        if date not in self.daily_cache:
            df = data_loader.get_daily_data(date)
            if not df.empty:
                cols = ['code', 'date', 'open', 'close', 'volume', 'turnover_ratio', 'money']
                extra_cols = ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']
                cols += [c for c in extra_cols if c in df.columns]
                self.daily_cache[date] = df[[c for c in cols if c in df.columns]].copy()
            else:
                self.daily_cache[date] = pd.DataFrame()
        return self.daily_cache[date]

    def _get_status(self, data_loader, date: str) -> pd.DataFrame:
        if date not in self.status_cache:
            self.status_cache[date] = data_loader.get_daily_status(date)
        return self.status_cache[date]

    def _get_barra(self, date: str) -> pd.DataFrame:
        if date not in self.barra_cache:
            path = self.data_dir / 'data_barra' / f'{date}.csv'
            self.barra_cache[date] = pd.read_csv(path) if path.exists() else pd.DataFrame()
        return self.barra_cache[date]

    def _get_industry(self, date: str) -> pd.DataFrame:
        if date not in self.industry_cache:
            path = self.data_dir / 'data_industry' / f'{date}.csv'
            self.industry_cache[date] = pd.read_csv(path) if path.exists() else pd.DataFrame()
        return self.industry_cache[date]

    def _get_first_5m(self, date: str) -> pd.DataFrame:
        if date not in self.min5_first_cache:
            path = self.min5_dir / f'{date}.csv'
            if not path.exists():
                self.min5_first_cache[date] = pd.DataFrame()
                return self.min5_first_cache[date]
            df = pd.read_csv(path, usecols=['code', 'datetime', 'volume'])
            if df.empty:
                self.min5_first_cache[date] = pd.DataFrame()
            else:
                first = df.sort_values(['code', 'datetime']).groupby('code').head(1)
                self.min5_first_cache[date] = first.set_index('code')[['volume']]
        return self.min5_first_cache[date]

    def _get_stock_pool(self, date: str, data_loader) -> List[str]:
        if date in self.stock_pool_cache:
            return self.stock_pool_cache[date]

        daily = self._get_daily(data_loader, date)
        if daily.empty:
            self.stock_pool_cache[date] = []
            return []
        stocks = daily['code'].tolist()

        status = self._get_status(data_loader, date)
        if not status.empty:
            status = status.copy()
            if 'st' in status.columns:
                status = status[status['st'] == 0]
            tradable = status[(status['paused'] == 0) & (status['zt'] == 0) & (status['dt'] == 0)]
            tradable_set = set(tradable['code'])
            stocks = [s for s in stocks if s in tradable_set]

        idx = self.date_to_idx.get(date)
        if idx is None:
            self.stock_pool_cache[date] = []
            return []

        min_days = max(self.window + 1, self.min_listed_days)
        if idx >= min_days:
            eligible_dates = self.trade_dates[idx - min_days: idx]
            frames = []
            for d in eligible_dates:
                df = self._get_daily(data_loader, d)
                if not df.empty:
                    frames.append(df[['code']])
            if frames:
                counts = pd.concat(frames)['code'].value_counts()
                min_required = int(min_days * self.min_listed_coverage)
                eligible = set(counts[counts >= min_required].index)
                stocks = [s for s in stocks if s in eligible]

        if idx > self.liquidity_window:
            hist_dates = self.trade_dates[idx - self.liquidity_window: idx]
            vol_frames = []
            stock_set = set(stocks)
            for d in hist_dates:
                df = self._get_daily(data_loader, d)
                if df.empty:
                    continue
                sub = df[df['code'].isin(stock_set)][['code', 'volume']]
                if not sub.empty:
                    vol_frames.append(sub)
            if vol_frames:
                vol_df = pd.concat(vol_frames)
                avg_vol = vol_df.groupby('code')['volume'].mean()
                stocks = avg_vol[avg_vol >= self.min_avg_volume].index.tolist()

        self.stock_pool_cache[date] = stocks
        return stocks

    def _overnight_panel(self, date: str, stocks: List[str], data_loader) -> pd.DataFrame:
        if date in self.panel_cache:
            return self.panel_cache[date]

        idx = self.date_to_idx.get(date)
        if idx is None or idx < self.window + 1:
            self.panel_cache[date] = pd.DataFrame()
            return self.panel_cache[date]

        # Need previous-day turnover and next-day overnight information.
        prev_dates = self.trade_dates[idx - self.window: idx]
        stock_set = set(stocks)
        frames = []

        for prev_date in prev_dates:
            prev_idx = self.date_to_idx[prev_date]
            if prev_idx + 1 >= len(self.trade_dates):
                continue
            next_date = self.trade_dates[prev_idx + 1]
            if next_date > date:
                continue

            prev_daily = self._get_daily(data_loader, prev_date)
            next_daily = self._get_daily(data_loader, next_date)
            if prev_daily.empty or next_daily.empty:
                continue

            prev_daily = prev_daily[prev_daily['code'].isin(stock_set)][['code', 'close', 'turnover_ratio']].rename(
                columns={'close': 'prev_close', 'turnover_ratio': 'prev_turnover'}
            )
            next_daily = next_daily[next_daily['code'].isin(stock_set)][['code', 'open', 'volume', 'turnover_ratio']].rename(
                columns={'open': 'next_open', 'volume': 'next_volume', 'turnover_ratio': 'next_turnover'}
            )
            merged = prev_daily.merge(next_daily, on='code', how='inner')
            if merged.empty:
                continue

            merged['date'] = prev_date
            merged['overnight_return'] = merged['next_open'] / merged['prev_close'] - 1
            merged['overnight_turnover'] = merged['next_turnover']

            first_5m = self._get_first_5m(next_date)
            if not first_5m.empty:
                first = first_5m.rename(columns={'volume': 'first_5m_volume'}).reset_index()
                merged = merged.merge(first, on='code', how='left')
                mask = (
                    merged['first_5m_volume'].notna()
                    & merged['next_volume'].notna()
                    & (merged['next_volume'] > 0)
                    & (merged['next_turnover'] > 0)
                )
                merged.loc[mask, 'overnight_turnover'] = (
                    merged.loc[mask, 'first_5m_volume']
                    / merged.loc[mask, 'next_volume']
                    * merged.loc[mask, 'next_turnover']
                )

            frames.append(merged[['code', 'date', 'prev_turnover', 'overnight_return', 'overnight_turnover']])

        if not frames:
            self.panel_cache[date] = pd.DataFrame()
        else:
            panel = pd.concat(frames, ignore_index=True)
            panel = panel.replace([np.inf, -np.inf], np.nan).dropna()
            panel = panel[panel['overnight_turnover'] > 0]
            self.panel_cache[date] = panel
        return self.panel_cache[date]

    def _calculate_ctr(self, panel: pd.DataFrame) -> pd.DataFrame:
        if panel.empty:
            return pd.DataFrame()

        df = panel.sort_values(['code', 'date']).copy()
        counts = df.groupby('code')['date'].transform('count')
        df = df[counts >= self.window]
        if df.empty:
            return pd.DataFrame()

        r_min = df.groupby('code')['overnight_return'].transform('min')
        r_max = df.groupby('code')['overnight_return'].transform('max')
        denom = (r_max - r_min).replace(0, np.nan)
        df['overnight_return_norm'] = (df['overnight_return'] - r_min) / denom
        df['overnight_smart'] = df['overnight_return_norm'] / df['overnight_turnover'].replace(0, np.nan)
        df = df.replace([np.inf, -np.inf], np.nan).dropna(
            subset=['overnight_smart', 'prev_turnover']
        )
        if df.empty:
            return pd.DataFrame()

        selected = df.sort_values(['code', 'overnight_smart']).groupby('code').head(self.cut_count)
        selected_counts = selected.groupby('code')['prev_turnover'].transform('count')
        selected = selected[selected_counts >= self.cut_count]
        if selected.empty:
            return pd.DataFrame()

        factor = selected.groupby('code')['prev_turnover'].mean().rename('CTR_raw').to_frame()
        return factor

    def _neutralize(self, factor_df: pd.DataFrame, date: str) -> pd.DataFrame:
        if factor_df.empty:
            return factor_df
        df = factor_df.copy()
        barra = self._get_barra(date)
        if self.neutralize_size and not barra.empty and 'size' in barra.columns:
            df = df.join(barra.set_index('code')['size'].rename('size_factor'), how='left')
        if self.neutralize_industry:
            industry = self._get_industry(date)
            if not industry.empty and 'industry' in industry.columns:
                df = df.join(industry.set_index('code')['industry'].rename('industry'), how='left')

        drop_cols = ['CTR_raw']
        if 'size_factor' in df.columns:
            drop_cols.append('size_factor')
        if self.neutralize_industry and 'industry' in df.columns:
            drop_cols.append('industry')
        df = df.dropna(subset=drop_cols)
        if df.empty:
            return pd.DataFrame()

        x_parts = [np.ones(len(df))]
        if 'size_factor' in df.columns:
            x_parts.append(df['size_factor'].values)
        if self.neutralize_industry and 'industry' in df.columns:
            dummies = pd.get_dummies(df['industry'], drop_first=True)
            if not dummies.empty:
                x_parts.append(dummies.values)

        y = df['CTR_raw'].values
        if len(x_parts) > 1:
            try:
                x = np.column_stack(x_parts)
                coef = np.linalg.lstsq(x, y, rcond=None)[0]
                resid = y - x.dot(coef)
            except Exception:
                resid = y - y.mean()
        else:
            resid = y - y.mean()
        df['CTR_neu'] = self._zscore(pd.Series(resid, index=df.index))
        return df

    def calculate_factor(self, date: str, data_loader, **kwargs) -> pd.DataFrame:
        self._ensure_trade_dates(data_loader)
        stocks = self._get_stock_pool(date, data_loader)
        if len(stocks) < self.min_stock_count:
            return pd.DataFrame()

        panel = self._overnight_panel(date, stocks, data_loader)
        if panel.empty:
            return pd.DataFrame()

        factor = self._calculate_ctr(panel)
        if factor.empty:
            return pd.DataFrame()

        factor = self._clip_outliers(factor, cols=['CTR_raw'])
        factor = self._neutralize(factor, date)
        if factor.empty or 'CTR_neu' not in factor.columns:
            return pd.DataFrame()

        result = factor[['CTR_neu']].rename(columns={'CTR_neu': 'factor_value'})
        result = result.dropna(subset=['factor_value']).reset_index()
        result['date'] = date
        return result[['code', 'date', 'factor_value']]

    def generate_signal(self, factor_df: pd.DataFrame, top_n: int = 10) -> list:
        if factor_df.empty or 'factor_value' not in factor_df.columns:
            return []
        sorted_df = factor_df.sort_values('factor_value', ascending=self.select_ascending)
        return sorted_df.head(top_n)['code'].tolist()
