from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis


# Call this in your app's startup/lifespan event
async def init_rate_limiter(redis_url: str):
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)


# Re-export RateLimiter for easy import in routes
__all__ = ["RateLimiter", "init_rate_limiter"]
