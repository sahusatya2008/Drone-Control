from __future__ import annotations

import time
from typing import Any

from protocols.base import DroneAdapter


class ROS2Adapter(DroneAdapter):
    """ROS2 adapter placeholder using deterministic telemetry for integration."""

    def __init__(self, source: str) -> None:
        super().__init__(source)
        self._state: dict[str, Any] = {"armed": True, "speed_mps": 4.7, "yaw_deg": 0.0}

    def fetch_metadata(self) -> dict[str, Any]:
        return {
            "drone_model": "ROS2-UAV",
            "flight_controller": "ROS2Bridge",
            "firmware": "n/a",
            "sensors": ["IMU", "GPS", "Lidar"],
            "motors": 6,
            "camera": True,
            "lidar": True,
            "gps_modules": 2,
            "battery_cells": 6,
        }

    def read_telemetry(self) -> dict[str, Any]:
        return {
            "timestamp": time.time(),
            "altitude_m": 12.4,
            "speed_mps": self._state["speed_mps"],
            "battery_pct": 82.1,
            "gps": {"lat": 48.8566, "lon": 2.3522},
            "yaw_deg": self._state["yaw_deg"],
            "armed": self._state["armed"],
            "link": "ros2",
        }

    def send_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command == "set_speed":
            self._state["speed_mps"] = max(0.0, float(payload.get("speed_mps", self._state["speed_mps"])))
        if command == "yaw":
            self._state["yaw_deg"] = float(payload.get("yaw_deg", self._state["yaw_deg"])) % 360
        if command == "hover":
            self._state["speed_mps"] = 0.0
        if command == "land":
            self._state["armed"] = False
        if command == "takeoff":
            self._state["armed"] = True
        return {"status": "ok", "command": command, "payload": payload, "protocol": "ros2"}
