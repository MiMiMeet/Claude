"""数据获取工具"""
import yfinance as yf
import pandas as pd


def fetch_stock_data(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    获取股票/指数历史数据

    Args:
        symbol: 代码，如 "000300.SS" (沪深300)、"AAPL" (苹果)
        start: 开始日期，格式 "YYYY-MM-DD"
        end: 结束日期，格式 "YYYY-MM-DD"

    Returns:
        DataFrame，包含 Open, High, Low, Close, Volume 列
    """
    df = yf.download(symbol, start=start, end=end, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df
