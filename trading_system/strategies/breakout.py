from .base import Strategy, direction_from_strength
from ..core.events import MarketDataEvent, SignalEvent
from ..data.cache import DataCache


class BreakoutStrategy(Strategy):
    def __init__(self, cache: DataCache, lookback: int = 3):
        self.cache = cache
        self.lookback = lookback

    def on_bar(self, event: MarketDataEvent) -> SignalEvent:
        self.cache.add(event.symbol, event.data.get("close", 0))
        prices = self.cache.history(event.symbol, self.lookback)
        if len(prices) < self.lookback:
            return SignalEvent(symbol=event.symbol, direction="HOLD", strength=0.0, rationale="insufficient data")
        breakout = prices[-1] - min(prices)
        direction = direction_from_strength(breakout)
        return SignalEvent(
            symbol=event.symbol,
            direction=direction,
            strength=float(breakout),
            rationale="breakout",
            features={"recent_min": float(min(prices)), "last": float(prices[-1])},
        )
