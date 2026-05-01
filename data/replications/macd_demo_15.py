import pandas as pd
import numpy as np

N = 20        # rolling window for P* computation
LAMBDA = 0.9  # crossover sensitivity (in-sample optimum ~0.9)


def signal(prices: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)

    for ticker in prices.columns:
        close = prices[ticker]

        # Approximate daily high-low range as abs(close-to-close change)
        # (no intraday OHLC available; open≈prev_close, high-low≈|Δclose|)
        hl_approx = close.diff().abs()

        # σ_i = rolling_std(high-low range) / close  (normalized range volatility)
        sigma = hl_approx.rolling(N, min_periods=2).std() / close.replace(0, np.nan)

        # r_i = (close-open)/(high-low) ≈ sign(daily return) given above approximation
        r = np.sign(close.diff())

        # P*_t = Σ(close·volume·σ·r) / Σ(volume)
        # volume constant → cancels; divide by N (rolling sum of 1s)
        numerator = (close * sigma * r).rolling(N, min_periods=N // 2).sum()
        P_star = numerator / N

        # VP-MACD and signal line
        ema12 = P_star.ewm(span=12, adjust=False).mean()
        ema26 = P_star.ewm(span=26, adjust=False).mean()
        vp_macd = ema12 - ema26
        sig_line = vp_macd.ewm(span=9, adjust=False).mean()

        # Continuous bullish score: positive ↔ VP-MACD above λ·Signal (buy zone)
        result[ticker] = vp_macd - LAMBDA * sig_line

    return result