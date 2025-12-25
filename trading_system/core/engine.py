import logging
import threading
from typing import Callable, Dict, List
from .event_bus import EventBus
from .events import (
    Event,
    MarketDataEvent,
    SignalEvent,
    RiskEvent,
    OrderEvent,
    FillEvent,
    SystemEvent,
)
from .state import StateManager

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, bus: EventBus, handlers: Dict[str, List[Callable[[Event], None]]], state: StateManager):
        self.bus = bus
        self.handlers = handlers
        self.state = state
        self.running = False
        self.paused = False
        self.kill_switch_engaged = False
        self.thread = None
        self._stop_status = "STOP"
        self._stopping = False

    def start(self):
        if self.running:
            return
        logger.info("Engine starting")
        self.running = True
        self._stopping = False
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        logger.info("Engine stopping")
        self._stopping = True
        self.bus.publish(SystemEvent(status=self._stop_status, message="engine_stop"))
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        self.running = False

    def pause(self):
        logger.info("Engine paused")
        self.paused = True

    def resume(self):
        logger.info("Engine resumed")
        self.paused = False

    def engage_kill_switch(self, reason: str):
        logger.warning("Kill switch engaged: %s", reason)
        self.kill_switch_engaged = True
        self.bus.publish(SystemEvent(status="KILL", message=reason))

    def disengage_kill_switch(self):
        logger.info("Kill switch disengaged")
        self.kill_switch_engaged = False

    def flatten_all(self):
        logger.info("Flatten all requested")
        self.bus.publish(SystemEvent(status="FLATTEN", message="flatten_all"))

    def _run_loop(self):
        while self.running or self._stopping:
            event = self.bus.get(timeout=0.5)
            if event is None:
                if self._stopping:
                    break
                continue
            if isinstance(event, SystemEvent) and event.status == self._stop_status:
                self._stopping = True
                if len(self.bus) == 0:
                    break
                continue
            if self.kill_switch_engaged or self.paused:
                continue
            self._dispatch(event)
        self.running = False

    def _dispatch(self, event: Event):
        handlers = self.handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.exception("Handler error for %s: %s", event, exc)
