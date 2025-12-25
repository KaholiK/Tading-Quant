from memesensei.core.strategies.momentum import MomentumBreakoutStrategy, MarketSnapshot
from memesensei.core.strategies.mean_reversion import MeanReversionStrategy, MeanReversionWindow


def test_momentum_breakout_signal():
    strat = MomentumBreakoutStrategy(min_volume=1000, min_liquidity=5000)
    snap = MarketSnapshot(price=1.0, volume_5m=2000, liquidity=6000)
    assert strat.generate_signal(snap) == "buy"


def test_mean_reversion_signal():
    strat = MeanReversionStrategy(exit_after_seconds=60)
    window = MeanReversionWindow(price=0.8, average=1.0, std=0.1)
    assert strat.generate_signal(window) == "buy"
    window2 = MeanReversionWindow(price=1.2, average=1.0, std=0.1)
    assert strat.generate_signal(window2) == "sell"
