import logging
from dataclasses import dataclass
from typing import Dict
from ..core.events import SignalEvent, RiskEvent, OrderEvent, FillEvent
from ..data.cache import DataCache
from .position_sizing import atr_based_size

logger = logging.getLogger(__name__)


@dataclass
class RiskConfig:
    max_positions: int
    daily_loss_limit: float
    max_drawdown_pct: float
    atr_period: int
    risk_per_trade: float


class RiskManager:
    def __init__(self, config: RiskConfig, cache: DataCache):
        self.config = config
        self.cache = cache
        self.position_counts: Dict[str, int] = {}
        self.daily_loss = 0.0
        self.max_equity = 100000.0

    def evaluate(self, signal: SignalEvent) -> RiskEvent:
        reason = ""
        approved = True
        open_symbols = sum(1 for qty in self.position_counts.values() if qty != 0)
        if open_symbols >= self.config.max_positions:
            approved = False
            reason = "max positions reached"
        quantity = atr_based_size(self.cache, signal.symbol, atr_period=self.config.atr_period, risk_per_trade=self.config.risk_per_trade)
        if quantity <= 0:
            approved = False
            reason = reason or "no size"
        event = RiskEvent(approved=approved, reason=reason, signal=signal)
        event.quantity = quantity  # attach for downstream
        return event

    def register_fill(self, fill: FillEvent):
        qty = self.position_counts.get(fill.symbol, 0)
        if fill.direction == "BUY":
            qty += fill.quantity
        else:
            qty -= fill.quantity
        self.position_counts[fill.symbol] = qty
