import numpy as np
from .base import Strategy, direction_from_strength
from ..core.events import MarketDataEvent, SignalEvent
from ..data.cache import DataCache


class MeanReversionStrategy(Strategy):
    def __init__(self, cache: DataCache, window: int = 5):
        self.cache = cache
        self.window = window

    def on_bar(self, event: MarketDataEvent) -> SignalEvent:
        self.cache.add(event.symbol, event.data.get("close", 0))
        prices = self.cache.history(event.symbol, self.window)
        if len(prices) < self.window:
            return SignalEvent(symbol=event.symbol, direction="HOLD", strength=0.0, rationale="insufficient data")
        mean = float(np.mean(prices))
        strength = mean - prices[-1]
        return SignalEvent(
            symbol=event.symbol,
            direction=direction_from_strength(strength),
            strength=float(strength),
            rationale="mean_reversion",
            features={"mean": mean, "last": float(prices[-1])},
        )
