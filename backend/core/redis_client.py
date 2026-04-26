from redis import asyncio as aioredis
from core.config import settings

redis_pool = aioredis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis():
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()
