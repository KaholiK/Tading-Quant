from memesensei.core.config import CoreConfig
from memesensei.core.clients.dexscreener import PairData
from memesensei.core.strategies.momentum import MomentumStrategy
from memesensei.core.strategies.mean_reversion import MeanReversionStrategy


def pair(volume_5m=8000, price=0.1, liquidity=15000, volume_1h=30000):
    return PairData(
        address="x",
        base_token="AAA",
        quote_token="USDC",
        price_usd=price,
        liquidity_usd=liquidity,
        volume_5m=volume_5m,
        volume_1h=volume_1h,
        age_seconds=4000,
    )


def test_momentum_signal_triggers_on_volume_spike():
    strategy = MomentumStrategy(CoreConfig())
    signal = strategy.generate(pair())
    assert signal is not None
    assert signal.action == "buy"


def test_mean_reversion_triggers_on_low_price_to_liquidity():
    strategy = MeanReversionStrategy(CoreConfig())
    signal = strategy.generate(pair(price=0.1, liquidity=500000, volume_1h=50000))
    assert signal is not None
    assert signal.action == "buy"


def test_no_signal_when_conditions_not_met():
    strategy = MomentumStrategy(CoreConfig())
    assert strategy.generate(pair(volume_5m=1000)) is None

