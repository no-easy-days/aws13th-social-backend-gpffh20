import logging
from urllib.parse import urlparse, urlunparse

import redis.asyncio as redis
from config import settings

redis_client: redis.Redis | None = None
logger = logging.getLogger(__name__)


def mask_redis_url(url: str) -> str:
    """Redis URL에서 비밀번호를 마스킹"""
    parsed = urlparse(url)
    if parsed.password:
        masked_netloc = f":{('*' * 3)}@{parsed.hostname}"
        if parsed.port:
            masked_netloc += f":{parsed.port}"
        masked = parsed._replace(netloc=masked_netloc)
        return urlunparse(masked)
    return url


async def init_redis_pool():
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Redis 연결 성공")
    except Exception:
        logger.error(f"Redis 연결 실패: {mask_redis_url(settings.redis_url)}")
        raise ConnectionError("Redis 연결 실패") from None


async def close_redis_pool():
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("redis not initialized")
    return redis_client
