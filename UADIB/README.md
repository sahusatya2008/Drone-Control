# UADIB - Universal Autonomous Drone Interface Builder

UADIB is a modular framework that detects authorized drone links, profiles connected systems, maps capabilities to a unified model, generates a dynamic dashboard definition, and exposes universal control APIs.

## Highlights

- Automatic protocol detection (MAVLink, ROS2, SDK/REST, TCP/UDP streams)
- Drone profiling and capability mapping
- FastAPI REST + WebSocket control/telemetry server
- Plugin-based extension system
- Rust telemetry parser for high-throughput decoding (with Python fallback)
- TypeScript dashboard schema generator
- Example simulator and test suite

## Quick Start

```bash
cd UADIB
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn api.server:app --reload --port 8080
```

Then open:
- Web UI: `http://127.0.0.1:8080/`
- UARIP mode UI: `http://127.0.0.1:8080/uarip`
- IPR page: `http://127.0.0.1:8080/ipr`
- Full manual page: `http://127.0.0.1:8080/static/manual.html`
- API docs: `http://127.0.0.1:8080/docs`
- WebSocket telemetry: `ws://127.0.0.1:8080/ws/telemetry`

Use token header for protected endpoints:

```text
X-UADIB-Token: changeme
```

## API Overview

- `GET /` UADIB web control UI
- `GET /api` API metadata JSON
- `GET /system/device` immutable per-device identity + device configuration
- `POST /system/connect` detect protocol + profile + map capabilities + generate dashboard
- `POST /system/connect/details` structured real-connection input (protocol/host/port/transport/device/topic)
- `POST /system/demo/simulation` one-click simulator demo flow (connect/takeoff/telemetry/land)
- `GET /system/dashboard` retrieve generated widget schema
- `POST /system/mission/build` optimize and simulate waypoint mission
- `POST /system/camera/configure` configure real camera source (RTSP/HTTP/USB index)
- `GET /system/camera/health` camera stream availability
- `GET /system/camera/stream?token=...` live MJPEG camera stream
- `POST /drone/takeoff`, `POST /drone/land`, `POST /drone/hover`, `POST /drone/rtl`
- `POST /drone/set_speed`, `POST /drone/yaw`, `POST /drone/move`
- `POST /drone/camera/start`, `POST /drone/camera/stop`
- `POST /drone/geofence` configure geofence safety boundary
- `GET /drone/telemetry` and `ws://.../ws/telemetry` for real-time updates

## UARIP Mode (Separate from UADIB Main Mode)

UARIP is added as an additional mode and does not replace or alter existing UADIB flows.

- `GET /uarip` dedicated UARIP page mode
- `GET /uarip/overview` architecture/layer overview
- `POST /uarip/protocol/infer` protocol reverse-engineering schema inference
- `POST /uarip/capability/graph` capability graph + dynamic panel generation
- `POST /uarip/swarm/step` swarm coordination AI step
- `GET /uarip/simulation/providers` simulation engines list
- `POST /uarip/simulation/launch` simulation launch metadata
- `POST /uarip/security/anomaly` anomaly score/classification

## Example Workflow

```bash
python -m simulator.mock_drone --endpoint mavlink://udp:127.0.0.1:14550
curl -X POST http://127.0.0.1:8080/system/connect -H 'content-type: application/json' -d '{"source":"mavlink://udp:127.0.0.1:14550"}'
```

## Frontend/Telemetry Components

- TypeScript dashboard generator: `ui/dashboard_generator.ts`
- Rust parser crate: `telemetry/Cargo.toml` + `telemetry/telemetry_parser.rs`
- Optional C++ protocol adapter skeleton: `protocols/cpp_adapter.cpp`

## Testing

```bash
cd UADIB
pytest
```

## Repository Layout

See the source tree in this repository. Core modules live under `core/`, protocol adapters in `protocols/`, and API in `api/`.
