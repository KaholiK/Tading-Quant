from memesensei.core.config.models import RiskLimits
from memesensei.core.risk.manager import RiskManager


def test_risk_manager_blocks_open_position_limit(monkeypatch):
    limits = RiskLimits(max_open_positions=1)
    manager = RiskManager(limits)
    manager.update_open_positions(1)
    decision = manager.can_open_position(liquidity=1e6, vol_5m=1e6, vol_1h=1e6, pair_age=9999)
    assert not decision.allowed
    assert decision.reason == "max open positions"


def test_risk_manager_enforces_liquidity_and_volume():
    limits = RiskLimits(min_liquidity_usd=50000, min_vol_5m_usd=1000, min_vol_1h_usd=2000)
    manager = RiskManager(limits)
    decision = manager.can_open_position(liquidity=1000, vol_5m=500, vol_1h=500, pair_age=9999)
    assert not decision.allowed
    assert decision.reason in {"low liquidity", "volume below threshold"}
