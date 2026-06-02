import numpy as np
import pandas as pd

from ubl_strategy import UBLStrategy


class PaperUBLStrategy(UBLStrategy):
    """
    Strict report-style UBL strategy from 模块1：威廉指标.pdf.

    Target formula:
        UBL = zscore(蜡烛上_std_desize) + zscore(威廉下_mean_desize)

    Definitions:
        蜡烛上影线 = high - max(open, close)
        威廉下影线 = close - low

    Daily shadow values are normalized by their trailing M-day mean, then:
        蜡烛上_std:  trailing N-day std of normalized candle upper shadow
        威廉下_mean: trailing N-day mean of normalized Williams lower shadow

    Each subfactor is desized by cross-sectional regression on size, then
    z-scored and added with equal weight.
    """

    def __init__(
        self,
        data_dir: str = './data',
        norm_window: int = 5,
        factor_window: int = 20,
        min_avg_volume: float = 5e5,
        liquidity_window: int = 20,
        min_stock_count: int = 200,
        min_listed_days: int = 60,
        min_listed_coverage: float = 0.8,
        outlier_method: str = 'sigma',
        outlier_param: float = 3.0,
        neutralize_industry: bool = False,
        select_ascending: bool = True,
    ):
        super().__init__(
            data_dir=data_dir,
            candle_window_short=norm_window,
            candle_window_long=factor_window,
            wr_window_short=norm_window,
            wr_window_long=factor_window,
            min_avg_volume=min_avg_volume,
            liquidity_window=liquidity_window,
            min_stock_count=min_stock_count,
            weights={'candle_upper_std': 1, 'william_lower_mean': 1},
            outlier_method=outlier_method,
            outlier_param=outlier_param,
            neutralize_industry=neutralize_industry,
            min_listed_days=min_listed_days,
            min_listed_coverage=min_listed_coverage,
            use_long_candle=False,
        )
        self.name = 'PaperUBL'
        self.norm_window = norm_window
        self.factor_window = factor_window
        self.select_ascending = select_ascending

    def _desize_factor(
        self,
        values: pd.Series,
        raw_df: pd.DataFrame,
        date: str,
        factor_name: str,
    ) -> pd.Series:
        df = pd.DataFrame({factor_name: values}).dropna()
        if df.empty:
            return pd.Series(dtype=float)

        for cap_col in ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']:
            if cap_col in raw_df.columns:
                df[cap_col] = raw_df[cap_col]
                break

        barra = self._get_barra(date)
        if not barra.empty and 'size' in barra.columns:
            df = df.join(barra.set_index('code')['size'].rename('barra_size'), how='left')

        cap_col = None
        for c in ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']:
            if c in df.columns:
                cap_col = c
                break

        if cap_col:
            df['size_factor'] = np.log(df[cap_col].astype(float).replace(0, np.nan))
        elif 'barra_size' in df.columns:
            df['size_factor'] = df['barra_size'].astype(float)

        if self.neutralize_industry:
            industry = self._get_industry(date)
            if not industry.empty and 'industry' in industry.columns:
                df = df.join(industry.set_index('code')['industry'].rename('industry'), how='left')

        drop_cols = [factor_name]
        if 'size_factor' in df.columns:
            drop_cols.append('size_factor')
        if self.neutralize_industry and 'industry' in df.columns:
            drop_cols.append('industry')

        df = df.dropna(subset=drop_cols)
        if df.empty:
            return pd.Series(dtype=float)

        x_parts = [np.ones(len(df))]
        if 'size_factor' in df.columns:
            x_parts.append(df['size_factor'].values)
        if self.neutralize_industry and 'industry' in df.columns:
            dummies = pd.get_dummies(df['industry'], drop_first=True)
            if not dummies.empty:
                x_parts.append(dummies.values)

        if len(x_parts) == 1:
            return (df[factor_name] - df[factor_name].mean()).rename(f'{factor_name}_desize')

        x = np.column_stack(x_parts)
        y = df[factor_name].values
        try:
            coef = np.linalg.lstsq(x, y, rcond=None)[0]
            resid = y - x.dot(coef)
        except Exception:
            resid = y - y.mean()
        return pd.Series(resid, index=df.index, name=f'{factor_name}_desize')

    def calculate_factor(self, date: str, data_loader, **kwargs) -> pd.DataFrame:
        self._ensure_trade_dates(data_loader)

        stocks = self._get_stock_pool(date, data_loader)
        if len(stocks) < self.min_stock_count:
            return pd.DataFrame()

        window = self.norm_window + self.factor_window
        panel = self._load_panel(date, stocks, data_loader, window)
        if panel.empty:
            return pd.DataFrame()

        df = panel.copy()
        hl = (df['high'] - df['low']).replace(0, np.nan)
        df['candle_upper'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['william_lower'] = df['close'] - df['low']

        grouped = df.groupby('code', group_keys=False)
        df['candle_upper_base'] = (
            grouped['candle_upper']
            .rolling(self.norm_window)
            .mean()
            .reset_index(level=0, drop=True)
        )
        df['william_lower_base'] = (
            grouped['william_lower']
            .rolling(self.norm_window)
            .mean()
            .reset_index(level=0, drop=True)
        )

        df['candle_upper_base'] = df['candle_upper_base'].replace(0, np.nan).fillna(hl)
        df['william_lower_base'] = df['william_lower_base'].replace(0, np.nan).fillna(hl)
        df['candle_upper_norm'] = df['candle_upper'] / df['candle_upper_base']
        df['william_lower_norm'] = df['william_lower'] / df['william_lower_base']

        df['candle_upper_std'] = (
            grouped['candle_upper_norm']
            .rolling(self.factor_window)
            .std()
            .reset_index(level=0, drop=True)
        )
        df['william_lower_mean'] = (
            grouped['william_lower_norm']
            .rolling(self.factor_window)
            .mean()
            .reset_index(level=0, drop=True)
        )

        latest = df.groupby('code').tail(1).set_index('code')
        factor_raw = latest[['candle_upper_std', 'william_lower_mean']].copy()
        for cap_col in ['market_cap', 'total_mv', 'mkt_cap', 'mv', 'circ_mv', 'float_mv']:
            if cap_col in latest.columns:
                factor_raw[cap_col] = latest[cap_col]
                break

        factor_raw = self._clip_outliers(
            factor_raw,
            cols=['candle_upper_std', 'william_lower_mean'],
        )

        candle_desize = self._desize_factor(
            factor_raw['candle_upper_std'],
            factor_raw,
            date,
            'candle_upper_std',
        )
        william_desize = self._desize_factor(
            factor_raw['william_lower_mean'],
            factor_raw,
            date,
            'william_lower_mean',
        )

        common = candle_desize.index.intersection(william_desize.index)
        if len(common) < self.min_stock_count:
            return pd.DataFrame()

        factor = pd.DataFrame(index=common)
        factor['candle_upper_std_desize_z'] = self._zscore(candle_desize.loc[common])
        factor['william_lower_mean_desize_z'] = self._zscore(william_desize.loc[common])
        factor['factor_value'] = (
            factor['candle_upper_std_desize_z'] +
            factor['william_lower_mean_desize_z']
        )
        factor = self._clip_outliers(factor, cols=['factor_value'])
        factor['factor_value'] = self._zscore(factor['factor_value'])

        result = factor[['factor_value']].dropna().reset_index()
        result['date'] = date
        return result[['code', 'date', 'factor_value']]

    def generate_signal(self, factor_df: pd.DataFrame, top_n: int = 10) -> list:
        if factor_df.empty or 'factor_value' not in factor_df.columns:
            return []
        sorted_df = factor_df.sort_values(
            'factor_value',
            ascending=self.select_ascending,
        )
        return sorted_df.head(top_n)['code'].tolist()
