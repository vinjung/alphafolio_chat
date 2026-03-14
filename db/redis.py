import redis.asyncio as redis
from redis.asyncio.client import Redis
from typing import Optional
from pydantic_settings import BaseSettings

_cache_redis: Optional[Redis] = None
_stream_redis: Optional[Redis] = None
_task_redis: Optional[Redis] = None


def create_redis_clients(env: BaseSettings):
    global _cache_redis, _stream_redis, _task_redis

    if _cache_redis is None:
        _cache_redis = redis.Redis.from_url(
            f"{env.REDIS_URL}/{env.REDIS_CACHING_INDEX}",
            decode_responses=True
        )

    if _stream_redis is None:
        _stream_redis = redis.Redis.from_url(
            f"{env.REDIS_URL}/{env.REDIS_STREAM_INDEX}",
            decode_responses=True
        )

    if _task_redis is None:
        _task_redis = redis.Redis.from_url(
            f"{env.REDIS_URL}/{env.REDIS_TASK_INDEX}",
            decode_responses=True
        )

    return _cache_redis, _stream_redis, _task_redis


async def close_redis_clients():
    if _cache_redis:
        await _cache_redis.close()
    if _stream_redis:
        await _stream_redis.close()
    if _task_redis:
        await _task_redis.close()
