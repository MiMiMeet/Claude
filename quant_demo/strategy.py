"""
Strategy module: moving-average crossover and signal generation.
"""
import pandas as pd
import numpy as np


def compute_signals(df: pd.DataFrame, fast: int = 5, slow: int = 20) -> pd.DataFrame:
    """
    Add MA crossover signals to the DataFrame.
    fast: short-term MA window
    slow: long-term MA window
    Returns df with added columns: ma_fast, ma_slow, signal, position
    """
    df = df.copy()
    df["ma_fast"] = df["close"].rolling(fast).mean()
    df["ma_slow"] = df["close"].rolling(slow).mean()

    # 1 when fast above slow (bullish), 0 otherwise
    df["signal"] = (df["ma_fast"] > df["ma_slow"]).astype(int)
    # Trade signal: 1=enter/keep long, -1=exit, 0=no change
    df["trade"] = df["signal"].diff()
    return df
