from trading_system.core.event_bus import EventBus
from trading_system.core.events import Event

def test_event_bus_publish_get():
    bus = EventBus()
    bus.publish(Event(type="TEST"))
    evt = bus.get(timeout=0.1)
    assert evt is not None and evt.type == "TEST"
