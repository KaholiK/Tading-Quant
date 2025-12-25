from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import httpx

from memesensei.core.config.models import RiskLimits
from memesensei.core.portfolio.state import PortfolioStore, Position, Trade


@dataclass
class Quote:
    in_amount: float
    out_amount: float
    slippage_bps: int


class ExecutionClient:
    def __init__(self, limits: RiskLimits, store: PortfolioStore, dry_run: bool = True):
        self.limits = limits
        self.store = store
        self.dry_run = dry_run

    async def fetch_quote(self, token: str, amount: float) -> Quote:
        # simplified placeholder
        return Quote(in_amount=amount, out_amount=amount * 0.99, slippage_bps=self.limits.slippage_bps)

    async def execute_swap(self, token: str, amount: float, price: float, reason: str) -> Trade:
        quote = await self.fetch_quote(token, amount)
        if quote.slippage_bps > self.limits.slippage_bps:
            raise ValueError("slippage too high")
        timestamp = time.time()
        position = Position(token=token, size=amount / price, entry_price=price, timestamp=timestamp)
        self.store.upsert_position(position)
        pnl = 0.0
        if self.dry_run:
            pnl = 0.0
        trade = Trade(token=token, side="buy", size=amount, price=price, pnl=pnl, timestamp=timestamp, reason=reason)
        self.store.record_trade(trade)
        return trade

    async def close_position(self, position: Position, price: float, reason: str) -> Trade:
        timestamp = time.time()
        pnl = (price - position.entry_price) * position.size
        trade = Trade(
            token=position.token,
            side="sell",
            size=position.size,
            price=price,
            pnl=pnl,
            timestamp=timestamp,
            reason=reason,
        )
        self.store.remove_position(position.token)
        self.store.record_trade(trade)
        return trade
