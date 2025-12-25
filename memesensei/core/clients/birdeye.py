from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp


@dataclass(slots=True)
class HolderInfo:
    top10_ratio: float
    holders: int


class BirdeyeClient:
    def __init__(self, api_key: Optional[str] = None, session: Optional[aiohttp.ClientSession] = None):
        self.api_key = api_key
        self._session = session

    async def fetch_holder_info(self, address: str) -> Optional[HolderInfo]:
        if not self.api_key:
            return None
        headers = {"X-API-KEY": self.api_key}
        session = self._session or aiohttp.ClientSession()
        url = f"https://public-api.birdeye.so/public/token/holder/{address}"
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status != 200:
                return None
            data: Dict[str, Any] = await resp.json()
        if self._session is None:
            await session.close()
        stats = data.get("data", {})
        return HolderInfo(top10_ratio=float(stats.get("top10_holder_ratio", 0)), holders=int(stats.get("holder", 0)))

