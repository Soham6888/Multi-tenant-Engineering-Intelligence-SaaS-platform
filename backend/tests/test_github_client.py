import httpx
import pytest
from pydantic import SecretStr

from app.integrations.github import GitHubClient, GitHubError

TOKEN = SecretStr("test-only-do-not-log")
REPO = {"id": 42, "full_name": "team/api", "private": True, "archived": False}


@pytest.mark.anyio
async def test_catalog_pagination_never_forwards_token_to_link_host():
    requests = []

    def respond(request):
        requests.append(request)
        page = request.url.params["page"]
        return httpx.Response(
            200,
            json={"total_count": 2, "repositories": [REPO]},
            headers={"link": '<https://attacker.invalid/steal>; rel="next"'} if page == "1" else {},
        )

    client = GitHubClient(transport=httpx.MockTransport(respond))
    first = await client.repositories(TOKEN)
    assert first.next_page == 2 and first.repositories[0].id == 42
    second = await client.repositories(TOKEN, page=first.next_page)
    assert second.next_page is None
    assert all(r.url.host == "api.github.com" for r in requests)
    assert requests[1].url.params["page"] == "2"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "status,headers,code,retryable,calls",
    [
        (401, {}, "github_access_denied", False, 1),
        (403, {}, "github_access_denied", False, 1),
        (404, {}, "github_access_denied", False, 1),
        (302, {"location": "https://attacker.invalid"}, "github_unexpected_status", False, 1),
        (429, {"retry-after": "120"}, "github_rate_limited", True, 1),
        (403, {"x-ratelimit-remaining": "0"}, "github_rate_limited", True, 1),
        (503, {}, "github_unavailable", True, 2),
    ],
)
async def test_safe_errors_and_bounded_retry(status, headers, code, retryable, calls):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(status, headers=headers, text=TOKEN.get_secret_value())

    with pytest.raises(GitHubError) as caught:
        await GitHubClient(transport=httpx.MockTransport(respond)).repositories(TOKEN)
    assert caught.value.code == code
    assert caught.value.retryable == retryable
    assert TOKEN.get_secret_value() not in str(caught.value)
    assert len(requests) == calls
    if status == 429:
        assert caught.value.retry_after == 120


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [b"not json", b"{}", b"x" * 2_000_001],
    ids=["invalid-json", "invalid-schema", "oversized"],
)
async def test_rejects_invalid_or_unbounded_responses(payload):
    with pytest.raises(GitHubError):
        await GitHubClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, content=payload))
        ).repositories(TOKEN)


@pytest.mark.anyio
async def test_transient_transport_recovers_once():
    calls = 0

    def respond(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectTimeout("sensitive detail", request=request)
        return httpx.Response(200, json={"total_count": 0, "repositories": []})

    result = await GitHubClient(transport=httpx.MockTransport(respond)).repositories(TOKEN)
    assert result.repositories == () and calls == 2


@pytest.mark.anyio
async def test_nonfinite_rate_limit_hint_is_safe():
    client = GitHubClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(429, headers={"retry-after": "Infinity"})
        )
    )
    with pytest.raises(GitHubError) as caught:
        await client.repositories(TOKEN)
    assert caught.value.retry_after == 60


@pytest.mark.anyio
async def test_transport_failure_is_bounded_and_sanitized():
    calls = 0

    def respond(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout(TOKEN.get_secret_value(), request=request)

    with pytest.raises(GitHubError, match="github_transport_error") as caught:
        await GitHubClient(transport=httpx.MockTransport(respond)).repositories(TOKEN)
    assert calls == 2
    assert TOKEN.get_secret_value() not in str(caught.value)
