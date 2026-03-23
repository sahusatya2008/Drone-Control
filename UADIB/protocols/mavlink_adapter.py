from __future__ import annotations

import random
import time
from typing import Any

from protocols.base import DroneAdapter


class MAVLinkAdapter(DroneAdapter):
    """MAVLink adapter; can be replaced with real MAVSDK bindings."""

    def __init__(self, source: str) -> None:
        super().__init__(source)
        self._armed = False
        self._last_alt = 0.0
        self._speed_mps = 0.0
        self._yaw_deg = 0.0
        self._camera_streaming = False
        self._position = {"lat": 37.7749, "lon": -122.4194}

    def fetch_metadata(self) -> dict[str, Any]:
        return {
            "drone_model": "PX4-Compatible",
            "flight_controller": "Pixhawk",
            "firmware": "PX4 1.15",
            "sensors": ["IMU", "GPS", "Barometer"],
            "motors": 4,
            "camera": True,
            "lidar": False,
            "gps_modules": 1,
            "battery_cells": 6,
        }

    def read_telemetry(self) -> dict[str, Any]:
        if self._armed:
            self._last_alt = max(0.0, self._last_alt + random.uniform(-0.3, 0.6))
            self._position["lat"] += random.uniform(-0.0002, 0.0002)
            self._position["lon"] += random.uniform(-0.0002, 0.0002)
        else:
            self._last_alt = max(0.0, self._last_alt - random.uniform(0.0, 0.2))
        return {
            "timestamp": time.time(),
            "altitude_m": round(self._last_alt, 2),
            "speed_mps": round(self._speed_mps if self._armed else 0.0, 2),
            "battery_pct": round(random.uniform(35, 100), 1),
            "gps": {"lat": self._position["lat"], "lon": self._position["lon"]},
            "armed": self._armed,
            "yaw_deg": round(self._yaw_deg, 1),
            "camera_streaming": self._camera_streaming,
            "link": "mavlink",
        }

    def send_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if command == "takeoff":
            self._armed = True
            self._last_alt = max(self._last_alt, float(payload.get("altitude_m", 5.0)))
            self._speed_mps = max(self._speed_mps, 2.0)
        elif command == "land":
            self._last_alt = 0.0
            self._armed = False
            self._speed_mps = 0.0
        elif command == "set_speed":
            self._speed_mps = max(0.0, float(payload.get("speed_mps", 0.0)))
        elif command == "yaw":
            self._yaw_deg = float(payload.get("yaw_deg", self._yaw_deg)) % 360
        elif command == "move":
            self._position["lat"] += float(payload.get("delta_lat", 0.0))
            self._position["lon"] += float(payload.get("delta_lon", 0.0))
            self._last_alt = max(0.0, self._last_alt + float(payload.get("delta_alt", 0.0)))
        elif command == "hover":
            self._speed_mps = 0.0
        elif command == "camera_start":
            self._camera_streaming = True
        elif command == "camera_stop":
            self._camera_streaming = False
        return {"status": "ok", "command": command, "payload": payload, "protocol": "mavlink"}
