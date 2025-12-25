from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


def _now():
    return datetime.utcnow()


@dataclass
class Event:
    type: str = ""
    timestamp: datetime = field(default_factory=_now)


@dataclass
class MarketDataEvent(Event):
    symbol: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.type = "MARKET"


@dataclass
class SignalEvent(Event):
    symbol: str = ""
    direction: str = "HOLD"
    strength: float = 0.0
    rationale: str = ""
    features: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.type = "SIGNAL"


@dataclass
class RiskEvent(Event):
    approved: bool = False
    reason: str = ""
    signal: Optional[SignalEvent] = None

    def __post_init__(self):
        self.type = "RISK"


@dataclass
class OrderEvent(Event):
    symbol: str = ""
    quantity: int = 0
    order_type: str = "MKT"
    direction: str = "BUY"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        self.type = "ORDER"


@dataclass
class FillEvent(Event):
    symbol: str = ""
    quantity: int = 0
    price: float = 0.0
    commission: float = 0.0
    order_id: str = ""
    direction: str = ""

    def __post_init__(self):
        self.type = "FILL"
        if self.direction not in {"BUY", "SELL"}:
            raise ValueError("FillEvent.direction must be 'BUY' or 'SELL'")


@dataclass
class SystemEvent(Event):
    status: str = ""
    message: str = ""

    def __post_init__(self):
        self.type = "SYSTEM"


@dataclass
class PositionEvent(Event):
    symbol: str = ""
    quantity: int = 0
    avg_price: float = 0.0

    def __post_init__(self):
        self.type = "POSITION"


__all__ = [
    "Event",
    "MarketDataEvent",
    "SignalEvent",
    "RiskEvent",
    "OrderEvent",
    "FillEvent",
    "SystemEvent",
    "PositionEvent",
]
