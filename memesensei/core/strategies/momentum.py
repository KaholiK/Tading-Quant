from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class MarketSnapshot:
    price: float
    volume_5m: float
    liquidity: float


class MomentumBreakoutStrategy:
    def __init__(self, min_volume: float, min_liquidity: float):
        self.min_volume = min_volume
        self.min_liquidity = min_liquidity

    def generate_signal(self, snapshot: MarketSnapshot) -> str:
        if snapshot.volume_5m >= self.min_volume and snapshot.liquidity >= self.min_liquidity:
            return "buy"
        return "hold"
