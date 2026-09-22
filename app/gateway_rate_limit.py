from __future__ import annotations
import time
from collections import defaultdict, deque

class SlidingWindowRateLimiter:
    def __init__(self, limit: int = 20, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.events = defaultdict(deque)

    def allow(self, identity: str) -> bool:
        now = time.time()
        q = self.events[identity]
        while q and q[0] <= now - self.window_seconds:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
