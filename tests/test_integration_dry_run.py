import asyncio
import pytest

from memesensei.core.config import CoreConfig
from memesensei.core.service import CoreService
from memesensei.core.clients.dexscreener import PairData
from memesensei.core.clients.rugcheck import RugCheckClient, RugCheckReport
from memesensei.core.clients.jupiter import JupiterClient, Quote


class StubDex:
    def __init__(self, pair: PairData):
        self.pair = pair
        self.calls = 0

    async def fetch_latest_boosts(self):
        self.calls += 1
        return [self.pair]


class SafeRug(RugCheckClient):
    async def fetch(self, address: str):
        return RugCheckReport(address=address, risk_score=0.1, trust_score=0.9)


class StubJupiter(JupiterClient):
    async def quote(self, in_amount: float, input_mint: str, output_mint: str, slippage_bps: int):
        return Quote(in_amount=in_amount, out_amount=in_amount * 2, slippage_bps=slippage_bps)

    async def swap(self, route: Quote):
        return {"txid": "ok"}


@pytest.mark.asyncio
async def test_core_runs_dry_run_loop(tmp_path, monkeypatch):
    pair = PairData(
        address="token",
        base_token="AAA",
        quote_token="USDC",
        price_usd=0.1,
        liquidity_usd=12000,
        volume_5m=6000,
        volume_1h=22000,
        age_seconds=4000,
    )
    cfg = CoreConfig(dry_run=True, kill_switch=False)
    monkeypatch.setenv("MEMESENSEI_DB_PATH", str(tmp_path / "state.db"))
    service = CoreService(
        config=cfg,
        store=None,
        dex=StubDex(pair),
        rugcheck=SafeRug(),
        birdeye=None,
        jupiter=StubJupiter(),
    )

    await service.run(duration_seconds=1, loop_sleep=0.0)
    decisions = service.store.list_decisions()
    assert decisions, "decisions recorded"
    trades = service.store.list_trades()
    assert trades, "trade executed in dry run"

