"""Formula-agnostic cross-sectional research runner.

The runner consumes precomputed, oriented alpha scores. It deliberately knows
nothing about how a signal was constructed, which keeps private formulas outside
the public package.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .metrics import performance_summary
from .portfolio import (
    apply_weight_change_band,
    normalize_dollar_neutral,
    transaction_cost,
)

REQUIRED_PANEL_COLUMNS = (
    "factor_date",
    "latest_factor_input_timestamp",
    "entry_timestamp",
    "exit_timestamp",
    "asset",
    "alpha_score",
    "forward_return",
)


@dataclass(frozen=True)
class BacktestConfig:
    """Fixed portfolio and cost assumptions for one research run."""

    long_fraction: float = 0.20
    short_fraction: float = 0.20
    cost_bps: float = 10.0
    band_bps: float = 0.0
    long_gross: float = 1.0
    short_gross: float = 1.0
    periods_per_year: int = 252

    def __post_init__(self) -> None:
        if not 0 < self.long_fraction <= 0.5:
            raise ValueError("long_fraction must be in (0, 0.5]")
        if not 0 < self.short_fraction <= 0.5:
            raise ValueError("short_fraction must be in (0, 0.5]")
        if self.long_fraction + self.short_fraction > 1.0:
            raise ValueError("long and short fractions cannot sum above one")
        if self.cost_bps < 0 or self.band_bps < 0:
            raise ValueError("cost_bps and band_bps cannot be negative")
        if self.long_gross <= 0 or self.short_gross <= 0:
            raise ValueError("long_gross and short_gross must be positive")
        if self.periods_per_year < 1:
            raise ValueError("periods_per_year must be positive")


@dataclass(frozen=True)
class ResearchResult:
    """Daily portfolio observations, security-level ledger, and summary metrics."""

    daily: pd.DataFrame
    weight_ledger: pd.DataFrame
    summary: dict[str, object]

    def return_series(self, column: str = "net_return") -> pd.Series:
        """Return one daily result column indexed by entry timestamp."""
        if column not in self.daily:
            raise KeyError(f"daily results do not contain {column!r}")
        return pd.Series(
            self.daily[column].to_numpy(float),
            index=pd.DatetimeIndex(self.daily["entry_timestamp"]),
            name=column,
        )


def validate_research_panel(panel: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize a point-in-time alpha/return panel.

    Required timing is strictly:

    latest_factor_input_timestamp < entry_timestamp < exit_timestamp

    alpha_score must already be oriented so that a higher value means a higher
    expected return.
    """
    if not isinstance(panel, pd.DataFrame):
        raise TypeError("panel must be a pandas DataFrame")
    missing = [column for column in REQUIRED_PANEL_COLUMNS if column not in panel]
    if missing:
        raise ValueError(f"panel is missing required columns: {missing}")

    frame = panel.loc[:, REQUIRED_PANEL_COLUMNS].copy()
    timestamp_columns = (
        "factor_date",
        "latest_factor_input_timestamp",
        "entry_timestamp",
        "exit_timestamp",
    )
    for column in timestamp_columns:
        frame[column] = pd.to_datetime(frame[column], errors="raise")
        if frame[column].isna().any():
            raise ValueError(f"{column} contains missing timestamps")

    if frame["asset"].isna().any():
        raise ValueError("asset contains missing identifiers")
    frame["asset"] = frame["asset"].astype(str)
    if (frame["asset"].str.len() == 0).any():
        raise ValueError("asset contains empty identifiers")

    for column in ("alpha_score", "forward_return"):
        frame[column] = pd.to_numeric(frame[column], errors="raise").astype(float)
        if not np.isfinite(frame[column].to_numpy()).all():
            raise ValueError(f"{column} contains NaN or infinite values")
    if (frame["forward_return"] <= -1.0).any():
        raise ValueError("forward_return contains a value at or below -100%")

    duplicated = frame.duplicated(["factor_date", "asset"])
    if duplicated.any():
        sample = (
            frame.loc[duplicated, ["factor_date", "asset"]].head().to_dict("records")
        )
        raise ValueError(f"duplicate factor-date/asset rows: {sample}")

    if (frame["factor_date"] > frame["latest_factor_input_timestamp"]).any():
        raise ValueError("factor_date cannot follow its latest input timestamp")
    if not (frame["latest_factor_input_timestamp"] < frame["entry_timestamp"]).all():
        raise ValueError("latest factor input must precede entry")
    if not (frame["entry_timestamp"] < frame["exit_timestamp"]).all():
        raise ValueError("entry must precede exit")

    timing_counts = frame.groupby("factor_date")[
        ["latest_factor_input_timestamp", "entry_timestamp", "exit_timestamp"]
    ].nunique()
    if (timing_counts > 1).any(axis=None):
        raise ValueError("each factor date must map to one timing interval")

    return frame.sort_values(["factor_date", "asset"]).reset_index(drop=True)


def scores_to_quantile_weights(
    scores: pd.Series,
    *,
    long_fraction: float = 0.20,
    short_fraction: float = 0.20,
    long_gross: float = 1.0,
    short_gross: float = 1.0,
) -> pd.Series:
    """Map oriented scores to equal-weighted high-minus-low tail weights."""
    if not isinstance(scores, pd.Series):
        raise TypeError("scores must be a pandas Series indexed by asset")
    values = scores.astype(float)
    if values.index.has_duplicates:
        raise ValueError("scores contain duplicate asset identifiers")
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("scores contain NaN or infinite values")
    if values.nunique() < 2:
        raise ValueError("scores need cross-sectional dispersion")
    if not 0 < long_fraction <= 0.5 or not 0 < short_fraction <= 0.5:
        raise ValueError("tail fractions must be in (0, 0.5]")
    if long_fraction + short_fraction > 1.0:
        raise ValueError("tail fractions cannot sum above one")

    long_count = max(1, int(np.floor(len(values) * long_fraction)))
    short_count = max(1, int(np.floor(len(values) * short_fraction)))
    if long_count + short_count > len(values):
        raise ValueError("cross-section is too small for the requested tails")

    # Stable sorting makes tie handling deterministic after assets are sorted.
    ordered = values.sort_index().sort_values(kind="mergesort")
    short_assets = ordered.index[:short_count]
    long_assets = ordered.index[-long_count:]
    if len(short_assets.intersection(long_assets)):
        raise ValueError("long and short tails overlap")

    raw = pd.Series(0.0, index=ordered.index)
    raw.loc[long_assets] = 1.0
    raw.loc[short_assets] = -1.0
    return normalize_dollar_neutral(
        raw[raw != 0.0],
        long_gross=long_gross,
        short_gross=short_gross,
    )


def _cross_sectional_correlations(
    scores: pd.Series,
    returns: pd.Series,
) -> tuple[float, float]:
    aligned = pd.concat(
        [scores.rename("score"), returns.rename("return")],
        axis=1,
        join="inner",
    ).dropna()
    if (
        len(aligned) < 2
        or aligned["score"].nunique() < 2
        or aligned["return"].nunique() < 2
    ):
        return float("nan"), float("nan")
    pearson = float(aligned["score"].corr(aligned["return"]))
    rank_ic = float(aligned["score"].rank().corr(aligned["return"].rank()))
    return pearson, rank_ic


def _ic_summary(values: pd.Series, prefix: str) -> dict[str, float | int]:
    clean = values.dropna().astype(float)
    if clean.empty:
        return {
            f"{prefix}_mean": float("nan"),
            f"{prefix}_std": float("nan"),
            f"{prefix}ir_raw": float("nan"),
            f"{prefix}_win_rate": float("nan"),
            f"{prefix}_observations": 0,
        }
    standard_deviation = float(clean.std(ddof=1)) if len(clean) > 1 else float("nan")
    ratio = (
        float(clean.mean()) / standard_deviation
        if np.isfinite(standard_deviation) and standard_deviation > 0
        else float("nan")
    )
    return {
        f"{prefix}_mean": float(clean.mean()),
        f"{prefix}_std": standard_deviation,
        f"{prefix}ir_raw": ratio,
        f"{prefix}_win_rate": float((clean > 0).mean()),
        f"{prefix}_observations": int(len(clean)),
    }


def run_cross_sectional_backtest(
    panel: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> ResearchResult:
    """Run a timing-safe quantile long/short backtest from oriented scores."""
    settings = config or BacktestConfig()
    frame = validate_research_panel(panel)
    previous: pd.Series | None = None
    daily_rows: list[dict[str, object]] = []
    ledger_frames: list[pd.DataFrame] = []

    for factor_date, group in frame.groupby("factor_date", sort=True):
        scores = group.set_index("asset")["alpha_score"]
        realized = group.set_index("asset")["forward_return"]
        target = scores_to_quantile_weights(
            scores,
            long_fraction=settings.long_fraction,
            short_fraction=settings.short_fraction,
            long_gross=settings.long_gross,
            short_gross=settings.short_gross,
        )
        executed = (
            apply_weight_change_band(
                target,
                previous,
                band_bps=settings.band_bps,
                renormalize=True,
                long_gross=settings.long_gross,
                short_gross=settings.short_gross,
            )
            if settings.band_bps > 0
            else target
        )

        previous_values = (
            pd.Series(dtype=float) if previous is None else previous.astype(float)
        )
        assets = (
            previous_values.index.union(target.index, sort=False)
            .union(executed.index, sort=False)
            .union(scores.index, sort=False)
        )
        previous_aligned = previous_values.reindex(assets, fill_value=0.0)
        target_aligned = target.reindex(assets, fill_value=0.0)
        executed_aligned = executed.reindex(assets, fill_value=0.0)
        returns_aligned = realized.reindex(assets)
        held_without_return = (executed_aligned.abs() > 1e-15) & returns_aligned.isna()
        if held_without_return.any():
            names = assets[held_without_return].tolist()[:5]
            raise ValueError(f"missing forward returns for held assets: {names}")
        returns_for_accounting = returns_aligned.fillna(0.0)
        weight_change = executed_aligned - previous_aligned

        # Allocate linear trading cost by absolute security-level weight change.
        cost_contribution = weight_change.abs() * float(settings.cost_bps) / 10_000.0
        gross_contribution = executed_aligned * returns_for_accounting
        net_contribution = gross_contribution - cost_contribution
        turnover = float(weight_change.abs().sum())
        gross_return = float(gross_contribution.sum())
        cost = transaction_cost(turnover, settings.cost_bps)
        net_return = gross_return - cost
        if not np.isclose(cost_contribution.sum(), cost, atol=1e-12):
            raise AssertionError("security costs do not sum to portfolio cost")
        if not np.isclose(net_contribution.sum(), net_return, atol=1e-12):
            raise AssertionError("security PnL does not sum to portfolio return")

        entry_timestamp = group["entry_timestamp"].iloc[0]
        exit_timestamp = group["exit_timestamp"].iloc[0]
        latest_input = group["latest_factor_input_timestamp"].iloc[0]
        pearson_ic, rank_ic = _cross_sectional_correlations(scores, realized)

        daily_rows.append(
            {
                "factor_date": factor_date,
                "latest_factor_input_timestamp": latest_input,
                "entry_timestamp": entry_timestamp,
                "exit_timestamp": exit_timestamp,
                "gross_return": gross_return,
                "full_turnover": turnover,
                "one_way_turnover": turnover / 2.0,
                "transaction_cost": cost,
                "net_return": net_return,
                "pearson_ic": pearson_ic,
                "rank_ic": rank_ic,
                "long_count": int((executed_aligned > 0).sum()),
                "short_count": int((executed_aligned < 0).sum()),
                "gross_exposure": float(executed_aligned.abs().sum()),
                "net_exposure": float(executed_aligned.sum()),
            }
        )

        side = np.select(
            [executed_aligned > 0, executed_aligned < 0],
            ["long", "short"],
            default="flat",
        )
        ledger_frames.append(
            pd.DataFrame(
                {
                    "factor_date": factor_date,
                    "latest_factor_input_timestamp": latest_input,
                    "entry_timestamp": entry_timestamp,
                    "exit_timestamp": exit_timestamp,
                    "asset": assets,
                    "alpha_score": scores.reindex(assets).to_numpy(),
                    "side": side,
                    "previous_weight": previous_aligned.to_numpy(),
                    "target_weight": target_aligned.to_numpy(),
                    "executed_weight": executed_aligned.to_numpy(),
                    "weight_change": weight_change.to_numpy(),
                    "forward_return": returns_aligned.to_numpy(),
                    "gross_pnl_contribution": gross_contribution.to_numpy(),
                    "cost_contribution": cost_contribution.to_numpy(),
                    "net_pnl_contribution": net_contribution.to_numpy(),
                }
            )
        )
        previous = executed

    daily = (
        pd.DataFrame(daily_rows).sort_values("entry_timestamp").reset_index(drop=True)
    )
    if daily.empty:
        raise ValueError("panel produced no portfolio observations")
    if daily["entry_timestamp"].duplicated().any():
        raise ValueError("entry timestamps must be unique across factor dates")
    ledger = pd.concat(ledger_frames, ignore_index=True)

    entry_index = pd.DatetimeIndex(daily["entry_timestamp"])
    net = pd.Series(daily["net_return"].to_numpy(float), index=entry_index)
    gross = pd.Series(daily["gross_return"].to_numpy(float), index=entry_index)
    turnover_series = pd.Series(
        daily["full_turnover"].to_numpy(float),
        index=entry_index,
    )
    summary: dict[str, object] = performance_summary(
        net,
        full_turnover=turnover_series,
        gross_returns=gross,
        periods_per_year=settings.periods_per_year,
    )
    summary.update(_ic_summary(daily["pearson_ic"], "pearson_ic"))
    summary.update(_ic_summary(daily["rank_ic"], "rank_ic"))
    summary.update(
        {
            "cost_bps": settings.cost_bps,
            "band_bps": settings.band_bps,
            "long_fraction": settings.long_fraction,
            "short_fraction": settings.short_fraction,
            "target_gross_exposure": settings.long_gross + settings.short_gross,
            "target_net_exposure": settings.long_gross - settings.short_gross,
            "timing_contract": (
                "latest_factor_input_timestamp < entry_timestamp < exit_timestamp"
            ),
        }
    )
    return ResearchResult(
        daily=daily,
        weight_ledger=ledger,
        summary=summary,
    )
