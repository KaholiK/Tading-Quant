from __future__ import annotations

from dataclasses import dataclass

from ..clients.dexscreener import PairData


@dataclass(slots=True)
class ReversionSignal:
    action: str
    confidence: float


class MeanReversionStrategy:
    def __init__(self, config):
        self.config = config

    def generate(self, pair: PairData) -> ReversionSignal | None:
        if pair.volume_1h == 0:
            return None
        price_to_liquidity = pair.price_usd / max(pair.liquidity_usd, 1)
        if price_to_liquidity < 0.00005 and pair.volume_1h > self.config.min_vol_1h_usd:
            return ReversionSignal(action="buy", confidence=0.55)
        return None

