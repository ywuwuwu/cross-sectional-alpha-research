"""
Ideal Reversal 策略（理想反转因子）是基于成交金额对收益率进行切割的日频量化投资策略。

核心逻辑：
- 在20日滚动窗口内，按成交金额(money)排序
- M_high: 成交金额最高的10天的收益率之和
- M_low:  成交金额最低的10天的收益率之和
- ideal_reverse = M_high - M_low

经济学含义：
- ideal_reverse > 0: 大额交易时涨得多，小额交易时涨得少 -> 机构在买入 -> 可能继续上涨
- ideal_reverse < 0: 大额交易时跌得多，小额交易时跌得少 -> 机构在卖出 -> 可能继续下跌

核心逻辑：
- 大额成交通常代表机构资金的行为
- 小额成交通常代表散户资金的行为
- 通过对比两者收益差异，捕捉机构资金的动向
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple
from multiprocessing import Pool

from strategy_base import Strategy


# ========== 多进程并行计算辅助函数 ==========

def _calc_single_stock(stock_data: Tuple) -> dict:
    """
    计算单只股票的理想反转因子（无状态函数，用于多进程并行）
    """
    code, stock_returns, stock_amounts, window, top_n_days = stock_data

    # 合并为DataFrame
    df = pd.DataFrame({
        'ret': stock_returns,
        'money': stock_amounts
    }).dropna()

    if len(df) < window:
        return None

    # 取最近 window 天的数据
    window_data = df.tail(window)

    if len(window_data) < window:
        return None

    # 按成交金额排序
    high_days = window_data.nlargest(top_n_days, 'money')
    M_high = high_days['ret'].sum()

    low_days = window_data.nsmallest(top_n_days, 'money')
    M_low = low_days['ret'].sum()

    ideal_reverse = M_high - M_low

    return {
        'code': code,
        'ideal_reverse': ideal_reverse,
        'M_high': M_high,
        'M_low': M_low,
    }


class IdealReversalStrategy(Strategy):
    """
    Ideal Reversal 策略 - 理想反转因子
    """

    def __init__(
        self,
        data_dir: str = './data',
        window: int = 20,  # 滚动窗口
        top_n_days: int = 10,  # 取成交金额最高/最低的N天
        min_avg_volume: float = 5e5,
        liquidity_window: int = 20,
        min_stock_count: int = 200,
        min_listed_days: int = 252,
        min_listed_coverage: float = 0.8,
        outlier_method: str = 'sigma',
        outlier_param: float = 3.0,
        neutralize: bool = False,  # 是否中性化
    ):
        super().__init__(name='IdealReversal')
        self.data_dir = Path(data_dir)
        self.window = window
        self.top_n_days = top_n_days
        self.min_avg_volume = min_avg_volume
        self.liquidity_window = liquidity_window
        self.min_stock_count = min_stock_count
        self.min_listed_days = min_listed_days
        self.min_listed_coverage = min_listed_coverage
        self.outlier_method = outlier_method
        self.outlier_param = outlier_param
        self.neutralize = neutralize
        self.use_multiprocessing: bool = True  # 是否使用多进程并行
        self.num_workers: int = 4  # 并行进程数

        # 缓存
        self.trade_dates: Optional[List[str]] = None
        self.date_to_idx: dict = {}
        self.daily_cache: dict = {}
        self.status_cache: dict = {}

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
                cols = ['code', 'open', 'high', 'low', 'close', 'volume', 'money', 'turnover_ratio', 'date']
                extra_cols = ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']
                cols += [c for c in extra_cols if c in df.columns]
                available = [c for c in cols if c in df.columns]
                df = df[available].copy()
                if 'date' in df.columns:
                    df['time'] = pd.to_datetime(df['date'])
                else:
                    df['time'] = pd.to_datetime(date)
            self.daily_cache[date] = df
        return self.daily_cache[date]

    def _get_status(self, data_loader, date: str) -> pd.DataFrame:
        if date not in self.status_cache:
            self.status_cache[date] = data_loader.get_daily_status(date)
        return self.status_cache[date]

    def _get_stock_pool(self, date: str, data_loader) -> List[str]:
        daily = self._get_daily(data_loader, date)
        if daily is None or daily.empty:
            return []

        stocks = daily['code'].tolist()

        status = self._get_status(data_loader, date)
        if status is not None and not status.empty:
            status = status.copy()
            if 'st' in status.columns:
                status = status[status['st'] == 0]
            tradable = status[
                (status['paused'] == 0) &
                (status['zt'] == 0) &
                (status['dt'] == 0)
            ]
            stocks = [s for s in stocks if s in set(tradable['code'])]

        idx = self.date_to_idx.get(date)
        if idx is None:
            return []

        min_days = max(self.window, self.min_listed_days)
        if idx >= min_days:
            eligible_dates = self.trade_dates[idx - min_days: idx]
            counts = {}
            for d in eligible_dates:
                df = self._get_daily(data_loader, d)
                if df is None or df.empty:
                    continue
                for code in df['code'].tolist():
                    counts[code] = counts.get(code, 0) + 1
            min_required = int(min_days * self.min_listed_coverage)
            stocks = [s for s in stocks if counts.get(s, 0) >= min_required]

        if idx <= self.liquidity_window:
            return stocks

        hist_dates = self.trade_dates[idx - self.liquidity_window: idx]
        vol_frames = []
        stock_set = set(stocks)
        for d in hist_dates:
            df = self._get_daily(data_loader, d)
            if df is None or df.empty:
                continue
            sub = df[df['code'].isin(stock_set)][['code', 'volume']]
            if not sub.empty:
                vol_frames.append(sub)

        if vol_frames:
            vol_df = pd.concat(vol_frames)
            avg_vol = vol_df.groupby('code')['volume'].mean()
            stocks = avg_vol[avg_vol >= self.min_avg_volume].index.tolist()

        return stocks

    def _load_panel(self, date: str, stocks: List[str], data_loader, window: int) -> pd.DataFrame:
        """加载历史面板数据（包含 close 和 money）"""
        idx = self.date_to_idx.get(date)
        if idx is None or idx < window:
            return pd.DataFrame()

        use_dates = self.trade_dates[idx - window + 1: idx + 1]
        frames = []
        stock_set = set(stocks)
        for d in use_dates:
            df = self._get_daily(data_loader, d)
            if df is None or df.empty:
                continue
            sub = df[df['code'].isin(stock_set)].copy()
            if not sub.empty:
                if 'time' not in sub.columns:
                    sub['time'] = pd.to_datetime(d)
                frames.append(sub)

        if not frames:
            return pd.DataFrame()

        panel = pd.concat(frames).sort_values(['code', 'time'])
        counts = panel.groupby('code').size()
        valid = counts[counts >= window].index
        return panel[panel['code'].isin(valid)]

    def _calculate_ideal_reversal(self, panel: pd.DataFrame) -> pd.DataFrame:
        """
        计算理想反转因子
        对每只股票，在20日窗口内按成交金额排序，取高10天和低10天的收益率差
        使用多进程并行加速（如果启用）
        """
        df = panel.copy()

        # 计算日收益率
        df = df.sort_values(['code', 'time'])
        df['ret'] = df.groupby('code')['close'].pct_change()

        # 准备数据：为每只股票提取 ret 和 money 序列
        stock_data_list = []
        for code, group in df.groupby('code'):
            group = group.dropna(subset=['ret', 'money'])
            if len(group) < self.window:
                continue
            stock_data_list.append((
                code,
                group.set_index('time')['ret'],
                group.set_index('time')['money'],
                self.window,
                self.top_n_days
            ))

        if not stock_data_list:
            return pd.DataFrame()

        # 使用多进程并行计算
        if self.use_multiprocessing and len(stock_data_list) > 10:
            try:
                with Pool(self.num_workers) as pool:
                    results = pool.map(_calc_single_stock, stock_data_list)
                results = [r for r in results if r is not None]
            except Exception:
                # 多进程失败则回退到单线程
                results = [_calc_single_stock(sd) for sd in stock_data_list]
                results = [r for r in results if r is not None]
        else:
            # 单线程回退
            results = [_calc_single_stock(sd) for sd in stock_data_list]
            results = [r for r in results if r is not None]

        if not results:
            return pd.DataFrame()

        result_df = pd.DataFrame(results).set_index('code')

        # 带入市值字段（用于中性化）
        latest = df.groupby('code').tail(1)
        for cap_col in ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']:
            if cap_col in latest.columns:
                cap_map = latest.set_index('code')[cap_col]
                result_df[cap_col] = cap_map
                break

        return result_df

    def _neutralize_factor(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """对因子进行中性化（对市值回归取残差）"""
        if factor_df.empty or not self.neutralize:
            return factor_df

        df = factor_df.copy()
        if 'ideal_reverse' not in df.columns:
            return factor_df

        # 找市值列
        cap_col = None
        for c in ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']:
            if c in df.columns:
                cap_col = c
                break

        if cap_col is None:
            return factor_df

        df['size_factor'] = np.log(df[cap_col].astype(float).replace(0, np.nan))
        df = df.dropna(subset=['ideal_reverse', 'size_factor'])
        if df.empty:
            return pd.DataFrame()

        try:
            import statsmodels.api as sm
            X = sm.add_constant(df['size_factor'])
            y = df['ideal_reverse'].values
            model = sm.OLS(y, X).fit()
            df['ideal_reverse_neu'] = model.resid
        except Exception:
            df['ideal_reverse_neu'] = df['ideal_reverse'] - df['ideal_reverse'].mean()

        return df

    def calculate_factor(self, date: str, data_loader, **kwargs) -> pd.DataFrame:
        self._ensure_trade_dates(data_loader)

        stocks = self._get_stock_pool(date, data_loader)
        if len(stocks) < self.min_stock_count:
            return pd.DataFrame()

        # 加载历史面板数据（需要 window+1 天，因为收益率要pct_change）
        panel = self._load_panel(date, stocks, data_loader, self.window + 1)
        if panel.empty:
            return pd.DataFrame()

        # 计算理想反转因子
        factor_raw = self._calculate_ideal_reversal(panel)
        if factor_raw.empty:
            return pd.DataFrame()

        # 去极值
        factor_raw = self._clip_outliers(factor_raw, cols=['ideal_reverse'])

        # 截面标准化
        factor_raw['ideal_reverse_z'] = self._zscore(factor_raw['ideal_reverse'])

        # 中性化
        factor_raw = self._neutralize_factor(factor_raw)

        # 确定最终因子列名
        if self.neutralize and 'ideal_reverse_neu' in factor_raw.columns:
            result = factor_raw[['ideal_reverse_neu']].rename(columns={'ideal_reverse_neu': 'factor_value'})
        else:
            result = factor_raw[['ideal_reverse']].rename(columns={'ideal_reverse': 'factor_value'})

        result = result.dropna(subset=['factor_value']).reset_index()
        result['date'] = date
        return result[['code', 'date', 'factor_value']]

    def generate_signal(self, factor_df: pd.DataFrame, top_n: int = 10) -> list:
        if factor_df.empty or 'factor_value' not in factor_df.columns:
            return []

        sorted_df = factor_df.sort_values('factor_value', ascending=False)
        return sorted_df.head(top_n)['code'].tolist()


# ========== 测试代码 ==========
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    from data_loader import DataLoader

    loader = DataLoader('./data')
    if len(loader.trade_dates) > 50:
        test_date = loader.trade_dates[50]
        print(f"测试日期: {test_date}")

        strategy = IdealReversalStrategy(data_dir='./data')
        factor_df = strategy.calculate_factor(test_date, loader)
        if not factor_df.empty:
            print(f"因子计算成功: {len(factor_df)} 只股票")
            print(factor_df.head())
            selected = strategy.generate_signal(factor_df, top_n=10)
            print(f"选股结果 (Top 10): {selected}")
        else:
            print("因子计算结果为空")
    else:
        print("交易日数据不足")
