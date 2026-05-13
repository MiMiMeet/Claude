"""
Quant demo — dual moving-average crossover strategy on A-shares.
Run: python quant_demo/main.py
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from quant_demo.data import fetch_a_share
from quant_demo.strategy import compute_signals
from quant_demo.backtest import run, report

plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ── parameters ──────────────────────────────────────────
SYMBOL = "688256"   # 寒武纪
START  = "2020-01-01"
END    = "2025-01-01"
FAST   = 5          # 短期均线
SLOW   = 20         # 长期均线
CAPITAL = 100_000   # 初始资金

# ── pipeline ─────────────────────────────────────────────
print(f"Fetching {SYMBOL} from {START} to {END}...")
data = fetch_a_share(SYMBOL, START, END)
print(f"Got {len(data)} trading days.")

signals = compute_signals(data, fast=FAST, slow=SLOW)
result = run(signals, capital=CAPITAL)

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

# Mark entry signals
buys = result[result["trade"] == 1]
sells = result[result["trade"] == -1]
ax1.scatter(buys.index, buys["close"], marker="^", s=60,
            color="red", zorder=5, label="Buy Signal")
ax1.scatter(sells.index, sells["close"], marker="v", s=60,
            color="green", zorder=5, label="Sell Signal")

ax1.set_title(f"{SYMBOL} — MA{FAST}/{SLOW} Crossover Strategy")
ax1.legend(loc="upper left", fontsize=8)
ax1.set_ylabel("Price (前复权)")
ax1.grid(alpha=0.3)

# Equity curves
ax2.plot(result.index, result["equity_strat"], label="Strategy", linewidth=1.2)
ax2.plot(result.index, result["equity_market"], label="Buy & Hold",
         alpha=0.5, linestyle="--")
ax2.fill_between(result.index, CAPITAL, result["equity_strat"],
                 alpha=0.15, color="green")
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
