from __future__ import annotations

from core.models import DroneCapabilities, DroneProfile
from plugins.base import UADIBPlugin


class CameraPlugin(UADIBPlugin):
    name = "camera-plugin"

    def supports(self, profile: DroneProfile, capabilities: DroneCapabilities) -> bool:
        return capabilities.camera_control and profile.camera

    def activate(self) -> dict[str, str]:
        return {"status": "active", "feature": "camera_stream"}
