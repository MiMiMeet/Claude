"""双均线策略示例"""
import pandas as pd
from .base_strategy import BaseStrategy


class SmaCrossStrategy(BaseStrategy):
    """
    简单双均线交叉策略（仅做多）

    当短期均线上穿长期均线时做多（1），下穿时空仓（0），不做空。
    """

    def __init__(self, short_window: int = 20, long_window: int = 60):
        super().__init__({"short": short_window, "long": long_window})
        self.short = short_window
        self.long = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        close = data["Close"].squeeze()
        short_ma = close.rolling(window=self.short, min_periods=1).mean()
        long_ma = close.rolling(window=self.long, min_periods=1).mean()

        signal = pd.Series(0, index=data.index)
        signal[short_ma > long_ma] = 1
        return signal
