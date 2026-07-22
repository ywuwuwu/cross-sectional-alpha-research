#!/usr/bin/env python3
"""Run the small public alpha-research package on deterministic synthetic data.

The example begins with precomputed, oriented scores. It demonstrates timing,
portfolio accounting, transaction costs, IC diagnostics, and report generation
without exposing or approximating any private strategy formula.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from alpha_research import (
    BacktestConfig,
    Visualizer,
    run_cross_sectional_backtest,
)


def generate_synthetic_panel(
    *,
    seed: int = 7,
    observations: int = 120,
    assets: int = 60,
) -> pd.DataFrame:
    """Create a point-in-time panel with an anonymous predictive score."""
    if observations < 20 or assets < 10:
        raise ValueError("example requires at least 20 dates and 10 assets")
    rng = np.random.default_rng(seed)
    calendar = pd.bdate_range("2020-01-02", periods=observations + 2)
    asset_names = [f"ASSET_{index:03d}" for index in range(assets)]
    score = rng.normal(size=assets)
    frames: list[pd.DataFrame] = []

    for index in range(observations):
        score = 0.65 * score + rng.normal(scale=0.8, size=assets)
        standardized = (score - score.mean()) / score.std(ddof=1)
        forward_return = 0.0010 * standardized + rng.normal(
            scale=0.012,
            size=assets,
        )
        factor_date = calendar[index]
        latest_input = factor_date + pd.Timedelta(hours=16)
        entry_timestamp = calendar[index + 1] + pd.Timedelta(hours=10)
        exit_timestamp = calendar[index + 2] + pd.Timedelta(hours=10)
        frames.append(
            pd.DataFrame(
                {
                    "factor_date": factor_date,
                    "latest_factor_input_timestamp": latest_input,
                    "entry_timestamp": entry_timestamp,
                    "exit_timestamp": exit_timestamp,
                    "asset": asset_names,
                    "alpha_score": score,
                    "forward_return": forward_return,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def run_example(output: Path) -> None:
    """Run the generic tail portfolio and save a compact tear sheet."""
    panel = generate_synthetic_panel()
    config = BacktestConfig(
        long_fraction=0.20,
        short_fraction=0.20,
        cost_bps=10.0,
        band_bps=5.0,
    )
    result = run_cross_sectional_backtest(panel, config)
    output.mkdir(parents=True, exist_ok=True)
    panel.to_csv(output / "synthetic_input.csv", index=False)
    paths = Visualizer(result).save_report(output)

    print("Synthetic sample completed")
    for key in (
        "observations",
        "net_total_return",
        "net_sharpe_0rf",
        "net_max_drawdown",
        "average_full_turnover",
        "rank_ic_mean",
    ):
        value = result.summary[key]
        if isinstance(value, float):
            print(f"  {key}: {value:.6g}")
        else:
            print(f"  {key}: {value}")
    print(f"  report: {paths['report']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/sample_package"),
    )
    args = parser.parse_args()
    run_example(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
