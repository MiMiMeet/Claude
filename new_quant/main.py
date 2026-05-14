"""入口文件：演示完整流程"""
from config.settings import DEFAULT_SYMBOL, DEFAULT_START, DEFAULT_END, INITIAL_CAPITAL, COMMISSION_RATE, SLIPPAGE
from utils.data_fetcher import fetch_stock_data
from strategy.sma_strategy import SmaCrossStrategy
from strategy.sma_trend_filter import SmaCrossWithTrendFilter
from backtest.engine import BacktestEngine
from visualization.plotter import plot_backtest
from optimizer.grid_search import grid_search_ma, grid_search_ma_with_stop_loss


def run_strategy(strategy, data, title: str, stop_loss: float = None, kelly: bool = False):
    print("2. 生成交易信号...")
    signals = strategy.generate_signals(data)
    long_count = int((signals == 1).sum())
    cash_count = int((signals == 0).sum())
    print(f"   持仓天数: {long_count}, 空仓天数: {cash_count}")

    print("3. 执行回测...")
    engine = BacktestEngine(
        data=data,
        signals=signals,
        initial_capital=INITIAL_CAPITAL,
        commission=COMMISSION_RATE,
        slippage=SLIPPAGE,
        stop_loss=stop_loss,
        kelly=kelly,
    )
    engine.run()
    engine.print_report()

    print("4. 绘制图表...")
    plot_backtest(engine.results, title=title)
    return engine


def main():
    print("1. 获取数据...")
    data = fetch_stock_data(DEFAULT_SYMBOL, DEFAULT_START, DEFAULT_END)
    print(f"   获取到 {len(data)} 条数据\n")
    if len(data) == 0:
        print("数据为空，请检查网络或稍后再试")
        return

    # ========== 参数优化 ==========
    print("========== 参数优化 ==========")
    print(">> 搜索最佳双均线参数...")
    best_ma = grid_search_ma(
        data, SmaCrossStrategy,
        short_windows=[10, 20, 30, 50],
        long_windows=[40, 60, 100, 150, 200],
    )
    print(best_ma.head(10))
    print()

    print(">> 搜索最佳均线 + 止损参数...")
    result = grid_search_ma_with_stop_loss(
        data, SmaCrossStrategy,
        short_windows=[10, 20, 30, 50],
        long_windows=[40, 60, 100, 150, 200],
        stop_losses=[0.05, 0.10, 0.15, 0.20, None],
    )
    print(result.head(10))
    print()

    # ========== 策略对比 ==========
    best_short = int(result["short"].iloc[0])
    best_long = int(result["long"].iloc[0])
    best_sl_str = result["止损"].iloc[0]
    best_sl = float(best_sl_str.strip("%")) / 100 if best_sl_str != "无" else None

    print("========== 策略 A：优化参数双均线 ==========")
    strategy_a = SmaCrossStrategy(short_window=best_short, long_window=best_long)
    engine_a = run_strategy(strategy_a, data, f"SMA({best_short},{best_long}) - {DEFAULT_SYMBOL}", stop_loss=best_sl)

    print("\n========== 策略 B：策略 A + Kelly 仓位管理 ==========")
    strategy_b = SmaCrossStrategy(short_window=best_short, long_window=best_long)
    engine_b = run_strategy(strategy_b, data, f"SMA+Kelly - {DEFAULT_SYMBOL}", stop_loss=best_sl, kelly=True)

    print("\n========== 策略 C：带趋势过滤 ==========")
    strategy_c = SmaCrossWithTrendFilter(short_window=20, medium_window=60, long_window=200)
    engine_c = run_strategy(strategy_c, data, f"SMA+Trend - {DEFAULT_SYMBOL}")

    # 简单对比
    print("\n========== 对比 ==========")
    print(f"{'指标':<12} {'优化SMA':<14} {'优化+Kelly':<14} {'趋势过滤':<14}")
    for key in ["总收益率", "年化收益率", "最大回撤", "夏普比率", "交易次数"]:
        print(
            f"{key:<12} "
            f"{str(engine_a.metrics.get(key, '')):<14} "
            f"{str(engine_b.metrics.get(key, '')):<14} "
            f"{str(engine_c.metrics.get(key, '')):<14}"
        )


if __name__ == "__main__":
    main()
