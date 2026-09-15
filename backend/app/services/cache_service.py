import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger

class CacheService:
    def __init__(self):
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis initialization failed, caching disabled: {str(e)}")

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        try:
            val = await self.redis_client.get(key)
            return json.loads(val) if val else None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.redis_client:
            return
        try:
            await self.redis_client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.warning(f"Redis set error: {str(e)}")

cache_service = CacheService()
