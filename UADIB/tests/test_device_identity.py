from pathlib import Path

from fastapi.testclient import TestClient

from api.server import app
from core.device_identity import DeviceIdentityManager


def test_device_id_persistent(tmp_path: Path) -> None:
    id_file = tmp_path / "device_identity.json"
    manager = DeviceIdentityManager(id_file=id_file)

    first = manager.get_or_create()
    second = manager.get_or_create()

    assert first.device_id == second.device_id
    assert first.created_at == second.created_at


def test_device_and_ipr_routes() -> None:
    client = TestClient(app)

    device = client.get("/system/device")
    assert device.status_code == 200
    body = device.json()
    assert "device_id" in body
    assert "configuration" in body

    ipr = client.get("/ipr")
    assert ipr.status_code == 200
    assert "Intellectual Property Rights" in ipr.text
