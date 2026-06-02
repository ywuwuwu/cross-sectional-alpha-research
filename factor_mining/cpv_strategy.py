"""
CPV策略（Close-Price-Volume Correlation Strategy）是基于日内收盘价与成交量相关性构建的日频量化投资策略。

核心逻辑：
- 每天从5分钟数据计算 close_volume_corr（收盘价与成交量的日内相关系数）
- PV_corr_avg: 20日滚动均值
- PV_corr_std: 20日滚动标准差
- 截面标准化后相加: CPV = zscore(PV_corr_avg) + zscore(PV_corr_std)

经济学含义：
- 正相关: 价格上涨伴随放量 -> 趋势确认 -> 可能继续上涨
- 负相关: 价格上涨但缩量 -> 趋势可疑 -> 可能反转
- 均值: 衡量价量关系的平均水平
- 标准差: 衡量价量关系的稳定性

注意: 5分钟数据仅覆盖2021年，因此回测区间受限
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional

from strategy_base import Strategy


# ========== Ray 并行计算辅助函数 ==========

def _calc_corr_for_date(filename: str, stock_set: set) -> pd.DataFrame:
    """
    计算单日 close-volume 相关系数（无状态函数，用于 Ray 并行）
    """
    try:
        df_5m = pd.read_csv(filename)
        if df_5m.empty:
            return pd.DataFrame()

        # 从文件名提取日期
        date = Path(filename).stem

        # 过滤股票池
        df_5m = df_5m[df_5m['code'].isin(stock_set)].copy()
        if df_5m.empty:
            return pd.DataFrame()

        # 计算每只股票日内 close-volume 相关系数
        correlations = df_5m.groupby('code').apply(
            lambda x: x['close'].corr(x['volume'])
        )

        result = correlations.to_frame().reset_index()
        result.columns = ['code', 'close_volume_corr']
        result['date'] = date
        return result
    except Exception:
        return pd.DataFrame()


# Ray 远程函数（必须在模块级别定义）
try:
    import ray

    @ray.remote
    def _calc_corr_ray(filename: str, stock_set_frozenset: frozenset) -> pd.DataFrame:
        """Ray 远程包装函数"""
        return _calc_corr_for_date(filename, set(stock_set_frozenset))
except ImportError:
    _calc_corr_ray = None


class CPVStrategy(Strategy):
    """
    CPV策略 - 价量相关性因子（真正的CPV，使用Volume数据）
    """

    def __init__(
        self,
        data_dir: str = './data',
        min5_dir: str = './data/data_5m',  # 5分钟数据目录
        corr_window: int = 20,  # 相关系数滚动窗口
        min_avg_volume: float = 5e5,
        liquidity_window: int = 20,
        min_stock_count: int = 200,
        min_listed_days: int = 252,
        min_listed_coverage: float = 0.8,
        outlier_method: str = 'sigma',
        outlier_param: float = 3.0,
        neutralize: bool = False,
    ):
        super().__init__(name='CPV')
        self.data_dir = Path(data_dir)
        self.min5_dir = Path(min5_dir)
        self.corr_window = corr_window
        self.min_avg_volume = min_avg_volume
        self.liquidity_window = liquidity_window
        self.min_stock_count = min_stock_count
        self.min_listed_days = min_listed_days
        self.min_listed_coverage = min_listed_coverage
        self.outlier_method = outlier_method
        self.outlier_param = outlier_param
        self.neutralize = neutralize

        # 缓存
        self.trade_dates: Optional[List[str]] = None
        self.date_to_idx: dict = {}
        self.daily_cache: dict = {}
        self.status_cache: dict = {}
        self.min5_cache: dict = {}  # 5分钟数据缓存
        self.corr_cache: dict = {}  # 已计算的相关系数缓存
        self.use_ray: bool = True    # 是否使用 Ray 并行
        self.ray_initialized: bool = False  # Ray 是否已初始化

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
                cols = ['code', 'open', 'high', 'low', 'close', 'volume', 'turnover_ratio', 'date']
                extra_cols = ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv', 'money']
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

    def _get_5min_data(self, date: str) -> pd.DataFrame:
        """读取5分钟数据"""
        if date not in self.min5_cache:
            path = self.min5_dir / f'{date}.csv'
            if path.exists():
                df = pd.read_csv(path)
                self.min5_cache[date] = df
            else:
                self.min5_cache[date] = pd.DataFrame()
        return self.min5_cache[date]

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

        min_days = max(self.corr_window, self.min_listed_days)
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

    def _calculate_daily_corr(self, date: str, stocks: List[str]) -> pd.DataFrame:
        """
        计算单日 close-volume 相关系数
        """
        df_5m = self._get_5min_data(date)
        if df_5m.empty:
            return pd.DataFrame()

        # 过滤股票池
        stock_set = set(stocks)
        df_5m = df_5m[df_5m['code'].isin(stock_set)].copy()

        if df_5m.empty:
            return pd.DataFrame()

        # 计算每只股票日内 close-volume 相关系数
        correlations = df_5m.groupby('code').apply(
            lambda x: x['close'].corr(x['volume'])
        )

        result = correlations.to_frame().reset_index()
        result.columns = ['code', 'close_volume_corr']
        result['date'] = date

        return result

    def _load_corr_history(self, date: str, stocks: List[str], window: int) -> pd.DataFrame:
        """
        加载历史 close_volume_corr 数据
        使用 Ray 并行加速（如果可用）
        """
        idx = self.date_to_idx.get(date)
        if idx is None or idx < window:
            return pd.DataFrame()

        use_dates = self.trade_dates[idx - window + 1: idx + 1]
        stock_set = set(stocks)

        # 尝试使用 Ray 并行
        if self.use_ray and _calc_corr_ray is not None:
            try:
                import ray
                if not self.ray_initialized:
                    ray.init(num_cpus=4, ignore_reinit_error=True, log_to_driver=False)
                    self.ray_initialized = True

                # 构建文件路径列表
                file_paths = [str(self.min5_dir / f'{d}.csv') for d in use_dates]
                file_paths = [f for f in file_paths if Path(f).exists()]

                if file_paths:
                    # 使用模块级别的 Ray 远程函数并行计算
                    futures = [_calc_corr_ray.remote(f, frozenset(stock_set)) for f in file_paths]
                    results = ray.get(futures)

                    frames = [r for r in results if not r.empty]
                    if frames:
                        panel = pd.concat(frames).sort_values(['code', 'date'])
                        counts = panel.groupby('code').size()
                        valid = counts[counts >= window].index
                        return panel[panel['code'].isin(valid)]
            except Exception:
                # Ray 失败则回退到单线程
                pass

        # 单线程回退
        frames = []
        for d in use_dates:
            corr_df = self._calculate_daily_corr(d, list(stock_set))
            if not corr_df.empty:
                frames.append(corr_df)

        if not frames:
            return pd.DataFrame()

        panel = pd.concat(frames).sort_values(['code', 'date'])
        counts = panel.groupby('code').size()
        valid = counts[counts >= window].index
        return panel[panel['code'].isin(valid)]

    def _calculate_cpv(self, corr_panel: pd.DataFrame) -> pd.DataFrame:
        """
        计算 CPV 因子
        PV_corr_avg: 20日滚动均值
        PV_corr_std: 20日滚动标准差
        CPV = zscore(PV_corr_avg) + zscore(PV_corr_std)
        """
        if corr_panel.empty:
            return pd.DataFrame()

        df = corr_panel.copy()
        grouped = df.groupby('code', group_keys=False)

        # 计算20日滚动均值和标准差
        df['PV_corr_avg'] = grouped['close_volume_corr'].rolling(self.corr_window).mean().reset_index(level=0, drop=True)
        df['PV_corr_std'] = grouped['close_volume_corr'].rolling(self.corr_window).std().reset_index(level=0, drop=True)

        # 提取最新一期数据
        latest = df.groupby('code').tail(1).set_index('code')
        result = pd.DataFrame(index=latest.index)
        result['PV_corr_avg'] = latest['PV_corr_avg']
        result['PV_corr_std'] = latest['PV_corr_std']

        return result

    def calculate_factor(self, date: str, data_loader, **kwargs) -> pd.DataFrame:
        self._ensure_trade_dates(data_loader)

        # 检查是否有5分钟数据
        df_5m = self._get_5min_data(date)
        if df_5m.empty:
            return pd.DataFrame()

        stocks = self._get_stock_pool(date, data_loader)
        if len(stocks) < self.min_stock_count:
            return pd.DataFrame()

        # 加载历史相关系数数据（需要 corr_window 天）
        corr_panel = self._load_corr_history(date, stocks, self.corr_window)
        if corr_panel.empty:
            return pd.DataFrame()

        # 计算 CPV 因子
        factor_raw = self._calculate_cpv(corr_panel)
        if factor_raw.empty:
            return pd.DataFrame()

        # 去极值
        factor_raw = self._clip_outliers(factor_raw, cols=['PV_corr_avg', 'PV_corr_std'])

        # 截面标准化
        factor_raw['PV_corr_avg_z'] = self._zscore(factor_raw['PV_corr_avg'])
        factor_raw['PV_corr_std_z'] = self._zscore(factor_raw['PV_corr_std'])

        # CPV = 标准化均值 + 标准化标准差
        factor_raw['CPV'] = factor_raw['PV_corr_avg_z'] + factor_raw['PV_corr_std_z']

        # 再次去极值
        factor_raw = self._clip_outliers(factor_raw, cols=['CPV'])

        result = factor_raw[['CPV']].rename(columns={'CPV': 'factor_value'})
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

    # CPV 策略只能回测2021年（5分钟数据覆盖的区间）
    # 找第一个有5分钟数据的交易日
    test_date = '2021-01-29'  # 需要20天历史数据，所以从1月29日开始

    print(f"测试日期: {test_date}")
    strategy = CPVStrategy(data_dir='./data', min5_dir='./data/data_5m')
    factor_df = strategy.calculate_factor(test_date, loader)
    if not factor_df.empty:
        print(f"因子计算成功: {len(factor_df)} 只股票")
        print(factor_df.head())
        selected = strategy.generate_signal(factor_df, top_n=10)
        print(f"选股结果 (Top 10): {selected}")
    else:
        print("因子计算结果为空（可能该日期没有5分钟数据）")
