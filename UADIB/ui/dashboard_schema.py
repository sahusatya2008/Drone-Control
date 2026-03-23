from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.models import DroneCapabilities


def generate_dashboard(capabilities: DroneCapabilities) -> dict[str, Any]:
    widgets: list[dict[str, Any]] = [
        {"id": "hud", "type": "flight_hud", "title": "Flight HUD"},
        {"id": "battery", "type": "battery_telemetry", "title": "Battery"},
    ]
    if capabilities.navigation:
        widgets.append({"id": "map", "type": "map_navigation", "title": "Map"})
    if capabilities.camera_control:
        widgets.append({"id": "camera", "type": "camera_view", "title": "Camera"})
    if capabilities.waypoint_navigation:
        widgets.append({"id": "mission", "type": "mission_planner", "title": "Mission Planner"})
    if capabilities.obstacle_avoidance:
        widgets.append({"id": "obstacles", "type": "obstacle_monitor", "title": "Obstacle Monitor"})
    widgets.append({"id": "joystick", "type": "manual_control", "title": "Joystick"})

    return {"capabilities": asdict(capabilities), "widgets": widgets}
