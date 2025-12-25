import logging
from typing import Optional
from ..core.events import OrderEvent, FillEvent
from ..core.event_bus import EventBus

logger = logging.getLogger(__name__)


class PaperBroker:
    def __init__(self, bus: Optional[EventBus], commission_per_share: float = 0.005, slippage_bps: float = 1):
        self.bus = bus
        self.commission_per_share = commission_per_share
        self.slippage_bps = slippage_bps

    def _build_fill(self, order: OrderEvent, last_price: float) -> FillEvent:
        slippage = last_price * (self.slippage_bps / 10000)
        fill_price = last_price + slippage if order.direction == "BUY" else last_price - slippage
        commission = order.quantity * self.commission_per_share
        return FillEvent(
            symbol=order.symbol,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            order_id=order.id,
            direction=order.direction,
        )

    def place_order(self, order: OrderEvent, last_price: float):
        fill = self._build_fill(order, last_price)
        logger.info("Paper fill generated %s", fill)
        if self.bus is None:
            raise RuntimeError("Event bus is required for live/paper order placement")
        self.bus.publish(fill)

    def simulate_fill(self, order: OrderEvent, last_price: float) -> FillEvent:
        """Generate a fill without publishing to the event bus (backtests)."""
        fill = self._build_fill(order, last_price)
        logger.info("Simulated fill generated %s", fill)
        return fill
