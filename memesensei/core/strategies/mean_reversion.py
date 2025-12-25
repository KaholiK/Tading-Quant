from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MeanReversionWindow:
    price: float
    average: float
    std: float


class MeanReversionStrategy:
    def __init__(self, exit_after_seconds: int = 300):
        self.exit_after_seconds = exit_after_seconds

    def generate_signal(self, window: MeanReversionWindow) -> str:
        if window.price < window.average - window.std:
            return "buy"
        if window.price > window.average + window.std:
            return "sell"
        return "hold"
