"""Information Coefficient report card.

For a signal panel and forward-return panel:
    IC_t = Spearman_corr(signal_t, forward_return_t+horizon)

Reports:
    ic_mean, ic_std, ICIR, t-stat, p-value
    decay across multiple horizons
    IC by GICS sector
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ICReport:
    ic_mean: float
    ic_std: float
    icir: float                  # mean(IC) / std(IC) * sqrt(N)
    t_stat: float
    p_value: float
    n_periods: int
    ic_series: list[float] = field(default_factory=list)
    decay: dict[int, float] = field(default_factory=dict)   # horizon_days -> ic_mean
    by_sector: dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "ic_mean": self.ic_mean,
            "ic_std": self.ic_std,
            "icir": self.icir,
            "t_stat": self.t_stat,
            "p_value": self.p_value,
            "n_periods": self.n_periods,
            "decay": self.decay,
            "by_sector": self.by_sector,
            "notes": self.notes,
        }

    def is_significant(self) -> bool:
        return self.t_stat > 2.0 and self.p_value < 0.05

    def grade(self) -> str:
        m = abs(self.ic_mean)
        if m > 0.10:
            return "suspicious (overfit?)"
        if m > 0.05:
            return "strong"
        if m > 0.02:
            return "decent"
        if m > 0.00:
            return "marginal"
        return "negative or noise"


def _spearman_per_row(signal_row: pd.Series, ret_row: pd.Series) -> float:
    aligned = pd.concat([signal_row, ret_row], axis=1).dropna()
    if len(aligned) < 5:
        return float("nan")
    rho, _ = stats.spearmanr(aligned.iloc[:, 0], aligned.iloc[:, 1])
    return rho


def compute_ic_report(
    signal: pd.DataFrame,
    forward_returns: pd.DataFrame,
    sector_map: Optional[pd.Series] = None,
    horizons: tuple[int, ...] = (5, 21, 63, 126),
    aux_signals: Optional[dict[int, pd.DataFrame]] = None,
    aux_returns: Optional[dict[int, pd.DataFrame]] = None,
) -> ICReport:
    """
    signal:           [date x ticker] cross-sectional signal at each rebalance
    forward_returns:  [date x ticker] realized forward returns aligned with signal
    sector_map:       optional ticker -> sector for sector-level IC

    aux_signals/aux_returns: optional {horizon: DataFrame} for decay analysis
    """
    common_dates = signal.index.intersection(forward_returns.index)
    sig = signal.loc[common_dates]
    fr = forward_returns.loc[common_dates]

    ic_series = []
    for d in common_dates:
        ic_series.append(_spearman_per_row(sig.loc[d], fr.loc[d]))
    ic_series = pd.Series(ic_series, index=common_dates).dropna()

    if len(ic_series) < 5:
        return ICReport(
            ic_mean=float("nan"), ic_std=float("nan"), icir=float("nan"),
            t_stat=float("nan"), p_value=float("nan"), n_periods=len(ic_series),
            notes="insufficient periods (<5)",
        )

    ic_mean = float(ic_series.mean())
    ic_std = float(ic_series.std(ddof=1))
    n = len(ic_series)
    icir = ic_mean / ic_std * np.sqrt(n) if ic_std > 0 else float("nan")
    t_stat, p_value = stats.ttest_1samp(ic_series.values, 0)

    # Decay analysis
    decay = {}
    if aux_signals and aux_returns:
        for h in horizons:
            if h in aux_signals and h in aux_returns:
                sub = aux_signals[h]
                fr_sub = aux_returns[h]
                cd = sub.index.intersection(fr_sub.index)
                series = [_spearman_per_row(sub.loc[d], fr_sub.loc[d]) for d in cd]
                series = pd.Series(series, index=cd).dropna()
                if len(series) > 0:
                    decay[h] = float(series.mean())

    # By sector
    by_sector = {}
    if sector_map is not None:
        for sector in sector_map.dropna().unique():
            tickers_in_sector = sector_map[sector_map == sector].index
            sig_sec = sig.reindex(columns=tickers_in_sector)
            fr_sec = fr.reindex(columns=tickers_in_sector)
            sec_ics = []
            for d in common_dates:
                rho = _spearman_per_row(sig_sec.loc[d], fr_sec.loc[d])
                if not np.isnan(rho):
                    sec_ics.append(rho)
            if sec_ics:
                by_sector[str(sector)] = float(np.mean(sec_ics))

    return ICReport(
        ic_mean=ic_mean,
        ic_std=ic_std,
        icir=icir,
        t_stat=float(t_stat),
        p_value=float(p_value),
        n_periods=n,
        ic_series=ic_series.tolist(),
        decay=decay,
        by_sector=by_sector,
    )
