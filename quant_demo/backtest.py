"""
Simple vectorized backtesting engine.
"""
import pandas as pd
import numpy as np


def run(df: pd.DataFrame, capital: float = 100_000) -> pd.DataFrame:
    """
    Run a vectorized backtest on the strategy signals.
    Returns df with equity curve columns.
    """
    df = df.copy()

    # Daily returns of the underlying
    df["ret"] = df["close"].pct_change()

    # Position: hold 1 unit (long) when signal==1, else 0 (cash)
    df["position"] = df["signal"].shift(1).fillna(0).astype(int)

    # Strategy daily return
    df["strat_ret"] = df["position"] * df["ret"]

    # Equity curves
    df["equity_market"] = (1 + df["ret"]).cumprod() * capital
    df["equity_strat"] = (1 + df["strat_ret"]).cumprod() * capital

    return df


def report(df: pd.DataFrame) -> dict:
    """Compute key performance metrics."""
    valid = df.dropna(subset=["ret", "strat_ret"])

    total_ret = valid["strat_ret"].sum()
    annual_ret = (1 + valid["strat_ret"]).prod() ** (252 / len(valid)) - 1
    vol = valid["strat_ret"].std() * np.sqrt(252)
    sharpe = annual_ret / vol if vol > 0 else 0
    mdd = _max_drawdown(valid["equity_strat"])
    win_rate = (valid["strat_ret"] > 0).sum() / (valid["strat_ret"] != 0).sum()

    return {
        "total_return": f"{total_ret:.2%}",
        "annual_return": f"{annual_ret:.2%}",
        "annual_volatility": f"{vol:.2%}",
        "sharpe_ratio": f"{sharpe:.2f}",
        "max_drawdown": f"{mdd:.2%}",
        "win_rate": f"{win_rate:.2%}",
    }


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return drawdown.min()
