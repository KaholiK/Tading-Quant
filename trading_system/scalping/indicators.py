from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - df["close"].shift()).abs(),
            (df["low"] - df["close"].shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period, min_periods=2).mean().fillna(0.0)


def vwap(df: pd.DataFrame) -> pd.Series:
    pv = (df["close"] * df["volume"]).cumsum()
    vol = df["volume"].cumsum().replace(0, 1)
    return pv / vol


def zscore(series: pd.Series, lookback: int = 20) -> pd.Series:
    m = series.rolling(lookback, min_periods=5).mean()
    s = series.rolling(lookback, min_periods=5).std().replace(0, 1)
    return (series - m) / s


def realized_vol(close: pd.Series, lookback: int = 20) -> pd.Series:
    ret = close.pct_change().fillna(0.0)
    return ret.rolling(lookback, min_periods=5).std().fillna(0.0)


def adx_proxy(df: pd.DataFrame, lookback: int = 14) -> pd.Series:
    slope = ema(df["close"], span=5).diff().abs()
    noise = (df["high"] - df["low"]).rolling(lookback, min_periods=3).mean().replace(0, 1)
    return (100 * slope / noise).clip(lower=0, upper=100).fillna(0)
