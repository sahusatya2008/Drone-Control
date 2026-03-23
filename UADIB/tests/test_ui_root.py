from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)


def test_root_serves_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_api_root_json() -> None:
    response = client.get("/api")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "UADIB API"
