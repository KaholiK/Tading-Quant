import queue
from typing import Optional
from .events import Event


class EventBus:
    """Thread-safe event bus using a queue with timeout support."""

    def __init__(self):
        self.queue: "queue.Queue[Event]" = queue.Queue()

    def publish(self, event: Event) -> None:
        self.queue.put(event)

    def get(self, timeout: Optional[float] = None) -> Optional[Event]:
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def __len__(self):
        return self.queue.qsize()
