from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_does_not_require_dependencies() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["x-request-id"].startswith("req_")


def test_unknown_route_uses_standard_error() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/missing")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_readiness_checks_database_and_redis() -> None:
    app = create_app()
    with TestClient(app) as client:
        connection = AsyncMock()
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=connection)
        context.__aexit__ = AsyncMock(return_value=False)
        app.state.engine = MagicMock()
        app.state.engine.connect.return_value = context
        app.state.redis = AsyncMock()
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        connection.execute.assert_awaited_once()
        app.state.redis.ping.assert_awaited_once()


def test_readiness_failure_does_not_expose_credentials() -> None:
    app = create_app()
    with TestClient(app) as client:
        app.state.engine = MagicMock()
        app.state.engine.connect.side_effect = RuntimeError("postgres://secret-password")
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
        assert "secret-password" not in response.text


def test_client_cannot_inject_request_id() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health/live", headers={"X-Request-ID": "untrusted"})
        assert response.headers["x-request-id"] != "untrusted"


def test_unhandled_error_is_sanitized() -> None:
    app = create_app()

    @app.get("/test-failure")
    async def failing_route() -> None:
        raise RuntimeError("confidential-internal-detail")

    with TestClient(app) as client:
        response = client.get("/test-failure")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
        assert "confidential-internal-detail" not in response.text
        assert response.headers["x-request-id"] == response.json()["error"]["request_id"]


def test_validation_error_does_not_echo_input() -> None:
    app = create_app()

    @app.get("/test-validation")
    async def validating_route(limit: int) -> dict[str, int]:
        return {"limit": limit}

    with TestClient(app) as client:
        response = client.get("/test-validation?limit=private-value")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "private-value" not in response.text
