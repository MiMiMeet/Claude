"""
Quant demo — dual moving-average crossover strategy on A-shares.
Run: python quant_demo/main.py
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from quant_demo.data import fetch_a_share
from quant_demo.strategy import compute_signals
from quant_demo.backtest import run, report
from quant_demo.cost import CostModel
from quant_demo.risk import RiskManager

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── parameters ──────────────────────────────────────────
SYMBOL = "688256"   # 寒武纪
START  = "2020-01-01"
END    = "2025-01-01"
FAST   = 5          # 短期均线
SLOW   = 20         # 长期均线
CAPITAL = 100_000   # 初始资金

# ── cost parameters ─────────────────────────────────────
COMMISSION  = 0.0003  # 佣金万三
STAMP_TAX   = 0.001   # 印花税千一
SLIPPAGE    = 0.0     # 滑点 (bps)

# ── risk parameters ─────────────────────────────────────
STOP_LOSS   = -0.10   # 止损 -10%
TAKE_PROFIT = 0.20    # 止盈 +20%
ENABLE_RISK = True

# ── pipeline ─────────────────────────────────────────────
print(f"Fetching {SYMBOL} from {START} to {END}...")
data = fetch_a_share(SYMBOL, START, END)
print(f"Got {len(data)} trading days.")

signals = compute_signals(data, fast=FAST, slow=SLOW)

cost = CostModel(
    commission_rate=COMMISSION,
    stamp_tax_rate=STAMP_TAX,
    slippage_bps=SLIPPAGE,
)
risk = RiskManager(
    stop_loss_pct=STOP_LOSS,
    take_profit_pct=TAKE_PROFIT,
) if ENABLE_RISK else None

result = run(signals, capital=CAPITAL, cost_model=cost, risk_manager=risk)

# ── report ───────────────────────────────────────────────
print("\n📊 Performance Report")
print("-" * 34)
for k, v in report(result).items():
    print(f"  {k:20s}: {v:>10s}")

# ── plot ─────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                gridspec_kw={"height_ratios": [3, 1]})

# Price + MAs
ax1.plot(result.index, result["close"], label="Close", linewidth=0.8, color="#333")
ax1.plot(result.index, result["ma_fast"], label=f"MA{FAST}", alpha=0.8)
ax1.plot(result.index, result["ma_slow"], label=f"MA{SLOW}", alpha=0.8)

pos_shift = result["position"].diff()

# Entry: position 0→1
buys = result[pos_shift == 1]
ax1.scatter(buys.index, buys["close"], marker="^", s=60,
            color="red", zorder=5, label="Buy Signal")

# Exit: signal (MA cross sell)
ss = result[(result["exit_reason"] == "signal") & (pos_shift == -1)]
ax1.scatter(ss.index, ss["close"], marker="v", s=60,
            color="green", zorder=5, label="Sell Signal")

# Stop-loss exits
sl = result[result["exit_reason"] == "stop_loss"]
ax1.scatter(sl.index, sl["close"], marker="v", s=60,
            color="purple", zorder=5, label="Stop Loss")

# Take-profit exits
tp = result[result["exit_reason"] == "take_profit"]
ax1.scatter(tp.index, tp["close"], marker="v", s=60,
            color="orange", zorder=5, label="Take Profit")

ax1.set_title(f"{SYMBOL} — MA{FAST}/{SLOW} Crossover + Cost Model + Risk Control")
ax1.legend(loc="upper left", fontsize=8)
ax1.set_ylabel("Price (前复权)")
ax1.grid(alpha=0.3)

# Equity curves
ax2.plot(result.index, result["equity_strat"], label="Strategy", linewidth=1.2)
ax2.plot(result.index, result["equity_market"], label="Buy & Hold",
         alpha=0.5, linestyle="--")
ax2.fill_between(result.index, CAPITAL, result["equity_strat"],
                 alpha=0.15, color="green")

# Mark stop-loss / take-profit on equity curve
ax2.scatter(sl.index, sl["equity_strat"], marker="v", s=60,
            color="purple", zorder=5, label="Stop Loss")
ax2.scatter(tp.index, tp["equity_strat"], marker="^", s=60,
            color="orange", zorder=5, label="Take Profit")

ax2.legend(loc="upper left", fontsize=8)
ax2.set_ylabel("Equity (¥)")
ax2.set_xlabel("Date")
ax2.grid(alpha=0.3)

ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

plt.tight_layout()
plt.savefig("quant_demo/result.png", dpi=150)
plt.show()
print("\n✅ Chart saved to quant_demo/result.png")
