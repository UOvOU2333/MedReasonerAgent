from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable


Listener = Callable[[dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self.listeners: list[Listener] = []
        self._events: list[dict[str, Any]] = []
        self._lock = Lock()

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        with self._lock:
            self.listeners.append(listener)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self.listeners:
                    self.listeners.remove(listener)

        return unsubscribe

    def emit(self, event: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "timestamp": datetime.now(timezone.utc).timestamp(),
            "state": {},
            **event,
        }
        with self._lock:
            self._events.append(payload)
            listeners = list(self.listeners)

        for listener in listeners:
            listener(payload)
        return payload

    def replay(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._events)


event_bus = EventBus()
