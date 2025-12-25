from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp


@dataclass(slots=True)
class PairData:
    address: str
    base_token: str
    quote_token: str
    price_usd: float
    liquidity_usd: float
    volume_5m: float
    volume_1h: float
    age_seconds: int


class DexScreenerClient:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None, retry_limit: int = 3):
        self._session = session
        self.retry_limit = retry_limit

    async def _get(self, url: str) -> Dict[str, Any]:
        attempts = 0
        while True:
            try:
                session = self._session or aiohttp.ClientSession()
                async with session.get(url, timeout=10) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    if self._session is None:
                        await session.close()
                    return data
            except Exception:
                attempts += 1
                if attempts >= self.retry_limit:
                    raise
                await asyncio.sleep(0.2 * attempts)

    async def fetch_latest_boosts(self) -> List[PairData]:
        data = await self._get("https://api.dexscreener.com/latest/dex/pairs/solana")
        return [self._parse_pair(item) for item in data.get("pairs", [])]

    async def fetch_pair(self, address: str) -> Optional[PairData]:
        data = await self._get(f"https://api.dexscreener.com/latest/dex/pairs/solana/{address}")
        pairs = data.get("pairs", [])
        if not pairs:
            return None
        return self._parse_pair(pairs[0])

    def _parse_pair(self, item: Dict[str, Any]) -> PairData:
        info = item.get("info", {})
        txns = item.get("txns", {})
        volume = item.get("volume", {})
        age_seconds = int(item.get("age", {}).get("since", 0))
        return PairData(
            address=item.get("pairAddress", ""),
            base_token=info.get("baseToken", {}).get("symbol", ""),
            quote_token=info.get("quoteToken", {}).get("symbol", ""),
            price_usd=float(info.get("priceUsd", item.get("priceUsd", 0)) or 0),
            liquidity_usd=float(item.get("liquidity", {}).get("usd", 0)),
            volume_5m=float(volume.get("m5", 0)),
            volume_1h=float(volume.get("h1", 0)),
            age_seconds=age_seconds,
        )


__all__ = ["DexScreenerClient", "PairData"]
