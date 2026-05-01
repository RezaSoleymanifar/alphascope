"""End-to-end signal backtest runner.

Inputs:
    signal_fn: callable(prices: DataFrame) -> DataFrame[date x ticker]
    universe, start, end, horizon_days, cost_bps, n_trials_for_dsr

Outputs: BacktestResult with IC report + DSR + portfolio stats + verdict.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable, Optional

import numpy as np
import pandas as pd

from ..data import load_price_panel, load_universe, compute_returns
from .ic_report import compute_ic_report, ICReport
from .dsr import deflated_sharpe_ratio


@dataclass
class BacktestResult:
    signal_name: str
    universe: str
    start: str
    end: str
    horizon_days: int
    cost_bps: float

    ic_report: ICReport
    dsr: dict

    sharpe: float
    ann_return: float
    ann_vol: float
    max_drawdown: float
    calmar: float
    turnover: float

    sharpe_oos: Optional[float] = None
    replication_score: Optional[float] = None

    verdict: str = "iterate"  # ship | iterate | kill
    verdict_reasoning: list[str] = field(default_factory=list)

    daily_returns: Optional[list[float]] = field(default=None, repr=False)


def long_top_quintile_long_short(signal: pd.DataFrame, top_pct: float = 0.20) -> pd.DataFrame:
    """For each rebalance, equal-weight long top quintile, short bottom quintile.
    Returns weights matrix [date x ticker]."""
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for d in signal.index:
        row = signal.loc[d].dropna()
        if len(row) < 10:
            continue
        n = max(5, int(len(row) * top_pct))
        long_idx = row.nlargest(n).index
        short_idx = row.nsmallest(n).index
        weights.loc[d, long_idx] = 0.5 / n
        weights.loc[d, short_idx] = -0.5 / n
    return weights


def long_top_quintile_long_only(signal: pd.DataFrame, top_pct: float = 0.20) -> pd.DataFrame:
    weights = pd.DataFrame(0.0, index=signal.index, columns=signal.columns)
    for d in signal.index:
        row = signal.loc[d].dropna()
        if len(row) < 5:
            continue
        n = max(5, int(len(row) * top_pct))
        long_idx = row.nlargest(n).index
        weights.loc[d, long_idx] = 1.0 / n
    return weights


def realized_returns_with_costs(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_bps: float,
) -> pd.Series:
    rets = compute_returns(prices).fillna(0.0)
    w = weights.reindex(rets.index, method="ffill").fillna(0.0).shift(1).fillna(0.0)
    port = (w * rets).sum(axis=1)
    turnover_per_day = w.diff().abs().sum(axis=1).fillna(0.0)
    costs = turnover_per_day * (cost_bps / 10_000)
    return port - costs


def perf_stats(rets: pd.Series) -> dict:
    r = rets.dropna()
    if len(r) == 0:
        return {}
    sharpe = (r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else float("nan")
    cum = (1 + r).cumprod()
    dd = cum / cum.cummax() - 1
    max_dd = float(dd.min())
    ann_ret = float((1 + r.mean()) ** 252 - 1)
    return {
        "sharpe": float(sharpe),
        "ann_return": ann_ret,
        "ann_vol": float(r.std() * np.sqrt(252)),
        "max_drawdown": max_dd,
        "calmar": ann_ret / abs(max_dd) if max_dd < 0 else float("nan"),
    }


def assign_verdict(
    ic: ICReport,
    dsr_res: dict,
    sharpe: float,
    sharpe_oos: float | None,
    replication_score: float | None = None,
) -> tuple[str, list[str]]:
    """Asymmetric verdict: bias toward 'iterate' to avoid false negatives.
    Only 'ship' if all gates pass; only 'kill' if multiple negatives.
    """
    reasons = []

    dsr_val = dsr_res.get("dsr", float("nan"))
    significant = dsr_res.get("significant_at_5pct", False)
    icir = ic.icir

    ship_gates = [
        ("DSR > 0.95", dsr_val > 0.95),
        ("ICIR > 0.3", icir is not None and not np.isnan(icir) and icir > 0.3),
        ("OOS Sharpe >= 0.5 * IS Sharpe", sharpe_oos is None or sharpe_oos >= 0.5 * sharpe),
        ("IC sign correct (positive)", ic.ic_mean is not None and ic.ic_mean > 0),
    ]
    if all(passed for _, passed in ship_gates):
        return "ship", [f"PASS {g}" for g, _ in ship_gates]

    kill_gates = [
        ("DSR < 0.5", dsr_val < 0.5),
        ("OOS Sharpe < 0", sharpe_oos is not None and sharpe_oos < 0),
        ("ICIR < 0.1", icir is not None and not np.isnan(icir) and icir < 0.1),
    ]
    kills = [g for g, p in kill_gates if p]
    if len(kills) >= 2:
        reasons = [f"FAIL {g}" for g in kills]
        return "kill", reasons

    # Default: iterate
    reasons = [
        ("PASS " if p else "FAIL ") + g for g, p in ship_gates
    ]
    return "iterate", reasons


def run_signal_backtest(
    signal_fn: Callable[[pd.DataFrame], pd.DataFrame],
    *,
    signal_name: str = "unnamed",
    universe: str = "sp500",
    start: str = "2014-01-01",
    end: str = "2026-04-01",
    horizon_days: int = 21,
    cost_bps: float = 5.0,
    n_trials_for_dsr: int = 1,
    rebal_freq: str = "ME",
    top_pct: float = 0.20,
    long_only: bool = False,
    expected_sharpe: tuple[float, float] | None = None,
    sector_map: pd.Series | None = None,
    oos_split_date: str | None = None,
) -> BacktestResult:
    """Standardized backtest pipeline.
    Returns BacktestResult with IC + DSR + verdict.
    """
    tickers = load_universe(universe)
    prices = load_price_panel(tickers=tickers, start=start, end=end).ffill(limit=5)
    prices = prices.dropna(how="all", axis=1)
    if prices.shape[1] == 0:
        raise RuntimeError(f"no usable tickers in universe={universe}")

    # Compute signal panel (signal_fn returns daily-or-rebalance signal)
    signal = signal_fn(prices)

    # Resample signal to rebalance frequency
    rebal_dates = pd.date_range(prices.index[0], prices.index[-1], freq=rebal_freq)
    rebal_dates = rebal_dates[rebal_dates.isin(prices.index)]
    sig_at_rebal = signal.reindex(rebal_dates, method="ffill")

    # Forward returns at horizon
    fr = (prices.shift(-horizon_days) / prices) - 1
    fr_at_rebal = fr.reindex(rebal_dates)

    # IC report
    ic = compute_ic_report(sig_at_rebal, fr_at_rebal, sector_map=sector_map)

    # Build portfolio weights + realize returns
    if long_only:
        weights = long_top_quintile_long_only(sig_at_rebal, top_pct=top_pct)
    else:
        weights = long_top_quintile_long_short(sig_at_rebal, top_pct=top_pct)

    daily_rets = realized_returns_with_costs(prices, weights, cost_bps)

    stats = perf_stats(daily_rets)

    # OOS split
    sharpe_oos = None
    if oos_split_date:
        oos_rets = daily_rets[daily_rets.index >= oos_split_date]
        if len(oos_rets) > 30:
            sharpe_oos = perf_stats(oos_rets).get("sharpe")

    # DSR
    dsr_res = deflated_sharpe_ratio(
        observed_sharpe=stats.get("sharpe", 0.0),
        returns=daily_rets.dropna().values,
        n_trials=n_trials_for_dsr,
        annualization=np.sqrt(252),
    )

    # Replication score
    rep_score = None
    if expected_sharpe is not None:
        lo, hi = expected_sharpe
        mid = (lo + hi) / 2
        if mid > 0:
            rep_score = stats.get("sharpe", 0.0) / mid

    # Verdict
    verdict, reasons = assign_verdict(
        ic=ic, dsr_res=dsr_res,
        sharpe=stats.get("sharpe", 0.0),
        sharpe_oos=sharpe_oos,
        replication_score=rep_score,
    )

    # Turnover
    turnover = float(weights.diff().abs().sum(axis=1).mean())

    return BacktestResult(
        signal_name=signal_name,
        universe=universe,
        start=start,
        end=end,
        horizon_days=horizon_days,
        cost_bps=cost_bps,
        ic_report=ic,
        dsr=dsr_res,
        sharpe=stats.get("sharpe", float("nan")),
        ann_return=stats.get("ann_return", float("nan")),
        ann_vol=stats.get("ann_vol", float("nan")),
        max_drawdown=stats.get("max_drawdown", float("nan")),
        calmar=stats.get("calmar", float("nan")),
        turnover=turnover,
        sharpe_oos=sharpe_oos,
        replication_score=rep_score,
        verdict=verdict,
        verdict_reasoning=reasons,
        daily_returns=daily_rets.dropna().tolist(),
    )
