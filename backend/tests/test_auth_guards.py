from fastapi.testclient import TestClient

from app.main import create_app


def test_unauthenticated_request_is_not_cached() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_origin_and_custom_header_required_without_database_access() -> None:
    with TestClient(create_app()) as client:
        payload = {"email": "alex@example.com", "password": "some long passphrase"}
        for headers in [
            {},
            {"Origin": "https://evil.example", "X-EIP-Request": "1"},
            {"Origin": "http://localhost:3000"},
        ]:
            response = client.post("/api/v1/auth/login", json=payload, headers=headers)
            assert response.status_code == 403


def test_large_auth_body_is_rejected_before_parsing() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/v1/auth/register", content="x" * 17000)
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
        assert response.headers["x-request-id"] == response.json()["error"]["request_id"]
