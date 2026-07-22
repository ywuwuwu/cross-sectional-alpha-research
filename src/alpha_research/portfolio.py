"""Security-weight portfolio construction and transaction-cost accounting."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def _validated_series(values: pd.Series, name: str) -> pd.Series:
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas Series indexed by security")
    result = values.astype(float)
    if result.index.has_duplicates:
        raise ValueError(f"{name} contains duplicate security identifiers")
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError(f"{name} contains NaN or infinite values")
    return result


def normalize_dollar_neutral(
    weights: pd.Series,
    *,
    long_gross: float = 1.0,
    short_gross: float = 1.0,
) -> pd.Series:
    """Scale positive and negative weights to fixed long and short gross exposure.

    The default result has long gross ``+1``, short gross ``-1``, net exposure
    zero, and total gross exposure two. Both sides must be present.
    """
    values = _validated_series(weights, "weights")
    if long_gross <= 0 or short_gross <= 0:
        raise ValueError("long_gross and short_gross must be positive")
    positive = values.clip(lower=0.0)
    negative = -values.clip(upper=0.0)
    if positive.sum() <= 0 or negative.sum() <= 0:
        raise ValueError("dollar-neutral normalization requires long and short names")
    return positive * (long_gross / positive.sum()) - negative * (
        short_gross / negative.sum()
    )


def combine_sleeves(
    sleeves: Mapping[str, pd.Series],
    *,
    risk_budgets: Mapping[str, float],
    training_volatility: Mapping[str, float],
    long_gross: float = 1.0,
    short_gross: float = 1.0,
) -> pd.Series:
    """Volatility-scale sleeves, combine security weights, then normalize.

    Costs must be applied after this function to the final aggregate weight
    changes. Averaging standalone net-return series would miss trade netting.
    Volatility estimates and risk budgets must be fixed before evaluation.
    """
    if not sleeves:
        raise ValueError("at least one sleeve is required")
    keys = set(sleeves)
    if keys != set(risk_budgets) or keys != set(training_volatility):
        raise ValueError(
            "sleeves, risk_budgets, and training_volatility must use identical keys"
        )
    if any(float(risk_budgets[key]) < 0 for key in keys):
        raise ValueError("risk budgets cannot be negative")
    if sum(float(risk_budgets[key]) for key in keys) <= 0:
        raise ValueError("risk budgets must have positive total weight")

    validated = {
        key: _validated_series(value, f"sleeve {key}") for key, value in sleeves.items()
    }
    index = pd.Index([])
    for values in validated.values():
        index = index.union(values.index, sort=False)
    combined = pd.Series(0.0, index=index, dtype=float)
    for key, values in validated.items():
        volatility = float(training_volatility[key])
        if not np.isfinite(volatility) or volatility <= 0:
            raise ValueError(f"training volatility for {key!r} must be positive")
        coefficient = float(risk_budgets[key]) / volatility
        combined = combined.add(values.reindex(index, fill_value=0.0) * coefficient)
    return normalize_dollar_neutral(
        combined, long_gross=long_gross, short_gross=short_gross
    )


def apply_weight_change_band(
    target: pd.Series,
    previous: pd.Series | None = None,
    *,
    band_bps: float = 7.5,
    renormalize: bool = True,
    long_gross: float = 1.0,
    short_gross: float = 1.0,
) -> pd.Series:
    """Retain prior weights when requested changes fall inside a no-trade band.

    ``band_bps`` is measured in absolute portfolio-weight basis points. New and
    removed securities are aligned to zero before the rule is applied. When
    ``renormalize`` is true, the requested long and short gross exposures are
    restored after applying the band.
    """
    target_values = _validated_series(target, "target")
    if band_bps < 0:
        raise ValueError("band_bps cannot be negative")
    previous_values = (
        pd.Series(0.0, index=target_values.index)
        if previous is None
        else _validated_series(previous, "previous")
    )
    index = target_values.index.union(previous_values.index, sort=False)
    aligned_target = target_values.reindex(index, fill_value=0.0)
    aligned_previous = previous_values.reindex(index, fill_value=0.0)
    threshold = float(band_bps) / 10_000.0
    result = aligned_target.where(
        (aligned_target - aligned_previous).abs() >= threshold,
        aligned_previous,
    )
    result = result[result.abs() > 1e-15]
    if not renormalize:
        return result
    return normalize_dollar_neutral(
        result,
        long_gross=long_gross,
        short_gross=short_gross,
    )


def full_turnover(current: pd.Series, previous: pd.Series | None = None) -> float:
    """Return ``sum(abs(w_t - w_t-1))`` on the union of securities."""
    current_values = _validated_series(current, "current")
    previous_values = (
        pd.Series(dtype=float)
        if previous is None
        else _validated_series(previous, "previous")
    )
    index = current_values.index.union(previous_values.index, sort=False)
    change = current_values.reindex(index, fill_value=0.0) - previous_values.reindex(
        index, fill_value=0.0
    )
    return float(change.abs().sum())


def one_way_turnover(current: pd.Series, previous: pd.Series | None = None) -> float:
    """Return half of full turnover for a conventionally scaled two-sided book."""
    return 0.5 * full_turnover(current, previous)


def transaction_cost(turnover: float, cost_bps: float) -> float:
    """Calculate cost as full turnover times basis points per dollar traded."""
    if turnover < 0 or cost_bps < 0:
        raise ValueError("turnover and cost_bps cannot be negative")
    return float(turnover) * float(cost_bps) / 10_000.0


def portfolio_return(
    weights: pd.Series,
    security_returns: pd.Series,
    *,
    missing: str = "raise",
) -> float:
    """Calculate ``sum(weight_i * return_i)`` with an explicit missing policy."""
    weight_values = _validated_series(weights, "weights")
    return_values = security_returns.astype(float)
    if return_values.index.has_duplicates:
        raise ValueError("security_returns contains duplicate security identifiers")
    aligned = return_values.reindex(weight_values.index)
    if aligned.isna().any():
        missing_names = aligned.index[aligned.isna()].tolist()[:5]
        if missing == "raise":
            raise ValueError(f"missing security returns for {missing_names}")
        if missing != "zero":
            raise ValueError("missing must be either 'raise' or 'zero'")
        aligned = aligned.fillna(0.0)
    if not np.isfinite(aligned.to_numpy()).all():
        raise ValueError("security_returns contains infinite values")
    return float(weight_values.dot(aligned))
