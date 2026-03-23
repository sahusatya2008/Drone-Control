from __future__ import annotations

from ai.capability_classifier import CapabilityClassifier
from core.models import DroneCapabilities, DroneProfile


class CapabilityMapper:
    """Maps drone profile into unified capabilities and augments unknowns via AI inference."""

    def __init__(self, classifier: CapabilityClassifier | None = None) -> None:
        self.classifier = classifier or CapabilityClassifier()

    def map(self, profile: DroneProfile) -> DroneCapabilities:
        inferred = self.classifier.infer_from_profile(profile)

        has_gps = "GPS" in {s.upper() for s in profile.sensors}
        return DroneCapabilities(
            navigation=has_gps,
            camera_control=profile.camera or inferred["camera_available"] > 0.6,
            waypoint_navigation=has_gps and profile.motors >= 4,
            obstacle_avoidance=profile.lidar or inferred["lidar_available"] > 0.65,
            payload_control=inferred["payload_system"] > 0.5,
            mission_builder=True,
            realtime_telemetry=True,
        )
