"""Price + universe loaders. Tries grain (parquet) first, falls back to yfinance."""
from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path

import pandas as pd
import polars as pl


def _grain_root() -> Path | None:
    candidates = [
        os.environ.get("GRAIN_DATA"),
        Path.home() / "dev" / "investor-copilot",
        Path(__file__).resolve().parents[3] / "investor-copilot",
    ]
    for c in candidates:
        if c is None:
            continue
        p = Path(c)
        if (p / "data" / "parquet" / "prices_daily.parquet").exists():
            return p
    return None


@cache
def _grain_prices_long() -> pl.DataFrame | None:
    root = _grain_root()
    if root is None:
        return None
    return pl.read_parquet(root / "data" / "parquet" / "prices_daily.parquet")


def load_price_panel(
    tickers: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    field: str = "adjusted_close",
) -> pd.DataFrame:
    """Wide price DataFrame: index=date, columns=ticker."""
    df = _grain_prices_long()
    if df is not None:
        if tickers is not None:
            df = df.filter(pl.col("ticker").is_in(tickers))
        if start:
            df = df.filter(pl.col("date") >= pl.lit(start).str.to_date())
        if end:
            df = df.filter(pl.col("date") <= pl.lit(end).str.to_date())
        wide = df.select(["date", "ticker", field]).pivot(
            on="ticker", index="date", values=field
        )
        pdf = wide.sort("date").to_pandas().set_index("date")
        pdf.index = pd.to_datetime(pdf.index)
        return pdf

    # yfinance fallback (OSS path)
    if not tickers:
        raise RuntimeError("yfinance fallback requires tickers list (no grain data found)")
    import yfinance as yf
    pdf = yf.download(
        tickers, start=start or "2015-01-01", end=end,
        auto_adjust=True, progress=False,
    )["Close"]
    pdf.index = pd.to_datetime(pdf.index)
    return pdf


def compute_returns(prices: pd.DataFrame, log: bool = False) -> pd.DataFrame:
    if log:
        import numpy as np
        return (prices / prices.shift(1)).map(np.log)
    return prices.pct_change()


def load_universe(name: str = "sp500") -> list[str]:
    """Try grain first, fall back to a hardcoded SP500 stub if unavailable."""
    root = _grain_root()
    if root is not None:
        p = root / "src" / "lib" / "data" / "universes.json"
        if p.exists():
            with p.open(encoding="utf-8") as f:
                u = json.load(f)
            return list(u.get("universes", u).get(name, []))
    return _stub_sp500()


def _stub_sp500() -> list[str]:
    """Tiny stub of mega-cap names if grain/yfinance unavailable.
    Replace with full SP500 list via Wikipedia scrape in production.
    """
    return [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK-B",
        "JPM", "V", "JNJ", "WMT", "PG", "MA", "HD", "DIS", "BAC", "XOM",
        "PFE", "KO", "PEP", "CSCO", "INTC", "VZ", "T", "ABT", "MRK", "CVX",
        "ORCL", "ADBE",
    ]
