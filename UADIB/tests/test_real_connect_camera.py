from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)
HEADERS = {"X-UADIB-Token": "changeme"}


def test_connect_details_endpoint() -> None:
    response = client.post(
        "/system/connect/details",
        json={
            "protocol": "mavlink",
            "host": "127.0.0.1",
            "port": 14550,
            "transport": "udp",
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resolved_source"].startswith("mavlink://")


def test_camera_health_without_source() -> None:
    response = client.get("/system/camera/health", headers=HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "camera" in body
    assert "opened" in body["camera"]
