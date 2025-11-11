from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional, Tuple


class TTLCache:
    """Simple in-memory TTL cache (process-local).

    Not shared across processes; safe enough for single-worker dev usage.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at and expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        expires_at = time.time() + max(0, int(ttl)) if ttl else 0
        self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


_cache = TTLCache()


def cached(ttl: int = 60, key_builder: Optional[Callable[..., str]] = None):
    """Decorator for simple memoization with TTL.

    Example:
        @cached(ttl=120)
        def expensive(a, b):
            ...
    """

    def _decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def _wrapper(*args: Any, **kwargs: Any) -> Any:
            key = key_builder(*args, **kwargs) if key_builder else f"{fn.__module__}:{fn.__name__}:{args}:{sorted(kwargs.items())}"
            val = _cache.get(key)
            if val is not None:
                return val
            res = fn(*args, **kwargs)
            _cache.set(key, res, ttl=ttl)
            return res

        return _wrapper

    return _decorator


def cache_get(key: str) -> Optional[Any]:
    return _cache.get(key)


def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    _cache.set(key, value, ttl)


def cache_delete(key: str) -> None:
    _cache.delete(key)


def cache_clear() -> None:
    _cache.clear()
