#!/usr/bin/env python3
"""
Research backtest runner for the factor_mining framework.

Examples:
    python run_research_backtest.py --strategy utr --start 2020-03-02 --end 2020-06-01

    python run_research_backtest.py --strategy ubl --top-n 50 --rebalance-freq month_start \
        --strategy-param candle_window_short=5 --strategy-param candle_window_long=20

    python run_research_backtest.py --strategy momentum --grid-param period=5,10,20 \
        --grid-param top_n=20,50 --start 2020-03-02 --end 2020-12-31
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Tuple

import pandas as pd
import visualizer

PROJECT_DIR = Path(__file__).resolve().parent
FACTOR_MINING_DIR = PROJECT_DIR / "factor_mining"
if str(FACTOR_MINING_DIR) not in sys.path:
    sys.path.insert(0, str(FACTOR_MINING_DIR))

from backtest_engine_strategy import BacktestEngine
from cpv_strategy import CPVStrategy
from ctr_strategy import CTRStrategy
from ideal_reversal_strategy import IdealReversalStrategy
from PaperUBL_Strategy import PaperUBLStrategy
from strategy_base import MomentumStrategy, ReversalStrategy
from ubl_strategy import UBLStrategy
from utr_strategy import UTRStrategy
from volume_momentum_strategy import VolumeMomentumStrategy


DEFAULT_DATA_DIR = PROJECT_DIR / "data"
DEFAULT_MIN5_DIR = PROJECT_DIR / "data_5m"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "reports"


StrategyFactory = Callable[[Dict[str, Any], argparse.Namespace], Any]


def _build_ubl(params: Dict[str, Any], args: argparse.Namespace) -> UBLStrategy:
    strategy_params = visualizer.STRATEGY_CFG.copy()
    strategy_params["data_dir"] = str(args.data_dir)
    strategy_params.update(params)
    return UBLStrategy(**strategy_params)


def _build_paper_ubl(params: Dict[str, Any], args: argparse.Namespace) -> PaperUBLStrategy:
    params.setdefault("data_dir", str(args.data_dir))
    return PaperUBLStrategy(**params)


def _build_utr(params: Dict[str, Any], args: argparse.Namespace) -> UTRStrategy:
    params.setdefault("data_dir", str(args.data_dir))
    return UTRStrategy(**params)


def _build_ideal_reversal(
    params: Dict[str, Any], args: argparse.Namespace
) -> IdealReversalStrategy:
    use_multiprocessing = params.pop("use_multiprocessing", None)
    num_workers = params.pop("num_workers", None)
    params.setdefault("data_dir", str(args.data_dir))
    strategy = IdealReversalStrategy(**params)
    if use_multiprocessing is not None:
        strategy.use_multiprocessing = bool(use_multiprocessing)
    if num_workers is not None:
        strategy.num_workers = int(num_workers)
    return strategy


def _build_cpv(params: Dict[str, Any], args: argparse.Namespace) -> CPVStrategy:
    use_ray = params.pop("use_ray", None)
    params.setdefault("data_dir", str(args.data_dir))
    params.setdefault("min5_dir", str(args.min5_dir))
    strategy = CPVStrategy(**params)
    if use_ray is not None:
        strategy.use_ray = bool(use_ray)
    return strategy


def _build_ctr(params: Dict[str, Any], args: argparse.Namespace) -> CTRStrategy:
    params.setdefault("data_dir", str(args.data_dir))
    params.setdefault("min5_dir", str(args.min5_dir))
    return CTRStrategy(**params)


def _build_volume_momentum(params: Dict[str, Any], args: argparse.Namespace) -> VolumeMomentumStrategy:
    params.setdefault("data_dir", str(args.data_dir))
    params.setdefault("min5_dir", str(args.min5_dir))
    return VolumeMomentumStrategy(**params)


def _build_momentum(params: Dict[str, Any], args: argparse.Namespace) -> MomentumStrategy:
    return MomentumStrategy(**params)


def _build_reversal(params: Dict[str, Any], args: argparse.Namespace) -> ReversalStrategy:
    return ReversalStrategy(**params)


STRATEGIES: Dict[str, StrategyFactory] = {
    "ubl": _build_ubl,
    "paper_ubl": _build_paper_ubl,
    "PaperUBL_Strategy": _build_paper_ubl,
    "utr": _build_utr,
    "ideal_reversal": _build_ideal_reversal,
    "ideal": _build_ideal_reversal,
    "cpv": _build_cpv,
    "ctr": _build_ctr,
    "volume_momentum": _build_volume_momentum,
    "momentum": _build_momentum,
    "reversal": _build_reversal,
}

ENGINE_PARAM_NAMES = {
    "top_n",
    "rebalance_freq",
    "enable_cost",
    "calculate_ic",
    "n_groups",
    "initial_capital",
    "commission_rate",
    "slippage_rate",
    "stamp_duty",
    "risk_free_rate",
}

METRIC_COLUMNS = [
    "run_id",
    "strategy",
    "start_date",
    "end_date",
    "top_n",
    "rebalance_freq",
    "enable_cost",
    "n_groups",
    "total_return",
    "annual_return",
    "annual_volatility",
    "sharpe_ratio",
    "max_drawdown",
    "calmar_ratio",
    "win_rate",
    "best_day",
    "worst_day",
    "ic_mean",
    "ic_std",
    "ir",
    "ic_win_rate",
    "total_cost",
    "trade_count",
    "avg_turnover",
    "final_nav",
]


def parse_value(raw: str) -> Any:
    text = raw.strip()
    lowered = text.lower()
    if lowered in {"true", "yes", "y", "on"}:
        return True
    if lowered in {"false", "no", "n", "off"}:
        return False
    if lowered in {"none", "null"}:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


def parse_key_values(items: Iterable[str]) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected KEY=VALUE, got {item!r}")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key in {item!r}")
        parsed[key] = parse_value(raw_value)
    return parsed


def parse_grid(items: Iterable[str]) -> List[Tuple[str, List[Any]]]:
    grid: List[Tuple[str, List[Any]]] = []
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected KEY=V1,V2,..., got {item!r}")
        key, raw_values = item.split("=", 1)
        values = [parse_value(v) for v in raw_values.split(",") if v.strip()]
        if not key.strip() or not values:
            raise ValueError(f"Invalid grid parameter {item!r}")
        grid.append((key.strip(), values))
    return grid


def expand_grid(base: Dict[str, Any], grid: List[Tuple[str, List[Any]]]) -> List[Dict[str, Any]]:
    if not grid:
        return [base.copy()]
    keys = [item[0] for item in grid]
    values = [item[1] for item in grid]
    runs = []
    for combo in itertools.product(*values):
        params = base.copy()
        params.update(dict(zip(keys, combo)))
        runs.append(params)
    return runs


def split_params(params: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    engine_params = {}
    strategy_params = {}
    for key, value in params.items():
        if key in ENGINE_PARAM_NAMES:
            engine_params[key] = value
        else:
            strategy_params[key] = value
    return engine_params, strategy_params


def normalize_rebalance_freq(value: Any) -> Any:
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return int(text)
    return value


def clean_scalar(value: Any) -> Any:
    if isinstance(value, (pd.Series, pd.DataFrame)):
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass
    return value


def format_pct(value: Any) -> str:
    value = clean_scalar(value)
    if value is None:
        return "NA"
    return f"{float(value) * 100:.2f}%"


def format_float(value: Any, digits: int = 4) -> str:
    value = clean_scalar(value)
    if value is None:
        return "NA"
    return f"{float(value):.{digits}f}"


def safe_float(value: Any) -> Any:
    value = clean_scalar(value)
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def build_run_id(index: int, strategy_name: str, engine_params: Dict[str, Any], strategy_params: Dict[str, Any]) -> str:
    pieces = [f"{index:03d}", strategy_name]
    for key in sorted({**engine_params, **strategy_params}):
        if key in {"data_dir", "min5_dir"}:
            continue
        value = {**engine_params, **strategy_params}[key]
        text = str(value).replace("/", "-").replace(" ", "")
        pieces.append(f"{key}-{text}")
    run_id = "__".join(pieces)
    return "".join(ch if ch.isalnum() or ch in "._=-" else "-" for ch in run_id)


def make_engine(args: argparse.Namespace, engine_params: Dict[str, Any]) -> BacktestEngine:
    return BacktestEngine(
        data_dir=str(args.data_dir),
        initial_capital=float(engine_params.get("initial_capital", args.initial_capital)),
        commission_rate=float(engine_params.get("commission_rate", args.commission_rate)),
        slippage_rate=float(engine_params.get("slippage_rate", args.slippage_rate)),
        stamp_duty=float(engine_params.get("stamp_duty", args.stamp_duty)),
        risk_free_rate=float(engine_params.get("risk_free_rate", args.risk_free_rate)),
    )


def run_one(
    run_index: int,
    args: argparse.Namespace,
    strategy_factory: StrategyFactory,
    raw_params: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    engine_params, strategy_params = split_params(raw_params)
    engine = make_engine(args, engine_params)
    strategy = strategy_factory(strategy_params.copy(), args)

    top_n = int(engine_params.get("top_n", args.top_n))
    rebalance_freq = normalize_rebalance_freq(
        engine_params.get("rebalance_freq", args.rebalance_freq)
    )
    enable_cost = bool(engine_params.get("enable_cost", args.enable_cost))
    calculate_ic = bool(engine_params.get("calculate_ic", args.calculate_ic))
    n_groups = int(engine_params.get("n_groups", args.n_groups))

    run_id = build_run_id(run_index, args.strategy, {
        "top_n": top_n,
        "rebalance_freq": rebalance_freq,
        "enable_cost": enable_cost,
        "n_groups": n_groups,
    }, strategy_params)
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print(f"Run {run_index}: {run_id}")
    print(f"Strategy params: {json.dumps(strategy_params, ensure_ascii=False, sort_keys=True)}")
    print("=" * 80)

    report = engine.run(
        start_date=args.start,
        end_date=args.end,
        strategy=strategy,
        top_n=top_n,
        rebalance_freq=rebalance_freq,
        enable_cost=enable_cost,
        calculate_ic=calculate_ic,
        n_groups=n_groups,
    )
    if args.print_report:
        engine.print_report(report)

    save_report_artifacts(
        report=report,
        run_dir=run_dir,
        run_id=run_id,
        args=args,
        strategy_name=strategy.name,
        engine_params={
            "top_n": top_n,
            "rebalance_freq": rebalance_freq,
            "enable_cost": enable_cost,
            "calculate_ic": calculate_ic,
            "n_groups": n_groups,
        },
        strategy_params=strategy_params,
        make_plots=args.plots,
    )

    summary = summarize_run(
        report=report,
        run_id=run_id,
        args=args,
        strategy_name=strategy.name,
        engine_params={
            "top_n": top_n,
            "rebalance_freq": rebalance_freq,
            "enable_cost": enable_cost,
            "n_groups": n_groups,
        },
    )
    summary["run_dir"] = str(run_dir)
    summary["strategy_params"] = json.dumps(strategy_params, ensure_ascii=False, sort_keys=True)
    return summary


def summarize_run(
    report: Dict[str, Any],
    run_id: str,
    args: argparse.Namespace,
    strategy_name: str,
    engine_params: Dict[str, Any],
) -> Dict[str, Any]:
    cumulative = report.get("cumulative_returns", pd.Series(dtype=float))
    summary = {
        "run_id": run_id,
        "strategy": strategy_name,
        "start_date": args.start,
        "end_date": args.end,
        "top_n": engine_params["top_n"],
        "rebalance_freq": engine_params["rebalance_freq"],
        "enable_cost": engine_params["enable_cost"],
        "n_groups": engine_params["n_groups"],
        "final_nav": cumulative.iloc[-1] if not cumulative.empty else None,
    }
    for key in METRIC_COLUMNS:
        if key in summary:
            continue
        summary[key] = safe_float(report.get(key))
    return summary


def save_series(series: Any, path: Path, value_name: str) -> None:
    if series is None or getattr(series, "empty", True):
        return
    df = series.rename(value_name).reset_index()
    df.columns = ["date", value_name]
    df.to_csv(path, index=False)


def save_report_artifacts(
    report: Dict[str, Any],
    run_dir: Path,
    run_id: str,
    args: argparse.Namespace,
    strategy_name: str,
    engine_params: Dict[str, Any],
    strategy_params: Dict[str, Any],
    make_plots: bool,
) -> None:
    save_series(report.get("daily_returns"), run_dir / "daily_returns.csv", "daily_return")
    save_series(report.get("cumulative_returns"), run_dir / "cumulative_returns.csv", "nav")
    save_series(report.get("ic_series"), run_dir / "ic_series.csv", "ic")
    save_series(report.get("group_ls_returns"), run_dir / "group_long_short.csv", "long_short_return")

    group_returns = report.get("group_returns")
    if group_returns is not None and not group_returns.empty:
        group_returns.to_csv(run_dir / "group_returns.csv", index=False)

    metrics = {
        key: safe_float(value)
        for key, value in report.items()
        if not isinstance(value, (pd.Series, pd.DataFrame))
    }
    payload = {
        "run_id": run_id,
        "strategy": strategy_name,
        "start_date": args.start,
        "end_date": args.end,
        "engine_params": engine_params,
        "strategy_params": strategy_params,
        "metrics": metrics,
    }
    (run_dir / "config_and_metrics.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    visual_report = visualizer.generate_visual_report(
        report=report,
        run_dir=run_dir,
        make_plots=make_plots,
    )
    (run_dir / "report.md").write_text(
        build_markdown_report(payload, report, visual_report),
        encoding="utf-8",
    )


def build_markdown_report(
    payload: Dict[str, Any],
    report: Dict[str, Any],
    visual_report: Dict[str, Any] | None = None,
) -> str:
    metrics = payload["metrics"]
    lines = [
        f"# Backtest Report: {payload['run_id']}",
        "",
        "## Setup",
        "",
        f"- Strategy: {payload['strategy']}",
        f"- Period: {payload['start_date']} to {payload['end_date']}",
        f"- Engine params: `{json.dumps(payload['engine_params'], ensure_ascii=False, sort_keys=True)}`",
        f"- Strategy params: `{json.dumps(payload['strategy_params'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Performance",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total return | {format_pct(metrics.get('total_return'))} |",
        f"| Annual return | {format_pct(metrics.get('annual_return'))} |",
        f"| Annual volatility | {format_pct(metrics.get('annual_volatility'))} |",
        f"| Sharpe | {format_float(metrics.get('sharpe_ratio'))} |",
        f"| Max drawdown | {format_pct(metrics.get('max_drawdown'))} |",
        f"| Calmar | {format_float(metrics.get('calmar_ratio'))} |",
        f"| Win rate | {format_pct(metrics.get('win_rate'))} |",
        f"| Best day | {format_pct(metrics.get('best_day'))} |",
        f"| Worst day | {format_pct(metrics.get('worst_day'))} |",
        "",
        "## Factor Quality",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| IC mean | {format_float(metrics.get('ic_mean'))} |",
        f"| IC std | {format_float(metrics.get('ic_std'))} |",
        f"| IR | {format_float(metrics.get('ir'))} |",
        f"| IC win rate | {format_pct(metrics.get('ic_win_rate'))} |",
        "",
        "## Trading",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total cost | {format_float(metrics.get('total_cost'), 2)} |",
        f"| Trade count | {format_float(metrics.get('trade_count'), 0)} |",
        f"| Avg turnover | {format_pct(metrics.get('avg_turnover'))} |",
    ]
    group_ls = report.get("group_ls_returns")
    if group_ls is not None and not group_ls.empty:
        lines.extend([
            "",
            "## Group Long-Short",
            "",
            f"- Mean daily long-short return: {format_pct(group_ls.mean())}",
            f"- Daily long-short volatility: {format_pct(group_ls.std())}",
            f"- Observations: {len(group_ls)}",
        ])
    markdown = "\n".join(lines) + "\n"
    if visual_report is not None:
        markdown += visualizer.build_visualizer_markdown(visual_report)
    return markdown


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one or many factor_mining strategy backtests and save research reports."
    )
    parser.add_argument("--strategy", choices=sorted(STRATEGIES), default="ubl")
    parser.add_argument("--start", default=visualizer.BACKTEST_CFG["start_date"])
    parser.add_argument("--end", default=visualizer.BACKTEST_CFG["end_date"])
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--min5-dir", type=Path, default=DEFAULT_MIN5_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    parser.add_argument("--top-n", type=int, default=visualizer.BACKTEST_CFG["top_n"])
    parser.add_argument("--rebalance-freq", default=visualizer.BACKTEST_CFG["rebalance_freq"])
    parser.add_argument("--n-groups", type=int, default=visualizer.BACKTEST_CFG["n_groups"])
    parser.add_argument("--initial-capital", type=float, default=visualizer.ENGINE_CFG["initial_capital"])
    parser.add_argument("--commission-rate", type=float, default=visualizer.ENGINE_CFG["commission_rate"])
    parser.add_argument("--slippage-rate", type=float, default=visualizer.ENGINE_CFG["slippage_rate"])
    parser.add_argument("--stamp-duty", type=float, default=visualizer.ENGINE_CFG["stamp_duty"])
    parser.add_argument("--risk-free-rate", type=float, default=visualizer.ENGINE_CFG["risk_free_rate"])

    parser.add_argument("--no-cost", action="store_false", dest="enable_cost")
    parser.set_defaults(enable_cost=True)
    parser.add_argument("--no-ic", action="store_false", dest="calculate_ic")
    parser.set_defaults(calculate_ic=True)
    parser.add_argument("--no-plots", action="store_false", dest="plots")
    parser.set_defaults(plots=True)
    parser.add_argument("--print-report", action="store_true")

    parser.add_argument(
        "--strategy-param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Strategy parameter override. Repeatable, e.g. --strategy-param turnover_window=10",
    )
    parser.add_argument(
        "--grid-param",
        action="append",
        default=[],
        metavar="KEY=V1,V2",
        help=(
            "Sweep strategy or engine parameters. Repeatable. Engine keys include "
            "top_n, rebalance_freq, enable_cost, n_groups, commission_rate."
        ),
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)

    args.data_dir = args.data_dir.resolve()
    args.min5_dir = args.min5_dir.resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = (args.output_dir / f"{args.strategy}_{timestamp}").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        base_params = parse_key_values(args.strategy_param)
        grid = parse_grid(args.grid_param)
    except ValueError as exc:
        parser.error(str(exc))

    run_params = expand_grid(base_params, grid)
    strategy_factory = STRATEGIES[args.strategy]

    summaries = []
    for i, params in enumerate(run_params, start=1):
        summaries.append(run_one(i, args, strategy_factory, params, output_dir))

    summary_df = pd.DataFrame(summaries)
    ordered_cols = [c for c in METRIC_COLUMNS if c in summary_df.columns]
    remaining_cols = [c for c in summary_df.columns if c not in ordered_cols]
    summary_df = summary_df[ordered_cols + remaining_cols]
    summary_path = output_dir / "summary.csv"
    summary_df.to_csv(summary_path, index=False)

    rank_col = "sharpe_ratio" if "sharpe_ratio" in summary_df.columns else "total_return"
    ranked = summary_df.sort_values(rank_col, ascending=False, na_position="last")
    print("\n" + "=" * 80)
    print(f"Saved reports to: {output_dir}")
    print(f"Summary CSV: {summary_path}")
    print(f"Top runs by {rank_col}:")
    display_cols = ["run_id", "total_return", "annual_return", "sharpe_ratio", "max_drawdown", "ic_mean", "ir"]
    display_cols = [c for c in display_cols if c in ranked.columns]
    print(ranked[display_cols].head(10).to_string(index=False))
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
