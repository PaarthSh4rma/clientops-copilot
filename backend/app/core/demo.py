from collections import OrderedDict, deque
from threading import Lock
from time import monotonic


class DemoChatLimiter:
    """A bounded, process-local soft limit for each anonymous browser session."""

    def __init__(self, hourly_limit: int):
        self.hourly_limit = hourly_limit
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def consume(self, visitor: str = "shared") -> bool:
        cutoff = monotonic() - 3600
        with self._lock:
            self._requests = {
                key: deque(stamp for stamp in stamps if stamp >= cutoff)
                for key, stamps in self._requests.items()
                if stamps and stamps[-1] >= cutoff
            }
            if visitor not in self._requests and len(self._requests) >= 1000:
                return False
            requests = self._requests.setdefault(visitor, deque())
            if len(requests) >= self.hourly_limit:
                return False
            requests.append(monotonic())
            return True


class DemoAnswerCache:
    """Reuse successful public-sample answers without retaining uploaded source material."""

    def __init__(self):
        self._entries = OrderedDict()
        self._lock = Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._entries.get(key)
            if entry and monotonic() - entry[0] < 3600:
                self._entries.move_to_end(key)
                return entry[1].model_copy(deep=True)
            self._entries.pop(key, None)
            return None

    def put(self, key: str, answer) -> None:
        with self._lock:
            self._entries[key] = (monotonic(), answer.model_copy(deep=True))
            self._entries.move_to_end(key)
            while len(self._entries) > 128:
                self._entries.popitem(last=False)
