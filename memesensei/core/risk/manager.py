from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from memesensei.core.config.models import RiskLimits


@dataclass
class RiskState:
    open_positions: int = 0
    daily_loss: float = 0.0
    last_trade_ts: float = 0.0
    loss_streak: int = 0


@dataclass
class RiskDecision:
    allowed: bool
    reason: Optional[str] = None


class RiskManager:
    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.state = RiskState()

    def record_trade(self, pnl: float) -> None:
        now = time.time()
        if pnl < 0:
            self.state.loss_streak += 1
            self.state.daily_loss += abs(pnl)
        else:
            self.state.loss_streak = 0
        self.state.last_trade_ts = now

    def update_open_positions(self, count: int) -> None:
        self.state.open_positions = count

    def can_open_position(self, liquidity: float, vol_5m: float, vol_1h: float, pair_age: int) -> RiskDecision:
        now = time.time()
        if self.state.open_positions >= self.limits.max_open_positions:
            return RiskDecision(False, "max open positions")
        if self.state.daily_loss >= self.limits.max_daily_loss_usd:
            return RiskDecision(False, "daily loss limit")
        if liquidity < self.limits.min_liquidity_usd:
            return RiskDecision(False, "low liquidity")
        if vol_5m < self.limits.min_vol_5m_usd or vol_1h < self.limits.min_vol_1h_usd:
            return RiskDecision(False, "volume below threshold")
        if pair_age < self.limits.min_pair_age_seconds:
            return RiskDecision(False, "pair too new")
        if now - self.state.last_trade_ts < self.limits.cooldown_seconds_after_trade:
            return RiskDecision(False, "cooldown active")
        if self.state.loss_streak >= self.limits.loss_streak_cooldown:
            return RiskDecision(False, "loss streak cooldown")
        return RiskDecision(True, None)
