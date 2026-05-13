"""Scan all 科创板 (688xxx) stocks for highest MA crossover win rate."""
import sys
sys.path.insert(0, "/Users/a1/Documents/CodeProject/Claude")

import baostock as bs
from quant_demo.strategy import compute_signals
from quant_demo.backtest import run, report
import pandas as pd

START = "2020-01-01"
END   = "2025-01-01"
FAST  = 5
SLOW  = 20

# ── Get all 688xxx stocks ────────────────────────────────
bs.login()
rs = bs.query_all_stock(day="2025-01-02")
all_stocks = {}
while rs.next():
    code_full, _, name = rs.get_row_data()
    all_stocks[code_full] = name  # e.g. "sh.688256" -> "寒武纪"
bs.logout()

# Only keep sh.688xxx (exclude 600688, 601688, 603688)
kcb_codes = {k: v for k, v in all_stocks.items() if k.startswith("sh.688")}
print(f"Found {len(kcb_codes)} 科创板 stocks\n")

# ── Scan each stock ──────────────────────────────────────
results = []
bs.login()
for i, (code_full, name) in enumerate(kcb_codes.items()):
    rs = bs.query_history_k_data_plus(
        code_full,
        "date,open,high,low,close,volume",
        start_date=START, end_date=END,
        frequency="d", adjustflag="2",
    )
    if rs is None or rs.error_code != "0":
        continue
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())

    if len(rows) < 200:
        continue

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    # Drop rows with empty open/close
    df = df[(df["open"] != "") & (df["close"] != "") & (df["volume"] != "")]
    if len(df) < 200:
        continue
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)

    try:
        signals = compute_signals(df, fast=FAST, slow=SLOW)
        result = run(signals)
        rep = report(result)
        results.append({
            "code": code_full.split(".")[1],
            "name": name,
            "days": len(df),
            "total_ret": rep["total_return"],
            "sharpe": rep["sharpe_ratio"],
            "win_rate": rep["win_rate"],
            "mdd": rep["max_drawdown"],
        })
    except Exception:
        continue

    if (i + 1) % 50 == 0:
        print(f"  Scanned {i+1}/{len(kcb_codes)}...")

bs.logout()

# ── Sort by win rate ─────────────────────────────────────
results.sort(key=lambda x: x["win_rate"], reverse=True)

fmt = "{:<5} {:<8} {:<10} {:<6} {:<12} {:<10} {:<8} {:<10}"
print(f"\n{fmt.format('Rank', 'Code', 'Name', 'Days', 'Win Rate', 'Total Ret', 'Sharpe', 'Max DD')}")
print("-" * 78)
for i, r in enumerate(results[:30]):
    print(f"{i+1:<5} {r['code']:<8} {r['name']:<10} {r['days']:<6} {r['win_rate']:<12} {r['total_ret']:<10} {r['sharpe']:<8} {r['mdd']:<10}")
