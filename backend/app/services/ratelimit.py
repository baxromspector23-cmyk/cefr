"""Oddiy xotiradagi login limiter (bitta server jarayoni uchun).
Bir nechta server bo'lsa, keyinroq Redis'ga o'tkaziladi."""
import time
from collections import defaultdict, deque

MAX_FAILS = 5
WINDOW_SEC = 15 * 60

_fails: dict[str, deque] = defaultdict(deque)


def _prune(key: str) -> deque:
    q = _fails[key]
    limit = time.monotonic() - WINDOW_SEC
    while q and q[0] < limit:
        q.popleft()
    return q


def is_blocked(key: str) -> bool:
    return len(_prune(key)) >= MAX_FAILS


def register_fail(key: str) -> None:
    _prune(key).append(time.monotonic())


def reset(key: str) -> None:
    _fails.pop(key, None)
