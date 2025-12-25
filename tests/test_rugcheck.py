import asyncio
import pytest

from memesensei.core.clients.rugcheck import RugCheckClient, RugCheckReport
from memesensei.core.safety.gates import SafetyGates
from memesensei.core.clients.dexscreener import PairData
from memesensei.core.config import CoreConfig


class DummyRug(RugCheckClient):
    def __init__(self, report: RugCheckReport):
        super().__init__(session=None)
        self.report = report

    async def fetch(self, address: str):
        return self.report


def pair():
    return PairData(
        address="token",
        base_token="AAA",
        quote_token="USDC",
        price_usd=0.1,
        liquidity_usd=12000,
        volume_5m=6000,
        volume_1h=22000,
        age_seconds=4000,
    )


@pytest.mark.asyncio
async def test_rugcheck_blocks_high_risk():
    config = CoreConfig()
    rug = DummyRug(RugCheckReport(address="token", risk_score=0.9, trust_score=0.1))
    gates = SafetyGates(config, rugcheck=rug, birdeye=None)
    decision = await gates.evaluate(pair())
    assert decision.allowed is False
    assert decision.reason == "rugcheck_high_risk"


@pytest.mark.asyncio
async def test_rugcheck_passes_safe():
    config = CoreConfig()
    rug = DummyRug(RugCheckReport(address="token", risk_score=0.1, trust_score=0.9))
    gates = SafetyGates(config, rugcheck=rug, birdeye=None)
    decision = await gates.evaluate(pair())
    assert decision.allowed is True
    assert decision.reason == "ok"

