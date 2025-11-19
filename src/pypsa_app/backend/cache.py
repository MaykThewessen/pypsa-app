"""Redis cache infrastructure and decorator"""

import hashlib
import json
import logging
from functools import wraps
from typing import Callable

from pypsa_app.backend.settings import settings

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


def cache(key_template: str, ttl: int):
    """
    Cache decorator for FastAPI endpoints.

    Args:
        key_template: Template string with {param_name} placeholders
                     Example: "map_buses:{network_id}"
                     For Pydantic models, use fields: "plot:{request.statistic}"
        ttl: Time to live in seconds
    """

    def decorator(func: Callable) -> Callable:
        import inspect

        param_names = list(inspect.signature(func).parameters.keys())

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Zip args to param names
            values = dict(zip(param_names, args))
            values.update(kwargs)

            # Simple approach: serialize all values and hash
            serializable = {}
            for key, value in values.items():
                if hasattr(value, "model_dump"):
                    serializable[key] = value.model_dump()
                else:
                    serializable[key] = value

            # Generate cache key by hashing all parameters
            cache_hash = hashlib.md5(
                json.dumps(serializable, sort_keys=True).encode()
            ).hexdigest()[:12]
            cache_key = f"{key_template.split(':')[0]}:{cache_hash}"

            # Check cache
            cached_data = cache_service.get(cache_key)
            if cached_data:
                logger.debug("Cache hit", extra={"cache_key": cache_key})
                return cached_data

            # Cache miss - call function and cache result
            logger.debug("Cache miss", extra={"cache_key": cache_key})
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


class CacheService:
    """Generic Redis cache service"""

    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        logger.info(
            "Connected to Redis",
            extra={
                "redis_url": settings.redis_url,
                "decode_responses": True,
            },
        )

    def get(self, key: str) -> dict | None:
        """Get cached data by key"""
        cached_data = self.redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None

    def set(self, key: str, value: dict, ttl: int) -> bool:
        """Set cached data with TTL"""
        serialized = json.dumps(value)
        size_bytes = len(serialized)
        size_mb = size_bytes / (1024 * 1024)

        self.redis_client.setex(key, ttl, serialized)
        logger.info(
            f"Cached data ({round(size_mb, 2)} MB)",
            extra={
                "cache_key": key,
                "ttl": ttl,
                "size_mb": round(size_mb, 2),
            },
        )
        return True

    def clear_plot_cache(self) -> int:
        """Clear all plot caches"""
        deleted = 0
        for key in self.redis_client.scan_iter(match="plot:*"):
            self.redis_client.delete(key)
            deleted += 1
        if deleted > 0:
            logger.info(
                "Cleared plot cache entries",
                extra={
                    "deleted_count": deleted,
                    "cache_type": "plot",
                    "pattern": "plot:*",
                },
            )
        return deleted

    def clear_map_cache(self) -> int:
        """Clear all map caches"""
        deleted = 0
        for key in self.redis_client.scan_iter(match="map_*:*"):
            self.redis_client.delete(key)
            deleted += 1
        if deleted > 0:
            logger.info(
                "Cleared map cache entries",
                extra={
                    "deleted_count": deleted,
                    "cache_type": "map",
                    "pattern": "map_*:*",
                },
            )
        return deleted

    def clear_network_cache(self, network_id: str) -> int:
        """Clear all cached data for a specific network (map caches + all plots)"""
        deleted = 0

        # Clear map-specific caches for this network
        map_pattern = f"map_*:{network_id}"
        for key in self.redis_client.scan_iter(match=map_pattern):
            self.redis_client.delete(key)
            deleted += 1

        # Clear all plot caches (plots can involve multiple networks)
        plot_pattern = "plot:*"
        for key in self.redis_client.scan_iter(match=plot_pattern):
            self.redis_client.delete(key)
            deleted += 1

        if deleted > 0:
            logger.info(
                "Cleared cache entries for network",
                extra={
                    "network_id": network_id,
                    "deleted_count": deleted,
                    "map_pattern": map_pattern,
                    "plot_pattern": plot_pattern,
                },
            )
        return deleted

    def clear_all_cache(self) -> int:
        """Clear all cached data"""
        deleted = 0
        for key in self.redis_client.scan_iter(match="*"):
            self.redis_client.delete(key)
            deleted += 1
        if deleted > 0:
            logger.info(
                "Cleared total cache entries",
                extra={
                    "deleted_count": deleted,
                    "pattern": "*",
                },
            )
        return deleted

    def ping(self) -> bool:
        """Check if Redis is accessible"""
        return self.redis_client.ping()


class DummyCacheService:
    """Dummy cache service when Redis is not available"""

    def __init__(self):
        logger.warning(
            "Redis not available - using dummy cache",
            extra={
                "cache_enabled": False,
                "reason": "Redis not available",
            },
        )

    def get(self, *args, **kwargs):
        return None

    def set(self, *args, **kwargs):
        return False

    def clear_plot_cache(self):
        return 0

    def clear_map_cache(self):
        return 0

    def clear_network_cache(self, *args, **kwargs):
        return 0

    def clear_all_cache(self):
        return 0

    def ping(self):
        return False


# Global cache service instance
if REDIS_AVAILABLE and settings.redis_url:
    try:
        cache_service = CacheService()
    except Exception as e:
        logger.error(
            "Failed to initialize Redis cache",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "redis_url": settings.redis_url,
                "fallback": "DummyCacheService",
            },
            exc_info=True,
        )
        cache_service = DummyCacheService()
else:
    cache_service = DummyCacheService()
