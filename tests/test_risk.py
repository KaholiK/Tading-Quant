from trading_system.risk.risk_manager import RiskManager, RiskConfig
from trading_system.data.cache import DataCache
from trading_system.core.events import SignalEvent, FillEvent


def test_risk_rejects_when_no_size():
    cache = DataCache()
    config = RiskConfig(max_positions=1, daily_loss_limit=1000, max_drawdown_pct=0.2, atr_period=14, risk_per_trade=0.01)
    risk = RiskManager(config, cache)
    signal = SignalEvent(symbol="SPY", direction="BUY")
    event = risk.evaluate(signal)
    assert not event.approved


def test_risk_limits_open_symbols():
    cache = DataCache()
    config = RiskConfig(max_positions=1, daily_loss_limit=1000, max_drawdown_pct=0.2, atr_period=14, risk_per_trade=0.01)
    risk = RiskManager(config, cache)
    risk.position_counts = {"SPY": 5, "QQQ": 0}
    signal = SignalEvent(symbol="AAPL", direction="BUY")
    event = risk.evaluate(signal)
    assert not event.approved and event.reason == "max positions reached"


def test_register_fill_updates_open_symbols():
    cache = DataCache()
    for price in [100, 101, 102]:
        cache.add("AAPL", price)
    config = RiskConfig(max_positions=1, daily_loss_limit=1000, max_drawdown_pct=0.2, atr_period=2, risk_per_trade=0.01)
    risk = RiskManager(config, cache)
    fill_buy = FillEvent(symbol="SPY", quantity=5, price=100.0, direction="BUY", commission=0.0, order_id="1")
    fill_sell = FillEvent(symbol="SPY", quantity=5, price=101.0, direction="SELL", commission=0.0, order_id="2")
    risk.register_fill(fill_buy)
    blocked = risk.evaluate(SignalEvent(symbol="AAPL", direction="BUY"))
    assert not blocked.approved and blocked.reason == "max positions reached"
    risk.register_fill(fill_sell)
    allowed = risk.evaluate(SignalEvent(symbol="AAPL", direction="BUY"))
    assert allowed.approved
