"""策略基类"""
import pandas as pd
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """所有策略的基类，子类需实现 generate_signals 方法"""

    def __init__(self, params: dict = None):
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        根据输入数据生成交易信号

        Args:
            data: 包含至少 Close 列的 DataFrame

        Returns:
            Series，取值为 1 (做多), -1 (做空), 0 (空仓)
        """
        pass
