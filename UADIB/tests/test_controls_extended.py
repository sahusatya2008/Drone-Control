from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)
HEADERS = {"X-UADIB-Token": "changeme"}


def setup_module() -> None:
    client.post("/system/connect", json={"source": "mavlink://udp:127.0.0.1:14550"}, headers=HEADERS)


def test_extended_controls() -> None:
    assert client.post("/drone/set_speed", json={"speed_mps": 6.5}, headers=HEADERS).status_code == 200
    assert client.post("/drone/yaw", json={"yaw_deg": 90}, headers=HEADERS).status_code == 200
    assert client.post(
        "/drone/move",
        json={"delta_lat": 0.0001, "delta_lon": 0.0001, "delta_alt": 1.0},
        headers=HEADERS,
    ).status_code == 200
    assert client.post("/drone/camera/stop", headers=HEADERS).status_code == 200


def test_manual_page_available() -> None:
    response = client.get("/static/manual.html")
    assert response.status_code == 200
    assert "UADIB Full Manual" in response.text
