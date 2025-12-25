import numpy as np
from .base import Strategy, direction_from_strength
from ..core.events import MarketDataEvent, SignalEvent
from ..data.cache import DataCache


class EMATrendStrategy(Strategy):
    def __init__(self, cache: DataCache, period: int = 3):
        self.cache = cache
        self.period = period

    def on_bar(self, event: MarketDataEvent) -> SignalEvent:
        self.cache.add(event.symbol, event.data.get("close", 0))
        prices = self.cache.history(event.symbol, self.period + 1)
        if len(prices) < self.period:
            return SignalEvent(symbol=event.symbol, direction="HOLD", strength=0.0, rationale="insufficient data")
        ema = np.mean(prices[-self.period :])
        strength = prices[-1] - ema
        return SignalEvent(
            symbol=event.symbol,
            direction=direction_from_strength(strength),
            strength=float(strength),
            rationale="ema_trend",
            features={"ema": float(ema), "last": float(prices[-1])},
        )
