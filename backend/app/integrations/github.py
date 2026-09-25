"""Bounded GitHub catalog reads. No tokens, response bodies or URLs in errors."""

import asyncio
import json
import math
import time
from dataclasses import dataclass

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError


class GitHubError(Exception):
    def __init__(self, code: str, *, retryable: bool = False, retry_after: float | None = None):
        super().__init__(code)
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after


class GitHubRepository(BaseModel):
    model_config = ConfigDict(strict=True)
    id: int = Field(gt=0)
    full_name: str = Field(min_length=3, max_length=256)
    private: bool
    archived: bool


class _CatalogPage(BaseModel):
    model_config = ConfigDict(strict=True)
    total_count: int = Field(ge=0)
    repositories: list[GitHubRepository] = Field(max_length=100)


@dataclass(frozen=True)
class CatalogPage:
    repositories: tuple[GitHubRepository, ...]
    next_page: int | None


class GitHubClient:
    """Inject transport for tests, not arbitrary origins or credential-bearing clients.

    One page per call so callers can checkpoint; rate limits return scheduling hints
    instead of sleeping in an HTTP request. Transient failures get at most one retry.
    """

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None):
        self._transport = transport

    async def repositories(self, token: SecretStr, *, page: int = 1) -> CatalogPage:
        if not 1 <= page <= 10000:
            raise ValueError("page must be between 1 and 10000")
        try:
            async with asyncio.timeout(20):
                return await self._read_page(token, page)
        except TimeoutError:
            raise GitHubError("github_timeout", retryable=True) from None

    async def _read_page(self, token: SecretStr, page: int) -> CatalogPage:
        async with httpx.AsyncClient(
            transport=self._transport,
            timeout=httpx.Timeout(8, connect=3),
            follow_redirects=False,
            trust_env=False,
        ) as client:
            for attempt in range(2):
                try:
                    async with client.stream(
                        "GET",
                        "https://api.github.com/installation/repositories",
                        params={"per_page": 100, "page": page},
                        headers={
                            "Authorization": f"Bearer {token.get_secret_value()}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2026-03-10",
                        },
                    ) as response:
                        self._check_status(response)
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > 2_000_000:
                                raise GitHubError("github_response_too_large")
                        try:
                            data = _CatalogPage.model_validate(json.loads(body))
                        except (ValueError, ValidationError):
                            raise GitHubError("github_invalid_response") from None
                        # Never follow Link URLs: construct the next request on the fixed host.
                        has_next = "next" in response.links
                        if has_next and (not data.repositories or page == 10000):
                            raise GitHubError("github_pagination_limit")
                        return CatalogPage(tuple(data.repositories), page + 1 if has_next else None)
                except httpx.TransportError:
                    if attempt:
                        raise GitHubError("github_transport_error", retryable=True) from None
                except GitHubError as error:
                    if error.code != "github_unavailable" or attempt:
                        raise
                await asyncio.sleep(0.2)
        raise AssertionError("unreachable")

    @staticmethod
    def _check_status(response: httpx.Response) -> None:
        status = response.status_code
        if status == 200:
            return
        if status == 429 or (
            status == 403
            and (
                response.headers.get("x-ratelimit-remaining") == "0"
                or "retry-after" in response.headers
            )
        ):
            delay = 60.0
            try:
                if "retry-after" in response.headers:
                    delay = max(delay, float(response.headers["retry-after"]))
                if response.headers.get("x-ratelimit-remaining") == "0":
                    delay = max(delay, float(response.headers["x-ratelimit-reset"]) - time.time())
            except (ValueError, KeyError):
                pass
            if not math.isfinite(delay):
                delay = 60.0
            raise GitHubError("github_rate_limited", retryable=True, retry_after=delay)
        if status in (401, 403, 404):
            raise GitHubError("github_access_denied")
        if status >= 500:
            raise GitHubError("github_unavailable", retryable=True)
        raise GitHubError("github_unexpected_status")
