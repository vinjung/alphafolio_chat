import asyncpg
from typing import Optional
from pydantic_settings import BaseSettings


_pg_pool: Optional[asyncpg.Pool] = None

def create_pg_client(env: BaseSettings) -> asyncpg.Pool:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = asyncpg.create_pool(
            dsn=env.database_url,
            min_size=env.POSTGRES_POOL_MIN,
            max_size=env.POSTGRES_POOL_MAX,
            command_timeout=60,
        )
    return _pg_pool

async def close_pg_client():
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
