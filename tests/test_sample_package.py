"""Tests for the small formula-agnostic alpha-research package."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alpha_research import (
    BacktestConfig,
    Visualizer,
    apply_weight_change_band,
    combine_sleeves,
    full_turnover,
    normalize_dollar_neutral,
    paired_moving_block_bootstrap,
    portfolio_return,
    run_cross_sectional_backtest,
    transaction_cost,
)


def make_toy_panel(observations: int = 4, assets: int = 8) -> pd.DataFrame:
    """Create a small panel with known positive score/return ordering."""
    calendar = pd.bdate_range("2021-01-04", periods=observations + 2)
    names = [f"A{index:02d}" for index in range(assets)]
    base_score = np.linspace(-1.0, 1.0, assets)
    frames = []
    for index in range(observations):
        score = base_score + index * 0.01
        frames.append(
            pd.DataFrame(
                {
                    "factor_date": calendar[index],
                    "latest_factor_input_timestamp": (
                        calendar[index] + pd.Timedelta(hours=16)
                    ),
                    "entry_timestamp": (calendar[index + 1] + pd.Timedelta(hours=10)),
                    "exit_timestamp": (calendar[index + 2] + pd.Timedelta(hours=10)),
                    "asset": names,
                    "alpha_score": score,
                    "forward_return": 0.01 * score + index * 0.0001,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def test_dollar_neutral_normalization_and_accounting() -> None:
    raw = pd.Series({"A": 3.0, "B": 1.0, "C": -2.0, "D": -1.0})
    weights = normalize_dollar_neutral(raw)
    assert weights[weights > 0].sum() == pytest.approx(1.0)
    assert weights[weights < 0].sum() == pytest.approx(-1.0)
    assert weights.abs().sum() == pytest.approx(2.0)
    realized = pd.Series({"A": 0.02, "B": 0.01, "C": -0.01, "D": 0.00})
    assert portfolio_return(weights, realized) == pytest.approx(weights.dot(realized))


def test_combine_before_costs_and_turnover_identity() -> None:
    first = normalize_dollar_neutral(
        pd.Series({"A": 2.0, "B": 1.0, "C": -1.0, "D": -2.0})
    )
    second = normalize_dollar_neutral(
        pd.Series({"A": -1.0, "B": 3.0, "C": -2.0, "D": 1.0})
    )
    combined = combine_sleeves(
        {"first": first, "second": second},
        risk_budgets={"first": 0.8, "second": 0.2},
        training_volatility={"first": 0.01, "second": 0.02},
    )
    assert combined.sum() == pytest.approx(0.0, abs=1e-12)
    assert combined.abs().sum() == pytest.approx(2.0)
    turnover = full_turnover(combined)
    assert turnover == pytest.approx(2.0)
    assert transaction_cost(turnover, 10.0) == pytest.approx(0.002)


def test_weight_change_band_retains_small_changes() -> None:
    previous = pd.Series({"A": 0.50, "B": 0.50, "C": -0.50, "D": -0.50})
    target = pd.Series({"A": 0.5002, "B": 0.4998, "C": -0.5002, "D": -0.4998})
    executed = apply_weight_change_band(
        target,
        previous,
        band_bps=7.5,
    )
    pd.testing.assert_series_equal(
        executed.sort_index(),
        previous.sort_index(),
    )


def test_runner_preserves_requested_exposure_with_band() -> None:
    result = run_cross_sectional_backtest(
        make_toy_panel(observations=2),
        BacktestConfig(
            long_fraction=0.25,
            short_fraction=0.25,
            band_bps=5.0,
            long_gross=0.60,
            short_gross=0.40,
        ),
    )
    assert np.allclose(result.daily["gross_exposure"], 1.0)
    assert np.allclose(result.daily["net_exposure"], 0.20)


def test_runner_enforces_timing_and_accounting_identities() -> None:
    result = run_cross_sectional_backtest(
        make_toy_panel(),
        BacktestConfig(
            long_fraction=0.25,
            short_fraction=0.25,
            cost_bps=10.0,
        ),
    )
    assert len(result.daily) == 4
    assert (
        result.daily["latest_factor_input_timestamp"] < result.daily["entry_timestamp"]
    ).all()
    assert (result.daily["entry_timestamp"] < result.daily["exit_timestamp"]).all()
    assert np.allclose(result.daily["gross_exposure"], 2.0)
    assert np.allclose(result.daily["net_exposure"], 0.0, atol=1e-12)

    ledger_sums = result.weight_ledger.groupby("factor_date").agg(
        executed_net=("executed_weight", "sum"),
        executed_gross=("executed_weight", lambda values: values.abs().sum()),
        gross_return=("gross_pnl_contribution", "sum"),
        cost=("cost_contribution", "sum"),
        net_return=("net_pnl_contribution", "sum"),
    )
    daily = result.daily.set_index("factor_date")
    assert np.allclose(ledger_sums["executed_net"], 0.0, atol=1e-12)
    assert np.allclose(ledger_sums["executed_gross"], 2.0)
    assert np.allclose(ledger_sums["gross_return"], daily["gross_return"])
    assert np.allclose(ledger_sums["cost"], daily["transaction_cost"])
    assert np.allclose(ledger_sums["net_return"], daily["net_return"])
    assert result.summary["rank_ic_mean"] == pytest.approx(1.0)


def test_runner_rejects_same_timestamp_factor_and_entry() -> None:
    panel = make_toy_panel()
    panel.loc[0, "latest_factor_input_timestamp"] = panel.loc[0, "entry_timestamp"]
    with pytest.raises(ValueError, match="latest factor input must precede entry"):
        run_cross_sectional_backtest(panel)


def test_paired_bootstrap_is_reproducible_and_preserves_pairing() -> None:
    rng = np.random.default_rng(3)
    baseline = pd.Series(rng.normal(0.0001, 0.01, 120))
    candidate = baseline + 0.0003
    first = paired_moving_block_bootstrap(
        baseline,
        candidate,
        block_length=5,
        resamples=250,
        seed=11,
    )
    second = paired_moving_block_bootstrap(
        baseline,
        candidate,
        block_length=5,
        resamples=250,
        seed=11,
    )
    pd.testing.assert_frame_equal(first, second)
    assert (first["sharpe_difference"] > 0).mean() > 0.95


def test_visualizer_saves_a_complete_synthetic_report(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    result = run_cross_sectional_backtest(
        make_toy_panel(observations=8),
        BacktestConfig(long_fraction=0.25, short_fraction=0.25),
    )
    paths = Visualizer(result).save_report(tmp_path)
    expected = {
        "daily",
        "weights",
        "summary",
        "report",
        "net_nav",
        "drawdown",
        "turnover",
        "rank_ic",
    }
    assert expected == set(paths)
    for path in paths.values():
        assert path.exists()
        assert path.stat().st_size > 0
    report = paths["report"].read_text(encoding="utf-8")
    assert "higher alpha_score means higher expected return" in report
    assert "latest_factor_input_timestamp < entry_timestamp" in report


def test_visualizer_writes_strict_json_for_unavailable_metrics(
    tmp_path: Path,
) -> None:
    result = run_cross_sectional_backtest(make_toy_panel(observations=1))
    path = Visualizer(result).save_report(tmp_path, make_plots=False)["summary"]
    serialized = path.read_text(encoding="utf-8")
    assert "NaN" not in serialized
    assert "Infinity" not in serialized
    assert json.loads(serialized)["net_sharpe_0rf"] is None


def test_public_plot_smoke() -> None:
    pytest.importorskip("matplotlib")
    from alpha_research.visualization import plot_net_nav

    index = pd.bdate_range("2021-01-01", periods=10)
    figure = plot_net_nav(
        pd.DataFrame(
            {
                "baseline": [0.001] * 10,
                "candidate": [0.002] * 10,
            },
            index=index,
        )
    )
    assert figure.axes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = PROJECT_ROOT / "examples" / "sample_outputs" / "ubl_lowvol_study"
PUBLIC_DATA = PUBLIC_ROOT / "data"


def test_public_metrics_match_committed_evidence() -> None:
    metrics = pd.read_csv(PUBLIC_DATA / "headline_metrics.csv")
    holdout = metrics[metrics["split"] == "research_holdout"].set_index("track")
    baseline = holdout.loc["UBL_ONLY"]
    selected = holdout.loc["UBL_80_LOWVOL_60_20"]
    assert int(baseline["observations"]) == 133
    assert int(selected["observations"]) == 133
    assert baseline["net_sharpe_0rf"] == pytest.approx(0.597460862991)
    assert selected["net_sharpe_0rf"] == pytest.approx(1.35837651655)
    assert baseline["net_total_return"] == pytest.approx(0.0209802804364)
    assert selected["net_total_return"] == pytest.approx(0.0486672370244)
    assert baseline["net_max_drawdown"] == pytest.approx(0.0481781677746)
    assert selected["net_max_drawdown"] == pytest.approx(0.0404615742380)
    assert baseline["average_full_turnover"] == pytest.approx(0.532030520977)
    assert selected["average_full_turnover"] == pytest.approx(0.462067502852)
    assert baseline["break_even_cost_bps"] == pytest.approx(13.1153381767)
    assert selected["break_even_cost_bps"] == pytest.approx(17.9306242732)

    draws = pd.read_csv(PUBLIC_DATA / "bootstrap_sharpe_differences.csv")
    assert len(draws) == 5_000
    assert (draws["sharpe_difference"] > 0).mean() == pytest.approx(0.952)


def test_public_evidence_manifest_hashes() -> None:
    manifest = json.loads(
        (PUBLIC_DATA / "evidence_manifest.json").read_text(encoding="utf-8")
    )
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((PUBLIC_ROOT / name).read_bytes()).hexdigest()
        assert actual == expected, name


def test_public_evidence_has_clean_reproducibility_provenance() -> None:
    manifest_path = PUBLIC_DATA / "evidence_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["source_worktree_was_dirty"] is False
    expected_snapshot = "20260722_ubl_lowvol_clean_provenance_v1"
    assert manifest["source_snapshot_id"] == expected_snapshot
    assert manifest["contract_version"] == "phase8_ubl_lowvol_portfolio_v1"

    source = manifest["research_source"]
    assert source["visibility"] == "private"
    assert source["worktree_clean_before_generation"] is True
    assert source["worktree_clean_at_public_curation"] is True
    assert source["snapshot_manifest_file_count"] == 55

    public = manifest["public_curation"]
    assert public["worktree_clean_before_generation"] is True
    assert public["builder"] == "tools/build_public_evidence.py"
    assert public["renderer"] == "examples/render_public_results.py"

    for record in (source, public):
        assert len(record["commit"]) == 40
        assert len(record["tree"]) == 40
        int(record["commit"], 16)
        int(record["tree"], 16)

    for key in (
        "snapshot_manifest_sha256",
        "source_environment_sha256",
        "configuration_sha256",
        "contract_sha256",
        "config_hashes_sha256",
        "dependency_lock_sha256",
    ):
        assert len(source[key]) == 64
        int(source[key], 16)

    assert (
        hashlib.sha256((PROJECT_ROOT / public["builder"]).read_bytes()).hexdigest()
        == public["builder_sha256"]
    )
    assert (
        hashlib.sha256((PROJECT_ROOT / public["renderer"]).read_bytes()).hexdigest()
        == public["renderer_sha256"]
    )

    serialized = manifest_path.read_text(encoding="utf-8")
    assert "/" + "home/" not in serialized
    assert "/" + "Users/" not in serialized
    assert len(manifest["files"]) == 14


def test_public_package_uses_only_declared_dependencies() -> None:
    package = Path(__file__).resolve().parents[1] / "src" / "alpha_research"
    allowed_roots = {
        "__future__",
        "collections",
        "dataclasses",
        "json",
        "math",
        "matplotlib",
        "numpy",
        "pandas",
        "pathlib",
        "typing",
    }
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
                assert roots <= allowed_roots, (path, roots - allowed_roots)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                root = (node.module or "").split(".", 1)[0]
                assert root in allowed_roots, (path, root)
