import time
from threading import Event as ThreadEvent
from trading_system.core.engine import Engine
from trading_system.core.event_bus import EventBus
from trading_system.core.events import Event
from trading_system.core.state import StateManager


def test_engine_dispatch():
    bus = EventBus()
    state = StateManager(db_path=":memory:")
    triggered = ThreadEvent()

    def handler(evt):
        triggered.set()

    engine = Engine(bus, {"TEST": [handler]}, state)
    engine.start()
    bus.publish(Event(type="TEST"))
    assert triggered.wait(timeout=1)
    engine.stop()


def test_engine_stop_unblocks():
    bus = EventBus()
    state = StateManager(db_path=":memory:")
    engine = Engine(bus, {}, state)
    engine.start()
    start = time.time()
    engine.stop()
    assert engine.thread is None or not engine.thread.is_alive()
    assert time.time() - start < 1


def test_engine_stop_while_paused_and_killed():
    bus = EventBus()
    state = StateManager(db_path=":memory:")
    engine = Engine(bus, {}, state)
    engine.start()
    engine.pause()
    engine.engage_kill_switch("test")
    engine.stop()
    assert engine.thread is None or not engine.thread.is_alive()
