from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)
HEADERS = {"X-UADIB-Token": "changeme"}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_connect_and_telemetry() -> None:
    response = client.post("/system/connect", json={"source": "mavlink://udp:127.0.0.1:14550"}, headers=HEADERS)
    assert response.status_code == 200
    telemetry = client.get("/drone/telemetry", headers=HEADERS)
    assert telemetry.status_code == 200
    assert "connected" in telemetry.json()
