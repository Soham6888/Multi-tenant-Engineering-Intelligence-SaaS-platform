from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings
from app.core.security import token_digest
from app.services.auth_errors import AuthError

INCREMENT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return n
"""


async def check_api_limit(redis: Redis, settings: Settings, user_id: str) -> None:
    try:
        key = f"api:user:{token_digest(user_id)}"
        count = await redis.eval(INCREMENT, 1, key, str(settings.api_window_seconds))  # type: ignore[misc]
        if int(count) > settings.api_user_limit:
            raise AuthError(429, "RATE_LIMITED", "Too many requests. Please try again later.")
    except RedisError as exc:
        raise AuthError(
            503, "DEPENDENCY_UNAVAILABLE", "Service is temporarily unavailable"
        ) from exc


async def check_auth_limit(redis: Redis, settings: Settings, ip: str, email: str | None) -> None:
    buckets = [(f"auth:ip:{token_digest(ip)}", settings.auth_ip_limit)]
    if email:
        buckets.append((f"auth:account:{token_digest(email)}", settings.auth_account_limit))
    try:
        for key, maximum in buckets:
            count = await redis.eval(INCREMENT, 1, key, str(settings.auth_window_seconds))  # type: ignore[misc]
            if int(count) > maximum:
                raise AuthError(429, "RATE_LIMITED", "Too many attempts. Please try again later.")
    except RedisError as exc:
        raise AuthError(
            503, "DEPENDENCY_UNAVAILABLE", "Authentication is temporarily unavailable"
        ) from exc
