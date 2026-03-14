#api/app/database.py
import asyncpg
from config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        try:
            # Split pool across uvicorn workers (each worker creates its own pool)
            pool_max = settings.POSTGRES_POOL_MAX // max(settings.UVICORN_WORKERS, 1)
            pool_min = max(settings.POSTGRES_POOL_MIN, 1)

            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=pool_min,
                max_size=pool_max,
                command_timeout=60
            )
            logger.info(f"DB pool created: min={pool_min}, max={pool_max} (total max across {settings.UVICORN_WORKERS} workers: {pool_max * settings.UVICORN_WORKERS})")
            logger.info("Database connected successfully")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database disconnected")

    async def fetch_one(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database connection not established. Call connect() first.")

        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database connection not established. Call connect() first.")

        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

# 전역 데이터베이스 인스턴스
db = Database()
