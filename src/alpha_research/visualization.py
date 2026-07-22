"""Formula-agnostic plots and report generation for portfolio research."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .metrics import drawdown_series
from .runner import ResearchResult

BASELINE_COLOR = "#4B5563"
CANDIDATE_COLOR = "#007C78"
ACCENT_COLOR = "#D97706"


def _plt():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "Plotting requires matplotlib. Install with: pip install -e '.[plots]'"
        ) from exc
    return plt


def _finish(ax, *, title: str, ylabel: str):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7, alpha=0.65)
    ax.spines[["top", "right"]].set_visible(False)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False)
    return ax.figure


def plot_net_nav(
    returns: pd.DataFrame,
    *,
    labels: Mapping[str, str] | None = None,
    split_starts: Mapping[str, pd.Timestamp] | None = None,
):
    """Plot compounded net asset value for one or more return columns."""
    plt = _plt()
    frame = returns.sort_index().astype(float)
    if frame.empty:
        raise ValueError("returns cannot be empty")
    nav = (1.0 + frame).cumprod()
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    colors = [BASELINE_COLOR, CANDIDATE_COLOR, ACCENT_COLOR]
    for index, column in enumerate(nav.columns):
        ax.plot(
            nav.index,
            nav[column],
            label=(labels or {}).get(column, column),
            color=colors[index % len(colors)],
            linewidth=2.0,
        )
    for split, date in (split_starts or {}).items():
        ax.axvline(date, color="#9CA3AF", linestyle="--", linewidth=1.0)
        ax.annotate(
            split,
            xy=(date, 1.0),
            xycoords=("data", "axes fraction"),
            xytext=(5, -5),
            textcoords="offset points",
            va="top",
            fontsize=9,
            color="#4B5563",
        )
    return _finish(ax, title="Net NAV comparison", ylabel="Growth of 1.00")


def plot_drawdown_comparison(
    returns: pd.DataFrame,
    *,
    labels: Mapping[str, str] | None = None,
):
    """Plot same-date compounded drawdowns for return columns."""
    if returns.empty:
        raise ValueError("returns cannot be empty")
    plt = _plt()
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    colors = [BASELINE_COLOR, CANDIDATE_COLOR, ACCENT_COLOR]
    for index, column in enumerate(returns.columns):
        drawdown = drawdown_series(returns[column].sort_index()) * 100.0
        ax.plot(
            drawdown.index,
            drawdown,
            label=(labels or {}).get(column, column),
            color=colors[index % len(colors)],
            linewidth=1.8,
        )
    return _finish(ax, title="Drawdown comparison", ylabel="Drawdown (%)")


def plot_cost_frontier(
    frame: pd.DataFrame,
    *,
    portfolio_column: str = "portfolio",
    cost_column: str = "cost_bps",
    sharpe_column: str = "net_sharpe_0rf",
    labels: Mapping[str, str] | None = None,
    portfolio_order: list[str] | None = None,
    color_map: Mapping[str, str] | None = None,
):
    """Plot net Sharpe against a transaction-cost grid."""
    required = {portfolio_column, cost_column, sharpe_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"cost frame is missing columns: {sorted(missing)}")
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    colors = [BASELINE_COLOR, CANDIDATE_COLOR, ACCENT_COLOR]
    order = portfolio_order or list(frame[portfolio_column].drop_duplicates())
    for index, portfolio in enumerate(order):
        group = frame[frame[portfolio_column] == portfolio]
        if group.empty:
            continue
        ordered = group.sort_values(cost_column)
        ax.plot(
            ordered[cost_column],
            ordered[sharpe_column],
            marker="o",
            linewidth=2.0,
            color=(color_map or {}).get(
                str(portfolio),
                colors[index % len(colors)],
            ),
            label=(labels or {}).get(str(portfolio), str(portfolio)),
        )
    ax.axhline(0.0, color="#111827", linewidth=1.0)
    ax.set_xlabel("Cost (bps per dollar traded)")
    return _finish(
        ax,
        title="Transaction-cost frontier",
        ylabel="Annualized net Sharpe",
    )


def plot_bootstrap_sharpe_difference(
    differences: pd.Series,
    *,
    difference_label: str = "Candidate minus baseline Sharpe",
):
    """Plot a paired-bootstrap distribution of Sharpe differences."""
    clean = differences.dropna().astype(float)
    if clean.empty:
        raise ValueError("differences cannot be empty")
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.hist(
        clean,
        bins=42,
        color=CANDIDATE_COLOR,
        alpha=0.82,
        edgecolor="white",
    )
    ax.axvline(0.0, color="#111827", linewidth=1.5, label="No difference")
    ax.axvline(
        clean.median(),
        color=ACCENT_COLOR,
        linewidth=1.8,
        label=f"Median: {clean.median():.2f}",
    )
    ax.set_xlabel(difference_label)
    return _finish(
        ax,
        title="Paired block-bootstrap Sharpe difference",
        ylabel="Resamples",
    )


def plot_walk_forward_folds(
    frame: pd.DataFrame,
    *,
    portfolio_column: str = "portfolio",
    fold_column: str = "fold",
    return_column: str = "net_total_return",
    labels: Mapping[str, str] | None = None,
    portfolio_order: list[str] | None = None,
    color_map: Mapping[str, str] | None = None,
):
    """Plot paired walk-forward fold returns for each portfolio."""
    required = {portfolio_column, fold_column, return_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"walk-forward frame is missing columns: {sorted(missing)}")
    plt = _plt()
    pivot = frame.pivot(
        index=fold_column,
        columns=portfolio_column,
        values=return_column,
    )
    portfolios = portfolio_order or list(pivot.columns)
    absent = [portfolio for portfolio in portfolios if portfolio not in pivot.columns]
    if absent:
        raise ValueError(f"walk-forward frame is missing portfolios: {absent}")
    positions = list(range(len(pivot.index)))
    width = min(0.8 / max(len(portfolios), 1), 0.36)
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    colors = [BASELINE_COLOR, CANDIDATE_COLOR, ACCENT_COLOR]
    for index, portfolio in enumerate(portfolios):
        offset = (index - (len(portfolios) - 1) / 2.0) * width
        ax.bar(
            [position + offset for position in positions],
            pivot[portfolio] * 100.0,
            width=width,
            color=(color_map or {}).get(
                str(portfolio),
                colors[index % len(colors)],
            ),
            label=(labels or {}).get(str(portfolio), str(portfolio)),
        )
    ax.axhline(0.0, color="#111827", linewidth=1.0)
    ax.set_xticks(positions, [f"Fold {fold}" for fold in pivot.index])
    return _finish(
        ax,
        title="Paired walk-forward fold returns",
        ylabel="Net return (%)",
    )


def _json_value(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


class Visualizer:
    """Create a compact tear sheet from a ResearchResult."""

    def __init__(self, result: ResearchResult):
        if not isinstance(result, ResearchResult):
            raise TypeError("result must be a ResearchResult")
        self.result = result

    def plot_nav(self):
        """Plot gross and net compounded portfolio NAV."""
        daily = self.result.daily
        index = pd.DatetimeIndex(daily["entry_timestamp"])
        returns = pd.DataFrame(
            {
                "gross": daily["gross_return"].to_numpy(float),
                "net": daily["net_return"].to_numpy(float),
            },
            index=index,
        )
        return plot_net_nav(
            returns,
            labels={"gross": "Gross", "net": "Net after costs"},
        )

    def plot_drawdown(self):
        """Plot the net portfolio drawdown path."""
        net = self.result.return_series("net_return")
        return plot_drawdown_comparison(
            net.to_frame("net"),
            labels={"net": "Net after costs"},
        )

    def plot_turnover(self):
        """Plot full and one-way turnover through time."""
        daily = self.result.daily
        index = pd.DatetimeIndex(daily["entry_timestamp"])
        plt = _plt()
        fig, ax = plt.subplots(figsize=(10.5, 4.8))
        ax.plot(
            index,
            daily["full_turnover"],
            label="Full turnover",
            color=BASELINE_COLOR,
            linewidth=1.6,
        )
        ax.plot(
            index,
            daily["one_way_turnover"],
            label="One-way turnover",
            color=CANDIDATE_COLOR,
            linewidth=1.6,
        )
        return _finish(ax, title="Portfolio turnover", ylabel="Turnover")

    def plot_rank_ic(self):
        """Plot daily RankIC and its 20-observation rolling mean."""
        daily = self.result.daily
        rank_ic = pd.Series(
            daily["rank_ic"].to_numpy(float),
            index=pd.DatetimeIndex(daily["entry_timestamp"]),
        )
        if rank_ic.dropna().empty:
            raise ValueError("result does not contain valid RankIC observations")
        plt = _plt()
        fig, ax = plt.subplots(figsize=(10.5, 4.8))
        ax.plot(
            rank_ic.index,
            rank_ic,
            color=BASELINE_COLOR,
            alpha=0.55,
            label="RankIC",
        )
        ax.plot(
            rank_ic.index,
            rank_ic.rolling(20, min_periods=5).mean(),
            color=CANDIDATE_COLOR,
            linewidth=2.0,
            label="20-observation mean",
        )
        ax.axhline(0.0, color="#111827", linewidth=1.0)
        return _finish(ax, title="Cross-sectional RankIC", ylabel="RankIC")

    def save_report(
        self,
        output_dir: str | Path,
        *,
        make_plots: bool = True,
    ) -> dict[str, Path]:
        """Save data, figures, and a Markdown report to output_dir."""
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        paths = {
            "daily": destination / "daily_results.csv",
            "weights": destination / "weight_ledger.csv",
            "summary": destination / "summary.json",
            "report": destination / "report.md",
        }
        self.result.daily.to_csv(paths["daily"], index=False)
        self.result.weight_ledger.to_csv(paths["weights"], index=False)
        paths["summary"].write_text(
            json.dumps(
                {key: _json_value(value) for key, value in self.result.summary.items()},
                indent=2,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
        )

        plot_paths: dict[str, Path] = {}
        if make_plots:
            plotters = {
                "net_nav": self.plot_nav,
                "drawdown": self.plot_drawdown,
                "turnover": self.plot_turnover,
                "rank_ic": self.plot_rank_ic,
            }
            plt = _plt()
            for name, plotter in plotters.items():
                figure = plotter()
                path = destination / f"{name}.png"
                figure.savefig(
                    path,
                    dpi=160,
                    bbox_inches="tight",
                    facecolor="white",
                )
                plt.close(figure)
                plot_paths[name] = path

        summary_lines = [
            "# Cross-Sectional Research Report",
            "",
            "## Contract",
            "",
            f"- Timing: {self.result.summary['timing_contract']}",
            "- Direction: higher alpha_score means higher expected return.",
            (
                "- Portfolio: high-score tail long, low-score tail short, "
                f"target gross {self.result.summary['target_gross_exposure']:.2f}."
            ),
            (
                f"- Cost: {self.result.summary['cost_bps']:.2f} bps per dollar "
                "traded on full turnover."
            ),
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
        for key, value in self.result.summary.items():
            if key == "timing_contract":
                continue
            if isinstance(value, float):
                display = "NA" if not np.isfinite(value) else f"{value:.6g}"
            else:
                display = str(value)
            summary_lines.append(f"| {key} | {display} |")
        summary_lines.extend(["", "## Files", ""])
        for name, path in {**paths, **plot_paths}.items():
            if name != "report":
                summary_lines.append(f"- [{name}]({path.name})")
        paths["report"].write_text(
            "\n".join(summary_lines) + "\n",
            encoding="utf-8",
        )
        return {**paths, **plot_paths}
