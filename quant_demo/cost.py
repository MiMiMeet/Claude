"""Trading cost model — A-share commissions, stamp tax, slippage."""


class CostModel:
    def __init__(
        self,
        commission_rate: float = 0.0003,
        stamp_tax_rate: float = 0.001,
        slippage_bps: float = 0.0,
        min_commission: float = 5.0,
    ):
        self.commission_rate = commission_rate
        self.stamp_tax_rate = stamp_tax_rate
        self.slippage_bps = slippage_bps
        self.min_commission = min_commission

    def trade_cost(self, price: float, shares: int, action: str) -> float:
        """action: 'buy' or 'sell'"""
        turnover = price * shares
        commission = max(turnover * self.commission_rate, self.min_commission)
        stamp_tax = turnover * self.stamp_tax_rate if action == "sell" else 0.0
        slippage = turnover * self.slippage_bps / 10000
        return commission + stamp_tax + slippage
