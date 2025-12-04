from __future__ import annotations

from fastapi.testclient import TestClient

from dbl_boundary_service.main import create_app


def test_health_endpoint_ok() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_index_serves_html() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/html")
    assert "DBL Boundary Service" in response.text
    assert "Governed LLM boundary" in response.text


def test_set_key_stores_api_key() -> None:
    app = create_app()
    client = TestClient(app)

    payload = {"api_key": "sk-test-1234567890"}
    response = client.patch("/set-key", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


def test_run_dry_run_without_api_key() -> None:
    """Dry run should work without API key."""
    app = create_app()
    # Use context manager to trigger lifespan
    with TestClient(app) as client:
        payload = {
            "prompt": "Hello, how are you?",
            "dry_run": True,
        }
        response = client.post("/run", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data.get("blocked") is False
        assert "[DRY RUN]" in data.get("content", "")
        assert "snapshot" in data
        snapshot = data["snapshot"]
        assert snapshot.get("dbl_outcome") == "allow"
        assert snapshot.get("dry_run") is True


def test_run_with_invalid_api_key_fails() -> None:
    """Real call with invalid API key should fail at OpenAI."""
    from dbl_boundary_service.security import api_key_store
    
    app = create_app()
    with TestClient(app) as client:
        # Set an invalid key
        api_key_store.set("sk-invalid-test-key")
        
        payload = {
            "prompt": "Hello",
            "dry_run": False,
        }
        response = client.post("/run", json=payload)

        # Should fail with 500 (OpenAI auth error)
        # In production, this would be a more specific error
        assert response.status_code == 500