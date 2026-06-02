from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


ENGINE_CFG = dict(
    data_dir="./data",
    initial_capital=1_000_000,
    commission_rate=0.0003,
    slippage_rate=0.001,
    stamp_duty=0.001,
    risk_free_rate=0.03,
)

STRATEGY_CFG = dict(
    data_dir="./data",
    candle_window_short=5,
    candle_window_long=20,
    wr_window_short=5,
    wr_window_long=20,
    min_avg_volume=5e5,
    liquidity_window=20,
    min_stock_count=200,
    min_listed_days=252,
    min_listed_coverage=0.8,
    outlier_method="sigma",
    outlier_param=3.0,
    neutralize_industry=True,
    use_long_candle=True,
    weights={"U": 1, "B": 1, "L": 1, "WR": 1, "TREND": 1},
)

BACKTEST_CFG = dict(
    start_date="2020-01-02",
    end_date="2022-01-21",
    top_n=50,
    rebalance_freq="month_start",
    enable_cost=True,
    calculate_ic=True,
    n_groups=10,
)

KEY_METRICS = [
    "total_return",
    "annual_return",
    "annual_volatility",
    "max_drawdown",
    "sharpe_ratio",
    "calmar_ratio",
    "win_rate",
    "ic_mean",
    "ic_std",
    "ir",
    "ic_win_rate",
]


def _format_value(value: Any) -> str:
    try:
        if pd.isna(value):
            return "NA"
    except TypeError:
        pass
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    display = df.reset_index()
    headers = [str(c) for c in display.columns]
    rows = []
    for _, row in display.iterrows():
        rows.append([_format_value(row[c]) for c in display.columns])
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _use_agg_backend() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _series_to_csv(series: pd.Series, path: Path, value_name: str) -> None:
    if series is None or series.empty:
        return
    df = series.rename(value_name).reset_index()
    df.columns = ["date", value_name]
    df.to_csv(path, index=False)


def get_key_metrics(report: Dict[str, Any]) -> pd.Series:
    summary = {k: report.get(k) for k in KEY_METRICS if k in report}
    return pd.Series(summary, name="value")


def get_group_pivot(report: Dict[str, Any]) -> pd.DataFrame:
    group_df = report.get("group_returns")
    if group_df is None or group_df.empty:
        return pd.DataFrame()
    group_df = group_df.sort_values("date")
    return group_df.pivot(index="date", columns="group", values="ret")


def get_group_cumulative_returns(report: Dict[str, Any]) -> pd.DataFrame:
    pivot = get_group_pivot(report)
    if pivot.empty:
        return pd.DataFrame()
    return (1 + pivot).cumprod()


def get_group_mean_returns(report: Dict[str, Any]) -> pd.Series:
    pivot = get_group_pivot(report)
    if pivot.empty:
        return pd.Series(dtype=float, name="mean_return")
    return pivot.mean().rename("mean_return")


def get_drawdown(report: Dict[str, Any]) -> pd.Series:
    cumulative = report.get("cumulative_returns")
    if cumulative is None or cumulative.empty:
        return pd.Series(dtype=float, name="drawdown")
    return (cumulative / cumulative.cummax() - 1).rename("drawdown")


def get_rolling_stats(report: Dict[str, Any]) -> pd.DataFrame:
    daily = report.get("daily_returns")
    if daily is None or daily.empty:
        return pd.DataFrame()
    rolling_vol = daily.rolling(63).std()
    return pd.DataFrame(
        {
            "rolling_21d_mean_return": daily.rolling(21).mean(),
            "rolling_63d_volatility": rolling_vol,
            "rolling_3m_sharpe": (
                daily.rolling(63).mean() / (rolling_vol + 1e-8)
            )
            * (252**0.5),
        }
    )


def plot_group_cumulative_returns(report: Dict[str, Any], path: Path) -> bool:
    cumulative = get_group_cumulative_returns(report)
    if cumulative.empty:
        return False
    plt = _use_agg_backend()
    fig, ax = plt.subplots(figsize=(10, 4))
    cumulative.plot(ax=ax, title="Group Cumulative Returns")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_group_mean_returns(report: Dict[str, Any], path: Path) -> bool:
    mean_returns = get_group_mean_returns(report)
    if mean_returns.empty:
        return False
    plt = _use_agg_backend()
    fig, ax = plt.subplots(figsize=(6, 3))
    mean_returns.plot(kind="bar", ax=ax, title="Group Mean Returns")
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_group_long_short_returns(report: Dict[str, Any], path: Path) -> bool:
    ls_series = report.get("group_ls_returns")
    if ls_series is None or ls_series.empty:
        return False
    plt = _use_agg_backend()
    fig, ax = plt.subplots(figsize=(8, 3))
    ls_series.sort_index().plot(ax=ax, title="Long-Short (Group) Returns")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_performance_overview(report: Dict[str, Any], path: Path) -> bool:
    cumulative = report.get("cumulative_returns")
    daily = report.get("daily_returns")
    if cumulative is None or cumulative.empty or daily is None or daily.empty:
        return False
    drawdown = get_drawdown(report)
    plt = _use_agg_backend()
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    cumulative.plot(ax=ax[0, 0], title="Cumulative Returns")
    daily.plot(ax=ax[0, 1], title="Daily Returns")
    drawdown.plot(ax=ax[1, 0], title="Drawdown")
    daily.hist(ax=ax[1, 1], bins=50)
    ax[1, 1].set_title("Daily Return Distribution")
    for axis in ax.ravel():
        axis.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_rolling_metrics(report: Dict[str, Any], path: Path) -> bool:
    rolling = get_rolling_stats(report)
    if rolling.empty:
        return False
    plt = _use_agg_backend()
    fig, ax = plt.subplots(2, 1, figsize=(10, 6))
    rolling["rolling_21d_mean_return"].plot(ax=ax[0], title="Rolling 21D Mean Return")
    rolling["rolling_3m_sharpe"].plot(ax=ax[1], title="Rolling 3M Sharpe")
    for axis in ax:
        axis.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_ic_series(report: Dict[str, Any], path: Path) -> bool:
    ic_series = report.get("ic_series")
    if ic_series is None or ic_series.empty:
        return False
    plt = _use_agg_backend()
    fig, ax = plt.subplots(figsize=(10, 4))
    ic_series.plot(ax=ax, title="Daily IC (Spearman)")
    ax.grid(True, linestyle="--", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def plot_ic_distribution(report: Dict[str, Any], path: Path) -> bool:
    ic_series = report.get("ic_series")
    if ic_series is None or ic_series.empty:
        return False
    plt = _use_agg_backend()
    fig, ax = plt.subplots(figsize=(6, 3))
    ic_series.hist(ax=ax, bins=40)
    ax.set_title("IC Distribution")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


def save_visualizer_results(report: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
    key_metrics = get_key_metrics(report)
    if not key_metrics.empty:
        key_metrics.to_csv(run_dir / "key_metrics.csv", header=True)

    group_pivot = get_group_pivot(report)
    if not group_pivot.empty:
        group_pivot.to_csv(run_dir / "group_returns_pivot.csv")

    group_cumulative = get_group_cumulative_returns(report)
    if not group_cumulative.empty:
        group_cumulative.to_csv(run_dir / "group_cumulative_returns.csv")

    group_mean = get_group_mean_returns(report)
    if not group_mean.empty:
        group_mean.to_csv(run_dir / "group_mean_returns.csv", header=True)

    drawdown = get_drawdown(report)
    _series_to_csv(drawdown, run_dir / "drawdown_series.csv", "drawdown")

    rolling = get_rolling_stats(report)
    if not rolling.empty:
        rolling.to_csv(run_dir / "rolling_metrics.csv", index_label="date")

    return {
        "key_metrics": key_metrics,
        "group_pivot": group_pivot,
        "group_cumulative": group_cumulative,
        "group_mean": group_mean,
        "drawdown": drawdown,
        "rolling": rolling,
    }


def save_visualizer_plots(report: Dict[str, Any], run_dir: Path) -> List[str]:
    plot_specs = [
        ("performance_overview.png", plot_performance_overview),
        ("rolling_metrics.png", plot_rolling_metrics),
        ("group_cumulative_returns.png", plot_group_cumulative_returns),
        ("group_mean_returns.png", plot_group_mean_returns),
        ("group_long_short_returns.png", plot_group_long_short_returns),
        ("ic_series.png", plot_ic_series),
        ("ic_distribution.png", plot_ic_distribution),
    ]
    saved: List[str] = []
    for filename, plotter in plot_specs:
        path = run_dir / filename
        if plotter(report, path):
            saved.append(filename)
    return saved


def generate_visual_report(
    report: Dict[str, Any], run_dir: Path, make_plots: bool = True
) -> Dict[str, Any]:
    tables = save_visualizer_results(report, run_dir)
    plots = save_visualizer_plots(report, run_dir) if make_plots else []
    return {"tables": tables, "plots": plots}


def build_visualizer_markdown(visual_report: Dict[str, Any]) -> str:
    tables = visual_report.get("tables", {})
    plots = visual_report.get("plots", [])
    lines: List[str] = ["", "## Notebook Visualizer Results", ""]

    key_metrics = tables.get("key_metrics")
    if key_metrics is not None and not key_metrics.empty:
        lines.extend(["### Key Metrics", "", "| Metric | Value |", "|---|---:|"])
        for metric, value in key_metrics.items():
            lines.append(f"| {metric} | {_format_value(value)} |")
        lines.append("")

    group_mean = tables.get("group_mean")
    if group_mean is not None and not group_mean.empty:
        lines.extend(["### Group Mean Returns", "", "| Group | Mean Return |", "|---:|---:|"])
        for group, value in group_mean.items():
            lines.append(f"| {group} | {_format_value(value)} |")
        lines.append("")

    rolling = tables.get("rolling")
    if rolling is not None and not rolling.empty:
        tail = rolling.tail(5)
        lines.extend(["### Rolling Metrics Tail", "", _dataframe_to_markdown(tail), ""])

    if plots:
        lines.extend(["### Plots", ""])
        for filename in plots:
            title = Path(filename).stem.replace("_", " ").title()
            lines.append(f"![{title}]({filename})")
            lines.append("")

    lines.extend(
        [
            "### Saved Result Files",
            "",
            "- `key_metrics.csv`",
            "- `drawdown_series.csv`",
            "- `rolling_metrics.csv`",
            "- `group_returns_pivot.csv`",
            "- `group_cumulative_returns.csv`",
            "- `group_mean_returns.csv`",
        ]
    )
    return "\n".join(lines) + "\n"
