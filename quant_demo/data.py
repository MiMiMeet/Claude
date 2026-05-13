"""Stock data fetching module — uses baostock for A-shares."""
import pandas as pd
import baostock as bs


def fetch_a_share(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Fetch A-share daily data via baostock.
    symbol: e.g. '600000'
    """
    bs.login()
    prefix = "sh." if symbol.startswith(("6", "5", "9")) else "sz."
    rs = bs.query_history_k_data_plus(
        f"{prefix}{symbol}",
        "date,open,high,low,close,volume",
        start_date=start, end_date=end,
        frequency="d", adjustflag="2",  # 前复权
    )
    if rs is None or rs.error_code != "0":
        bs.logout()
        raise ValueError(f"Query failed for {symbol}: {rs.error_msg if rs else 'no response'}")
    rows = []
    while rs.next():
        rows.append(rs.get_row_data())
    bs.logout()

    if not rows:
        raise ValueError(f"No data for {symbol}")

    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df.set_index("date", inplace=True)
    df.sort_index(inplace=True)
    return df
