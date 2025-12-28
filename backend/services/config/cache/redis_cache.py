"""Redis cache layer for Configuration Service."""
import os
import json
import logging
from typing import Optional, Any

import redis.asyncio as redis

logger = logging.getLogger("config-service.cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default


class RedisCache:
    """Redis cache for fast config access."""
    
    _client: Optional[redis.Redis] = None
    
    @classmethod
    async def connect(cls):
        """Connect to Redis."""
        if cls._client is None:
            cls._client = redis.from_url(REDIS_URL, decode_responses=True)
            logger.info(f"Connected to Redis: {REDIS_URL}")
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from Redis."""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Disconnected from Redis")
    
    @classmethod
    async def ping(cls) -> bool:
        """Check Redis connection."""
        try:
            if cls._client:
                await cls._client.ping()
                return True
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
        return False
    
    @classmethod
    async def get(cls, key: str) -> Optional[dict]:
        """Get cached value."""
        try:
            if cls._client:
                data = await cls._client.get(key)
                if data:
                    return json.loads(data)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: int = CACHE_TTL):
        """Set cached value with TTL."""
        try:
            if cls._client:
                await cls._client.setex(key, ttl, json.dumps(value, default=str))
                logger.debug(f"Cached: {key}")
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    @classmethod
    async def delete(cls, key: str):
        """Delete cached value."""
        try:
            if cls._client:
                await cls._client.delete(key)
                logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    @classmethod
    async def invalidate_pattern(cls, pattern: str):
        """Delete all keys matching pattern."""
        try:
            if cls._client:
                keys = await cls._client.keys(pattern)
                if keys:
                    await cls._client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} keys matching: {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    # Convenience methods for config types
    @classmethod
    def assistant_key(cls, assistant_id: str) -> str:
        return f"config:assistant:{assistant_id}"
    
    @classmethod
    def sip_key(cls, sip_id: str) -> str:
        return f"config:sip:{sip_id}"
    
    @classmethod
    def phone_key(cls, phone_id: str) -> str:
        return f"config:phone:{phone_id}"
    
    @classmethod
    async def cache_assistant(cls, assistant_id: str, data: dict):
        """Cache assistant config."""
        await cls.set(cls.assistant_key(assistant_id), data)
    
    @classmethod
    async def get_assistant(cls, assistant_id: str) -> Optional[dict]:
        """Get cached assistant config."""
        return await cls.get(cls.assistant_key(assistant_id))
    
    @classmethod
    async def cache_sip(cls, sip_id: str, data: dict):
        """Cache SIP config."""
        await cls.set(cls.sip_key(sip_id), data)
    
    @classmethod
    async def get_sip(cls, sip_id: str) -> Optional[dict]:
        """Get cached SIP config."""
        return await cls.get(cls.sip_key(sip_id))
    
    @classmethod
    async def cache_phone(cls, phone_id: str, data: dict):
        """Cache phone config."""
        await cls.set(cls.phone_key(phone_id), data)
    
    @classmethod
    async def get_phone(cls, phone_id: str) -> Optional[dict]:
        """Get cached phone config."""
        return await cls.get(cls.phone_key(phone_id))
