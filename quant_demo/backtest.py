"""Vectorized backtesting engine with per-bar cost/risk integration."""
import pandas as pd
import numpy as np


def run(
    df: pd.DataFrame,
    capital: float = 100_000,
    cost_model=None,
    risk_manager=None,
) -> pd.DataFrame:
    df = df.copy()
    df["ret"] = df["close"].pct_change()

    n = len(df)
    position = [0] * n
    exit_reason = [""] * n
    cost_arr = [0.0] * n
    strat_ret = [0.0] * n

    shares = 0
    in_position = False

    # signals from MA crossover (already in df)
    signals = df["signal"].fillna(0).astype(int).values
    closes = df["close"].values

    for i in range(1, n):
        cost = 0.0
        prev_signal = signals[i - 1]

        # 1. risk check first
        if in_position and risk_manager is not None:
            reason = risk_manager.check(closes[i])
            if reason != "hold":
                cost = _close_position(
                    closes[i], shares, "sell", cost_model, risk_manager
                )
                shares = 0
                in_position = False
                exit_reason[i] = reason

        # 2. signal check — use prev bar's signal (matching old position[t]=signal[t-1])
        if not in_position and prev_signal == 1:
            shares, cost = _open_position(closes[i], capital, "buy", cost_model, risk_manager)
            in_position = True
        elif in_position and prev_signal == 0:
            cost = _close_position(closes[i], shares, "sell", cost_model, risk_manager)
            shares = 0
            in_position = False
            exit_reason[i] = "signal"

        position[i] = 1 if in_position else 0
        cost_arr[i] = cost
        strat_ret[i] = (position[i] * df["ret"].iloc[i])

    df["position"] = position
    df["exit_reason"] = exit_reason
    df["trade_cost"] = cost_arr
    df["strat_ret"] = strat_ret

    # deduct costs from strat returns
    df["strat_ret"] = df["strat_ret"] - df["trade_cost"] / capital

    df["equity_market"] = (1 + df["ret"]).cumprod() * capital
    df["equity_strat"] = (1 + df["strat_ret"]).cumprod() * capital

    return df


def _open_position(price, capital, action, cost_model, risk_manager):
    shares = int(capital / price / 100) * 100
    cost = cost_model.trade_cost(price, shares, action) if cost_model else 0.0
    if risk_manager:
        risk_manager.record_entry(price)
    return shares, cost


def _close_position(price, shares, action, cost_model, risk_manager):
    cost = cost_model.trade_cost(price, shares, action) if cost_model else 0.0
    if risk_manager:
        risk_manager.reset()
    return cost


def report(df: pd.DataFrame) -> dict:
    valid = df.dropna(subset=["ret", "strat_ret"])

    total_ret = valid["strat_ret"].sum()
    annual_ret = (1 + valid["strat_ret"]).prod() ** (252 / len(valid)) - 1
    vol = valid["strat_ret"].std() * np.sqrt(252)
    sharpe = annual_ret / vol if vol > 0 else 0
    mdd = _max_drawdown(valid["equity_strat"])
    win_rate = (valid["strat_ret"] > 0).sum() / (valid["strat_ret"] != 0).sum()

    total_costs = df["trade_cost"].sum()
    stop_loss_count = (df["exit_reason"] == "stop_loss").sum()
    take_profit_count = (df["exit_reason"] == "take_profit").sum()
    signal_exit_count = (df["exit_reason"] == "signal").sum()
    trades = signal_exit_count + stop_loss_count + take_profit_count

    return {
        "total_return": f"{total_ret:.2%}",
        "annual_return": f"{annual_ret:.2%}",
        "annual_volatility": f"{vol:.2%}",
        "sharpe_ratio": f"{sharpe:.2f}",
        "max_drawdown": f"{mdd:.2%}",
        "win_rate": f"{win_rate:.2%}",
        "total_costs": f"¥{total_costs:,.0f}",
        "trades": f"{trades}",
        "stop_loss": f"{stop_loss_count}",
        "take_profit": f"{take_profit_count}",
    }


def _max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return drawdown.min()
