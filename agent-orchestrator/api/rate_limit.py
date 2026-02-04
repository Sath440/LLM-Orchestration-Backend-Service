import redis.asyncio as redis

from api.config import settings


class RateLimiter:
    def __init__(self) -> None:
        self.redis = redis.from_url(settings.redis_url, decode_responses=True)

    async def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window_seconds)
        return current <= limit

    async def close(self) -> None:
        await self.redis.close()
