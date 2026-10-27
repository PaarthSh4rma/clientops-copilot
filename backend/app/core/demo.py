from collections import deque
from threading import Lock
from time import monotonic


class DemoChatLimiter:
    """Small process-local spend guard for a single-instance portfolio demo."""

    def __init__(self, hourly_limit: int):
        self.hourly_limit = hourly_limit
        self._requests: deque[float] = deque()
        self._lock = Lock()

    def consume(self) -> bool:
        cutoff = monotonic() - 3600
        with self._lock:
            while self._requests and self._requests[0] < cutoff:
                self._requests.popleft()
            if len(self._requests) >= self.hourly_limit:
                return False
            self._requests.append(monotonic())
            return True
