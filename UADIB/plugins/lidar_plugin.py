from __future__ import annotations

from core.models import DroneCapabilities, DroneProfile
from plugins.base import UADIBPlugin


class LidarPlugin(UADIBPlugin):
    name = "lidar-plugin"

    def supports(self, profile: DroneProfile, capabilities: DroneCapabilities) -> bool:
        return capabilities.obstacle_avoidance and profile.lidar

    def activate(self) -> dict[str, str]:
        return {"status": "active", "feature": "obstacle_monitor"}
