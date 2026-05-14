"""参数网格搜索"""
import itertools
from typing import List, Callable
import pandas as pd
from strategy.base_strategy import BaseStrategy
from backtest.engine import BacktestEngine


def _split_data(data: pd.DataFrame, train_ratio: float = 0.8):
    split_idx = int(len(data) * train_ratio)
    return data.iloc[:split_idx].copy(), data.iloc[split_idx:].copy()


def _make_strategy(strategy_class, kwargs) -> BaseStrategy:
    sig = strategy_class.__init__.__code__.co_varnames[1:strategy_class.__init__.__code__.co_argcount]
    filtered = {k: v for k, v in kwargs.items() if k in sig}
    return strategy_class(**filtered)


def grid_search_ma(
    data: pd.DataFrame,
    strategy_class: type,
    short_windows: List[int] = None,
    long_windows: List[int] = None,
    initial_capital: float = 100000,
    commission: float = 0.0003,
    slippage: float = 0.001,
    train_ratio: float = 0.8,
    metric: str = "夏普比率",
    kelly: bool = False,
) -> pd.DataFrame:
    """
    搜索最佳均线参数组合。

    Returns:
        DataFrame，按指定指标降序排列
    """
    short_windows = short_windows or [10, 20, 30, 50]
    long_windows = long_windows or [40, 60, 100, 150, 200]

    if len(data) < 100:
        print(f"数据不足（{len(data)} 条），无法搜索")
        return pd.DataFrame()

    train_data, test_data = _split_data(data, train_ratio)
    results = []

    total = len(short_windows) * len(long_windows)
    print(f"搜索 {total} 个参数组合 (训练集 {len(train_data)} 条, 验证集 {len(test_data)} 条)...")

    for i, (short, long) in enumerate(itertools.product(short_windows, long_windows)):
        if short >= long:
            continue

        strategy = _make_strategy(strategy_class, {"short_window": short, "long_window": long})
        signals = strategy.generate_signals(data)

        # 训练集回测
        train_signals = signals.loc[train_data.index]
        engine = BacktestEngine(
            data=train_data,
            signals=train_signals,
            initial_capital=initial_capital,
            commission=commission,
            slippage=slippage,
            kelly=kelly,
        )
        engine.run()
        train_sharpe = float(engine.metrics[metric]) if metric in engine.metrics else engine.metrics.get("夏普比率", 0)
        train_return = engine.metrics.get("总收益率", "0%")

        # 验证集回测
        test_signals = signals.loc[test_data.index]
        engine_test = BacktestEngine(
            data=test_data,
            signals=test_signals,
            initial_capital=initial_capital,
            commission=commission,
            slippage=slippage,
            kelly=kelly,
        )
        engine_test.run()
        test_sharpe = float(engine_test.metrics[metric]) if metric in engine_test.metrics else engine_test.metrics.get("夏普比率", 0)
        test_return = engine_test.metrics.get("总收益率", "0%")

        results.append({
            "short": short, "long": long,
            "训练集夏普": f"{train_sharpe:.2f}",
            "验证集夏普": f"{test_sharpe:.2f}",
            "训练集收益": str(train_return),
            "验证集收益": str(test_return),
            "_sort": test_sharpe,
        })

        print(f"  [{i+1}/{total}] short={short}, long={long} → 验证夏普={test_sharpe:.2f}")

    df = pd.DataFrame(results).sort_values("_sort", ascending=False).drop(columns=["_sort"]).reset_index(drop=True)
    print(f"\n最佳参数: short={df['short'].iloc[0]}, long={df['long'].iloc[0]}")
    return df


def grid_search_ma_with_stop_loss(
    data: pd.DataFrame,
    strategy_class: type,
    short_windows: List[int] = None,
    long_windows: List[int] = None,
    stop_losses: List[float] = None,
    initial_capital: float = 100000,
    commission: float = 0.0003,
    slippage: float = 0.001,
    train_ratio: float = 0.8,
    metric: str = "夏普比率",
    kelly: bool = False,
) -> pd.DataFrame:
    """
    搜索最佳均线参数 + 止损比例组合。
    """
    short_windows = short_windows or [10, 20, 30, 50]
    long_windows = long_windows or [40, 60, 100, 150, 200]
    stop_losses = stop_losses or [0.05, 0.10, 0.15, 0.20, None]

    if len(data) < 100:
        print(f"数据不足（{len(data)} 条），无法搜索")
        return pd.DataFrame()

    train_data, test_data = _split_data(data, train_ratio)
    results = []

    total = len(short_windows) * len(long_windows) * len(stop_losses)
    print(f"搜索 {total} 个参数组合 (训练集 {len(train_data)} 条, 验证集 {len(test_data)} 条)...")

    count = 0
    for short, long, sl in itertools.product(short_windows, long_windows, stop_losses):
        if short >= long:
            continue

        count += 1
        strategy = _make_strategy(strategy_class, {"short_window": short, "long_window": long})
        signals = strategy.generate_signals(data)

        def run_one(d, sigs, sl_val):
            engine = BacktestEngine(
                data=d, signals=sigs, initial_capital=initial_capital,
                commission=commission, slippage=slippage,
                stop_loss=sl_val, kelly=kelly,
            )
            engine.run()
            return engine.metrics

        train_metrics = run_one(train_data, signals.loc[train_data.index], sl)
        test_metrics = run_one(test_data, signals.loc[test_data.index], sl)

        results.append({
            "short": short, "long": long,
            "止损": f"{sl:.0%}" if sl is not None else "无",
            "训练集夏普": f"{float(train_metrics[metric]):.2f}" if metric in train_metrics else "-",
            "验证集夏普": f"{float(test_metrics[metric]):.2f}" if metric in test_metrics else "-",
            "训练集收益": str(train_metrics.get("总收益率", "-")),
            "验证集收益": str(test_metrics.get("总收益率", "-")),
            "_sort": float(test_metrics.get(metric, 0)),
        })

        if count % 10 == 0 or count == 1:
            print(f"  [{count}] short={short}, long={long}, sl={sl}")

    df = pd.DataFrame(results).sort_values("_sort", ascending=False).drop(columns=["_sort"]).reset_index(drop=True)
    print(f"\n最佳: short={df['short'].iloc[0]}, long={df['long'].iloc[0]}, 止损={df['止损'].iloc[0]}")
    return df
