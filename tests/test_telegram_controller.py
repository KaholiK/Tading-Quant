import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from memesensei.core.config.models import Config, RiskLimits
from memesensei.telegram.bot import TelegramController


class MockTransport(httpx.MockTransport):
    def __init__(self, handler):
        super().__init__(handler)


def test_telegram_rejects_non_admin():
    config = Config(admin_telegram_ids=[123])
    controller = TelegramController(config=config, client=httpx.AsyncClient())
    resp = asyncio.get_event_loop().run_until_complete(controller.handle_command(999, "/status"))
    assert not resp.allowed
    assert resp.message == "Unauthorized"


@pytest.mark.asyncio
async def test_telegram_routes_commands():
    async def handler(request: httpx.Request):
        if request.url.path == "/status":
            return httpx.Response(200, json={"dry_run": True})
        if request.url.path == "/positions":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={})

    transport = MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://localhost:8000")
    config = Config(admin_telegram_ids=[1])
    controller = TelegramController(config=config, client=client)
    resp = await controller.handle_command(1, "/start")
    assert "DRY_RUN" in resp.message
    resp = await controller.handle_command(1, "/positions")
    assert resp.allowed
