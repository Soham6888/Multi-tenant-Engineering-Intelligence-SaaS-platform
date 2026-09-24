import asyncio

import pytest
from fakeredis.aioredis import FakeRedis
from pydantic import ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.config import Settings
from app.core.rate_limit import check_auth_limit
from app.core.security import csrf_value, hash_password, token_digest, verify_password
from app.schemas.auth import RegisterInput
from app.services.auth_errors import AuthError


def test_password_is_salted_and_correctly_verified() -> None:
    password = "a long memorable passphrase"
    first, second = hash_password(password), hash_password(password)
    assert first != second
    assert first.startswith("$argon2id$")
    assert verify_password(password, first)
    assert not verify_password("wrong password", first)
    assert not verify_password(password, "invalid-hash")


def test_credentials_have_separate_one_way_digests() -> None:
    token = "random-secret"
    assert len(token_digest(token)) == 64
    assert csrf_value(token) != token_digest(token)
    assert token not in csrf_value(token)


def test_registration_normalizes_identity_but_preserves_password() -> None:
    data = RegisterInput(
        name="  Alex  ", email="ALEX@Example.com", password="  this is a passphrase  "
    )
    assert data.name == "Alex"
    assert data.email == "alex@example.com"
    assert data.password.get_secret_value() == "  this is a passphrase  "
    assert "passphrase" not in repr(data)


@pytest.mark.parametrize(
    "changes",
    [
        {"password": "short"},
        {"name": "   "},
        {"email": "invalid"},
        {"password": "a" * 129},
        {"role": "OWNER"},
    ],
)
def test_invalid_registration_is_rejected(changes: dict[str, str]) -> None:
    data = {"name": "Alex", "email": "alex@example.com", "password": "a long passphrase"}
    data.update(changes)
    with pytest.raises(ValidationError):
        RegisterInput(**data)


def test_production_requires_https_origins() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production")
    settings = Settings(environment="production", allowed_origins=["https://app.example.com"])
    assert settings.cookie_name == "__Host-eip_session"


def test_atomic_rate_limit_and_expiry() -> None:
    async def run() -> None:
        redis = FakeRedis()
        settings = Settings(auth_ip_limit=50, auth_account_limit=3)
        outcomes = await asyncio.gather(
            *[check_auth_limit(redis, settings, "127.0.0.1", "alex@example.com") for _ in range(8)],
            return_exceptions=True,
        )
        assert sum(value is None for value in outcomes) == 3
        assert all(
            isinstance(value, AuthError) and value.status == 429 for value in outcomes if value
        )
        keys = await redis.keys("auth:*")
        assert len(keys) == 2
        for key in keys:
            assert b"alex" not in key
            assert 0 < await redis.ttl(key) <= 300
        await redis.aclose()

    asyncio.run(run())


def test_rate_limit_fails_closed() -> None:
    from unittest.mock import AsyncMock

    async def run() -> None:
        redis = AsyncMock()
        redis.eval.side_effect = RedisConnectionError("secret-connection-details")
        with pytest.raises(AuthError) as exc:
            await check_auth_limit(redis, Settings(), "127.0.0.1", None)
        assert exc.value.status == 503
        assert "secret-connection" not in exc.value.message

    asyncio.run(run())
