"""A small in-process cache of each user's effective permissions.

Permissions are read from the database, and every request needs them, so they are cached briefly (60 seconds by
default). Anything that changes a role or an assignment calls `invalidate_user` / `invalidate_all`, which clears this
process's cache immediately; other worker processes see the change within the time limit. A time limit of 0 turns
the cache off.
"""

import time

from app.core.config import settings

_cache: dict[str, tuple[float, frozenset[str]]] = {}


def get(user_id: str) -> frozenset[str] | None:
    ttl = settings.PERMISSION_CACHE_SECONDS
    if ttl <= 0:
        return None
    hit = _cache.get(user_id)
    if hit is None or hit[0] < time.monotonic():
        _cache.pop(user_id, None)
        return None
    return hit[1]


def put(user_id: str, permissions: frozenset[str]) -> None:
    ttl = settings.PERMISSION_CACHE_SECONDS
    if ttl > 0:
        _cache[user_id] = (time.monotonic() + ttl, permissions)


def invalidate_user(user_id: str) -> None:
    _cache.pop(user_id, None)


def invalidate_all() -> None:
    _cache.clear()
