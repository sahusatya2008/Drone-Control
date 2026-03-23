from __future__ import annotations


class PermissionManager:
    def __init__(self, allowed_commands: set[str] | None = None) -> None:
        self.allowed_commands = allowed_commands or {
            "takeoff",
            "land",
            "set_waypoint",
            "set_speed",
            "yaw",
            "move",
            "hover",
            "camera_start",
            "camera_stop",
            "rtl",
        }

    def ensure_allowed(self, command: str) -> None:
        if command not in self.allowed_commands:
            raise PermissionError(f"Command not allowed: {command}")
