"""Adversarial fixture: pure random signal. Pipeline MUST kill this.

Used to detect false positives in the verdict pipeline. If this ever produces
verdict=ship, the pipeline has a bug or the thresholds are too lax.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 42


def signal(prices: pd.DataFrame) -> pd.DataFrame:
    """Return a random signal (uniform [-1, 1]) per stock per day, deterministic by seed."""
    rng = np.random.default_rng(SEED)
    sig = pd.DataFrame(
        rng.uniform(-1.0, 1.0, size=prices.shape),
        index=prices.index,
        columns=prices.columns,
    )
    # Mask where prices NaN (don't fake a signal for missing data)
    sig = sig.where(~prices.isna())
    return sig


SPEC = {
    "fixture_id": "adversarial_random_signal",
    "hypothesis": "[ADVERSARIAL] Random uniform values predict returns. Should not work.",
    "formula": "uniform(-1, 1) per stock per day",
    "data_required": ["adjusted_close"],
    "universe": "sp500",
    "rebalance_freq": "monthly",
    "horizon_days": 21,
    "expected_sign": "both",
    "claimed_sharpe": 0.0,
}
