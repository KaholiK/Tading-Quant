import logging
from abc import ABC, abstractmethod
from typing import Dict
from ..core.events import MarketDataEvent, SignalEvent

logger = logging.getLogger(__name__)


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, event: MarketDataEvent) -> SignalEvent:
        ...


def direction_from_strength(strength: float) -> str:
    if strength > 0:
        return "BUY"
    if strength < 0:
        return "SELL"
    return "HOLD"
