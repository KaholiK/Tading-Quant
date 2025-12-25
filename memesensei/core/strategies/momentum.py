from __future__ import annotations

from dataclasses import dataclass

from ..clients.dexscreener import PairData


@dataclass(slots=True)
class StrategySignal:
    action: str
    confidence: float


class MomentumStrategy:
    def __init__(self, config):
        self.config = config

    def generate(self, pair: PairData) -> StrategySignal | None:
        liquidity_ok = pair.liquidity_usd >= self.config.min_liquidity_usd
        volume_spike = pair.volume_5m > (self.config.min_vol_5m_usd * 1.5)
        if liquidity_ok and volume_spike:
            return StrategySignal(action="buy", confidence=0.75)
        return None

