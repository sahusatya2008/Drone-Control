# UADIB — Universal Autonomous Drone Interface Builder STAGE I

> **Version:** 0.1.0 · **Python:** ≥3.11 · **License:** Proprietary · **Developer:** Satya Narayan Sahu

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Core Module Reference](#core-module-reference)
4. [Protocol Adapter Layer](#protocol-adapter-layer)
5. [AI Inference Engine](#ai-inference-engine)
6. [Plugin System](#plugin-system)
7. [Security Model](#security-model)
8. [Telemetry Subsystem](#telemetry-subsystem)
9. [REST API Reference](#rest-api-reference)
10. [WebSocket API](#websocket-api)
11. [UARIP Mode](#uarip-mode)
12. [Camera Stream System](#camera-stream-system)
13. [Mission Builder](#mission-builder)
14. [Safety System](#safety-system)
15. [Device Identity](#device-identity)
16. [Dashboard Generation](#dashboard-generation)
17. [Simulator](#simulator)
18. [Frontend Architecture](#frontend-architecture)
19. [Configuration](#configuration)
20. [Installation & Deployment](#installation--deployment)
21. [Testing](#testing)
22. [Repository Layout](#repository-layout)

---

## Executive Summary

UADIB is a modular, polyglot framework for universal drone interfacing. It performs automatic protocol detection over MAVLink, ROS2, SDK/REST, and raw TCP/UDP telemetry streams, profiles connected UAV hardware, maps capabilities to a unified domain model, generates dynamic control dashboards, and exposes REST + WebSocket APIs for real-time control and telemetry ingestion.

The system is designed around an adapter pattern where each protocol implementation conforms to a common `DroneAdapter` interface. A runtime orchestrator (`UADIBRuntime`) manages the full lifecycle: detection → profiling → capability mapping → plugin activation → command execution → telemetry streaming → safety enforcement.

### Key Design Principles

- **Protocol Agnosticism:** All drone interaction goes through abstracted adapters; the API layer never touches raw protocol bytes.
- **Capability-Driven UI:** Dashboard widgets are generated dynamically based on inferred drone capabilities, not hardcoded per model.
- **Defense-in-Depth Safety:** Preflight checks, geofence enforcement, battery failsafe, and command permission layers prevent unsafe operations.
- **Polyglot Core:** Python orchestration, Rust telemetry parsing (optional), TypeScript dashboard schema generation, C++ adapter skeleton for proprietary protocols.
- **Plugin Autoloading:** Plugins self-register and activate based on a predicate over the drone profile and capability set.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Flight   │  │ Camera   │  │ Mission  │  │ UARIP Mode       │   │
│  │ HUD      │  │ View     │  │ Planner  │  │ (Swarm/Protocol) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│       └──────────────┴──────────────┴────────────────┘             │
│                    HTTP / WebSocket                                │
└────────────────────────────┬───────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Server (api/server.py)                  │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐  │
│  │ Drone Control  │  │ System Endpts  │  │ UARIP Endpoints     │  │
│  │ Router         │  │ (connect/      │  │ (protocol/          │  │
│  │ (/drone/*)     │  │  dashboard/    │  │  swarm/simulation/  │  │
│  │                │  │  camera)       │  │  anomaly)           │  │
│  └────────┬───────┘  └────────┬───────┘  └──────────┬──────────┘  │
│           └───────────────────┴─────────────────────┘             │
│                         │                                          │
│  ┌──────────────────────▼──────────────────────────────────────┐   │
│  │              UADIBRuntime (core/runtime.py)                 │   │
│  │  ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │ Protocol       │ │ Drone        │ │ Capability       │  │   │
│  │  │ Detector       │ │ Profiler     │ │ Mapper           │  │   │
│  │  └───────┬────────┘ └──────┬───────┘ └────────┬─────────┘  │   │
│  │          │                 │                   │            │   │
│  │  ┌───────▼─────────────────▼───────────────────▼─────────┐  │   │
│  │  │              DroneAdapter (Abstract)                  │  │   │
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐           │  │   │
│  │  │  │ MAVLink   │ │ ROS2      │ │ SDK/REST  │           │  │   │
│  │  │  │ Adapter   │ │ Adapter   │ │ Adapter   │           │  │   │
│  │  │  └───────────┘ └───────────┘ └───────────┘           │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  │                                                              │   │
│  │  ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐  │   │
│  │  │ Safety System  │ │ Plugin Mgr   │ │ Mission Builder  │  │   │
│  │  │ (Geofence/     │ │ (Auto-load)  │ │ (Optimize/       │  │   │
│  │  │  Failsafe)     │ │              │ │  Simulate)       │  │   │
│  │  └────────────────┘ └──────────────┘ └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Connect → Command → Telemetry

1. **Connect:** `POST /system/connect` → `ProtocolDetector.detect()` → adapter instantiation → `DroneProfiler.build_profile()` → `CapabilityMapper.map()` → `PluginManager.autoload()` → dashboard generation
2. **Command:** `POST /drone/<command>` → `PermissionManager.ensure_allowed()` → `UADIBRuntime.safe_command()` → optional preflight → retry loop → `DroneAdapter.send_command()`
3. **Telemetry:** `WS /ws/telemetry` → `TelemetryStream.stream()` → `UADIBRuntime.telemetry()` → `DroneAdapter.read_telemetry()` → geofence check → failsafe evaluation → JSON emission

---

## Core Module Reference

### `core/models.py` — Domain Data Models

Defines the fundamental data structures used across the system:

```python
class ProtocolType(StrEnum):
    MAVLINK = "mavlink"
    ROS2 = "ros2"
    SDK = "sdk"
    TELEMETRY_STREAM = "telemetry_stream"
    UNKNOWN = "unknown"

@dataclass(slots=True)
class DetectedEndpoint:
    protocol: ProtocolType    # Detected protocol type
    source: str               # Original source URI
    confidence: float         # Detection confidence [0.0, 1.0]
    metadata: dict            # Additional detection metadata

@dataclass(slots=True)
class DroneProfile:
    drone_model: str          # Manufacturer/model string
    flight_controller: str    # FC type (e.g., "Pixhawk", "ROS2Bridge")
    firmware: str             # Firmware version string
    sensors: list[str]        # Sensor list (e.g., ["IMU", "GPS", "Barometer"])
    motors: int               # Motor count
    camera: bool              # Camera presence flag
    lidar: bool               # LiDAR presence flag
    gps_modules: int          # GPS module count
    battery_cells: int        # Battery cell count (S-rating)

@dataclass(slots=True)
class DroneCapabilities:
    navigation: bool                # GPS-based navigation
    camera_control: bool            # Camera stream/command support
    waypoint_navigation: bool       # Waypoint mission support
    obstacle_avoidance: bool        # Obstacle detection/avoidance
    payload_control: bool           # Payload release/actuation
    mission_builder: bool           # Mission planning capability
    realtime_telemetry: bool        # Real-time telemetry streaming
```

### `core/protocol_detector.py` — Protocol Detection Engine

The `ProtocolDetector` class identifies the communication protocol from a source URI using a multi-tier heuristic:

| Detection Tier | Method | Confidence |
|---|---|---|
| **Tier 1** | URI scheme prefix match (`mavlink://`, `ros2://`, `sdk://`) | 0.95 |
| **Tier 2** | Transport scheme match (`udp://`, `tcp://`, `serial://`) | 0.75 |
| **Tier 3** | Content heuristic (`:14550` → MAVLink, `/topic/` → ROS2, `http://` → SDK) | 0.60–0.70 |
| **Tier 4** | Unknown fallback | 0.20 |

The `scan_sources()` method accepts multiple source candidates and returns the highest-confidence detection.

### `core/drone_profiler.py` — Hardware Profiling

`DroneProfiler.build_profile(adapter)` calls `DroneAdapter.fetch_metadata()` and normalizes the result into a `DroneProfile` dataclass. Default values are applied for missing fields:
- Default sensors: `["IMU", "GPS"]`
- Default motors: `4`
- Default battery cells: `4`

### `core/capability_mapper.py` — Capability Inference

`CapabilityMapper` combines deterministic rules with AI-inferred scores from `CapabilityClassifier`:

| Capability | Deterministic Condition | AI Augmentation |
|---|---|---|
| `navigation` | `"GPS" in sensors` | — |
| `camera_control` | `profile.camera` | OR `inferred["camera_available"] > 0.6` |
| `waypoint_navigation` | `"GPS" in sensors AND motors >= 4` | — |
| `obstacle_avoidance` | `profile.lidar` | OR `inferred["lidar_available"] > 0.65` |
| `payload_control` | — | `inferred["payload_system"] > 0.5` |
| `mission_builder` | Always `True` | — |
| `realtime_telemetry` | Always `True` | — |

### `core/mission_builder.py` — Mission Planning

`MissionBuilder` implements waypoint mission optimization and simulation:

- **`optimize_path(waypoints)`:** For 3+ waypoints, computes centroid and reorders points by ascending distance from centroid (nearest-neighbor heuristic using `numpy`).
- **`simulate(waypoints, speed_mps)`:** Calculates total Haversine-approximated distance using 111,111 m/degree scaling, then computes ETA as `distance / speed_mps`.

**Waypoint Model:**
```python
@dataclass(slots=True)
class Waypoint:
    lat: float   # Latitude in degrees
    lon: float   # Longitude in degrees
    alt: float   # Altitude in meters AGL
```

### `core/safety.py` — Safety System

`SafetySystem` enforces operational safety boundaries:

- **Geofence:** Configurable rectangular boundary (`min_lat`, `max_lat`, `min_lon`, `max_lon`). Default: full globe.
- **Connection Timeout:** 5.0 seconds (configurable).
- **Failsafe Trigger:** Battery below 15% OR connection loss → `should_failsafe_land()` returns `True`.
- **Battery Warnings:** <20% → hard failure in preflight; 20–30% → warning.

### `core/device_identity.py` — Device Identity Management

`DeviceIdentityManager` creates and persists a unique, immutable device identifier:

- **Device ID Format:** `UADIB-<16 hex chars>` (SHA-256 derived)
- **Host Fingerprint:** SHA-256 of `hostname::arch::os::MAC` (first 24 hex chars)
- **Persistence:** `~/.uadib/device_identity.json` with `0o444` permissions
- **Fallback Chain:** Home directory → `/tmp/.uadib/` → volatile (process-lifetime)
- **Config Metadata:** hostname, OS, OS version, architecture, Python version, CPU count

---

## Protocol Adapter Layer

### `protocols/base.py` — Abstract Adapter Interface

All protocol implementations must subclass `DroneAdapter` and implement three methods:

```python
class DroneAdapter(ABC):
    def __init__(self, source: str) -> None: ...
    
    @abstractmethod
    def fetch_metadata(self) -> dict[str, Any]: ...
    
    @abstractmethod
    def read_telemetry(self) -> dict[str, Any]: ...
    
    @abstractmethod
    def send_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]: ...
```

### `protocols/mavlink_adapter.py` — MAVLink Adapter

Simulates a PX4-compatible quadcopter over MAVLink. Supports internal state tracking for armed status, altitude, speed, yaw, GPS position, and camera streaming.

**Metadata Profile:** Pixhawk FC, PX4 1.15 firmware, 4 motors, 6S battery, IMU/GPS/Barometer sensors, camera enabled.

**Supported Commands:**

| Command | Payload Fields | Behavior |
|---|---|---|
| `takeoff` | `altitude_m` (default: 5.0) | Arms motors, sets altitude, speed ≥2.0 m/s |
| `land` | — | Disarms, altitude → 0, speed → 0 |
| `set_speed` | `speed_mps` | Updates cruise speed |
| `yaw` | `yaw_deg` | Sets heading modulo 360° |
| `move` | `delta_lat`, `delta_lon`, `delta_alt` | Relative position adjustment |
| `hover` | — | Sets speed to 0 |
| `camera_start` | — | Enables streaming flag |
| `camera_stop` | — | Disables streaming flag |

**Telemetry Output:**
```json
{
  "timestamp": 1711000000.0,
  "altitude_m": 5.23,
  "speed_mps": 3.14,
  "battery_pct": 87.3,
  "gps": {"lat": 37.7749, "lon": -122.4194},
  "armed": true,
  "yaw_deg": 45.0,
  "camera_streaming": true,
  "link": "mavlink"
}
```

### `protocols/ros2_adapter.py` — ROS2 Adapter

Deterministic telemetry adapter for ROS2-based systems. Static altitude (12.4m), GPS (Paris, France), 82.1% battery. Supports speed, yaw, hover, land, and takeoff state mutations.

**Metadata Profile:** 6 motors, LiDAR enabled, 2 GPS modules, 6S battery.

### `protocols/sdk_adapter.py` — SDK/REST Adapter

Generic REST/SDK bridge for vendor-specific APIs. Tracks armed state, camera streaming, speed, yaw, and position. Supports all standard commands plus camera start/stop.

**Metadata Profile:** 4 motors, 4S battery, IMU/GPS sensors, camera enabled.

### `protocols/cpp_adapter.cpp` — C++ Adapter Skeleton

Optional C++ class for proprietary protocol integration. Provides `connect()` and `read_packet()` interface. Build separately with CMake if required.

---

## AI Inference Engine

### `ai/system_inference_model.py` — Scoring Model

`SystemInferenceModel.predict(features)` applies element-wise sigmoid normalization over a 4-channel feature vector:

```
σ(x) = 1 / (1 + e^(-x)),  x ∈ [-8, 8]
```

**Output Channels:**

| Index | Channel | Description |
|---|---|---|
| 0 | `camera_available` | Probability of camera availability |
| 1 | `gps_available` | Probability of GPS availability |
| 2 | `lidar_available` | Probability of LiDAR availability |
| 3 | `payload_system` | Probability of payload actuation system |

> **Production Note:** The current model uses raw sigmoid scoring. Replace with a trained neural network by subclassing and loading weights in `_try_init_torch_model()`.

### `ai/capability_classifier.py` — Feature Extraction

`CapabilityClassifier.infer_from_profile(profile)` transforms a `DroneProfile` into a 4-element NumPy feature vector:

| Feature | Positive Signal | Negative Signal |
|---|---|---|
| Camera | `profile.camera → +2.0` | `!profile.camera → -1.2` |
| GPS | `"GPS" in sensors → +2.5` | `no GPS → -1.5` |
| LiDAR | `profile.lidar → +1.8` | `!profile.lidar → -1.3` |
| Payload | `motors >= 6 → +0.8` | `motors < 6 → -0.4` |

---

## Plugin System

### `plugins/base.py` — Plugin Interface

```python
class UADIBPlugin(ABC):
    name = "unnamed-plugin"

    @abstractmethod
    def supports(self, profile: DroneProfile, capabilities: DroneCapabilities) -> bool: ...

    @abstractmethod
    def activate(self) -> dict[str, Any]: ...
```

### `plugins/plugin_manager.py` — Auto-Discovery & Activation

`PluginManager` uses `pkgutil.iter_modules()` to discover all classes in the `plugins` package that subclass `UADIBPlugin`. On `autoload(profile, capabilities)`:

1. Clear previous active plugins
2. Iterate registry; for each plugin, evaluate `supports(profile, capabilities)`
3. If supported, call `activate()` and store result in `self.active[plugin.name]`

### Built-in Plugins

| Plugin | Activation Condition | Output |
|---|---|---|
| `camera-plugin` | `capabilities.camera_control AND profile.camera` | `{"status": "active", "feature": "camera_stream"}` |
| `lidar-plugin` | `capabilities.obstacle_avoidance AND profile.lidar` | `{"status": "active", "feature": "obstacle_monitor"}` |

### Writing Custom Plugins

1. Create `plugins/my_plugin.py`
2. Subclass `UADIBPlugin`
3. Implement `supports()` and `activate()`
4. The plugin manager auto-discovers it on next runtime initialization

---

## Security Model

### `security/authentication.py` — API Token Authentication

Uses FastAPI's `APIKeyHeader` dependency injection. The `X-UADIB-Token` header is validated against `UADIB_AUTH_TOKEN` environment variable (default: `"changeme"`).

```python
def validate_api_token(token: str | None = Security(API_TOKEN_HEADER)) -> str:
    expected = os.getenv("UADIB_AUTH_TOKEN", "changeme")
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token
```

**Protected Endpoints:** All `/system/*` and `/drone/*` routes except `/system/demo/simulation` and public web pages.

### `security/permission_manager.py` — Command Whitelisting

`PermissionManager` maintains a whitelist of allowed drone commands:

```python
allowed_commands = {
    "takeoff", "land", "set_waypoint", "set_speed",
    "yaw", "move", "hover", "camera_start",
    "camera_stop", "rtl",
}
```

Unauthorized commands raise `PermissionError`, which the API layer translates to HTTP 400.

### HTTP Security Headers

Applied via FastAPI middleware on every response:

| Header | Value |
|---|---|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `no-referrer` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(self)` |
| `Cache-Control` | `no-store` |
| `Content-Security-Policy` | `default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' ws: wss:; frame-ancestors 'none'; object-src 'none'` |

---

## Telemetry Subsystem

### `telemetry/telemetry_stream.py` — Async Streaming

`TelemetryStream` wraps `UADIBRuntime.telemetry()` in an `AsyncIterator` that yields samples at a configurable interval (default: 0.5s).

```python
class TelemetryStream:
    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        while True:
            yield self.runtime.telemetry()
            await asyncio.sleep(self.interval_s)
```

### `telemetry/telemetry_parser.rs` — Rust Parser Crate

A standalone Rust library (`uadib_telemetry_parser`) for high-throughput key-value telemetry parsing:

```rust
pub fn parse_line(line: &str) -> HashMap<String, String>
```

Parses semicolon-delimited `key=value` pairs (e.g., `"alt=12.3;speed=4.2;mode=AUTO"`).

**Build:** `cargo build --release` in `telemetry/` directory. Link as a shared library via PyO3 or cffi for Python integration.

### `telemetry/Cargo.toml`

```toml
[package]
name = "uadib_telemetry_parser"
version = "0.1.0"
edition = "2021"
```

---

## REST API Reference

### System Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Web control UI (HTML) |
| `GET` | `/api` | No | API metadata JSON |
| `GET` | `/health` | No | Health check `{"status": "ok"}` |
| `GET` | `/status` | No | Connection status + loaded plugins |
| `GET` | `/system/device` | No | Immutable device identity + hardware config |
| `POST` | `/system/connect` | **Yes** | Connect drone via source URI |
| `POST` | `/system/connect/details` | **Yes** | Structured connection (protocol/host/port/transport/device/topic) |
| `POST` | `/system/demo/simulation` | No | One-click simulator demo flow |
| `GET` | `/system/plugins` | **Yes** | List loaded plugin names |
| `GET` | `/system/dashboard` | **Yes** | Retrieve generated dashboard widget schema |
| `POST` | `/system/mission/build` | **Yes** | Build + simulate waypoint mission |
| `POST` | `/system/camera/configure` | **Yes** | Configure camera source |
| `GET` | `/system/camera/health` | **Yes** | Camera stream availability |
| `GET` | `/system/camera/frame` | **Yes** | Single JPEG frame |
| `GET` | `/system/camera/stream` | Query token | MJPEG multipart stream |

### Drone Control Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/drone/profile` | **Yes** | Current drone profile |
| `GET` | `/drone/capabilities` | **Yes** | Current capability set |
| `GET` | `/drone/telemetry` | **Yes** | Telemetry snapshot |
| `GET` | `/drone/preflight` | **Yes** | Preflight safety check |
| `POST` | `/drone/takeoff` | **Yes** | Arm + takeoff |
| `POST` | `/drone/land` | **Yes** | Land + disarm |
| `POST` | `/drone/hover` | **Yes** | Stop horizontal movement |
| `POST` | `/drone/rtl` | **Yes** | Return-to-launch |
| `POST` | `/drone/set_speed` | **Yes** | Set cruise speed (m/s) |
| `POST` | `/drone/yaw` | **Yes** | Set heading (degrees) |
| `POST` | `/drone/move` | **Yes** | Relative position delta |
| `POST` | `/drone/set_waypoint` | **Yes** | Navigate to waypoint |
| `POST` | `/drone/camera/start` | **Yes** | Start camera stream |
| `POST` | `/drone/camera/stop` | **Yes** | Stop camera stream |
| `POST` | `/drone/geofence` | **Yes** | Configure geofence boundary |
| `POST` | `/drone/command` | **Yes** | Generic command dispatch |

### Connection Details Request Schema

`POST /system/connect/details` accepts a structured payload:

```json
{
  "protocol": "mavlink",
  "host": "192.168.1.100",
  "port": 14550,
  "transport": "udp",
  "device": null,
  "topic": null,
  "camera_source": "rtsp://192.168.1.100:8554/live"
}
```

The server resolves this into a source URI:
- **MAVLink:** `mavlink://{transport}:{host}:{port}`
- **ROS2:** `ros2://{topic}` or `ros2://{host}`
- **Serial:** `serial://{device}`
- **UDP/TCP:** `{protocol}://{host}:{port}`
- **SDK:** `sdk://{host}[:{port}]`

---

## WebSocket API

### `ws://host:port/ws/telemetry`

Establishes a persistent WebSocket connection for real-time telemetry streaming.

**Message Format:** JSON-encoded telemetry object (same schema as `GET /drone/telemetry`).

**Example Message:**
```json
{
  "connected": true,
  "timestamp": 1711000000.0,
  "altitude_m": 5.23,
  "speed_mps": 3.14,
  "battery_pct": 87.3,
  "gps": {"lat": 37.7749, "lon": -122.4194},
  "armed": true,
  "yaw_deg": 45.0,
  "camera_streaming": true,
  "link": "mavlink",
  "inside_geofence": true,
  "failsafe_recommended": false
}
```

**Lifecycle:**
1. Client connects → server calls `ws.accept()`
2. Server enters `async for sample in telemetry_stream.stream()` loop
3. Each sample is JSON-serialized and sent via `ws.send_text()`
4. On `WebSocketDisconnect`, the handler returns cleanly
5. On unexpected exception, the server attempts `ws.close(code=1011)` if still connected

---

## UARIP Mode

**UARIP** (Universal Autonomous Robotics Intelligence Platform) is an additional mode layered into UADIB without replacing existing drone flows. All routes are namespaced under `/uarip/*`.

### Architecture Layers

1. **User Interface Layer** — Dynamic panel generation based on capability graphs
2. **AI Intelligence Layer** — Protocol reverse-engineering, neural inference
3. **Robotics Abstraction Layer** — Capability graph construction, multi-domain support
4. **Communication Layer** — Protocol inference from raw packet captures
5. **Hardware Interface Layer** — Simulation provider integration

### Supported Domains

Drones, rovers, robotic arms, underwater robots.

### UARIP Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/uarip` | UARIP web UI page |
| `GET` | `/uarip/overview` | Architecture and layer metadata |
| `POST` | `/uarip/protocol/infer` | Protocol schema inference from hex packets |
| `POST` | `/uarip/capability/graph` | Capability graph + dynamic panel generation |
| `POST` | `/uarip/swarm/step` | Multi-agent swarm coordination step |
| `GET` | `/uarip/simulation/providers` | Available simulation engines |
| `POST` | `/uarip/simulation/launch` | Launch simulation metadata |
| `POST` | `/uarip/security/anomaly` | Anomaly scoring and classification |

### Protocol Reverse Engineering

`ProtocolReverseEngineer.infer_schema(packets)` processes raw byte packets through `NeuralProtocolInference`:

1. **Byte-Level Analysis:** Converts packets to uint8 arrays
2. **Boundary Detection:** Identifies delimiter bytes (0x00, 0xFE, 0xFF)
3. **Message Classification:** Assigns message type IDs via statistical or neural inference
4. **Schema Assembly:** Returns message type histogram, field boundaries, and command candidates

**Neural Path (Optional):** Enable with `UARIP_ENABLE_TORCH=1`. Uses a 2-layer Transformer encoder with 128-dim embeddings, 8 attention heads, and 256-token vocabulary. Falls back to statistical inference if PyTorch is unavailable.

### Capability Graph

`CapabilityGraph.from_capabilities(capabilities)` constructs a directed graph:

```
Robot
├── Movement (if navigation=True)
│   ├── Takeoff
│   ├── Land
│   ├── MoveXYZ
│   └── Hover
├── Sensors
│   ├── Camera (if camera_control=True)
│   ├── GPS (if navigation=True)
│   ├── Lidar (if obstacle_avoidance=True)
│   └── Barometer
└── Actuators
    ├── Motor
    ├── Gimbal (if camera_control=True)
    └── Payload (if payload_control=True)
```

Optional NetworkX integration for graph algorithms. Falls back to adjacency dict representation.

### Swarm Coordinator

`SwarmCoordinator.step(agents)` implements Reynolds flocking rules:

- **Alignment:** Steer towards average heading of neighbors within `neighbor_radius` (default: 25.0 units)
- **Cohesion:** Steer towards average position of neighbors
- **Separation:** Steer away from neighbors proportional to inverse distance
- **Goal Seeking:** Steer towards assigned goal position

Velocity update formula:
```
v_new = v + 0.5·align + 0.3·cohesion + 0.7·separation + 0.2·goal
pos_new = pos + v_new · 0.1
```

### Anomaly Monitor

`AnomalyMonitor` computes z-score-based anomaly detection:

```
score = clip(mean(|z_scores|) / 3.0, 0.0, 1.0)
```

Classification thresholds:
- `score >= 0.75` → `"critical"`
- `score >= 0.4` → `"warning"`
- `score < 0.4` → `"normal"`

### Simulation Environment

`SimulationEnvironment` provides metadata for external simulation providers:
- **Gazebo** — ROS-native physics simulation
- **PyBullet** — Python rigid-body dynamics
- **AirSim** — Unreal Engine-based UAV simulation

Returns integration metadata; attach provider runtime separately.

---

## Camera Stream System

### `api/camera_stream.py` — CameraStreamManager

Thread-safe camera stream manager using OpenCV `VideoCapture`:

**Features:**
- **Source Types:** RTSP/HTTP URLs, USB device indices (string digits)
- **Thread Safety:** All operations guarded by `threading.Lock`
- **Lazy Initialization:** Capture opened on first read, reopened if source changes
- **Health Monitoring:** Reports source, open status, resolution (width × height)

**API Methods:**

| Method | Description |
|---|---|
| `configure(source)` | Set camera source; releases previous capture if source changed |
| `health()` | Returns `CameraState(source, opened, width, height)` |
| `read_jpeg()` | Captures frame, encodes as JPEG, returns `bytes` |
| `close()` | Releases capture device |

**MJPEG Streaming:** The `/system/camera/stream` endpoint implements `multipart/x-mixed-replace` with `--frame` boundary, emitting JPEG frames at ~12.5 FPS (80ms interval).

---

## Mission Builder

### Waypoint Optimization

For missions with 3+ waypoints, `MissionBuilder.optimize_path()` applies a centroid-based reordering:

1. Compute centroid of all waypoint coordinates
2. Calculate Euclidean distance from each waypoint to centroid
3. Sort waypoints by ascending distance
4. Return reordered list

This heuristic minimizes total travel distance for clustered waypoint sets.

### Mission Simulation

`MissionBuilder.simulate()` calculates:
- **Total Distance:** Sum of segment distances using flat-Earth approximation (111,111 m/degree)
- **ETA:** `distance / speed_mps` (default speed: 5.0 m/s, minimum: 0.5 m/s)

---

## Safety System

### Preflight Check Flow

`UADIBRuntime.preflight_check()` performs comprehensive pre-flight validation:

```python
{
    "ok": bool,                    # True if all checks pass
    "issues": list[str],           # Blocking failures
    "warnings": list[str],         # Non-blocking warnings
    "telemetry": dict,             # Current telemetry snapshot
    "camera_available": bool,      # Camera hardware present
    "connected_for_s": float       # Connection duration
}
```

**Blocking Issues:**
- No connected drone session
- Telemetry link timeout (>3s since last sample)
- Battery below 20%
- Failsafe recommended by safety system
- Drone outside configured geofence
- GPS telemetry missing (when navigation capability enabled)

**Warnings:**
- Battery between 20–30%
- Camera detected but capability mapping disabled camera control

### Safe Command Execution

`UADIBRuntime.safe_command()` wraps command execution with:
1. **Permission Check:** `PermissionManager.ensure_allowed(command)`
2. **Preflight Gate:** Critical commands (`takeoff`, `land`, `move`, `set_waypoint`, `rtl`) require passing preflight
3. **Retry Logic:** Up to 2 retries with 80ms delay between attempts
4. **Error Propagation:** Final failure raises `RuntimeError` with original exception details

---

## Device Identity

### Identity Generation

```
host_fingerprint = SHA256("hostname::arch::os::mac_address")[:24]
seed = "UADIB::{fingerprint}::{uuid4}"
device_id = "UADIB-" + SHA256(seed)[:16].upper()
```

### Persistence

- **Primary Path:** `~/.uadib/device_identity.json`
- **Override:** `UADIB_DEVICE_ID_FILE` environment variable
- **Fallback Chain:** Home directory → `/tmp/.uadib/` → volatile (process-lifetime)
- **Permissions:** `0o444` (read-only) where filesystem supports it

### Device Configuration

```json
{
  "hostname": "drone-station-01",
  "os": "Darwin",
  "os_version": "24.4.0",
  "architecture": "arm64",
  "python": "3.11.8",
  "cpu_count": 8
}
```

---

## Dashboard Generation

### `ui/dashboard_schema.py` — Python Generator

`generate_dashboard(capabilities)` returns a JSON schema with capability metadata and widget list:

**Base Widgets (Always Present):**
- `flight_hud` — Primary flight display
- `battery_telemetry` — Battery status indicator

**Conditional Widgets:**

| Widget | Condition |
|---|---|
| `map_navigation` | `capabilities.navigation` |
| `camera_view` | `capabilities.camera_control` |
| `mission_planner` | `capabilities.waypoint_navigation` |
| `obstacle_monitor` | `capabilities.obstacle_avoidance` |
| `manual_control` | Always present |

### `ui/dashboard_generator.ts` — TypeScript Generator

Type-safe dashboard generation for frontend integration. Each widget includes grid positioning (`x`, `y`, `w`, `h`) for responsive layout.

### `ui/map_view.ts` — GeoJSON Utilities

`toGeoJSONPath(points)` converts GPS waypoints to GeoJSON `LineString` Feature for map rendering.

---

## Simulator

### `simulator/mock_drone.py` — UDP Telemetry Generator

Standalone script that streams random telemetry packets over UDP:

```bash
python -m simulator.mock_drone --endpoint mavlink://udp:127.0.0.1:14550
```

**Packet Format:**
```json
{
  "altitude_m": 12.34,
  "speed_mps": 5.67,
  "battery_pct": 85.2,
  "ts": 1711000000.0
}
```

**Stream Rate:** 5 Hz (200ms interval). Useful for integration testing without physical hardware.

---

## Frontend Architecture

### `ui/web/index.html` — Main Control Center

Single-page application with sections for:
- **Access** — API token configuration
- **Simulation Demo** — One-click demo flow
- **Real Drone Connect** — Structured connection form with protocol/host/port fields
- **Camera View** — Real drone camera configuration and MJPEG live view
- **Flight Controls** — Preflight, takeoff, land, hover, RTL, speed, yaw
- **Movement + Camera** — Delta movement and camera start/stop
- **Telemetry** — WebSocket live stream and REST snapshot
- **Mission Builder** — 3-waypoint mission planning
- **Safety** — Geofence configuration
- **Generated Dashboard** — Capability-driven widget schema display

### `ui/web/app.js` — Application Logic

Vanilla JavaScript (ES modules) with no framework dependencies. Key functions:
- `requestJson()` — Fetch wrapper with error handling
- `runDemo()` — Triggers `/system/demo/simulation`
- `connectReal()` / `connectRealDetails()` — Real drone connection flows
- `startTelemetry()` / `stopTelemetry()` — WebSocket lifecycle
- `command()` — Generic command dispatcher
- `runPreflight()` — Preflight check execution
- `autoEnableCameraIfAvailable()` — Auto-configure camera on connection

### `ui/web/device_meta.js` — Device Identity Display

Fetches and displays device identity from `/system/device` on page load.

### `ui/web/security_lock.js` — Client-Side Security

Enforces security policies on the client side.

### `ui/web/styles.css` — Styling

Responsive CSS with grid layouts, card-based UI, and security-conscious defaults.

---

## Configuration

### `config.yaml`

```yaml
server:
  host: 0.0.0.0
  port: 8080

security:
  token_env: UADIB_AUTH_TOKEN    # Environment variable for API token

protocols:
  enabled: [mavlink, ros2, sdk, telemetry_stream]

telemetry:
  stream_interval_s: 0.5         # WebSocket stream interval

mission:
  default_speed_mps: 5.0         # Default mission simulation speed
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `UADIB_AUTH_TOKEN` | `changeme` | API authentication token |
| `UADIB_DEVICE_ID_FILE` | `~/.uadib/device_identity.json` | Device identity persistence path |
| `UADIB_PORT` | `8080` | Server port (used by `master_run.sh`) |
| `UADIB_START_SIMULATOR` | `1` | Auto-start mock simulator (`master_run.sh`) |
| `UADIB_SIM_ENDPOINT` | `mavlink://udp:127.0.0.1:14550` | Simulator endpoint |
| `UADIB_MAX_PORT_SCAN` | `20` | Max ports to scan if default is busy |
| `UARIP_ENABLE_TORCH` | `0` | Enable PyTorch-based neural protocol inference |

### `.env.example`

```
UADIB_AUTH_TOKEN=changeme
UADIB_PORT=8080
UADIB_START_SIMULATOR=1
UADIB_SIM_ENDPOINT=mavlink://udp:127.0.0.1:14550
UARIP_ENABLE_TORCH=0
```

---

## Installation & Deployment

### Quick Start (Development)

```bash
cd UADIB
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn api.server:app --reload --port 8080
```

### Master Run Script

```bash
./scripts/master_run.sh
```

This script:
1. Kills any existing UADIB processes
2. Creates/reuses virtual environment
3. Installs all dependencies
4. Starts mock simulator (if `UADIB_START_SIMULATOR=1`)
5. Resolves available port (scans up to `UADIB_MAX_PORT_SCAN` ports)
6. Starts uvicorn with signal handlers for clean shutdown

### Makefile Targets

```bash
make install    # pip install -e .[dev]
make test       # pytest
make run        # uvicorn --reload --port 8080
make lint       # ruff check .
```

### Dependencies

**Core:**
- `fastapi>=0.115` — Async web framework
- `uvicorn[standard]>=0.30` — ASGI server
- `pydantic>=2.8` — Data validation
- `numpy>=2.0` — Numerical computation
- `opencv-python>=4.10` — Camera stream encoding
- `websockets>=12.0` — WebSocket protocol support

**Development:**
- `pytest>=8.2` — Test framework
- `httpx>=0.27` — Async HTTP client for tests
- `ruff>=0.6` — Linter

**Optional:**
- `networkx` — Graph algorithms for capability graphs
- `torch` — Neural protocol inference (set `UARIP_ENABLE_TORCH=1`)

---

## Testing

```bash
cd UADIB
pytest
```

### Test Suite

| Test File | Coverage |
|---|---|
| `test_api.py` | Health check, connect + telemetry flow |
| `test_controls_extended.py` | Speed, yaw, move, camera stop, manual page availability |
| `test_preflight.py` | Preflight check flow with connected drone |
| `test_capability_mapper.py` | Capability inference logic |
| `test_device_identity.py` | Device identity creation and persistence |
| `test_mission_builder.py` | Waypoint optimization and simulation |
| `test_protocol_detector.py` | Protocol detection heuristics |
| `test_uarip.py` | UARIP page, overview, protocol inference, swarm step |
| `test_dashboard.py` | Dashboard schema generation |
| `test_ui_root.py` | Web UI root page serving |
| `test_real_connect_camera.py` | Real connection with camera configuration |

### Test Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

All tests use `FastAPI.TestClient` with the `X-UADIB-Token: changeme` header for authenticated endpoints.

---

## Repository Layout

```
UADIB/
├── main.py                          # Entry point (uvicorn launcher)
├── config.yaml                      # System configuration
├── pyproject.toml                   # Build system + dependencies
├── requirements.txt                 # Pinned dependencies
├── Makefile                         # Build/test/run targets
├── .env.example                     # Environment variable template
├── .gitignore
│
├── core/                            # Core domain logic
│   ├── models.py                    # Domain data models (ProtocolType, DroneProfile, etc.)
│   ├── protocol_detector.py         # Protocol detection heuristics
│   ├── drone_profiler.py            # Hardware profiling
│   ├── capability_mapper.py         # Capability inference (deterministic + AI)
│   ├── mission_builder.py           # Waypoint optimization + simulation
│   ├── safety.py                    # Geofence + failsafe system
│   ├── device_identity.py           # Device ID generation + persistence
│   └── runtime.py                   # UADIBRuntime orchestrator
│
├── protocols/                       # Protocol adapter implementations
│   ├── base.py                      # Abstract DroneAdapter interface
│   ├── mavlink_adapter.py           # MAVLink adapter (PX4-compatible)
│   ├── ros2_adapter.py              # ROS2 adapter
│   ├── sdk_adapter.py               # SDK/REST adapter
│   └── cpp_adapter.cpp              # C++ proprietary protocol skeleton
│
├── ai/                              # AI inference engine
│   ├── capability_classifier.py     # Feature extraction from drone profile
│   └── system_inference_model.py    # Sigmoid scoring model
│
├── plugins/                         # Plugin system
│   ├── base.py                      # Abstract UADIBPlugin interface
│   ├── plugin_manager.py            # Auto-discovery + activation
│   ├── camera_plugin.py             # Camera stream plugin
│   └── lidar_plugin.py              # Obstacle monitor plugin
│
├── security/                        # Security layer
│   ├── authentication.py            # API token validation
│   └── permission_manager.py        # Command whitelisting
│
├── telemetry/                       # Telemetry subsystem
│   ├── telemetry_stream.py          # Async telemetry streaming
│   ├── telemetry_parser.rs          # Rust high-throughput parser
│   └── Cargo.toml                   # Rust crate manifest
│
├── api/                             # FastAPI application
│   ├── server.py                    # Main app, routes, middleware
│   ├── drone_control_endpoints.py   # /drone/* control router
│   ├── uarip_endpoints.py           # /uarip/* UARIP router
│   └── camera_stream.py             # Camera stream manager
│
├── simulator/                       # Simulation
│   └── mock_drone.py                # UDP telemetry generator
│
├── ui/                              # User interface
│   ├── dashboard_schema.py          # Python dashboard generator
│   ├── dashboard_generator.ts       # TypeScript dashboard generator
│   ├── map_view.ts                  # GeoJSON utilities
│   ├── widgets/                     # Widget documentation
│   └── web/                         # Static web assets
│       ├── index.html               # Main control center
│       ├── uarip.html               # UARIP mode page
│       ├── ipr.html                 # IPR page
│       ├── manual.html              # Full manual page
│       ├── app.js                   # Application logic
│       ├── device_meta.js           # Device identity display
│       ├── security_lock.js         # Client-side security
│       └── styles.css               # Styling
│
├── uarip/                           # UARIP mode modules
│   ├── README.md                    # UARIP documentation
│   ├── protocol_ai/                 # Protocol reverse engineering
│   │   ├── neural_protocol_inference.py
│   │   └── protocol_reverse_engine.py
│   ├── robot_graph/                 # Capability graph
│   │   └── capability_graph.py
│   ├── swarm_ai/                    # Swarm coordination
│   │   └── swarm_coordinator.py
│   ├── simulation/                  # Simulation environment
│   │   └── environment.py
│   ├── security/                    # Anomaly detection
│   │   └── anomaly_monitor.py
│   └── ui_generator/                # Dynamic panel generation
│       └── dynamic_panel_generator.py
│
├── scripts/                         # Shell scripts
│   ├── master_run.sh                # Full system launcher
│   └── run_dev.sh                   # Development server
│
└── tests/                           # Test suite
    ├── conftest.py                  # Test configuration
    ├── test_api.py
    ├── test_controls_extended.py
    ├── test_preflight.py
    ├── test_capability_mapper.py
    ├── test_device_identity.py
    ├── test_mission_builder.py
    ├── test_protocol_detector.py
    ├── test_uarip.py
    ├── test_dashboard.py
    ├── test_ui_root.py
    └── test_real_connect_camera.py
```

---

## API Quick Reference

### One-Line Connection

```bash
curl -X POST http://127.0.0.1:8080/system/connect \
  -H 'Content-Type: application/json' \
  -H 'X-UADIB-Token: changeme' \
  -d '{"source":"mavlink://udp:127.0.0.1:14550"}'
```

### Structured Connection

```bash
curl -X POST http://127.0.0.1:8080/system/connect/details \
  -H 'Content-Type: application/json' \
  -H 'X-UADIB-Token: changeme' \
  -d '{"protocol":"mavlink","host":"192.168.1.100","port":14550,"transport":"udp"}'
```

### Takeoff

```bash
curl -X POST http://127.0.0.1:8080/drone/takeoff \
  -H 'Content-Type: application/json' \
  -H 'X-UADIB-Token: changeme' \
  -d '{"payload":{"altitude_m":10.0}}'
```

### WebSocket Telemetry

```javascript
const ws = new WebSocket('ws://127.0.0.1:8080/ws/telemetry');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### UARIP Protocol Inference

```bash
curl -X POST http://127.0.0.1:8080/uarip/protocol/infer \
  -H 'Content-Type: application/json' \
  -d '{"packets_hex":["fe01020304ff","fe01020505ff"]}'
```

---

## Extending UADIB

### Adding a New Protocol Adapter

1. Create `protocols/my_adapter.py`
2. Subclass `DroneAdapter` and implement `fetch_metadata()`, `read_telemetry()`, `send_command()`
3. Add the protocol type to `ProtocolType` enum in `core/models.py`
4. Register in `UADIBRuntime._build_adapter()` in `core/runtime.py`
5. Add detection heuristic to `ProtocolDetector._prefix_map` in `core/protocol_detector.py`

### Adding a New Plugin

1. Create `plugins/my_plugin.py`
2. Subclass `UADIBPlugin` with a unique `name` attribute
3. Implement `supports()` predicate and `activate()` method
4. Plugin is auto-discovered on next runtime initialization

### Replacing the AI Model

1. Subclass or modify `SystemInferenceModel`
2. Load trained weights in `__init__`
3. Implement `predict(features) -> dict[str, float]`
4. Inject into `CapabilityClassifier(model=MyTrainedModel())`

---

## Performance Characteristics

| Operation | Latency | Notes |
|---|---|---|
| Protocol Detection | <1ms | String prefix matching |
| Drone Profiling | ~5ms | Single adapter metadata fetch |
| Capability Mapping | ~2ms | Sigmoid inference over 4 features |
| Dashboard Generation | <1ms | Static widget list construction |
| Telemetry Sample | ~1ms | Per-sample read + geofence check |
| WebSocket Stream | 0.5s interval | Configurable via `config.yaml` |
| Mission Optimization | ~3ms | NumPy centroid sort for 3 waypoints |
| Camera JPEG Encode | ~8ms | OpenCV imencode at 640×480 |
| Preflight Check | ~2ms | Multi-field validation |
| Plugin Autoload | ~1ms | Predicate evaluation per plugin |
