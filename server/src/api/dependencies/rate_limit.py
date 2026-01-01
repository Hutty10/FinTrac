from enum import Enum

from fastapi import Request, Response

from src.core.rate_limiter import rate_limiter
from src.core.utils.exceptions.base import BaseAppException
from src.core.utils.user_utils import (
    extract_email,
    extract_user_id,
    extract_username,
    get_client_ip,
)


class RateLimitIdentifier(str, Enum):
    IP = "ip"
    USER = "user"
    EMAIL = "email"
    USERNAME = "username"


async def get_rate_limit_identifier(
    request: Request, identifier_type: RateLimitIdentifier
) -> str:
    """Get the rate limit identifier based on the specified type."""
    if identifier_type == RateLimitIdentifier.IP:
        return f"ip:{get_client_ip(request)}"
    elif identifier_type == RateLimitIdentifier.USER:
        user_id = await extract_user_id(request)
        if user_id:
            return f"user:{user_id}"
        else:
            return f"ip:{get_client_ip(request)}"
    elif identifier_type == RateLimitIdentifier.EMAIL:
        user_email = await extract_email(request)
        if user_email:
            return f"email:{user_email.lower()}"
        else:
            return f"ip:{get_client_ip(request)}"
    elif identifier_type == RateLimitIdentifier.USERNAME:
        username = await extract_username(request)
        if username:
            return f"username:{username.lower()}"
        else:
            return f"ip:{get_client_ip(request)}"
    else:
        return f"ip:{get_client_ip(request)}"


def RateLimit(
    capacity: int,
    refill_rate: float,
    identifier_type: RateLimitIdentifier = RateLimitIdentifier.IP,
):
    """Factory to create dynamic limits for different routes."""

    async def _check_limit(request: Request, response: Response):
        identifier = await get_rate_limit_identifier(request, identifier_type)
        allowed, remaining, reset = await rate_limiter.allow_request(
            identifier=f"{request.url.path}:{identifier}",
            capacity=capacity,
            refill_rate=refill_rate,
        )

        limit_headers = {
            "X-RateLimit-Limit": str(capacity),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
        }

        if not allowed:
            limit_headers["Retry-After"] = "1"
            raise BaseAppException(
                status_code=429, message="Rate limit exceeded", headers=limit_headers
            )
        for key, value in limit_headers.items():
            response.headers[key] = value

    return _check_limit
