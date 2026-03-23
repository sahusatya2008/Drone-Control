from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ProtocolType(StrEnum):
    MAVLINK = "mavlink"
    ROS2 = "ros2"
    SDK = "sdk"
    TELEMETRY_STREAM = "telemetry_stream"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class DetectedEndpoint:
    protocol: ProtocolType
    source: str
    confidence: float
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class DroneProfile:
    drone_model: str
    flight_controller: str
    firmware: str
    sensors: list[str]
    motors: int
    camera: bool
    lidar: bool
    gps_modules: int
    battery_cells: int


@dataclass(slots=True)
class DroneCapabilities:
    navigation: bool
    camera_control: bool
    waypoint_navigation: bool
    obstacle_avoidance: bool
    payload_control: bool
    mission_builder: bool
    realtime_telemetry: bool
