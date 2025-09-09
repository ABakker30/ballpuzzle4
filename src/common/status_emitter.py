# Timer-driven emitter wrapper, called by engines' existing timers
from __future__ import annotations
import threading
from typing import Callable, Optional
from .status_snapshot import Snapshot, atomic_write_json

class StatusEmitter:
    def __init__(self, path: str, interval_ms: int):
        self.path = path
        self.interval = max(50, int(interval_ms))
        self._timer: Optional[threading.Timer] = None
        self._provider: Optional[Callable[[], Snapshot]] = None
        self._running = False

    def start(self, provider: Callable[[], Snapshot]):
        self._provider = provider
        self._running = True
        self._schedule()

    def _schedule(self):
        if not self._running:
            return
        self._timer = threading.Timer(self.interval / 1000.0, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self):
        if not (self._running and self._provider):
            return
        try:
            snap = self._provider()
            atomic_write_json(self.path, snap.to_json_str())
        except Exception:
            # Silently continue on errors to avoid disrupting engine
            pass
        finally:
            self._schedule()

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
