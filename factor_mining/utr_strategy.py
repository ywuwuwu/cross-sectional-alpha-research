"""
UTR策略（Ultimate Turnover Rate Strategy）是基于换手率水平和换手率波动构建的日频量化投资策略。

核心逻辑：
- Turn20: 20日平均换手率，衡量换手率水平
- STR: 20日换手率标准差，衡量换手率波动
- UTR: 综合排名因子，结合 STR 和 Turn20 的截面排名

经济学含义：
- 高波动 + 低换手: 换手率突然放大后又萎缩 -> 筹码趋于集中 -> 看好
- 高波动 + 高换手: 持续高换手高波动 -> 投机氛围重 -> 回避
- 低波动 + 高换手: 稳定的高换手 -> 流动性好 -> 看好
- 低波动 + 低换手: 无人问津的冷门股 -> 回避
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional

from strategy_base import Strategy


class UTRStrategy(Strategy):
    """
    UTR策略 - 优加换手率因子
    """

    def __init__(
        self,
        data_dir: str = './data',
        turnover_window: int = 20,  # 换手率计算窗口
        min_avg_volume: float = 5e5,
        liquidity_window: int = 20,
        min_stock_count: int = 200,
        min_listed_days: int = 252,
        min_listed_coverage: float = 0.8,
        outlier_method: str = 'sigma',
        outlier_param: float = 3.0,
        neutralize: bool = True,  # 是否对UTR进行中性化
    ):
        super().__init__(name='UTR')
        self.data_dir = Path(data_dir)
        self.turnover_window = turnover_window
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

        min_days = max(self.turnover_window, self.min_listed_days)
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
        """加载历史面板数据（包含 turnover_ratio）"""
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

    def _calculate_turn20_str(self, panel: pd.DataFrame) -> pd.DataFrame:
        """
        计算 Turn20 和 STR
        """
        df = panel.copy()
        grouped = df.groupby('code', group_keys=False)

        # Turn20: 20日平均换手率
        df['Turn20'] = grouped['turnover_ratio'].rolling(self.turnover_window).mean().reset_index(level=0, drop=True)
        # STR: 20日换手率标准差
        df['STR'] = grouped['turnover_ratio'].rolling(self.turnover_window).std().reset_index(level=0, drop=True)

        # 提取最新一期数据
        latest = df.groupby('code').tail(1).set_index('code')
        result = pd.DataFrame(index=latest.index)
        result['Turn20'] = latest['Turn20']
        result['STR'] = latest['STR']

        # 带入市值字段（用于中性化）
        for cap_col in ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']:
            if cap_col in latest.columns:
                result[cap_col] = latest[cap_col]
                break

        return result

    def _calculate_utr(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算 UTR = score1 + score2
        score1 = STR 的截面排名
        score2: STR 前50%用 Turn20 反向排名，后50%用 Turn20 正向排名
        """
        if factor_df.empty:
            return factor_df

        df = factor_df.copy()

        # 去极值
        df = self._clip_outliers(df, cols=['Turn20', 'STR'])

        # 截面标准化
        df['Turn20_z'] = self._zscore(df['Turn20'])
        df['STR_z'] = self._zscore(df['STR'])

        # score1: STR 的排名 (1~N)
        df['score1'] = df['STR'].rank()

        # tag1: STR 的百分比排名 (0~1)
        df['tag1'] = df['STR'].rank(pct=True)

        # score2 分情况计算
        df['score2'] = 0.0

        # STR 前50% (高波动): Turn20 反向排名 (换手率越低越好)
        mask_high = df['tag1'] < 0.5
        if mask_high.any():
            df.loc[mask_high, 'score2'] = df.loc[mask_high, 'Turn20'].rank(ascending=False)

        # STR 后50% (低波动): Turn20 正向排名 (换手率越高越好)
        mask_low = df['tag1'] >= 0.5
        if mask_low.any():
            df.loc[mask_low, 'score2'] = df.loc[mask_low, 'Turn20'].rank(ascending=True)

        # UTR = score1 + score2
        df['UTR'] = df['score1'] + df['score2']

        return df

    def _neutralize_utr(self, factor_df: pd.DataFrame) -> pd.DataFrame:
        """对 UTR 进行中性化（对 STR 和 Turn20 回归取残差）"""
        if factor_df.empty or not self.neutralize:
            return factor_df

        df = factor_df.copy()
        required_cols = ['UTR', 'STR', 'Turn20']
        for col in required_cols:
            if col not in df.columns:
                return factor_df

        df = df.dropna(subset=required_cols)
        if df.empty:
            return pd.DataFrame()

        try:
            import statsmodels.api as sm
            X = sm.add_constant(df[['STR', 'Turn20']])
            y = df['UTR'].values
            model = sm.OLS(y, X).fit()
            df['UTR_neu'] = model.resid
        except Exception:
            # 回归失败则简单减去均值
            df['UTR_neu'] = df['UTR'] - df['UTR'].mean()

        return df

    def calculate_factor(self, date: str, data_loader, **kwargs) -> pd.DataFrame:
        self._ensure_trade_dates(data_loader)

        stocks = self._get_stock_pool(date, data_loader)
        if len(stocks) < self.min_stock_count:
            return pd.DataFrame()

        # 加载历史面板数据（需要 turnover_window 天）
        panel = self._load_panel(date, stocks, data_loader, self.turnover_window)
        if panel.empty:
            return pd.DataFrame()

        # 计算 Turn20 和 STR
        factor_raw = self._calculate_turn20_str(panel)
        if factor_raw.empty:
            return pd.DataFrame()

        # 计算 UTR
        factor = self._calculate_utr(factor_raw)
        if factor.empty or 'UTR' not in factor.columns:
            return pd.DataFrame()

        # 中性化
        factor = self._neutralize_utr(factor)

        # 确定最终因子列名
        if self.neutralize and 'UTR_neu' in factor.columns:
            result = factor[['UTR_neu']].rename(columns={'UTR_neu': 'factor_value'})
        else:
            result = factor[['UTR']].rename(columns={'UTR': 'factor_value'})

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

        strategy = UTRStrategy(data_dir='./data')
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
