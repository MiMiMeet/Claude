"""Risk manager — stop-loss and take-profit based on entry price."""


class RiskManager:
    def __init__(self, stop_loss_pct: float = -0.10, take_profit_pct: float = 0.20):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.entry_price = None

    def record_entry(self, price: float) -> None:
        self.entry_price = price

    def check(self, current_price: float) -> str:
        """Returns 'hold' | 'stop_loss' | 'take_profit'"""
        if self.entry_price is None:
            return "hold"
        pct_change = (current_price - self.entry_price) / self.entry_price
        if pct_change <= self.stop_loss_pct:
            return "stop_loss"
        if pct_change >= self.take_profit_pct:
            return "take_profit"
        return "hold"

    def reset(self) -> None:
        self.entry_price = None
