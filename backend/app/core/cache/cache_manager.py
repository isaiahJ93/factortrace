"""
Cache Manager for Redis caching of emission factors
"""

from typing import Dict, Optional
from uuid import UUID
import redis.asyncio as redis
import json
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching for emission factors"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Initialize Redis connection"""
        self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            
    async def get(self, key: str) -> Optional[Dict]:
        """Get cached value"""
        if not self._redis:
            return None
            
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
            
    async def set(self, key: str, value: Dict, ttl: int = 3600):
        """Set cached value with TTL"""
        if not self._redis:
            return
            
        try:
            await self._redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if not self._redis:
            return
            
        try:
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
