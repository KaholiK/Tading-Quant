from __future__ import annotations

import httpx
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PairData:
    token_address: str
    pair_address: str
    liquidity_usd: float
    volume_5m_usd: float
    volume_1h_usd: float
    age_seconds: int


class DexScreenerClient:
    def __init__(self, base_url: str = "https://api.dexscreener.com/latest/dex"):
        self.base_url = base_url

    async def fetch_latest(self) -> List[PairData]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/pairs/solana/trending")
            resp.raise_for_status()
            data = resp.json()
            return self.parse_pairs(data)

    def parse_pairs(self, payload: Dict[str, Any]) -> List[PairData]:
        pairs = []
        for item in payload.get("pairs", []):
            pairs.append(
                PairData(
                    token_address=item.get("baseToken", {}).get("address", ""),
                    pair_address=item.get("pairAddress", ""),
                    liquidity_usd=float(item.get("liquidity", {}).get("usd", 0.0)),
                    volume_5m_usd=float(item.get("txns", {}).get("m5", {}).get("volume", 0.0)),
                    volume_1h_usd=float(item.get("txns", {}).get("h1", {}).get("volume", 0.0)),
                    age_seconds=int(item.get("age", 0)),
                )
            )
        return pairs
