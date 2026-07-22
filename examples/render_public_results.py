#!/usr/bin/env python3
"""Regenerate the selected figures from public aggregate CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

# Select the non-interactive backend before importing pyplot.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from alpha_research.visualization import (  # noqa: E402
    BASELINE_COLOR,
    CANDIDATE_COLOR,
    plot_bootstrap_sharpe_difference,
    plot_cost_frontier,
    plot_drawdown_comparison,
    plot_net_nav,
    plot_walk_forward_folds,
)


LABELS = {
    "UBL_ONLY": "UBL only",
    "UBL_80_LOWVOL_60_20": "80% UBL / 20% LOWVOL",
    "ubl_net_return": "UBL only",
    "selected_net_return": "80% UBL / 20% LOWVOL",
}
PORTFOLIO_ORDER = ["UBL_ONLY", "UBL_80_LOWVOL_60_20"]
COLOR_MAP = {
    "UBL_ONLY": BASELINE_COLOR,
    "UBL_80_LOWVOL_60_20": CANDIDATE_COLOR,
}


def save(figure, path: Path) -> None:
    """Save and close one publication figure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def render(root: Path) -> list[Path]:
    """Render all public figures from the aggregate evidence under ``root``."""
    data = root / "data"
    plots = root / "plots"
    returns = pd.read_csv(data / "portfolio_returns.csv", parse_dates=["date"])
    returns = returns.sort_values("date").set_index("date")
    return_frame = returns[["ubl_net_return", "selected_net_return"]]
    split_starts = {
        split.replace("research_", "").title(): group.index.min()
        for split, group in returns.groupby("split")
        if split != "train"
    }
    outputs = []
    figure = plot_net_nav(return_frame, labels=LABELS, split_starts=split_starts)
    figure.axes[0].set_title(
        "Net NAV at 10 bps per dollar traded",
        loc="left",
        fontsize=13,
        fontweight="bold",
    )
    outputs.append(plots / "01_net_nav_comparison.png")
    save(figure, outputs[-1])

    figure = plot_drawdown_comparison(return_frame, labels=LABELS)
    figure.axes[0].set_title(
        "Net drawdown at 10 bps per dollar traded",
        loc="left",
        fontsize=13,
        fontweight="bold",
    )
    outputs.append(plots / "02_drawdown_comparison.png")
    save(figure, outputs[-1])

    costs = pd.read_csv(data / "cost_sensitivity.csv")
    figure = plot_cost_frontier(
        costs,
        labels=LABELS,
        portfolio_order=PORTFOLIO_ORDER,
        color_map=COLOR_MAP,
    )
    figure.axes[0].set_title(
        "Transaction-cost frontier (full common sample)",
        loc="left",
        fontsize=13,
        fontweight="bold",
    )
    outputs.append(plots / "03_transaction_cost_frontier.png")
    save(figure, outputs[-1])

    bootstrap = pd.read_csv(data / "bootstrap_sharpe_differences.csv")
    figure = plot_bootstrap_sharpe_difference(bootstrap["sharpe_difference"])
    figure.axes[0].set_title(
        "Holdout paired bootstrap: Sharpe difference",
        loc="left",
        fontsize=13,
        fontweight="bold",
    )
    outputs.append(plots / "04_paired_bootstrap_sharpe_difference.png")
    save(figure, outputs[-1])

    folds = pd.read_csv(data / "walk_forward_folds.csv")
    figure = plot_walk_forward_folds(
        folds,
        labels=LABELS,
        portfolio_order=PORTFOLIO_ORDER,
        color_map=COLOR_MAP,
    )
    outputs.append(plots / "05_walk_forward_fold_returns.png")
    save(figure, outputs[-1])

    concentration = pd.read_csv(data / "pnl_concentration.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    values = (
        concentration.set_index("portfolio").reindex(PORTFOLIO_ORDER)[
            "top_five_day_pnl_share"
        ]
        * 100.0
    )
    labels = [LABELS.get(name, name) for name in values.index]
    bars = ax.bar(labels, values, color=[BASELINE_COLOR, CANDIDATE_COLOR], width=0.58)
    ax.bar_label(bars, fmt="%.1f%%", padding=3)
    ax.set_title(
        "Top-five-day PnL concentration", loc="left", fontsize=13, fontweight="bold"
    )
    ax.set_ylabel("Share of full-sample arithmetic net PnL (%)")
    ax.grid(axis="y", color="#D1D5DB", linewidth=0.7, alpha=0.65)
    ax.spines[["top", "right"]].set_visible(False)
    outputs.append(plots / "06_pnl_concentration.png")
    save(fig, outputs[-1])
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("examples/sample_outputs/ubl_lowvol_study"),
    )
    args = parser.parse_args()
    for path in render(args.root):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
