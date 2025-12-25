from memesensei.core.config import CoreConfig
from memesensei.core.risk.manager import RiskManager


def test_risk_blocks_on_limits():
    cfg = CoreConfig(max_open_positions=0)
    risk = RiskManager(cfg)
    decision = risk.can_open(size_usd=100, slippage_bps=10, liquidity_usd=20000)
    assert decision.allowed is False
    assert decision.reason == "max_open_positions"


def test_risk_blocks_slippage():
    cfg = CoreConfig(slippage_bps=50)
    risk = RiskManager(cfg)
    decision = risk.can_open(size_usd=100, slippage_bps=100, liquidity_usd=20000)
    assert decision.allowed is False
    assert decision.reason == "slippage_cap"


def test_risk_allows_when_within_limits():
    cfg = CoreConfig()
    risk = RiskManager(cfg)
    decision = risk.can_open(size_usd=100, slippage_bps=10, liquidity_usd=20000)
    assert decision.allowed is True

