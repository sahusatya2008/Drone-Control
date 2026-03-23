from __future__ import annotations

from dataclasses import asdict
import time
from typing import Any

from ai.capability_classifier import CapabilityClassifier
from core.mission_builder import MissionBuilder, Waypoint
from core.capability_mapper import CapabilityMapper
from core.drone_profiler import DroneProfiler
from core.models import DroneCapabilities, DroneProfile, ProtocolType
from core.protocol_detector import ProtocolDetector
from core.safety import Geofence, SafetySystem
from plugins.plugin_manager import PluginManager
from protocols.base import DroneAdapter
from protocols.mavlink_adapter import MAVLinkAdapter
from protocols.ros2_adapter import ROS2Adapter
from protocols.sdk_adapter import SDKAdapter


class UADIBRuntime:
    def __init__(self) -> None:
        self.detector = ProtocolDetector()
        self.profiler = DroneProfiler()
        self.mapper = CapabilityMapper(CapabilityClassifier())
        self.plugins = PluginManager()
        self.safety = SafetySystem()
        self.missions = MissionBuilder()
        self.adapter: DroneAdapter | None = None
        self.profile: DroneProfile | None = None
        self.capabilities: DroneCapabilities | None = None
        self._connected_at: float | None = None
        self._last_telemetry: dict[str, Any] = {}
        self._last_telemetry_ts: float | None = None

    def connect(self, source: str) -> dict[str, Any]:
        endpoint = self.detector.detect(source)
        self.adapter = self._build_adapter(endpoint.protocol, source)
        self.profile = self.profiler.build_profile(self.adapter)
        self.capabilities = self.mapper.map(self.profile)
        self.plugins.autoload(self.profile, self.capabilities)
        self._connected_at = time.time()
        self.telemetry()  # Prime link and telemetry state.

        return {
            "endpoint": asdict(endpoint),
            "profile": asdict(self.profile),
            "capabilities": asdict(self.capabilities),
            "plugins": self.plugins.loaded_plugin_names(),
        }

    def telemetry(self) -> dict[str, Any]:
        if not self.adapter:
            return {"connected": False}
        sample = {"connected": True, **self.adapter.read_telemetry()}
        gps = sample.get("gps") or {}
        if "lat" in gps and "lon" in gps:
            inside_geofence = self.safety.check_geofence(float(gps["lat"]), float(gps["lon"]))
            sample["inside_geofence"] = inside_geofence
        sample["failsafe_recommended"] = self.safety.should_failsafe_land(
            connected=True, battery_pct=float(sample.get("battery_pct", 100))
        )
        self._last_telemetry = sample
        self._last_telemetry_ts = time.time()
        return sample

    def command(self, name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.adapter:
            raise RuntimeError("No drone connected")
        return self.adapter.send_command(name, payload or {})

    def safe_command(
        self,
        name: str,
        payload: dict[str, Any] | None = None,
        retries: int = 2,
        require_preflight: bool = False,
    ) -> dict[str, Any]:
        if not self.adapter:
            raise RuntimeError("No drone connected")

        if require_preflight:
            preflight = self.preflight_check()
            if not preflight["ok"]:
                raise RuntimeError(f"Preflight failed: {', '.join(preflight['issues'])}")

        error: Exception | None = None
        for _ in range(max(1, retries)):
            try:
                result = self.command(name, payload or {})
                return {"status": "ok", "result": result}
            except Exception as exc:  # pragma: no cover - retry path
                error = exc
                time.sleep(0.08)

        raise RuntimeError(f"Command execution failed after retries: {error}")

    def preflight_check(self) -> dict[str, Any]:
        issues: list[str] = []
        warnings: list[str] = []

        if not self.adapter or not self.profile or not self.capabilities:
            issues.append("No connected drone session")
            return {"ok": False, "issues": issues, "warnings": warnings, "telemetry": {}}

        telemetry = self.telemetry()
        now = time.time()
        if self._last_telemetry_ts is None or now - self._last_telemetry_ts > 3.0:
            issues.append("Telemetry link timeout")

        battery = float(telemetry.get("battery_pct", 100))
        if battery < 20.0:
            issues.append(f"Battery too low for safe operation ({battery:.1f}%)")
        elif battery < 30.0:
            warnings.append(f"Battery low ({battery:.1f}%)")

        if telemetry.get("failsafe_recommended", False):
            issues.append("Failsafe recommended by safety system")

        if "inside_geofence" in telemetry and not bool(telemetry["inside_geofence"]):
            issues.append("Drone is outside configured geofence")

        if self.capabilities.navigation and "gps" not in telemetry:
            issues.append("GPS telemetry missing")

        if self.profile.camera and not self.capabilities.camera_control:
            warnings.append("Camera detected but capability mapping disabled camera control")

        return {
            "ok": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "telemetry": telemetry,
            "camera_available": bool(self.profile.camera),
            "connected_for_s": round(now - (self._connected_at or now), 2),
        }

    def build_mission(self, points: list[dict[str, float]]) -> dict[str, Any]:
        waypoints = [Waypoint(**point) for point in points]
        optimized = self.missions.optimize_path(waypoints)
        simulation = self.missions.simulate(optimized)
        return {
            "waypoints": [asdict(wp) for wp in optimized],
            "simulation": simulation,
        }

    def configure_geofence(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> dict[str, float]:
        self.safety.set_geofence(Geofence(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon))
        return {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
        }

    @staticmethod
    def _build_adapter(protocol: ProtocolType, source: str) -> DroneAdapter:
        if protocol == ProtocolType.MAVLINK:
            return MAVLinkAdapter(source)
        if protocol == ProtocolType.ROS2:
            return ROS2Adapter(source)
        if protocol == ProtocolType.SDK:
            return SDKAdapter(source)
        return SDKAdapter(source)
