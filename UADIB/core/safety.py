from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Geofence:
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


class SafetySystem:
    def __init__(self) -> None:
        self.geofence = Geofence(min_lat=-90, max_lat=90, min_lon=-180, max_lon=180)
        self.connection_timeout_s = 5.0

    def set_geofence(self, geofence: Geofence) -> None:
        self.geofence = geofence

    def check_geofence(self, lat: float, lon: float) -> bool:
        return (
            self.geofence.min_lat <= lat <= self.geofence.max_lat
            and self.geofence.min_lon <= lon <= self.geofence.max_lon
        )

    def should_failsafe_land(self, connected: bool, battery_pct: float) -> bool:
        return (not connected) or battery_pct < 15.0
