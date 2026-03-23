from __future__ import annotations


def generate_control_panel(capability_graph: dict[str, list[str]]) -> dict[str, object]:
    widgets: list[dict[str, str]] = []

    flattened = {node.lower() for node in capability_graph.keys()}
    for children in capability_graph.values():
        flattened.update(child.lower() for child in children)

    if "movement" in flattened:
        widgets.append({"type": "joystick", "title": "Movement Joystick"})
        widgets.append({"type": "flight_buttons", "title": "Takeoff / Land / Hover / RTL"})
    if "camera" in flattened:
        widgets.append({"type": "video_feed", "title": "Camera Feed"})
    if "gps" in flattened:
        widgets.append({"type": "map", "title": "Map Navigation"})
    if "lidar" in flattened:
        widgets.append({"type": "obstacle", "title": "Obstacle View"})

    widgets.append({"type": "telemetry_graph", "title": "Telemetry Trends"})

    return {
        "layout": "adaptive-grid",
        "widgets": widgets,
    }
