import numpy as np
from ..data.cache import DataCache


def atr_based_size(cache: DataCache, symbol: str, equity: float = 100000, atr_period: int = 14, risk_per_trade: float = 0.01):
    prices = cache.history(symbol, atr_period + 1)
    if len(prices) < 2:
        return 0
    diffs = np.abs(np.diff(prices))
    atr = np.mean(diffs) if len(diffs) else 0.5
    risk_amount = equity * risk_per_trade
    size = int(risk_amount / max(atr, 0.5))
    return max(size, 1)
