from __future__ import annotations

import time
from typing import Any

from protocols.base import DroneAdapter


class SDKAdapter(DroneAdapter):
    """REST/SDK bridge adapter for vendor APIs."""

    def __init__(self, source: str) -> None:
        super().__init__(source)
        self._state: dict[str, Any] = {
            "armed": False,
            "camera_streaming": False,
            "speed_mps": 0.0,
            "yaw_deg": 0.0,
            "lat": 0.0,
            "lon": 0.0,
            "altitude_m": 0.0,
        }

    def fetch_metadata(self) -> dict[str, Any]:
        return {
            "drone_model": "SDK-Generic",
            "flight_controller": "Vendor FC",
            "firmware": "2026.1",
            "sensors": ["IMU", "GPS"],
            "motors": 4,
            "camera": True,
            "lidar": False,
            "gps_modules": 1,
            "battery_cells": 4,
        }

    def read_telemetry(self) -> dict[str, Any]:
        return {
            "timestamp": time.time(),
            "altitude_m": self._state["altitude_m"] if self._state["armed"] else 0.0,
            "speed_mps": self._state["speed_mps"] if self._state["armed"] else 0.0,
            "battery_pct": 74.0,
            "gps": {"lat": self._state["lat"], "lon": self._state["lon"]},
            "yaw_deg": self._state["yaw_deg"],
            "armed": self._state["armed"],
            "camera_streaming": self._state["camera_streaming"],
            "link": "sdk",
        }

    def send_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command == "takeoff":
            self._state["armed"] = True
            self._state["altitude_m"] = max(self._state["altitude_m"], float(payload.get("altitude_m", 3.0)))
        if command == "land":
            self._state["armed"] = False
            self._state["altitude_m"] = 0.0
            self._state["speed_mps"] = 0.0
        if command == "set_speed":
            self._state["speed_mps"] = max(0.0, float(payload.get("speed_mps", 0.0)))
        if command == "yaw":
            self._state["yaw_deg"] = float(payload.get("yaw_deg", self._state["yaw_deg"])) % 360
        if command == "move":
            self._state["lat"] += float(payload.get("delta_lat", 0.0))
            self._state["lon"] += float(payload.get("delta_lon", 0.0))
            self._state["altitude_m"] = max(0.0, self._state["altitude_m"] + float(payload.get("delta_alt", 0.0)))
        if command == "hover":
            self._state["speed_mps"] = 0.0
        if command == "camera_start":
            self._state["camera_streaming"] = True
        if command == "camera_stop":
            self._state["camera_streaming"] = False
        return {"status": "ok", "command": command, "payload": payload, "protocol": "sdk"}
