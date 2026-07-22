"""Performance metrics and paired resampling for return-series comparisons."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _returns(values: pd.Series, name: str = "returns") -> pd.Series:
    if not isinstance(values, pd.Series):
        values = pd.Series(values, dtype=float)
    result = values.astype(float).dropna()
    if result.empty:
        raise ValueError(f"{name} cannot be empty")
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError(f"{name} contains infinite values")
    if (result <= -1.0).any():
        raise ValueError(f"{name} contains a return at or below -100%")
    return result


def annualized_sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized zero-hurdle Sharpe using sample volatility."""
    values = _returns(returns)
    if len(values) < 2:
        return float("nan")
    volatility = float(values.std(ddof=1))
    if volatility <= 0:
        return float("nan")
    return math.sqrt(periods_per_year) * float(values.mean()) / volatility


def drawdown_series(returns: pd.Series) -> pd.Series:
    """Return drawdowns from the running peak of compounded wealth."""
    values = _returns(returns)
    wealth = (1.0 + values).cumprod()
    peak = (
        pd.concat([pd.Series([1.0]), wealth.reset_index(drop=True)]).cummax().iloc[1:]
    )
    result = wealth.to_numpy() / peak.to_numpy() - 1.0
    return pd.Series(result, index=values.index, name="drawdown")


def max_drawdown(returns: pd.Series) -> float:
    """Return maximum drawdown as a positive fraction."""
    return float(-drawdown_series(returns).min())


def performance_summary(
    net_returns: pd.Series,
    *,
    full_turnover: pd.Series | None = None,
    gross_returns: pd.Series | None = None,
    periods_per_year: int = 252,
) -> dict[str, float | int]:
    """Summarize a daily net return path with standardized conventions."""
    net = _returns(net_returns, "net_returns")
    observations = len(net)
    total_return = float((1.0 + net).prod() - 1.0)
    annualized_return = float(
        (1.0 + total_return) ** (periods_per_year / observations) - 1.0
    )
    summary: dict[str, float | int] = {
        "observations": observations,
        "net_total_return": total_return,
        "net_annualized_return": annualized_return,
        "net_sharpe_0rf": annualized_sharpe(net, periods_per_year),
        "net_max_drawdown": max_drawdown(net),
    }
    if full_turnover is not None:
        turnover = full_turnover.reindex(net.index).astype(float)
        if turnover.isna().any() or (turnover < 0).any():
            raise ValueError("full_turnover must be nonnegative and aligned")
        summary["average_full_turnover"] = float(turnover.mean())
        summary["average_one_way_turnover"] = float(turnover.mean() / 2.0)
        if gross_returns is not None and turnover.mean() > 0:
            gross = gross_returns.reindex(net.index).astype(float)
            if gross.isna().any():
                raise ValueError("gross_returns must align with net_returns")
            summary["break_even_cost_bps"] = float(
                gross.mean() / turnover.mean() * 10_000.0
            )
    return summary


def _moving_block_indices(
    observations: int,
    block_length: int,
    resamples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    blocks = math.ceil(observations / block_length)
    starts = rng.integers(0, observations - block_length + 1, size=(resamples, blocks))
    pieces = [starts + offset for offset in range(block_length)]
    return np.stack(pieces, axis=2).reshape(resamples, -1)[:, :observations]


def _vector_sharpe(values: np.ndarray, periods_per_year: int) -> np.ndarray:
    volatility = values.std(axis=1, ddof=1)
    result = np.full(len(values), np.nan)
    valid = volatility > 0
    result[valid] = (
        math.sqrt(periods_per_year) * values[valid].mean(axis=1) / volatility[valid]
    )
    return result


def paired_moving_block_bootstrap(
    baseline_returns: pd.Series,
    candidate_returns: pd.Series,
    *,
    block_length: int = 5,
    resamples: int = 5_000,
    seed: int = 20_260_721,
    periods_per_year: int = 252,
) -> pd.DataFrame:
    """Resample aligned paths and return paired Sharpe differences.

    The same moving-block indices are applied to both paths. This preserves
    their observed same-date dependence and supports direct strategy deltas.
    """
    joined = pd.concat(
        [baseline_returns.rename("baseline"), candidate_returns.rename("candidate")],
        axis=1,
        join="inner",
    ).dropna()
    if len(joined) < 2:
        raise ValueError("paired bootstrap requires at least two aligned observations")
    if block_length < 1 or block_length > len(joined):
        raise ValueError("block_length must be between one and sample length")
    if resamples < 1:
        raise ValueError("resamples must be positive")
    rng = np.random.default_rng(seed)
    indices = _moving_block_indices(len(joined), block_length, resamples, rng)
    baseline = _vector_sharpe(
        joined["baseline"].to_numpy(float)[indices], periods_per_year
    )
    candidate = _vector_sharpe(
        joined["candidate"].to_numpy(float)[indices], periods_per_year
    )
    return pd.DataFrame(
        {
            "baseline_sharpe": baseline,
            "candidate_sharpe": candidate,
            "sharpe_difference": candidate - baseline,
        }
    )
