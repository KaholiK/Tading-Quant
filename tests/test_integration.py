import asyncio
import time

import pytest

from memesensei.core.config.models import Config, RiskLimits
from memesensei.core.scanners.dexscreener import PairData
from memesensei.core.service import CoreService


@pytest.mark.asyncio
async def test_core_run_dry_run(monkeypatch, tmp_path):
    cfg = Config(dry_run=True, risk_limits=RiskLimits(max_position_usd=10))
    service = CoreService(cfg)

    async def fake_fetch_latest():
        return [
            PairData(
                token_address="token1",
                pair_address="pair1",
                liquidity_usd=100000,
                volume_5m_usd=20000,
                volume_1h_usd=80000,
                age_seconds=5000,
            )
        ]

    monkeypatch.setattr(service.scanner, "fetch_latest", fake_fetch_latest)
    await service.run(run_seconds=2)
    trades = service.store.list_trades()
    assert trades, "expected at least one simulated trade"
    assert service.status()["dry_run"]
    assert not service.kill_switch

    service.toggle_kill(True)
    await service.run_once()
    assert service.status()["kill_switch"]
