from core.models import DroneCapabilities
from ui.dashboard_schema import generate_dashboard


def test_dashboard_includes_camera_widget() -> None:
    caps = DroneCapabilities(
        navigation=True,
        camera_control=True,
        waypoint_navigation=True,
        obstacle_avoidance=False,
        payload_control=False,
        mission_builder=True,
        realtime_telemetry=True,
    )
    dashboard = generate_dashboard(caps)
    widget_ids = {w["id"] for w in dashboard["widgets"]}
    assert "camera" in widget_ids
    assert "map" in widget_ids
