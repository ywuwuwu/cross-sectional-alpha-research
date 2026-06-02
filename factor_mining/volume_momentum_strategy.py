"""
Volume-corrected momentum strategy.

Partial local-data reproduction of 模块4：成交量对动量因子的修正.pdf.

Default target factor: mom_1430_smart.

Paper logic, simplified:
1. Split 20-day momentum into intraday and overnight pieces.
2. Use turnover/volume to cut each stock's 20 observations into low/high
   information buckets.
3. Combine low-turnover reversal and high-turnover momentum/reversal components
   after cross-sectional z-scoring.
4. For the final smart factor, use previous-day 14:30-15:00 turnover for the
   overnight component, and smart AM/PM intraday turnover for the intraday
   component.

Local-data limitation:
The paper uses 1-minute bars, opening auction turnover, exact intraday turnover,
full A-share 2014-2023 data, and monthly group tests. Local data has daily
turnover_ratio and 5-minute bars for 2021 only. This class therefore implements
factor-logic validation with 5-minute proxies, not exact performance replication.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from strategy_base import Strategy


class VolumeMomentumStrategy(Strategy):
    def __init__(
        self,
        data_dir: str = './data',
        min5_dir: str = './data_5m',
        window: int = 20,
        variant: str = 'mom_1430_smart',
        smart_pct: float = 0.20,
        min_avg_volume: float = 5e5,
        liquidity_window: int = 20,
        min_stock_count: int = 200,
        min_listed_days: int = 60,
        min_listed_coverage: float = 0.8,
        outlier_method: str = 'sigma',
        outlier_param: float = 3.0,
        neutralize: bool = False,
        neutralize_industry: bool = False,
        select_ascending: bool = True,
    ):
        super().__init__(name=f'VolumeMomentum_{variant}')
        self.data_dir = Path(data_dir)
        self.min5_dir = Path(min5_dir)
        self.window = int(window)
        self.variant = variant
        self.smart_pct = float(smart_pct)
        self.min_avg_volume = float(min_avg_volume)
        self.liquidity_window = int(liquidity_window)
        self.min_stock_count = int(min_stock_count)
        self.min_listed_days = int(min_listed_days)
        self.min_listed_coverage = float(min_listed_coverage)
        self.outlier_method = outlier_method
        self.outlier_param = float(outlier_param)
        self.neutralize = bool(neutralize)
        self.neutralize_industry = bool(neutralize_industry)
        self.select_ascending = bool(select_ascending)

        self.trade_dates: Optional[List[str]] = None
        self.date_to_idx: Dict[str, int] = {}
        self.daily_cache: Dict[str, pd.DataFrame] = {}
        self.status_cache: Dict[str, pd.DataFrame] = {}
        self.bar5_cache: Dict[str, pd.DataFrame] = {}
        self.feature_cache: Dict[str, pd.DataFrame] = {}
        self.stock_pool_cache: Dict[str, List[str]] = {}
        self.barra_cache: Dict[str, pd.DataFrame] = {}
        self.industry_cache: Dict[str, pd.DataFrame] = {}

    @staticmethod
    def _zscore(series: pd.Series) -> pd.Series:
        s = series.astype(float)
        std = s.std()
        if std == 0 or np.isnan(std):
            return s * 0.0
        return (s - s.mean()) / (std + 1e-8)

    def _ensure_trade_dates(self, data_loader) -> None:
        if self.trade_dates is None:
            self.trade_dates = data_loader.get_all_dates()
            self.date_to_idx = {d: i for i, d in enumerate(self.trade_dates)}

    def _get_daily(self, data_loader, date: str) -> pd.DataFrame:
        if date not in self.daily_cache:
            df = data_loader.get_daily_data(date)
            if df.empty:
                self.daily_cache[date] = pd.DataFrame()
            else:
                cols = ['date', 'code', 'open', 'close', 'volume', 'turnover_ratio', 'money']
                self.daily_cache[date] = df[[c for c in cols if c in df.columns]].copy()
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

    def _get_5m(self, date: str) -> pd.DataFrame:
        if date not in self.bar5_cache:
            path = self.min5_dir / f'{date}.csv'
            if not path.exists():
                self.bar5_cache[date] = pd.DataFrame()
            else:
                df = pd.read_csv(path)
                if not df.empty:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df['time'] = df['datetime'].dt.strftime('%H:%M:%S')
                self.bar5_cache[date] = df
        return self.bar5_cache[date]

    def _session_aggregate(self, bars: pd.DataFrame, session: str) -> pd.DataFrame:
        if bars.empty:
            return pd.DataFrame()
        if session == 'am':
            sub = bars[(bars['time'] >= '09:35:00') & (bars['time'] <= '11:30:00')].copy()
        elif session == 'pm':
            sub = bars[(bars['time'] >= '13:05:00') & (bars['time'] <= '15:00:00')].copy()
        elif session == 'last30':
            sub = bars[(bars['time'] >= '14:35:00') & (bars['time'] <= '15:00:00')].copy()
        else:
            sub = bars.copy()
        if sub.empty:
            return pd.DataFrame()

        grouped = sub.sort_values(['code', 'datetime']).groupby('code')
        agg = grouped.agg(
            first_open=('open', 'first'),
            last_close=('close', 'last'),
            session_volume=('volume', 'sum'),
        )
        agg[f'{session}_ret'] = agg['last_close'] / agg['first_open'] - 1
        return agg[[f'{session}_ret', 'session_volume']].rename(
            columns={'session_volume': f'{session}_volume'}
        )

    def _smart_turnover(self, bars: pd.DataFrame, session: str, daily_turnover: pd.Series) -> pd.Series:
        if bars.empty:
            return pd.Series(dtype=float)
        if session == 'am':
            sub = bars[(bars['time'] >= '09:35:00') & (bars['time'] <= '11:30:00')].copy()
        else:
            sub = bars[(bars['time'] >= '13:05:00') & (bars['time'] <= '15:00:00')].copy()
        if sub.empty:
            return pd.Series(dtype=float)

        sub['bar_ret'] = sub['close'] / sub['open'] - 1
        sub['smart_score'] = sub['bar_ret'].abs() / np.sqrt(sub['volume'].clip(lower=1))
        counts = sub.groupby('code')['smart_score'].transform('count')
        keep_n = np.ceil(counts * self.smart_pct).clip(lower=1)
        ranks = sub.groupby('code')['smart_score'].rank(method='first', ascending=False)
        smart_vol = sub[ranks <= keep_n].groupby('code')['volume'].sum()
        total_vol = bars.groupby('code')['volume'].sum()
        aligned_turnover = daily_turnover.reindex(smart_vol.index)
        smart_turnover = smart_vol / total_vol.reindex(smart_vol.index).replace(0, np.nan) * aligned_turnover
        return smart_turnover

    def _daily_features(self, date: str, data_loader) -> pd.DataFrame:
        if date in self.feature_cache:
            return self.feature_cache[date]

        idx = self.date_to_idx.get(date)
        if idx is None or idx == 0:
            self.feature_cache[date] = pd.DataFrame()
            return self.feature_cache[date]

        prev_date = self.trade_dates[idx - 1]
        daily = self._get_daily(data_loader, date)
        prev_daily = self._get_daily(data_loader, prev_date)
        if daily.empty or prev_daily.empty:
            self.feature_cache[date] = pd.DataFrame()
            return self.feature_cache[date]

        df = daily[['code', 'open', 'close', 'volume', 'turnover_ratio']].merge(
            prev_daily[['code', 'close']].rename(columns={'close': 'prev_close'}),
            on='code',
            how='inner',
        )
        if df.empty:
            self.feature_cache[date] = pd.DataFrame()
            return self.feature_cache[date]

        df = df.set_index('code')
        df['date'] = date
        df['intraday_ret'] = df['close'] / df['open'] - 1
        df['overnight_ret'] = df['open'] / df['prev_close'] - 1
        df['intraday_turnover'] = df['turnover_ratio']
        df['half_hour_turnover'] = df['turnover_ratio']
        df['am_ret'] = df['intraday_ret'] / 2.0
        df['pm_ret'] = df['intraday_ret'] / 2.0
        df['am_smart_turnover'] = df['turnover_ratio'] / 2.0
        df['pm_smart_turnover'] = df['turnover_ratio'] / 2.0
        df['am_turnover'] = df['turnover_ratio'] / 2.0
        df['pm_turnover'] = df['turnover_ratio'] / 2.0

        bars = self._get_5m(date)
        if not bars.empty:
            total_5m_vol = bars.groupby('code')['volume'].sum().replace(0, np.nan)
            daily_turnover = df['turnover_ratio']
            last30 = self._session_aggregate(bars, 'last30')
            am = self._session_aggregate(bars, 'am')
            pm = self._session_aggregate(bars, 'pm')

            if not last30.empty:
                df['half_hour_turnover'] = (
                    last30['last30_volume'] / total_5m_vol.reindex(last30.index) * daily_turnover.reindex(last30.index)
                ).reindex(df.index).fillna(df['half_hour_turnover'])
            if not am.empty:
                df['am_ret'] = am['am_ret'].reindex(df.index).fillna(df['am_ret'])
                df['am_turnover'] = (
                    am['am_volume'] / total_5m_vol.reindex(am.index) * daily_turnover.reindex(am.index)
                ).reindex(df.index).fillna(df['am_turnover'])
            if not pm.empty:
                df['pm_ret'] = pm['pm_ret'].reindex(df.index).fillna(df['pm_ret'])
                df['pm_turnover'] = (
                    pm['pm_volume'] / total_5m_vol.reindex(pm.index) * daily_turnover.reindex(pm.index)
                ).reindex(df.index).fillna(df['pm_turnover'])

            am_smart = self._smart_turnover(bars, 'am', daily_turnover)
            pm_smart = self._smart_turnover(bars, 'pm', daily_turnover)
            if not am_smart.empty:
                df['am_smart_turnover'] = am_smart.reindex(df.index).fillna(df['am_smart_turnover'])
            if not pm_smart.empty:
                df['pm_smart_turnover'] = pm_smart.reindex(df.index).fillna(df['pm_smart_turnover'])

        result_cols = [
            'date', 'volume', 'intraday_ret', 'overnight_ret', 'intraday_turnover',
            'half_hour_turnover', 'am_ret', 'pm_ret', 'am_turnover', 'pm_turnover',
            'am_smart_turnover', 'pm_smart_turnover',
        ]
        result = df[result_cols].replace([np.inf, -np.inf], np.nan).dropna().reset_index()
        self.feature_cache[date] = result
        return result

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
            tradable = status[(status['paused'] == 0) & (status['zt'] == 0) & (status['dt'] == 0)]
            stocks = [s for s in stocks if s in set(tradable['code'])]

        idx = self.date_to_idx.get(date)
        if idx is None:
            self.stock_pool_cache[date] = []
            return []

        min_days = max(self.window + 1, self.min_listed_days)
        if idx >= min_days:
            frames = []
            for d in self.trade_dates[idx - min_days: idx]:
                df = self._get_daily(data_loader, d)
                if not df.empty:
                    frames.append(df[['code']])
            if frames:
                counts = pd.concat(frames)['code'].value_counts()
                min_required = int(min_days * self.min_listed_coverage)
                eligible = set(counts[counts >= min_required].index)
                stocks = [s for s in stocks if s in eligible]

        if idx > self.liquidity_window:
            vol_frames = []
            stock_set = set(stocks)
            for d in self.trade_dates[idx - self.liquidity_window: idx]:
                df = self._get_daily(data_loader, d)
                if not df.empty:
                    sub = df[df['code'].isin(stock_set)][['code', 'volume']]
                    if not sub.empty:
                        vol_frames.append(sub)
            if vol_frames:
                avg_vol = pd.concat(vol_frames).groupby('code')['volume'].mean()
                stocks = avg_vol[avg_vol >= self.min_avg_volume].index.tolist()

        self.stock_pool_cache[date] = stocks
        return stocks

    def _history_panel(self, date: str, stocks: List[str], data_loader) -> pd.DataFrame:
        idx = self.date_to_idx.get(date)
        if idx is None or idx < self.window + 1:
            return pd.DataFrame()

        dates = self.trade_dates[idx - self.window: idx + 1]
        stock_set = set(stocks)
        frames = []
        for d in dates:
            feats = self._daily_features(d, data_loader)
            if feats.empty:
                continue
            feats = feats[feats['code'].isin(stock_set)].copy()
            if not feats.empty:
                frames.append(feats)
        if not frames:
            return pd.DataFrame()

        panel = pd.concat(frames, ignore_index=True).sort_values(['code', 'date'])
        panel['prev_half_hour_turnover'] = panel.groupby('code')['half_hour_turnover'].shift(1)
        return panel.replace([np.inf, -np.inf], np.nan)

    def _partial_cut_factor(self, panel: pd.DataFrame, sort_col: str, ret_col: str, prefix: str) -> pd.DataFrame:
        if panel.empty:
            return pd.DataFrame()
        df = panel[['code', 'date', sort_col, ret_col]].dropna().sort_values(['code', 'date'])
        if df.empty:
            return pd.DataFrame()

        counts = df.groupby('code')['date'].transform('count')
        df = df[counts >= self.window].copy()
        if df.empty:
            return pd.DataFrame()

        # Keep the latest window observations for each stock.
        rev_order = df.groupby('code').cumcount(ascending=False)
        df = df[rev_order < self.window].copy()
        counts = df.groupby('code')['date'].transform('count')
        df = df[counts >= self.window].copy()
        if df.empty:
            return pd.DataFrame()

        cut_count = max(1, int(round(self.window * 0.2)))
        ordered = df.sort_values(['code', sort_col])
        rank_asc = ordered.groupby('code').cumcount() + 1
        group_count = ordered.groupby('code')[ret_col].transform('count')
        selected = ordered[(rank_asc <= cut_count) | (rank_asc > group_count - cut_count)].copy()
        selected['bucket'] = np.where(rank_asc.loc[selected.index] <= cut_count, 'part1', 'part5')
        pivot = selected.pivot_table(index='code', columns='bucket', values=ret_col, aggfunc='mean')
        if pivot.empty or not {'part1', 'part5'}.issubset(pivot.columns):
            return pd.DataFrame()
        pivot = pivot.rename(columns={'part1': f'{prefix}_part1', 'part5': f'{prefix}_part5'})
        return pivot[[f'{prefix}_part1', f'{prefix}_part5']].dropna()

    def _combine_low_high(self, parts: pd.DataFrame, prefix: str) -> pd.Series:
        p1 = parts[f'{prefix}_part1']
        p5 = parts[f'{prefix}_part5']
        return -self._zscore(p1) + self._zscore(p5)

    def _clip_outliers(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        if df.empty or col not in df.columns:
            return df
        s = df[col].astype(float)
        method = (self.outlier_method or '').lower()
        if method == 'quantile':
            q = self.outlier_param
            df[col] = s.clip(s.quantile(q), s.quantile(1 - q))
        else:
            std = s.std()
            if std and not np.isnan(std):
                df[col] = s.clip(s.mean() - self.outlier_param * std, s.mean() + self.outlier_param * std)
        return df

    def _neutralize_factor(self, factor: pd.DataFrame, date: str) -> pd.DataFrame:
        if factor.empty or not self.neutralize:
            return factor
        df = factor.copy()
        barra = self._get_barra(date)
        if not barra.empty:
            exposure_cols = [c for c in barra.columns if c != 'code']
            df = df.join(barra.set_index('code')[exposure_cols], how='left')
        if self.neutralize_industry:
            industry = self._get_industry(date)
            if not industry.empty and 'industry' in industry.columns:
                df = df.join(industry.set_index('code')['industry'], how='left')

        x_cols = [c for c in df.columns if c not in {'factor_value', 'industry'}]
        drop_cols = ['factor_value'] + x_cols
        if self.neutralize_industry and 'industry' in df.columns:
            drop_cols.append('industry')
        df = df.dropna(subset=drop_cols)
        if df.empty:
            return pd.DataFrame()

        x_parts = [np.ones(len(df))]
        if x_cols:
            x_parts.append(df[x_cols].values)
        if self.neutralize_industry and 'industry' in df.columns:
            dummies = pd.get_dummies(df['industry'], drop_first=True)
            if not dummies.empty:
                x_parts.append(dummies.values)
        try:
            x = np.column_stack(x_parts)
            y = df['factor_value'].values
            coef = np.linalg.lstsq(x, y, rcond=None)[0]
            df['factor_value'] = y - x.dot(coef)
        except Exception:
            df['factor_value'] = df['factor_value'] - df['factor_value'].mean()
        return df[['factor_value']]

    def calculate_factor(self, date: str, data_loader, **kwargs) -> pd.DataFrame:
        self._ensure_trade_dates(data_loader)
        stocks = self._get_stock_pool(date, data_loader)
        if len(stocks) < self.min_stock_count:
            return pd.DataFrame()

        panel = self._history_panel(date, stocks, data_loader)
        if panel.empty:
            return pd.DataFrame()

        day_old_parts = self._partial_cut_factor(panel, 'intraday_turnover', 'intraday_ret', 'day_old')
        night_old_parts = self._partial_cut_factor(panel, 'prev_half_hour_turnover', 'overnight_ret', 'night_1430')
        am_parts = self._partial_cut_factor(panel, 'am_smart_turnover', 'am_ret', 'am_smart')
        pm_parts = self._partial_cut_factor(panel, 'pm_smart_turnover', 'pm_ret', 'pm_smart')

        pieces = []
        if not day_old_parts.empty:
            pieces.append(self._combine_low_high(day_old_parts, 'day_old').rename('day_old'))
        if not night_old_parts.empty:
            pieces.append(self._combine_low_high(night_old_parts, 'night_1430').rename('night_1430'))
        if not am_parts.empty:
            pieces.append(self._combine_low_high(am_parts, 'am_smart').rename('am_smart'))
        if not pm_parts.empty:
            pieces.append(self._combine_low_high(pm_parts, 'pm_smart').rename('pm_smart'))
        if not pieces:
            return pd.DataFrame()

        comp = pd.concat(pieces, axis=1).dropna()
        if comp.empty:
            return pd.DataFrame()

        if 'am_smart' in comp.columns and 'pm_smart' in comp.columns:
            comp['day_smart'] = self._zscore(comp['am_smart']) + self._zscore(comp['pm_smart'])
        if 'day_old' in comp.columns and 'night_1430' in comp.columns:
            comp['mom_1430'] = self._zscore(comp['day_old']) + self._zscore(comp['night_1430'])
        if 'day_smart' in comp.columns and 'night_1430' in comp.columns:
            comp['mom_1430_smart'] = self._zscore(comp['day_smart']) + self._zscore(comp['night_1430'])

        target = self.variant
        if target not in comp.columns:
            if 'mom_1430_smart' in comp.columns:
                target = 'mom_1430_smart'
            elif 'mom_1430' in comp.columns:
                target = 'mom_1430'
            else:
                target = comp.columns[-1]

        factor = comp[[target]].rename(columns={target: 'factor_value'}).dropna()
        factor = self._clip_outliers(factor, 'factor_value')
        factor['factor_value'] = self._zscore(factor['factor_value'])
        factor = self._neutralize_factor(factor, date)
        if factor.empty:
            return pd.DataFrame()
        result = factor.reset_index()
        result['date'] = date
        return result[['code', 'date', 'factor_value']]

    def generate_signal(self, factor_df: pd.DataFrame, top_n: int = 10) -> list:
        if factor_df.empty or 'factor_value' not in factor_df.columns:
            return []
        sorted_df = factor_df.sort_values('factor_value', ascending=self.select_ascending)
        return sorted_df.head(top_n)['code'].tolist()
