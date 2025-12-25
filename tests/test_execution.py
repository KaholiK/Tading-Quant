from trading_system.execution.paper_broker import PaperBroker
from trading_system.core.event_bus import EventBus
from trading_system.core.events import OrderEvent, FillEvent


def test_paper_broker_publishes_fill():
    bus = EventBus()
    broker = PaperBroker(bus)
    order = OrderEvent(symbol="SPY", quantity=10, direction="BUY")
    broker.place_order(order, last_price=100)
    evt = bus.get()
    assert isinstance(evt, FillEvent)
