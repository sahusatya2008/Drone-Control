from __future__ import annotations

from core.models import DroneProfile
from protocols.base import DroneAdapter


class DroneProfiler:
    """Extract metadata and normalize profile fields."""

    def build_profile(self, adapter: DroneAdapter) -> DroneProfile:
        metadata = adapter.fetch_metadata()
        sensors = metadata.get("sensors", ["IMU", "GPS"])
        return DroneProfile(
            drone_model=metadata.get("drone_model", "Unknown"),
            flight_controller=metadata.get("flight_controller", "Unknown FC"),
            firmware=metadata.get("firmware", "unknown"),
            sensors=sensors,
            motors=int(metadata.get("motors", 4)),
            camera=bool(metadata.get("camera", False)),
            lidar=bool(metadata.get("lidar", False)),
            gps_modules=int(metadata.get("gps_modules", 1)),
            battery_cells=int(metadata.get("battery_cells", 4)),
        )
