import json
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def _safe_call(coro):
    try:
        return await coro
    except (RedisConnectionError, RedisTimeoutError):
        return None


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    data = await _safe_call(r.get(key))
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    await _safe_call(r.setex(key, ttl, json.dumps(value, default=str)))


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await _safe_call(r.delete(key))


async def cache_delete_pattern(pattern: str) -> None:
    r = await get_redis()
    cursor = 0
    while True:
        try:
            cursor, keys = await r.scan(cursor=cursor, match=pattern)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break
        except (RedisConnectionError, RedisTimeoutError):
            break


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
