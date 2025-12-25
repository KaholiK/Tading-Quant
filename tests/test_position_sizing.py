from trading_system.risk.position_sizing import atr_based_size
from trading_system.data.cache import DataCache


def test_atr_based_size_positive():
    cache = DataCache()
    for price in [100, 101, 102, 103]:
        cache.add("SPY", price)
    size = atr_based_size(cache, "SPY")
    assert size > 0
