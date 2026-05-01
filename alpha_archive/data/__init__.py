"""Data loaders for backtesting. Default backend = grain repo (private),
yfinance fallback for OSS users without grain access.
"""
from .prices import load_price_panel, load_universe, compute_returns

__all__ = ["load_price_panel", "load_universe", "compute_returns"]
