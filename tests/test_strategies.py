from trading_system.strategies.ema_trend import EMATrendStrategy
from trading_system.strategies.mean_reversion import MeanReversionStrategy
from trading_system.strategies.breakout import BreakoutStrategy
from trading_system.data.cache import DataCache
from trading_system.core.events import MarketDataEvent


def test_strategies_generate_signals():
    cache = DataCache()
    event = MarketDataEvent(symbol="SPY", data={"close": 100})
    ema = EMATrendStrategy(cache)
    mean = MeanReversionStrategy(cache)
    bo = BreakoutStrategy(cache)
    cache.add("SPY", 100)
    cache.add("SPY", 101)
    cache.add("SPY", 102)
    assert ema.on_bar(event).type == "SIGNAL"
    assert mean.on_bar(event).type == "SIGNAL"
    assert bo.on_bar(event).type == "SIGNAL"
