# apps/core/cache.py
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis
from apps.api.settings import get_settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_cache() -> Optional[redis.Redis]:
    global _redis_client

    settings = get_settings()
    redis_url = getattr(settings, "redis_url", None)

    if not redis_url:
        return None

    if _redis_client is None:
        try:
            _redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
            )
            _redis_client.ping()
        except Exception:
            logger.exception("Redis cache unavailable")
            _redis_client = None

    return _redis_client


def cache_get(key: str) -> Any | None:
    client = get_cache()
    if not client:
        return None

    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception:
        logger.exception("Cache get failed: %s", key)
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> None:
    client = get_cache()
    if not client:
        return

    try:
        client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception:
        logger.exception("Cache set failed: %s", key)


def cache_delete(key: str) -> None:
    client = get_cache()
    if not client:
        return

    try:
        client.delete(key)
    except Exception:
        logger.exception("Cache delete failed: %s", key)

def cache_delete_pattern(pattern: str) -> None:
    client = get_cache()
    if not client:
        return

    try:
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)

            if keys:
                client.delete(*keys)

            if cursor == 0:
                break

    except Exception:
        logger.exception("Cache delete pattern failed: %s", pattern)