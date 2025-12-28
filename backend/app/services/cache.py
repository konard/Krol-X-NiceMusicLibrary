"""Redis cache service for statistics caching."""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching data in Redis."""

    def __init__(
        self,
        redis_client: redis.Redis | None = None,  # type: ignore[type-arg]
    ) -> None:
        """Initialize cache service.

        Args:
            redis_client: Redis client instance. If None, creates a new one.
        """
        self._client: redis.Redis | None = redis_client  # type: ignore[type-arg]
        self._connected = False

    async def _get_client(self) -> redis.Redis | None:  # type: ignore[type-arg]
        """Get or create Redis client.

        Returns:
            Redis client or None if connection fails.
        """
        if self._client is not None:
            return self._client

        try:
            self._client = redis.from_url(  # type: ignore[no-untyped-call]
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()  # type: ignore[misc]
            self._connected = True
            return self._client
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._connected = False
            return None

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        client = await self._get_client()
        if client is None:
            return None

        try:
            value = await client.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Failed to get from cache: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 300,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache (must be JSON serializable).
            ttl_seconds: Time to live in seconds. Default 5 minutes.

        Returns:
            True if successful, False otherwise.
        """
        client = await self._get_client()
        if client is None:
            return False

        try:
            serialized = json.dumps(value, default=str)
            await client.setex(key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key.

        Returns:
            True if successful, False otherwise.
        """
        client = await self._get_client()
        if client is None:
            return False

        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete from cache: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        """Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "stats:user:*").

        Returns:
            True if successful, False otherwise.
        """
        client = await self._get_client()
        if client is None:
            return False

        try:
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete pattern from cache: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._connected = False


# Singleton instance
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get cache service singleton.

    Returns:
        Cache service instance.
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
