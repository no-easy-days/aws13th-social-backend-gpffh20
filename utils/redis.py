import redis.asyncio as redis
from config import settings

redis_client: redis.Redis | None = None


async def init_redis_pool():
    global redis_client
    redis_client = redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )


async def close_redis_pool():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("redis not initialized")
    return redis_client
