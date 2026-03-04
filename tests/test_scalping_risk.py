from trading_system.scalping.config import BotConfig
from trading_system.scalping.risk import PropRiskManager
from trading_system.scalping.strategy import Signal


def test_reject_when_kill_switch_active():
    cfg = BotConfig()
    rm = PropRiskManager(cfg)
    rm.trading_halted = True
    decision = rm.check(Signal("SPY", "BUY", 0.7, "trend_pullback", 99), price=100)
    assert not decision.approved


def test_size_respects_risk_budget():
    cfg = BotConfig()
    cfg.risk.risk_per_trade_pct = 0.001
    rm = PropRiskManager(cfg)
    d = rm.check(Signal("SPY", "BUY", 0.7, "trend_pullback", 99), price=100)
    assert d.approved
    assert d.quantity > 0


def test_daily_loss_halts_trading():
    cfg = BotConfig()
    cfg.limits.daily_max_loss_pct = 0.01
    rm = PropRiskManager(cfg)
    rm.register_pnl(-cfg.starting_equity * 0.02)
    assert rm.trading_halted
