from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp


@dataclass(slots=True)
class Quote:
    in_amount: float
    out_amount: float
    slippage_bps: int


class JupiterClient:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self._session = session

    async def quote(self, in_amount: float, input_mint: str, output_mint: str, slippage_bps: int) -> Quote:
        session = self._session or aiohttp.ClientSession()
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": int(in_amount),
            "slippageBps": slippage_bps,
        }
        async with session.get("https://quote-api.jup.ag/v6/quote", params=params, timeout=10) as resp:
            resp.raise_for_status()
            data: Dict[str, Any] = await resp.json()
        if self._session is None:
            await session.close()
        out_amount = float(data.get("outAmount", 0))
        return Quote(in_amount=float(in_amount), out_amount=out_amount, slippage_bps=slippage_bps)

    async def swap(self, route: Quote) -> Dict[str, Any]:
        session = self._session or aiohttp.ClientSession()
        async with session.post("https://quote-api.jup.ag/v6/swap", json={}, timeout=10) as resp:
            resp.raise_for_status()
            data = await resp.json()
        if self._session is None:
            await session.close()
        return data

