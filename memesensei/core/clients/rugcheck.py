from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp


@dataclass(slots=True)
class RugCheckReport:
    address: str
    risk_score: float
    trust_score: float


class RugCheckClient:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self._session = session

    async def fetch(self, address: str) -> RugCheckReport:
        url = f"https://api.rugcheck.xyz/v1/solana/coins/{address}"
        session = self._session or aiohttp.ClientSession()
        async with session.get(url, timeout=10) as resp:
            resp.raise_for_status()
            data: Dict[str, Any] = await resp.json()
        if self._session is None:
            await session.close()
        risk = float(data.get("risk", 1))
        trust = float(data.get("trust", 0))
        return RugCheckReport(address=address, risk_score=risk, trust_score=trust)

    async def is_safe(self, address: str, threshold: float) -> tuple[bool, str]:
        try:
            report = await self.fetch(address)
        except Exception as exc:  # pragma: no cover - network failure branch
            return False, f"rugcheck_error:{exc}" 
        if report.risk_score > threshold:
            return False, "rugcheck_high_risk"
        return True, "ok"

