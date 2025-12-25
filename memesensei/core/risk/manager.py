from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..utils import metrics


@dataclass(slots=True)
class RiskDecision:
    allowed: bool
    reason: str


class RiskManager:
    def __init__(self, config):
        self.config = config
        self.daily_loss = 0.0
        self.open_positions_value = 0.0
        self.open_positions_count = 0
        self.last_trade_ts: Optional[float] = None
        self.loss_streak = 0

    def update_after_fill(self, pnl: float) -> None:
        if pnl < 0:
            self.loss_streak += 1
            self.daily_loss += abs(pnl)
        else:
            self.loss_streak = 0
        self.last_trade_ts = time.time()

    def can_open(self, size_usd: float, slippage_bps: int, liquidity_usd: float) -> RiskDecision:
        if self.config.kill_switch:
            return RiskDecision(False, "kill_switch")
        if self.open_positions_count >= self.config.max_open_positions:
            return RiskDecision(False, "max_open_positions")
        if self.daily_loss >= self.config.max_daily_loss_usd:
            return RiskDecision(False, "max_daily_loss")
        if size_usd > self.config.max_position_usd:
            return RiskDecision(False, "size_exceeds_limit")
        if slippage_bps > self.config.slippage_bps:
            return RiskDecision(False, "slippage_cap")
        if liquidity_usd < self.config.min_liquidity_usd:
            return RiskDecision(False, "insufficient_liquidity")
        now = time.time()
        if self.last_trade_ts and now - self.last_trade_ts < self.config.cooldown_seconds_after_trade:
            return RiskDecision(False, "cooldown")
        if self.loss_streak >= 2 and self.last_trade_ts and now - self.last_trade_ts < self.config.loss_streak_cooldown:
            return RiskDecision(False, "loss_streak_cooldown")
        return RiskDecision(True, "ok")

    def record_open(self, size_usd: float) -> None:
        self.open_positions_count += 1
        self.open_positions_value += size_usd
        metrics.open_positions.set(self.open_positions_count)

    def record_close(self, size_usd: float) -> None:
        self.open_positions_count = max(0, self.open_positions_count - 1)
        self.open_positions_value = max(0, self.open_positions_value - size_usd)
        metrics.open_positions.set(self.open_positions_count)

