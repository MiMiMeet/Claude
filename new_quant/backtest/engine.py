"""回测引擎"""
import pandas as pd
import numpy as np
from typing import Dict


class BacktestEngine:
    """
    基于向量化的简单回测引擎

    假设：
    - 按收盘价成交
    - 每次调仓时全仓买入/卖出
    - 支持手续费和滑点
    """

    def __init__(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        initial_capital: float = 100000.0,
        commission: float = 0.0003,
        slippage: float = 0.001,
        stop_loss: float = None,
        target_volatility: float = None,
        kelly: bool = False,
        kelly_window: int = 60,
        kelly_half: bool = True,
        kelly_clip: tuple = (0.05, 1.0),
    ):
        self.data = data
        self.signals = signals
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.stop_loss = stop_loss
        self.target_volatility = target_volatility
        self.kelly = kelly
        self.kelly_window = kelly_window
        self.kelly_half = kelly_half
        self.kelly_clip = kelly_clip

        self.results: pd.DataFrame = pd.DataFrame()
        self.metrics: Dict[str, float] = {}

    def run(self) -> pd.DataFrame:
        """执行回测，返回每日持仓和资金记录"""
        df = self.data.copy()
        df["signal"] = self.signals

        # 计算每日收益率
        close = df["Close"].squeeze()
        df["returns"] = close.pct_change()

        # 仓位：用前一日信号决定当日持仓（避免未来函数）
        df["position"] = df["signal"].shift(1).fillna(0)

        # 应用 Kelly 仓位管理
        if self.kelly:
            df = self._apply_kelly(df)

        # 应用波动率目标仓位管理
        if self.target_volatility is not None and self.target_volatility > 0:
            df = self._apply_volatility_target(df)

        # 应用止损
        if self.stop_loss is not None and self.stop_loss > 0:
            df = self._apply_stop_loss(df)

        # 计算策略每日收益（持仓 × 资产收益）
        df["strategy_returns"] = df["position"] * df["returns"]

        # 计算调仓日（信号变化的日子），扣除手续费+滑点
        df["trade"] = df["position"].diff().abs()
        transaction_cost = self.commission + self.slippage
        df["strategy_returns"] -= df["trade"] * transaction_cost

        # 计算净值曲线
        df["cumulative_returns"] = (1 + df["strategy_returns"].fillna(0)).cumprod()
        df["portfolio_value"] = self.initial_capital * df["cumulative_returns"]

        self.results = df
        self._calculate_metrics()
        return df

    def _apply_kelly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Kelly 公式仓位管理：
        f = μ / σ² — 用滚动窗口的收益率均值（μ）比上方差（σ²）来决定仓位。
        半仓 Kelly（默认）避免极端仓位，叠加上下限裁剪。
        """
        rolling_ret = df["returns"].rolling(window=self.kelly_window)
        mu = rolling_ret.mean() * 252  # 年化
        var = rolling_ret.var() * 252
        var = var.replace(0, 1e-8)

        kelly_fraction = mu / var
        if self.kelly_half:
            kelly_fraction = kelly_fraction / 2

        kelly_fraction = np.clip(kelly_fraction, self.kelly_clip[0], self.kelly_clip[1])
        df["position"] = df["position"] * kelly_fraction
        return df

    def _apply_volatility_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        波动率目标仓位管理：
        - 根据近期 20 日滚动波动率动态调整仓位
        - 波动率越高，仓位越轻；波动率越低（趋势明确），仓位越重
        - 仓位范围限制在 5% ~ 100%
        """
        # 计算滚动年化波动率
        rolling_vol = df["returns"].rolling(window=20).std() * np.sqrt(252)

        # 波动率目标 / 实际波动率 = 仓位系数
        vol_scalar = self.target_volatility / rolling_vol.fillna(self.target_volatility)
        vol_scalar = np.clip(vol_scalar, 0.05, 1.0)

        df["position"] = df["position"] * vol_scalar
        df["vol_scalar"] = vol_scalar  # 记录用于调试
        return df

    def _apply_stop_loss(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        逐日应用止损：从入场价算起，亏损超过 stop_loss 时强制清仓。
        止损后保持空仓，直到原始信号方向发生改变并重新开仓。
        """
        close = df["Close"].squeeze().to_numpy()
        position = df["position"].copy().to_numpy()

        in_position = False
        entry_price = 0.0
        direction = 0

        for i in range(len(position)):
            price = close[i]
            pos = position[i]

            if not in_position and pos != 0:
                # 新开仓
                in_position = True
                direction = 1 if pos > 0 else -1
                entry_price = price
            elif in_position:
                # 检查是否触发止损
                if direction == 1:
                    loss = (entry_price - price) / entry_price
                else:
                    loss = (price - entry_price) / entry_price

                if loss > self.stop_loss:
                    position[i] = 0
                    in_position = False
                    direction = 0
                    entry_price = 0.0
                    continue

                # 检查是否因信号变化而平仓
                if pos == 0:
                    in_position = False
                    direction = 0
                    entry_price = 0.0
                elif (pos > 0 and direction == -1) or (pos < 0 and direction == 1):
                    # 方向翻转，视为新开仓
                    direction = 1 if pos > 0 else -1
                    entry_price = price

        df["position"] = position
        return df

    def _calculate_metrics(self):
        """计算回测指标"""
        returns = self.results["strategy_returns"].dropna()

        # 总收益率
        total_return = self.results["portfolio_value"].iloc[-1] / self.initial_capital - 1

        # 年化收益率（按252个交易日）
        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / n_days) - 1 if n_days > 0 else 0

        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)

        # 最大回撤
        cummax = self.results["portfolio_value"].cummax()
        drawdown = (self.results["portfolio_value"] - cummax) / cummax
        max_drawdown = drawdown.min()

        # 夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        sharpe_ratio = (
            (annual_return - risk_free_rate) / annual_volatility
            if annual_volatility > 0
            else 0
        )

        # 交易次数
        trade_count = int(self.results["trade"].sum())

        self.metrics = {
            "总收益率": f"{total_return:.2%}",
            "年化收益率": f"{annual_return:.2%}",
            "年化波动率": f"{annual_volatility:.2%}",
            "最大回撤": f"{max_drawdown:.2%}",
            "夏普比率": f"{sharpe_ratio:.2f}",
            "交易次数": trade_count,
        }

    def print_report(self):
        """打印回测报告"""
        print("\n========== 回测报告 ==========")
        for k, v in self.metrics.items():
            print(f"{k}: {v}")
        print("==============================\n")
