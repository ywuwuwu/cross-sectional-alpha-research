#!/usr/bin/env python3
"""Build public-safe aggregate results from a clean private snapshot.

The builder validates the private snapshot manifest and Git provenance before
writing aggregate CSVs and figures. Security identifiers, weights, factor
values, raw market data, local paths, and private formulas are excluded.
The detailed build record is generated locally and ignored by Git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
for module_dir in (PROJECT_ROOT / "src", PROJECT_ROOT / "examples"):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from alpha_research import paired_moving_block_bootstrap  # noqa: E402
from render_public_results import render  # noqa: E402


BASELINE = "UBL_ONLY"
SELECTED = "UBL_80_LOWVOL_60_20"
PUBLIC_PORTFOLIOS = [BASELINE, SELECTED]
REQUIRED_SOURCE_FILES = (
    "metrics.csv",
    "returns.csv",
    "costs.csv",
    "paired_bootstrap.csv",
    "paired_walk_forward_folds.csv",
    "paired_walk_forward_summary.csv",
    "pnl_concentration.csv",
    "execution_delay_metrics.csv",
    "config.json",
    "code_commit.txt",
    "source_environment.json",
    "snapshot_manifest.json",
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a stable public CSV representation."""
    frame.to_csv(path, index=False, float_format="%.12g")


def one(frame: pd.DataFrame, **criteria: object) -> pd.Series:
    """Select exactly one row using equality criteria."""
    selected = frame
    for column, value in criteria.items():
        selected = selected[selected[column] == value]
    if len(selected) != 1:
        raise ValueError(f"Expected one row for {criteria}, found {len(selected)}")
    return selected.iloc[0]


def git_output(repo: Path, *arguments: str) -> str:
    """Run one read-only Git command and return stripped stdout."""
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def clean_git_state(repo: Path, label: str) -> dict[str, Any]:
    """Return Git provenance, failing when the repository is dirty."""
    status = git_output(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if status:
        raise RuntimeError(
            f"Refusing to build evidence from a dirty {label} repository:\n{status}"
        )
    return {
        "commit": git_output(repo, "rev-parse", "HEAD"),
        "tree": git_output(repo, "rev-parse", "HEAD^{tree}"),
        "worktree_clean_before_generation": True,
    }


def parse_key_value_file(path: Path) -> dict[str, str]:
    """Parse a newline-delimited key=value provenance file."""
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            raise ValueError(f"Malformed provenance line in {path.name}: {line!r}")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_digest(value: object, label: str, length: int = 64) -> str:
    """Validate and return a lowercase hexadecimal digest."""
    text = str(value)
    if re.fullmatch(rf"[0-9a-f]{{{length}}}", text) is None:
        raise ValueError(f"Invalid {label}: {text!r}")
    return text


def validate_private_snapshot(source: Path) -> dict[str, Any]:
    """Verify snapshot hashes and clean private-source provenance."""
    source = source.resolve()
    missing = [name for name in REQUIRED_SOURCE_FILES if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Snapshot is missing required artifacts: {missing}")

    manifest_path = source / "snapshot_manifest.json"
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("Private snapshot manifest must be a nonempty list")

    recorded_paths: set[str] = set()
    for entry in entries:
        relative = Path(str(entry["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe private manifest path: {relative}")
        artifact = source / relative
        if not artifact.is_file():
            raise FileNotFoundError(f"Private manifest artifact is missing: {relative}")
        if artifact.stat().st_size != int(entry["bytes"]):
            raise ValueError(f"Private artifact size mismatch: {relative}")
        if sha256_file(artifact) != entry["sha256"]:
            raise ValueError(f"Private artifact hash mismatch: {relative}")
        recorded_paths.add(relative.as_posix())

    required_recorded = set(REQUIRED_SOURCE_FILES) - {"snapshot_manifest.json"}
    absent_from_manifest = sorted(required_recorded - recorded_paths)
    if absent_from_manifest:
        raise ValueError(
            "Required private artifacts are absent from snapshot_manifest.json: "
            f"{absent_from_manifest}"
        )

    commit_record = parse_key_value_file(source / "code_commit.txt")
    source_commit = validate_digest(commit_record.get("commit"), "source commit", 40)
    source_tree = validate_digest(commit_record.get("tree"), "source tree", 40)
    if commit_record.get("dirty", "").lower() != "false":
        raise RuntimeError("Private snapshot was generated from a dirty source tree")

    environment_path = source / "source_environment.json"
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    recorded_source = environment.get("source", {})
    if recorded_source.get("worktree_clean_before_generation") is not True:
        raise RuntimeError("Private source environment does not record a clean tree")
    if recorded_source.get("commit") != source_commit:
        raise ValueError("Private source commit records disagree")
    if recorded_source.get("tree") != source_tree:
        raise ValueError("Private source tree records disagree")

    private_repo = Path(git_output(source, "rev-parse", "--show-toplevel")).resolve()
    current_private = clean_git_state(private_repo, "private research source")
    if current_private["commit"] != source_commit:
        raise RuntimeError(
            "Private repository HEAD no longer matches the snapshot source commit"
        )
    if current_private["tree"] != source_tree:
        raise RuntimeError(
            "Private repository tree no longer matches the snapshot source tree"
        )

    contract = json.loads((source / "config.json").read_text(encoding="utf-8"))
    return {
        "snapshot_id": source.name,
        "commit": source_commit,
        "tree": source_tree,
        "worktree_clean_before_generation": True,
        "worktree_clean_at_public_curation": True,
        "snapshot_manifest_sha256": sha256_file(manifest_path),
        "snapshot_manifest_file_count": len(entries),
        "source_environment_sha256": sha256_file(environment_path),
        "configuration_sha256": sha256_file(source / "config.json"),
        "contract_sha256": validate_digest(
            environment.get("contract_sha256"), "contract hash"
        ),
        "config_hashes_sha256": validate_digest(
            environment.get("config_hashes_sha256"), "config collection hash"
        ),
        "dependency_lock_sha256": validate_digest(
            environment.get("dependency_lock_sha256"), "dependency lock hash"
        ),
        "python": environment.get("python"),
        "packages": environment.get("packages", {}),
        "contract_version": contract["contract"]["contract_version"],
    }


def curate_tables(source: Path, output: Path) -> list[Path]:
    """Write public portfolio-level tables into a staging directory."""
    output.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    metrics = pd.read_csv(source / "metrics.csv")
    public_metrics = metrics[
        metrics["track"].isin(PUBLIC_PORTFOLIOS)
        & metrics["split"].isin(["train", "validation", "research_holdout", "all"])
    ][
        [
            "track",
            "split",
            "observations",
            "net_total_return",
            "net_annualized_return",
            "net_sharpe_0rf",
            "net_max_drawdown",
            "average_full_turnover",
            "average_one_way_turnover",
            "break_even_cost_bps",
        ]
    ].sort_values(
        ["split", "track"]
    )
    path = output / "headline_metrics.csv"
    write_csv(public_metrics, path)
    created.append(path)

    returns = pd.read_csv(source / "returns.csv", parse_dates=["date"])
    selected_returns = returns[returns["track"].isin(PUBLIC_PORTFOLIOS)][
        ["date", "split", "track", "net_return", "full_turnover", "transaction_cost"]
    ]
    baseline = selected_returns[selected_returns["track"] == BASELINE].drop(
        columns="track"
    )
    blend = selected_returns[selected_returns["track"] == SELECTED].drop(
        columns="track"
    )
    public_returns = baseline.merge(
        blend,
        on=["date", "split"],
        suffixes=("_ubl", "_selected"),
        validate="one_to_one",
    ).sort_values("date")
    public_returns = public_returns.rename(
        columns={
            "net_return_ubl": "ubl_net_return",
            "full_turnover_ubl": "ubl_full_turnover",
            "transaction_cost_ubl": "ubl_transaction_cost",
            "net_return_selected": "selected_net_return",
            "full_turnover_selected": "selected_full_turnover",
            "transaction_cost_selected": "selected_transaction_cost",
        }
    )
    if len(public_returns) != 424:
        raise ValueError(
            f"Expected 424 common portfolio return rows, found {len(public_returns)}"
        )
    path = output / "portfolio_returns.csv"
    write_csv(public_returns, path)
    created.append(path)

    costs = pd.read_csv(source / "costs.csv")
    public_costs = costs[
        costs["portfolio"].isin(PUBLIC_PORTFOLIOS)
        & (costs["split"] == "all")
        & costs["cost_bps"].isin([5.0, 10.0, 15.0, 20.0])
    ][
        [
            "portfolio",
            "cost_bps",
            "net_total_return",
            "net_sharpe_0rf",
            "net_max_drawdown",
            "average_full_turnover",
        ]
    ].sort_values(
        ["portfolio", "cost_bps"]
    )
    path = output / "cost_sensitivity.csv"
    write_csv(public_costs, path)
    created.append(path)

    folds = pd.read_csv(source / "paired_walk_forward_folds.csv")
    public_folds = folds[
        (folds["pair"] == SELECTED) & folds["portfolio"].isin(PUBLIC_PORTFOLIOS)
    ][
        [
            "fold",
            "test_start",
            "test_end",
            "portfolio",
            "net_total_return",
            "net_sharpe_0rf",
            "net_max_drawdown",
        ]
    ].sort_values(
        ["fold", "portfolio"]
    )
    path = output / "walk_forward_folds.csv"
    write_csv(public_folds, path)
    created.append(path)

    bootstrap = pd.read_csv(source / "paired_bootstrap.csv")
    public_bootstrap = bootstrap[
        bootstrap["sample"] == "research_holdout_common"
    ].copy()
    path = output / "bootstrap_method_summary.csv"
    write_csv(public_bootstrap, path)
    created.append(path)

    holdout = public_returns[public_returns["split"] == "research_holdout"].set_index(
        "date"
    )
    draws = paired_moving_block_bootstrap(
        holdout["ubl_net_return"],
        holdout["selected_net_return"],
        block_length=5,
        resamples=5_000,
        seed=20_260_721,
    )
    path = output / "bootstrap_sharpe_differences.csv"
    write_csv(draws[["sharpe_difference"]], path)
    created.append(path)

    concentration = pd.read_csv(source / "pnl_concentration.csv")
    public_concentration = concentration[
        (concentration["split"] == "all")
        & concentration["portfolio"].isin(PUBLIC_PORTFOLIOS)
    ][
        [
            "portfolio",
            "observations",
            "total_arithmetic_net_pnl",
            "top_five_day_net_pnl",
            "top_five_day_pnl_share",
        ]
    ].sort_values(
        "portfolio"
    )
    path = output / "pnl_concentration.csv"
    write_csv(public_concentration, path)
    created.append(path)

    walk_summary = pd.read_csv(source / "paired_walk_forward_summary.csv")
    selected_walk = one(walk_summary, portfolio=SELECTED, pair=SELECTED)
    delay = pd.read_csv(source / "execution_delay_metrics.csv")
    selected_delay = one(
        delay,
        portfolio=SELECTED,
        split="all",
        scenario="entry_delayed_one_additional_day",
    )
    selected_validation = one(metrics, track=SELECTED, split="validation")
    selected_all = one(metrics, track=SELECTED, split="all")
    selected_cost_15 = one(
        costs,
        portfolio=SELECTED,
        split="all",
        cost_bps=15.0,
    )
    robustness = pd.DataFrame(
        [
            {
                "check": "validation_net_sharpe",
                "value": selected_validation["net_sharpe_0rf"],
                "sample": "validation",
            },
            {
                "check": "full_common_net_sharpe",
                "value": selected_all["net_sharpe_0rf"],
                "sample": "all common dates",
            },
            {
                "check": "net_sharpe_at_15bps",
                "value": selected_cost_15["net_sharpe_0rf"],
                "sample": "all common dates",
            },
            {
                "check": "paired_walk_forward_sharpe",
                "value": selected_walk["net_sharpe_0rf"],
                "sample": "4 paired folds",
            },
            {
                "check": "positive_walk_forward_folds",
                "value": selected_walk["positive_fold_count"],
                "sample": "out of 4",
            },
            {
                "check": "one_day_delay_sharpe",
                "value": selected_delay["net_sharpe_0rf"],
                "sample": "all common delayed dates",
            },
        ]
    )
    path = output / "robustness_summary.csv"
    write_csv(robustness, path)
    created.append(path)
    return created


def install_staged_files(staging_root: Path, output_root: Path) -> list[Path]:
    """Atomically replace the audited public artifact set."""
    staged = sorted(path for path in staging_root.rglob("*") if path.is_file())
    installed: list[Path] = []
    for source in staged:
        relative = source.relative_to(staging_root)
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        shutil.copy2(source, temporary)
        temporary.replace(destination)
        installed.append(destination)
    return installed


def build(source: Path, output_root: Path) -> list[Path]:
    """Validate provenance, build aggregate evidence, and install atomically."""
    public_state = clean_git_state(PROJECT_ROOT, "public")
    private_state = validate_private_snapshot(source)
    output_root = output_root.resolve()
    try:
        output_root.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Public output must remain inside this repository") from exc

    with tempfile.TemporaryDirectory(prefix="public_alpha_evidence_") as temporary:
        staging_root = Path(temporary) / "ubl_lowvol_study"
        data_dir = staging_root / "data"
        created_data = curate_tables(source.resolve(), data_dir)
        created_plots = render(staging_root)

        files = {
            path.relative_to(staging_root).as_posix(): sha256_file(path)
            for path in [*created_data, *created_plots]
        }
        manifest = {
            "source_snapshot_id": private_state.pop("snapshot_id"),
            "contract_version": private_state.pop("contract_version"),
            "source_worktree_was_dirty": False,
            "research_source": {
                "visibility": "private",
                **private_state,
            },
            "public_curation": {
                **public_state,
                "builder": "tools/build_public_evidence.py",
                "builder_sha256": sha256_file(Path(__file__)),
                "renderer": "examples/render_public_results.py",
                "renderer_sha256": sha256_file(
                    PROJECT_ROOT / "examples" / "render_public_results.py"
                ),
            },
            "public_scope": "aggregate portfolio evidence only",
            "excluded": [
                "raw market data",
                "security identifiers and weights",
                "factor values and private UBL formulas",
                "local filesystem paths",
                "private strategy implementation and research engine",
            ],
            "files": files,
        }
        serialized = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        if str(Path.home()) in serialized or str(source.resolve()) in serialized:
            raise RuntimeError("Local audit manifest contains a private local path")
        manifest_path = data_dir / "evidence_manifest.json"
        manifest_path.write_text(serialized, encoding="utf-8")
        return install_staged_files(staging_root, output_root)


def main() -> int:
    """Run the command-line public evidence build."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Clean immutable private snapshot to curate.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("examples/sample_outputs/ubl_lowvol_study"),
    )
    args = parser.parse_args()
    for path in build(args.source, args.output_root):
        print(path.relative_to(PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
