import asyncio
import pytest

from memesensei.core.config import CoreConfig
from memesensei.core.execution.executor import Executor
from memesensei.core.clients.jupiter import JupiterClient, Quote


class DummyJupiter(JupiterClient):
    async def quote(self, in_amount: float, input_mint: str, output_mint: str, slippage_bps: int):
        return Quote(in_amount=in_amount, out_amount=in_amount * 2, slippage_bps=slippage_bps)

    async def swap(self, route: Quote):  # pragma: no cover - unused in dry run
        return {"txid": "live"}


@pytest.mark.asyncio
async def test_dry_run_returns_simulation():
    cfg = CoreConfig(dry_run=True)
    executor = Executor(cfg, DummyJupiter())
    result = await executor.execute_swap(10, "USDC", "TOKEN")
    assert result.simulated is True
    assert result.txid == "dry-run"
    assert result.received == 20

