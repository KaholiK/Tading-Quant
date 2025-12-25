import logging
from ..core.events import OrderEvent, FillEvent
from ..core.state import StateManager

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, state: StateManager):
        self.state = state

    def record_order(self, order: OrderEvent):
        self.state.insert(
            "INSERT OR REPLACE INTO orders(id, symbol, quantity, direction, timestamp) VALUES(?,?,?,?,?)",
            (order.id, order.symbol, order.quantity, order.direction, str(order.timestamp)),
        )
        logger.info("Order recorded %s", order)

    def record_fill(self, fill: FillEvent):
        self.state.insert(
            "INSERT INTO fills(order_id, symbol, quantity, price, commission, timestamp) VALUES(?,?,?,?,?,?)",
            (fill.order_id, fill.symbol, fill.quantity, fill.price, fill.commission, str(fill.timestamp)),
        )
