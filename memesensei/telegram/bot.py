from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, List

import httpx

from memesensei.core.config.models import Config, load_config

logger = logging.getLogger(__name__)


@dataclass
class CommandResponse:
    message: str
    allowed: bool = True


class TelegramController:
    def __init__(self, config: Config | None = None, client: httpx.AsyncClient | None = None):
        self.config = config or load_config()
        self.client = client or httpx.AsyncClient()
        self.admin_ids = {int(i) for i in self.config.admin_telegram_ids}

    def _is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    async def _post(self, path: str, **kwargs):
        url = f"http://localhost:{self.config.core_api_port}{path}"
        resp = await self.client.post(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def _get(self, path: str):
        url = f"http://localhost:{self.config.core_api_port}{path}"
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def handle_command(self, user_id: int, command: str, args: List[str] | None = None) -> CommandResponse:
        if not self._is_admin(user_id):
            logger.warning("Rejected unauthorized user %s", user_id)
            return CommandResponse("Unauthorized", allowed=False)
        args = args or []
        if command == "/start":
            status = await self._get("/status")
            mode = "DRY_RUN" if status.get("dry_run") else "LIVE"
            return CommandResponse(f"MemeSensei online. Mode: {mode}")
        if command == "/status":
            status = await self._get("/status")
            return CommandResponse(str(status))
        if command == "/positions":
            positions = await self._get("/positions")
            return CommandResponse(str(positions))
        if command == "/pnl":
            trades = await self._get("/trades")
            pnl = sum([t.get("pnl", 0) for t in trades])
            return CommandResponse(f"Realized PnL: {pnl:.2f}")
        if command == "/recent":
            decisions = await self._get("/decisions")
            return CommandResponse(str(decisions[:5]))
        if command == "/pause":
            await self._post("/control/pause")
            return CommandResponse("Paused entries")
        if command == "/resume":
            await self._post("/control/resume")
            return CommandResponse("Resumed entries")
        if command == "/killswitch":
            await self._post("/control/killswitch", params={"state": True})
            return CommandResponse("Kill switch enabled")
        if command.startswith("/setrisk") and len(args) == 2:
            key, value = args
            await self._post("/control/setrisk", params={"key": key, "value": float(value)})
            return CommandResponse(f"Updated {key} to {value}")
        return CommandResponse("Unknown command")
