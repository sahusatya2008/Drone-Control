from __future__ import annotations

from urllib.parse import urlparse

from core.models import DetectedEndpoint, ProtocolType


class ProtocolDetector:
    """Detects UAV transport/protocol from endpoint signatures."""

    _prefix_map = {
        "mavlink": ProtocolType.MAVLINK,
        "ros2": ProtocolType.ROS2,
        "sdk": ProtocolType.SDK,
        "udp": ProtocolType.MAVLINK,
        "tcp": ProtocolType.TELEMETRY_STREAM,
        "serial": ProtocolType.MAVLINK,
    }

    def detect(self, source: str) -> DetectedEndpoint:
        if not source:
            return DetectedEndpoint(ProtocolType.UNKNOWN, source, 0.0)

        parsed = urlparse(source)
        scheme = parsed.scheme.lower()

        if scheme in self._prefix_map:
            protocol = self._prefix_map[scheme]
            confidence = 0.95 if scheme in {"mavlink", "ros2", "sdk"} else 0.75
            return DetectedEndpoint(protocol=protocol, source=source, confidence=confidence)

        src = source.lower()
        if "mav" in src or ":14550" in src:
            return DetectedEndpoint(ProtocolType.MAVLINK, source, 0.7)
        if "ros" in src or "/topic/" in src:
            return DetectedEndpoint(ProtocolType.ROS2, source, 0.65)
        if src.startswith("http://") or src.startswith("https://"):
            return DetectedEndpoint(ProtocolType.SDK, source, 0.6)

        return DetectedEndpoint(ProtocolType.UNKNOWN, source, 0.2)

    def scan_sources(self, sources: list[str]) -> DetectedEndpoint:
        best = DetectedEndpoint(protocol=ProtocolType.UNKNOWN, source="", confidence=0.0)
        for source in sources:
            detected = self.detect(source)
            if detected.confidence > best.confidence:
                best = detected
        return best
