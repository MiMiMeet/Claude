# quant_demo: Add Cost Model & Risk Controls

**Date**: 2026-05-17  
**Status**: approved  
**Approach**: B — modular split (cost.py + risk.py + backtest refactor)

## Scope

Add two features to the existing quant_demo framework:
1. **Trading cost model** — commissions, stamp tax, slippage reflecting A-share real costs
2. **Risk controls** — stop-loss and take-profit based on entry price

Non-goals: parameter optimization, multi-stock backtesting, additional indicators, event-driven engine rewrite.

## Module 1: `cost.py` — Trading Cost Model

```
class CostModel:
    params:
      commission_rate: float = 0.0003    # 万三
      stamp_tax_rate: float = 0.001      # 千一 (sell only)
      slippage_bps: float = 0.0          # slippage in bps
      min_commission: float = 5.0         # min commission in CNY

    def trade_cost(self, price: float, shares: int, action: str) -> float
        commission = max(turnover * commission_rate, min_commission)
        stamp_tax = turnover * stamp_tax_rate if action == "sell" else 0
        slippage = turnover * slippage_bps / 10000
        return commission + stamp_tax + slippage
```

- `action` is `"buy"` or `"sell"`
- `shares` = `capital // price` (round to multiples of 100 for A-shares)
- Returns total cost in CNY

## Module 2: `risk.py` — Risk Manager

```
class RiskManager:
    params:
      stop_loss_pct: float    # e.g. -0.10
      take_profit_pct: float  # e.g. 0.20

    internal state:
      entry_price: float | None
      entry_date: Timestamp | None

    def record_entry(self, price, date) -> None
        # record the price at which the current position was entered

    def check(self, current_price, date) -> str  # "hold" | "stop_loss" | "take_profit"
        # returns "hold" if no position or no trigger
        # returns "stop_loss" if price dropped below stop_loss_pct from entry
        # returns "take_profit" if price rose above take_profit_pct from entry

    def reset(self) -> None
        # clear entry state when position is closed
```

Both stop-loss and take-profit are based on entry price (not trailing / highest-high). When triggered, the position is closed at the trigger bar's close price.

## Module 3: `backtest.py` — Backtest Engine (Refactored)

Current engine is fully vectorized. Risk controls require per-bar tracking of entry price, so a lightweight loop replaces the vectorized position logic:

```
def run(df, capital, cost_model=None, risk_manager=None) -> DataFrame

    Per-bar loop:
      for each bar (index i):
        1. If holding position:
             reason = risk_manager.check(close[i], date[i])
             if reason != "hold":
                 close position at close[i]
                 deduct cost_model.trade_cost(close[i], shares, "sell")
                 risk_manager.reset()
                 record exit_reason = reason
        2. Check MA signal:
             if signal[i] == 1 and no position:
                 open position at close[i]
                 deduct cost_model.trade_cost(close[i], shares, "buy")
                 risk_manager.record_entry(close[i], date[i])
                 record exit_reason = "signal"
             elif signal[i] == 0 and has position:
                 close position at close[i]
                 deduct cost_model.trade_cost(close[i], shares, "sell")
                 risk_manager.reset()
                 record exit_reason = "signal"
        3. Compute daily strat return:
             strat_ret[i] = (position * ret[i]) - cost_at_bar[i]
        4. Compute equity curves (unchanged logic)

    New output columns:
      - exit_reason: "" | "signal" | "stop_loss" | "take_profit"
      - trade_cost: cost incurred at this bar (0 if no trade)
      - position: 1 or 0 (already exists, unchanged)
```

**report() additions:**
- `total_costs`: sum of all trade costs in CNY
- `stop_loss_count`: number of stop-loss triggers
- `take_profit_count`: number of take-profit triggers  
- `win_rate`: adjusted to account for risk-controlled exits

Share calculation: `shares = (capital // close_price // 100) * 100` (round lot).

## `main.py` Changes

Add configuration section:
```python
# ── cost parameters ──────────
COMMISSION  = 0.0003  # 万三
STAMP_TAX   = 0.001   # 千一卖出
SLIPPAGE    = 0.0

# ── risk parameters ──────────
STOP_LOSS   = -0.10   # -10%
TAKE_PROFIT = 0.20    # +20%
ENABLE_RISK = True    # toggle risk controls
```

Pipeline updated to instantiate and pass cost/risk objects. Plot updated to mark stop-loss and take-profit exit points with distinct markers.

## File Changes Summary

| File | Action |
|------|--------|
| `quant_demo/cost.py` | **New** — CostModel class |
| `quant_demo/risk.py` | **New** — RiskManager class |
| `quant_demo/backtest.py` | **Modify** — add per-bar loop, cost deduction, risk checking |
| `quant_demo/main.py` | **Modify** — new params, pass cost/risk, updated plot |
| `quant_demo/data.py` | No change |
| `quant_demo/strategy.py` | No change |

## Backward Compatibility

If `cost_model` and `risk_manager` are not passed to `run()`, behavior matches current (no costs, signal-only exits). All existing code paths remain functional.
