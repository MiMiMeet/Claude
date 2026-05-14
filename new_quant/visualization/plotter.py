"""可视化模块"""
import matplotlib.pyplot as plt
import pandas as pd


def plot_backtest(data: pd.DataFrame, title: str = "Backtest Result"):
    """
    绘制回测结果：价格+信号、净值曲线、回撤

    Args:
        data: 包含 Close, signal, portfolio_value 的 DataFrame
        title: 图表标题
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    close = data["Close"].squeeze()
    signal = data["signal"]
    portfolio = data["portfolio_value"]

    # 1. 价格与信号
    ax1 = axes[0]
    ax1.plot(close.index, close, label="Close", color="black", linewidth=1)
    long_mask = signal == 1
    ax1.scatter(
        close.index[long_mask],
        close[long_mask],
        color="red",
        marker="^",
        s=30,
        label="Long",
        zorder=5,
    )
    # 标记离场点（信号从1变0的位置）
    exit_mask = (signal.shift(1) == 1) & (signal == 0)
    ax1.scatter(
        close.index[exit_mask],
        close[exit_mask],
        color="green",
        marker="v",
        s=20,
        label="Exit",
        zorder=5,
    )
    ax1.set_title(f"{title} - Price & Signals")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. 净值曲线
    ax2 = axes[1]
    ax2.plot(portfolio.index, portfolio, label="Strategy", color="blue", linewidth=1.5)
    # 基准：买入持有
    benchmark = (close / close.iloc[0]) * portfolio.iloc[0]
    ax2.plot(benchmark.index, benchmark, label="Buy & Hold", color="gray", linewidth=1, linestyle="--")
    ax2.set_title("Portfolio Value")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. 回撤
    ax3 = axes[2]
    cummax = portfolio.cummax()
    drawdown = (portfolio - cummax) / cummax
    ax3.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.3)
    ax3.plot(drawdown.index, drawdown, color="red", linewidth=1)
    ax3.set_title("Drawdown")
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("backtest_result.png", dpi=150)
    plt.show()
    print("图表已保存为 backtest_result.png")
