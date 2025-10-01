from __future__ import annotations
import json
import os
import sqlite3
import time
from typing import Any, Optional

from ..config import settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class Cache:
    def get_json(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    def set_json(self, key: str, value: Any, ttl_seconds: int = 600) -> None:
        raise NotImplementedError


class RedisCache(Cache):
    def __init__(self, url: str):
        assert redis is not None, "redis package not installed"
        self.client = redis.Redis.from_url(url)

    def get_json(self, key: str) -> Optional[Any]:
        raw = self.client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 600) -> None:
        self.client.setex(key, ttl_seconds, json.dumps(value))


class SQLiteCache(Cache):
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at INTEGER
                )
                """
            )
            conn.commit()

    def get_json(self, key: str) -> Optional[Any]:
        now = int(time.time())
        with sqlite3.connect(self.path) as conn:
            row = conn.execute("SELECT value, expires_at FROM cache WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        value, expires_at = row
        if expires_at and expires_at < now:
            # expired
            with sqlite3.connect(self.path) as conn:
                conn.execute("DELETE FROM cache WHERE key=?", (key,))
                conn.commit()
            return None
        try:
            return json.loads(value)
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 600) -> None:
        expires_at = int(time.time()) + ttl_seconds if ttl_seconds else None
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "REPLACE INTO cache(key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expires_at),
            )
            conn.commit()


def get_cache() -> Cache:
    # Auto-detect: prefer Redis if configured and available
    if settings.CACHE_BACKEND in ("auto", "redis") and settings.REDIS_URL and redis is not None:
        try:
            client = RedisCache(settings.REDIS_URL)
            # probe
            client.set_json("__probe__", {"ok": True}, ttl_seconds=1)
            _ = client.get_json("__probe__")
            return client
        except Exception:
            pass
    # Fallback to SQLite cache
    return SQLiteCache(settings.SQLITE_CACHE_PATH)

class CacheManager:
    """Manager for cache operations with async interface."""
    
    def __init__(self, cache: Optional[Cache] = None):
        self.cache = cache or get_cache()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache.get_json(key)
    
    async def set(self, key: str, value: Any, ttl: int = 600) -> None:
        """Set value in cache with TTL."""
        self.cache.set_json(key, value, ttl_seconds=ttl)
    
    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        # For now, we'll set a very short TTL to effectively delete
        self.cache.set_json(key, None, ttl_seconds=1)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.cache.get_json(key) is not None