from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)


def test_uarip_page() -> None:
    response = client.get("/uarip")
    assert response.status_code == 200
    assert "UARIP Mode" in response.text


def test_uarip_overview() -> None:
    response = client.get("/uarip/overview")
    assert response.status_code == 200
    assert response.json()["name"] == "UARIP"


def test_uarip_protocol_infer() -> None:
    response = client.post("/uarip/protocol/infer", json={"packets_hex": ["fe01020304ff", "fe01020505ff"]})
    assert response.status_code == 200
    assert "schema" in response.json()


def test_uarip_swarm_step() -> None:
    payload = {
        "agents": [
            {"id": "d1", "pos": [0, 0, 10], "vel": [1, 0, 0], "goal": [10, 10, 10]},
            {"id": "d2", "pos": [1, 0, 10], "vel": [1, 0.1, 0], "goal": [10, 10, 10]},
        ]
    }
    response = client.post("/uarip/swarm/step", json=payload)
    assert response.status_code == 200
    assert len(response.json()["agents"]) == 2
