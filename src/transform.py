"""Includes data transformation between schemas used by yfinance, pypfopt, and zipline"""
import typing as T

import pandas as pd
import zipline as zp


def yfinance2pypfopt(df: pd.DataFrame) -> pd.DataFrame:
    """https://pyportfolioopt.readthedocs.io/en/latest/UserGuide.html#processing-historical-prices"""
    df = df.dropna()
    df = df.iloc[:, df.columns.get_level_values(1) == "Close"]
    df.columns = df.columns.get_level_values(0)
    return df


def yfinance2zipline(df: pd.DataFrame, savedir: str) -> T.Dict[str, pd.DataFrame]:
    """https://zipline.ml4trading.io/bundles.html"""
    data = {}
    df = df.dropna()
    assets = df.columns.get_level_values(0).unique()
    for asset in assets:
        _df = df[asset][["Open", "High", "Low", "Close", "Volume"]]
        _df.columns = _df.columns.str.lower()
        _df.index.name = "date"
        _df["dividend"] = 0.0
        _df["split"] = 1.0
        if asset == "ETH-USD":
            _df.close = _df.close / 1000
        if asset == "BTC-USD":
            _df.close = _df.close / 10000
        _df.to_csv(f"{savedir}/daily/{asset}.csv")
        data[asset] = _df
    return data


def zipline2pypfopt(
    context: zp.TradingAlgorithm,
    data: zp.protocol.BarData,
) -> pd.DataFrame:
    symbols = [zp.api.symbol(s) for s in context.assets]
    df = data.history(
        symbols, "close", bar_count=context.recalc_weights_per, frequency="1d"
    )
    df.columns = [col.symbol for col in df.columns]
    return df
