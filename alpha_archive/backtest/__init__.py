"""Backtest engine: signal evaluation, IC report, DSR, walk-forward."""
from .ic_report import compute_ic_report, ICReport
from .dsr import deflated_sharpe_ratio
from .runner import run_signal_backtest, BacktestResult

__all__ = [
    "compute_ic_report", "ICReport",
    "deflated_sharpe_ratio",
    "run_signal_backtest", "BacktestResult",
]
