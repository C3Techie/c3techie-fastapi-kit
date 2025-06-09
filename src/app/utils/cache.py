import redis.asyncio as redis
from typing import Optional, Any


class RedisCache:
    def __init__(self, url: str):
        self._client = redis.from_url(url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, expire: int = 3600):
        await self._client.set(key, value, ex=expire)

    async def delete(self, key: str):
        await self._client.delete(key)

    async def close(self):
        await self._client.close()
