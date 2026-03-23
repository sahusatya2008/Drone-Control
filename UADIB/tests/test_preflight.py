from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)
HEADERS = {"X-UADIB-Token": "changeme"}


def test_preflight_flow() -> None:
    client.post("/system/connect", json={"source": "mavlink://udp:127.0.0.1:14550"}, headers=HEADERS)
    response = client.get("/drone/preflight", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "ok" in body
    assert "telemetry" in body
