import logging
import time
from functools import wraps
from typing import Callable, Optional

from fastapi import Request

from src.config.manager import settings
from src.core.cache_manager import CacheManager, cache_manager
from src.core.utils.exceptions.base import BaseAppException
from src.core.utils.user_utils import extract_user_id, get_client_ip

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Production-ready Redis-based Token Bucket rate limiter for FastAPI.
    Supports distributed systems, custom key functions, and graceful degradation.
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Initialize rate limiter with cache manager.

        Args:
            cache_manager: CacheManager instance for Redis operations
        """
        self.cache_manager = cache_manager
        self.lua_script = None

    async def initialize(self) -> None:
        """Load Lua script for atomic operations. Call during FastAPI startup."""
        lua_code = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local required = tonumber(ARGV[4])
        local ttl = tonumber(ARGV[5])

        local data = redis.call('GET', key)
        local bucket = {}

        if data == false then
            bucket.tokens = capacity
            bucket.last_refill = now
        else
            local decoded = cjson.decode(data)
            bucket.tokens = decoded.tokens
            bucket.last_refill = decoded.last_refill
        end

        -- Refill tokens based on time elapsed
        local elapsed = math.max(0, now - bucket.last_refill)
        bucket.tokens = math.min(capacity, bucket.tokens + elapsed * refill_rate)
        bucket.last_refill = now

        -- Check if request is allowed
        local allowed = 0
        if bucket.tokens >= required then
            bucket.tokens = bucket.tokens - required
            allowed = 1
        end

        -- Store updated bucket
        redis.call('SET', key, cjson.encode(bucket), 'EX', ttl)

        -- Return: allowed (1/0), remaining tokens, reset time
        return {allowed, math.floor(bucket.tokens), bucket.last_refill + ttl}
        """

        assert self.cache_manager.client is not None
        self.lua_script = self.cache_manager.client.register_script(lua_code)
        logger.info("Token bucket Lua script loaded")

    async def allow_request(
        self,
        identifier: str,
        capacity: int,
        refill_rate: float,
        required_tokens: float = 1.0,
        ttl: Optional[int] = None,
    ) -> tuple[bool, int, int]:
        """
        Check if request is allowed using token bucket algorithm.

        Args:
            identifier: Unique identifier (user ID, IP, API key)
            capacity: Max tokens in bucket (burst capacity)
            refill_rate: Tokens per second
            required_tokens: Tokens required for this request (default 1)
            ttl: Key expiration in seconds (default from settings)

        Returns:
            Tuple of (allowed: bool, remaining_tokens: int, reset_timestamp: int)

        Raises:
            Exception: If Redis operation fails
        """
        self.cache_manager._check_initialized()
        assert self.lua_script is not None

        ttl = ttl or settings.REDIS_CACHE_TTL
        key = self.cache_manager.cache_key("ratelimit:tb", identifier)
        now = time.time()

        try:
            result = await self.lua_script(
                keys=[key],
                args=[capacity, refill_rate, int(now), required_tokens, ttl],
            )

            allowed, remaining, reset = result
            return bool(allowed), int(remaining), int(reset)

        except Exception as e:
            logger.error(f"Token bucket check failed for {identifier}: {e}")
            # Fail open in production (allow request if cache fails)
            return True, capacity, int(now) + ttl

    async def get_bucket_info(self, identifier: str) -> Optional[dict]:
        """
        Get current bucket state for monitoring/debugging.

        Args:
            identifier: Unique identifier

        Returns:
            Dict with tokens, last_refill, or None if bucket doesn't exist
        """
        key = self.cache_manager.cache_key("ratelimit:tb", identifier)
        return await self.cache_manager.get(key)

    async def reset_bucket(self, identifier: str) -> bool:
        """Reset bucket to full capacity."""
        key = self.cache_manager.cache_key("ratelimit:tb", identifier)
        return await self.cache_manager.delete(key) > 0

    async def reset_pattern(self, pattern: str) -> int:
        """Reset all buckets matching a pattern (e.g., 'user:123:*')."""
        key_pattern = self.cache_manager.cache_key("ratelimit:tb", pattern)
        return await self.cache_manager.clear_pattern(key_pattern)


# Global instance
rate_limiter: TokenBucketRateLimiter = TokenBucketRateLimiter(cache_manager)


# ============================================================================
# Dependency Functions
# ============================================================================


async def rate_limit_by_ip(
    request: Request,
    capacity: int = 100,
    refill_rate: float = 10.0,
) -> tuple[bool, dict]:
    """
    Rate limit by client IP.

    Args:
        request: FastAPI request
        capacity: Burst capacity (default 100 requests)
        refill_rate: Refill rate in requests per second (default 10 req/s = 600 req/min)

    Returns:
        Tuple of (allowed, headers_dict)
    """
    assert rate_limiter is not None

    client_ip = get_client_ip(request)
    identifier = f"ip:{client_ip}"

    allowed, remaining, reset = await rate_limiter.allow_request(
        identifier, capacity, refill_rate
    )

    headers = {
        "X-RateLimit-Limit": str(capacity),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset),
    }

    if not allowed:
        retry_after = max(1, int(reset - time.time()))
        headers["Retry-After"] = str(retry_after)
        raise BaseAppException(
            status_code=429,
            message="Rate limit exceeded",
            headers=headers,
        )

    return allowed, headers


async def rate_limit_by_user(
    request: Request,
    capacity: int = 1000,
    refill_rate: float = 50.0,
) -> tuple[bool, dict]:
    """
    Rate limit by authenticated user ID.
    Falls back to IP if user not authenticated.

    Args:
        request: FastAPI request
        capacity: Burst capacity (default 1000 requests)
        refill_rate: Refill rate in req/s (default 50 req/s = 3000 req/min)
    """
    assert rate_limiter is not None

    user_id = await extract_user_id(request)
    if user_id:
        identifier = f"user:{user_id}"
    else:
        identifier = f"ip:{get_client_ip(request)}"

    allowed, remaining, reset = await rate_limiter.allow_request(
        identifier, capacity, refill_rate
    )

    headers = {
        "X-RateLimit-Limit": str(capacity),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset),
    }

    if not allowed:
        retry_after = max(1, int(reset - time.time()))
        headers["Retry-After"] = str(retry_after)
        raise BaseAppException(
            status_code=429,
            message="Rate limit exceeded",
            headers=headers,
        )

    return allowed, headers


async def tiered_rate_limit(
    request: Request,
) -> tuple[bool, dict]:
    """
    Tiered rate limiting based on user status.
    - Anonymous: 100 req/min (capacity 100, refill 1.67 req/s)
    - Authenticated: 1000 req/min (capacity 1000, refill 16.67 req/s)
    - Premium: 10000 req/min (capacity 10000, refill 166.7 req/s)
    """
    assert rate_limiter is not None

    user_id = await extract_user_id(request)

    # Determine tier (implement based on your user model)
    if user_id:
        tier = "premium"  # Would check user.tier in real implementation
        capacity, refill_rate = 10000, 166.7
        identifier = f"user:{user_id}"
    else:
        tier = "anonymous"
        capacity, refill_rate = 100, 1.67
        identifier = f"ip:{get_client_ip(request)}"

    allowed, remaining, reset = await rate_limiter.allow_request(
        identifier, capacity, refill_rate
    )

    headers = {
        "X-RateLimit-Tier": tier,
        "X-RateLimit-Limit": str(capacity),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset),
    }

    if not allowed:
        retry_after = max(1, int(reset - time.time()))
        headers["Retry-After"] = str(retry_after)
        raise BaseAppException(
            status_code=429,
            message=f"Rate limit exceeded for {tier} tier",
            headers=headers,
        )

    return allowed, headers


# ============================================================================
# Decorator for Class-Based Rate Limiting
# ============================================================================


def rate_limit(
    capacity: int = 100,
    refill_rate: float = 10.0,
    key_func: Optional[Callable[[Request], str]] = None,
):
    """
    Decorator for endpoints with custom rate limiting.

    Usage:
        @app.get("/endpoint")
        @rate_limit(capacity=50, refill_rate=5.0)
        async def my_endpoint():
            return {"message": "success"}

        # Custom key function
        def custom_key(request: Request) -> str:
            return f"custom:{get_user_id(request)}"

        @app.get("/custom")
        @rate_limit(capacity=100, key_func=custom_key)
        async def custom_endpoint():
            return {"message": "success"}
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            assert rate_limiter is not None

            if key_func:
                identifier = key_func(request)
            else:
                identifier = f"ip:{get_client_ip(request)}"

            allowed, remaining, reset = await rate_limiter.allow_request(
                identifier, capacity, refill_rate
            )

            if not allowed:
                retry_after = max(1, int(reset - time.time()))
                raise BaseAppException(
                    status_code=429,
                    message="Rate limit exceeded",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Reset": str(reset),
                    },
                )

            # Inject headers into response
            if hasattr(request, "_rate_limit_headers"):
                request._rate_limit_headers = {  # type: ignore
                    "X-RateLimit-Limit": str(capacity),
                    "X-RateLimit-Remaining": str(max(0, remaining)),
                    "X-RateLimit-Reset": str(reset),
                }

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Monitoring/Admin Endpoints
# ============================================================================


async def get_rate_limit_status(identifier: str) -> dict:
    """Get rate limit status for identifier."""
    assert rate_limiter is not None
    bucket_info = await rate_limiter.get_bucket_info(identifier)
    return {
        "identifier": identifier,
        "bucket": bucket_info,
        "timestamp": time.time(),
    }


async def reset_rate_limit(identifier: str) -> bool:
    """Reset rate limit for identifier."""
    assert rate_limiter is not None
    return await rate_limiter.reset_bucket(identifier)
