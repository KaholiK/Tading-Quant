import asyncio
import pytest

from memesensei.core.config.models import RiskLimits
from memesensei.core.execution.executor import ExecutionClient
from memesensei.core.portfolio.state import PortfolioStore


def store_temp():
    import tempfile
    path = tempfile.NamedTemporaryFile(delete=False)
    return path.name


async def _trade_flow():
    path = store_temp()
    store = PortfolioStore(db_path=path)
    exec_client = ExecutionClient(RiskLimits(), store, dry_run=True)
    trade = await exec_client.execute_swap("token", amount=100, price=1.0, reason="test")
    positions = store.list_positions()
    assert positions[0].token == "token"
    closed = await exec_client.close_position(positions[0], price=1.1, reason="exit")
    return trade, closed, store


def test_paper_trading_flow():
    trade, closed, store = asyncio.get_event_loop().run_until_complete(_trade_flow())
    assert trade.side == "buy"
    assert closed.side == "sell"
    assert closed.pnl == pytest.approx(0.1 * trade.size)
    assert store.realized_pnl() != 0
