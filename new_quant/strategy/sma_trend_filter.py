"""带趋势过滤的双均线策略"""
import pandas as pd
from .base_strategy import BaseStrategy


class SmaCrossWithTrendFilter(BaseStrategy):
    """
    双均线交叉 + 200日趋势过滤器（仅做多）

    只在「中期均线位于长期均线之上」时响应金叉做多，
    其余时间空仓，不做空。
    """

    def __init__(
        self,
        short_window: int = 20,
        medium_window: int = 60,
        long_window: int = 200,
    ):
        super().__init__(
            {"short": short_window, "medium": medium_window, "long": long_window}
        )
        self.short = short_window
        self.medium = medium_window
        self.long = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = data["Close"].squeeze()

        short_ma = close.rolling(window=self.short, min_periods=1).mean()
        medium_ma = close.rolling(window=self.medium, min_periods=1).mean()
        long_ma = close.rolling(window=self.long, min_periods=1).mean()

        # 原始交叉信号（只做多，不做空）
        raw_long = short_ma > medium_ma

        # 趋势方向：中期均线位于长期均线之上才允许做多
        trend_up = medium_ma > long_ma

        # 仅做多：趋势向上 + 金叉 = 持仓，其余空仓
        signal = pd.Series(0, index=data.index)
        signal[raw_long & trend_up] = 1

        return signal
