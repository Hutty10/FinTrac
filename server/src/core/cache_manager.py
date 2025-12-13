import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Union

import redis.asyncio as redis

from src.config.manager import settings
from src.core.utils.exceptions.cache import RedisConnectionError

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Production-ready async Redis manager for FastAPI with connection pooling,
    error handling, and common operations. Compatible with redis-py 6.4.0+
    """

    def __init__(self):
        """
        Initialize async Redis manager with settings from Pydantic.
        """
        self.client: redis.Redis | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize Redis connection. Should be called in FastAPI startup event.
        """
        if self._initialized:
            return

        try:
            client_kwargs = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": settings.REDIS_DB,
                "socket_timeout": settings.REDIS_SOCKET_TIMEOUT,
                "socket_connect_timeout": settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                "health_check_interval": 30,
                "decode_responses": True,
            }

            # if settings.REDIS_PASSWORD:
            #     client_kwargs["password"] = settings.REDIS_PASSWORD

            self.client = redis.Redis(**client_kwargs)

            # Test connection
            await self.client.ping()
            self._initialized = True
            logger.info(
                f"Redis initialized: {settings.REDIS_HOST}:"
                f"{settings.REDIS_PORT}/db{settings.REDIS_DB}"
            )
        except redis.ConnectionError as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise RedisConnectionError(
                f"Cannot connect to Redis at {settings.REDIS_HOST}:"
                f"{settings.REDIS_PORT}/db{settings.REDIS_DB}"
            ) from e

    async def ping(self) -> bool:
        assert self.client is not None
        await self.client.ping()
        return True

    async def close(self) -> None:
        """Close Redis connection. Should be called in FastAPI shutdown event."""
        if self.client:
            await self.client.close()
        self._initialized = False
        logger.info("Redis connection closed")

    def _check_initialized(self) -> None:
        """Check if Redis is initialized."""
        if not self._initialized or not self.client:
            raise RuntimeError(
                "Redis not initialized. Call await cache_manager.initialize() first."
            )

    async def _retry_wrapper(self, coro_func, *args, **kwargs) -> Any:
        """Wrapper for retry logic on async operations."""
        last_exception = None

        for attempt in range(settings.REDIS_MAX_RETRIES):
            try:
                return await coro_func(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if not settings.REDIS_RETRY_ON_TIMEOUT:
                    raise
                last_exception = e
                if attempt < settings.REDIS_MAX_RETRIES - 1:
                    wait_time = settings.REDIS_RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)
            except Exception:
                raise

        if last_exception:
            raise last_exception

    @asynccontextmanager
    async def pipeline(self):
        """Async context manager for Redis pipeline transactions."""
        self._check_initialized()
        assert self.client is not None
        pipe = self.client.pipeline()
        try:
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
        finally:
            await pipe.reset()

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set a key-value pair with optional TTL.

        Args:
            key: Redis key
            value: Value (automatically JSON serialized if dict/list)
            ttl: Time to live in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if set successfully, False otherwise
        """
        self._check_initialized()
        client = self.client
        assert client is not None

        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        ttl = ttl or settings.REDIS_CACHE_TTL

        async def _set():
            result = await client.set(key, value, ex=ttl, nx=nx, xx=xx)
            if result:
                logger.debug(f"Set key {key}")
            return result

        return await self._retry_wrapper(_set)

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value by key with automatic JSON deserialization.

        Args:
            key: Redis key
            default: Default value if key doesn't exist

        Returns:
            Deserialized value or default
        """
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _get():
            value = await client.get(key)
            if value is None:
                return default
            return self._deserialize(value)

        return await self._retry_wrapper(_get)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _delete():
            count = await client.delete(*keys)
            logger.debug(f"Deleted {count} keys")
            return count

        return await self._retry_wrapper(_delete)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        self._check_initialized()
        assert self.client is not None

        return await self._retry_wrapper(self.client.exists, *keys)

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        self._check_initialized()
        assert self.client is not None

        return await self._retry_wrapper(self.client.incrby, key, amount)

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a counter."""
        self._check_initialized()
        assert self.client is not None

        return await self._retry_wrapper(self.client.decrby, key, amount)

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to list head."""
        self._check_initialized()
        assert self.client is not None

        serialized = [
            json.dumps(v) if isinstance(v, (dict, list)) else v for v in values
        ]
        return await self._retry_wrapper(self.client.lpush, key, *serialized)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to list tail."""
        self._check_initialized()
        assert self.client is not None

        serialized = [
            json.dumps(v) if isinstance(v, (dict, list)) else v for v in values
        ]
        return await self._retry_wrapper(self.client.rpush, key, *serialized)

    async def lpop(self, key: str, count: int = 1) -> Union[Any, List[Any], None]:
        """Pop values from list head."""
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _lpop():
            result = await client.lpop(key, count=count)  # type: ignore
            if result is None:
                return None
            if isinstance(result, list):
                return [self._deserialize(v) for v in result]
            return self._deserialize(result)

        return await self._retry_wrapper(_lpop)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get range of values from list."""
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _lrange():
            values = await client.lrange(key, start, end)  # type: ignore
            return [self._deserialize(v) for v in values]

        return await self._retry_wrapper(_lrange)

    async def hset(self, key: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields."""
        self._check_initialized()
        assert self.client is not None

        serialized = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else v
            for k, v in mapping.items()
        }
        return await self._retry_wrapper(self.client.hset, key, mapping=serialized)

    async def hget(self, key: str, field: str, default: Any = None) -> Any:
        """Get hash field value."""
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _hget():
            value = await client.hget(key, field)  # type: ignore
            if value is None:
                return default
            return self._deserialize(value)

        return await self._retry_wrapper(_hget)

    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields."""
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _hgetall():
            data = await client.hgetall(key)  # type: ignore
            return {k: self._deserialize(v) for k, v in data.items()}

        return await self._retry_wrapper(_hgetall)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set key expiration time."""
        self._check_initialized()
        assert self.client is not None

        return await self._retry_wrapper(self.client.expire, key, ttl)

    async def ttl(self, key: str) -> int:
        """Get remaining TTL in seconds. Returns -1 if no expiry, -2 if not exists."""
        self._check_initialized()
        assert self.client is not None

        return await self._retry_wrapper(self.client.ttl, key)

    async def clear(self) -> bool:
        """Delete all keys in the current database."""
        self._check_initialized()
        assert self.client is not None

        return await self._retry_wrapper(self.client.flushdb)

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Redis pattern (e.g., "user:*", "session:*:data")

        Returns:
            Number of keys deleted
        """
        self._check_initialized()
        client = self.client
        assert client is not None

        async def _clear_pattern():
            keys = await client.keys(pattern)
            if not keys:
                return 0
            return await client.delete(*keys)

        return await self._retry_wrapper(_clear_pattern)

    @staticmethod
    def cache_key(*parts: str) -> str:
        """
        Build a cache key from parts using colon separator.

        Args:
            *parts: Key parts to join (e.g., "user", "123", "profile")

        Returns:
            Formatted cache key (e.g., "user:123:profile")
        """
        return ":".join(str(part) for part in parts)

    @staticmethod
    def _deserialize(value: str) -> Any:
        """Deserialize JSON strings back to objects."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value


cache_manager = CacheManager()
