"""Small, formula-agnostic sample package for cross-sectional alpha research."""

from .metrics import (
    annualized_sharpe,
    drawdown_series,
    max_drawdown,
    paired_moving_block_bootstrap,
    performance_summary,
)
from .portfolio import (
    apply_weight_change_band,
    combine_sleeves,
    full_turnover,
    normalize_dollar_neutral,
    one_way_turnover,
    portfolio_return,
    transaction_cost,
)
from .runner import (
    REQUIRED_PANEL_COLUMNS,
    BacktestConfig,
    ResearchResult,
    run_cross_sectional_backtest,
    scores_to_quantile_weights,
    validate_research_panel,
)
from .visualization import Visualizer

__all__ = [
    "REQUIRED_PANEL_COLUMNS",
    "BacktestConfig",
    "ResearchResult",
    "Visualizer",
    "annualized_sharpe",
    "apply_weight_change_band",
    "combine_sleeves",
    "drawdown_series",
    "full_turnover",
    "max_drawdown",
    "normalize_dollar_neutral",
    "one_way_turnover",
    "paired_moving_block_bootstrap",
    "performance_summary",
    "portfolio_return",
    "run_cross_sectional_backtest",
    "scores_to_quantile_weights",
    "transaction_cost",
    "validate_research_panel",
]

__version__ = "0.2.0"
