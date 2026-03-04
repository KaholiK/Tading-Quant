from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import StrategyConfig
from .indicators import adx_proxy, atr, ema, realized_vol, vwap, zscore


@dataclass
class Signal:
    symbol: str
    side: str
    strength: float
    module: str
    stop_price: float


class RegimeFilter:
    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg

    def classify(self, frame: pd.DataFrame) -> str:
        if len(frame) < 20:
            return "unknown"
        frame = frame.copy()
        frame["atr"] = atr(frame)
        frame["rv"] = realized_vol(frame["close"])
        frame["adx"] = adx_proxy(frame)
        row = frame.iloc[-1]
        if row["atr"] > self.cfg.atr_max or row["rv"] > 0.02:
            return "high_volatility"
        if row["adx"] > 25:
            return "trending"
        return "choppy"

    def tradable(self, frame: pd.DataFrame) -> bool:
        row = frame.iloc[-1]
        spread_bps = ((row["high"] - row["low"]) / max(row["close"], 1e-6)) * 10000
        return (
            spread_bps <= self.cfg.spread_bps_max
            and self.cfg.atr_min <= row.get("atr", 0) <= self.cfg.atr_max
            and row["volume"] >= self.cfg.min_volume
        )


class CompositeScalpingStrategy:
    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg
        self.regime_filter = RegimeFilter(cfg)

    def evaluate(self, symbol: str, frame: pd.DataFrame) -> Signal | None:
        if len(frame) < 30:
            return None
        frame = frame.copy()
        frame["ema_fast"] = ema(frame["close"], 9)
        frame["ema_slow"] = ema(frame["close"], 21)
        frame["atr"] = atr(frame)
        frame["vwap"] = vwap(frame)
        frame["z"] = zscore(frame["close"] - frame["vwap"])

        if not self.regime_filter.tradable(frame):
            return None

        regime = self.regime_filter.classify(frame)
        if regime == "trending" and "trend_pullback" in self.cfg.modules_enabled:
            return self._trend_pullback(symbol, frame)
        if regime == "choppy" and "mean_reversion" in self.cfg.modules_enabled:
            return self._mean_reversion(symbol, frame)
        if regime == "high_volatility" and "breakout" in self.cfg.modules_enabled:
            return self._breakout(symbol, frame)
        return None

    def _trend_pullback(self, symbol: str, frame: pd.DataFrame) -> Signal | None:
        row = frame.iloc[-1]
        if row["ema_fast"] > row["ema_slow"] and row["close"] <= row["ema_fast"]:
            return Signal(symbol, "BUY", 0.7, "trend_pullback", stop_price=row["close"] - row["atr"])
        if row["ema_fast"] < row["ema_slow"] and row["close"] >= row["ema_fast"]:
            return Signal(symbol, "SELL", 0.7, "trend_pullback", stop_price=row["close"] + row["atr"])
        return None

    def _mean_reversion(self, symbol: str, frame: pd.DataFrame) -> Signal | None:
        row = frame.iloc[-1]
        if row["z"] <= -1.8:
            return Signal(symbol, "BUY", 0.6, "mean_reversion", stop_price=row["close"] - 0.8 * row["atr"])
        if row["z"] >= 1.8:
            return Signal(symbol, "SELL", 0.6, "mean_reversion", stop_price=row["close"] + 0.8 * row["atr"])
        return None

    def _breakout(self, symbol: str, frame: pd.DataFrame) -> Signal | None:
        recent = frame.iloc[-6:-1]
        row = frame.iloc[-1]
        high_break = recent["high"].max()
        low_break = recent["low"].min()
        if row["close"] > high_break and row["volume"] > 1.2 * recent["volume"].mean():
            return Signal(symbol, "BUY", 0.75, "breakout", stop_price=row["close"] - row["atr"])
        if row["close"] < low_break and row["volume"] > 1.2 * recent["volume"].mean():
            return Signal(symbol, "SELL", 0.75, "breakout", stop_price=row["close"] + row["atr"])
        return None
