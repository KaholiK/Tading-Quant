from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..clients.birdeye import BirdeyeClient
from ..clients.dexscreener import PairData
from ..clients.rugcheck import RugCheckClient
from ..utils import metrics


@dataclass(slots=True)
class SafetyDecision:
    allowed: bool
    reason: str


class SafetyGates:
    def __init__(self, config, rugcheck: RugCheckClient, birdeye: Optional[BirdeyeClient] = None):
        self.config = config
        self.rugcheck = rugcheck
        self.birdeye = birdeye

    async def evaluate(self, pair: PairData) -> SafetyDecision:
        if pair.liquidity_usd < self.config.min_liquidity_usd:
            metrics.blocked_total.labels(reason="liquidity").inc()
            return SafetyDecision(False, "liquidity_too_low")
        if pair.volume_5m < self.config.min_vol_5m_usd:
            metrics.blocked_total.labels(reason="volume_5m").inc()
            return SafetyDecision(False, "volume_5m_low")
        if pair.volume_1h < self.config.min_vol_1h_usd:
            metrics.blocked_total.labels(reason="volume_1h").inc()
            return SafetyDecision(False, "volume_1h_low")
        if pair.age_seconds < self.config.min_pair_age_seconds:
            metrics.blocked_total.labels(reason="age").inc()
            return SafetyDecision(False, "too_new")

        safe, reason = await self.rugcheck.is_safe(pair.address, self.config.rugcheck_threshold)
        if not safe:
            metrics.blocked_total.labels(reason=reason).inc()
            return SafetyDecision(False, reason)

        if self.birdeye:
            holder_info = await self.birdeye.fetch_holder_info(pair.address)
            if holder_info and holder_info.top10_ratio > 0.5:
                metrics.blocked_total.labels(reason="holder_concentration").inc()
                return SafetyDecision(False, "holder_concentration")

        return SafetyDecision(True, "ok")

