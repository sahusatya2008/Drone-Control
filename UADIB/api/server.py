from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any
from dataclasses import asdict

from fastapi import Depends, FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException, Query
from pydantic import BaseModel
from starlette.websockets import WebSocketDisconnect, WebSocketState
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import StreamingResponse

from api.camera_stream import CameraStreamManager
from api.drone_control_endpoints import router as drone_router
from api.uarip_endpoints import router as uarip_router
from core.device_identity import DeviceIdentityManager
from core.runtime import UADIBRuntime
from security.authentication import validate_api_token
from telemetry.telemetry_stream import TelemetryStream
from ui.dashboard_schema import generate_dashboard

app = FastAPI(title="UADIB API", version="0.1.0")
runtime = UADIBRuntime()
telemetry_stream = TelemetryStream(runtime)
device_identity = DeviceIdentityManager()
camera_stream = CameraStreamManager()
WEB_DIR = Path(__file__).resolve().parents[1] / "ui" / "web"

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

app.include_router(drone_router)
app.include_router(uarip_router)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'; "
        "object-src 'none'"
    )
    return response


class ConnectRequest(BaseModel):
    source: str


class MissionRequest(BaseModel):
    waypoints: list[dict[str, float]]


class DemoConnectRequest(BaseModel):
    source: str = "mavlink://udp:127.0.0.1:14550"


class ConnectionDetailsRequest(BaseModel):
    protocol: str
    host: str | None = None
    port: int | None = None
    transport: str | None = None
    device: str | None = None
    topic: str | None = None
    camera_source: str | None = None


class CameraConfigRequest(BaseModel):
    source: str


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/uarip")
def uarip_mode() -> FileResponse:
    return FileResponse(WEB_DIR / "uarip.html")


@app.get("/ipr")
def ipr_mode() -> FileResponse:
    return FileResponse(WEB_DIR / "ipr.html")


@app.get("/ipr/")
def ipr_mode_slash() -> FileResponse:
    return FileResponse(WEB_DIR / "ipr.html")


@app.get("/api")
def api_root() -> dict[str, Any]:
    return {
        "name": "UADIB API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/system/device")
def system_device() -> dict[str, Any]:
    identity = device_identity.get_or_create()
    return {
        "device_id": identity.device_id,
        "created_at": identity.created_at,
        "host_fingerprint": identity.host_fingerprint,
        "configuration": device_identity.device_config(),
        "immutable_note": "Device ID is persisted locally and reused across code updates.",
    }


@app.get("/system/device/")
def system_device_slash() -> dict[str, Any]:
    return system_device()


@app.get("/api/system/device")
def system_device_api_alias() -> dict[str, Any]:
    return system_device()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "connected": runtime.adapter is not None,
        "plugins": runtime.plugins.loaded_plugin_names(),
    }


@app.post("/system/connect")
def connect_drone(body: ConnectRequest, _: str = Depends(validate_api_token)) -> dict[str, Any]:
    result = runtime.connect(body.source)
    if runtime.capabilities:
        result["dashboard"] = generate_dashboard(runtime.capabilities)
    result["preflight"] = runtime.preflight_check()
    return result


@app.post("/system/connect/details")
def connect_drone_details(body: ConnectionDetailsRequest, _: str = Depends(validate_api_token)) -> dict[str, Any]:
    source = _build_source_from_details(body)
    result = runtime.connect(source)
    if runtime.capabilities:
        result["dashboard"] = generate_dashboard(runtime.capabilities)
    result["resolved_source"] = source
    result["input_details"] = body.model_dump()
    result["preflight"] = runtime.preflight_check()

    if body.camera_source:
        camera_stream.configure(body.camera_source)
        result["camera"] = asdict(camera_stream.health())
    return result


@app.post("/system/demo/simulation")
def connect_demo_simulation(body: DemoConnectRequest) -> dict[str, Any]:
    result = runtime.connect(body.source)
    if runtime.capabilities:
        result["dashboard"] = generate_dashboard(runtime.capabilities)

    demo_flow = [
        {"step": "connect", "status": "ok", "source": body.source},
        {"step": "takeoff", "result": runtime.command("takeoff", {"altitude_m": 5.0})},
        {"step": "telemetry_sample", "result": runtime.telemetry()},
        {"step": "land", "result": runtime.command("land", {})},
    ]
    result["demo_flow"] = demo_flow
    result["facilities"] = [
        "Automatic protocol detection and adapter selection",
        "Drone profile extraction and capability mapping",
        "Dynamic dashboard widget generation",
        "REST and WebSocket control/telemetry APIs",
        "Plugin auto-loading based on detected features",
        "Mission build/simulation and geofence safety controls",
    ]
    return result


@app.get("/system/plugins")
def list_plugins(_: str = Depends(validate_api_token)) -> dict[str, list[str]]:
    return {"plugins": runtime.plugins.loaded_plugin_names()}


@app.get("/system/dashboard")
def dashboard(_: str = Depends(validate_api_token)) -> dict[str, Any]:
    if not runtime.capabilities:
        return {"widgets": []}
    return generate_dashboard(runtime.capabilities)


@app.post("/system/mission/build")
def build_mission(body: MissionRequest, _: str = Depends(validate_api_token)) -> dict[str, Any]:
    return runtime.build_mission(body.waypoints)


@app.post("/system/camera/configure")
def camera_configure(body: CameraConfigRequest, _: str = Depends(validate_api_token)) -> dict[str, Any]:
    camera_stream.configure(body.source)
    return {"status": "ok", "camera": asdict(camera_stream.health())}


@app.get("/system/camera/health")
def camera_health(_: str = Depends(validate_api_token)) -> dict[str, Any]:
    return {"camera": asdict(camera_stream.health())}


@app.get("/system/camera/frame")
def camera_frame(_: str = Depends(validate_api_token)) -> StreamingResponse:
    try:
        frame = camera_stream.read_jpeg()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return StreamingResponse(iter([frame]), media_type="image/jpeg")


@app.get("/system/camera/stream")
def camera_stream_mjpeg(token: str = Query(default="")) -> StreamingResponse:
    _validate_query_token(token)

    boundary = "frame"

    def generate():
        while True:
            try:
                frame = camera_stream.read_jpeg()
            except RuntimeError:
                break
            yield (
                b"--" + boundary.encode("utf-8") + b"\r\n"
                + b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )
            time.sleep(0.08)

    return StreamingResponse(
        generate(),
        media_type=f"multipart/x-mixed-replace; boundary={boundary}",
    )


@app.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket) -> None:
    await ws.accept()
    try:
        async for sample in telemetry_stream.stream():
            await ws.send_text(json.dumps(sample))
            await asyncio.sleep(0)
    except WebSocketDisconnect:
        # Normal client-side close; no server action needed.
        return
    except Exception:
        # Avoid sending an extra close frame if already closed/disconnected.
        if ws.application_state == WebSocketState.CONNECTED:
            await ws.close(code=1011)


def _build_source_from_details(details: ConnectionDetailsRequest) -> str:
    protocol = details.protocol.lower().strip()
    host = (details.host or "").strip()
    transport = (details.transport or "").strip().lower()
    device = (details.device or "").strip()
    topic = (details.topic or "").strip()
    port = details.port

    if protocol == "serial":
        if not device:
            raise HTTPException(status_code=422, detail="Serial connection requires device path")
        return f"serial://{device}"

    if protocol == "ros2":
        if topic:
            return f"ros2://{topic}"
        if host:
            return f"ros2://{host}"
        raise HTTPException(status_code=422, detail="ROS2 connection requires topic or host")

    if protocol == "mavlink":
        tr = transport or "udp"
        if not host:
            raise HTTPException(status_code=422, detail="MAVLink connection requires host")
        return f"mavlink://{tr}:{host}:{port or 14550}"

    if protocol in {"udp", "tcp"}:
        if not host or port is None:
            raise HTTPException(status_code=422, detail=f"{protocol.upper()} connection requires host and port")
        return f"{protocol}://{host}:{port}"

    if protocol == "sdk":
        if not host:
            raise HTTPException(status_code=422, detail="SDK connection requires host")
        return f"sdk://{host}:{port}" if port else f"sdk://{host}"

    raise HTTPException(status_code=422, detail=f"Unsupported protocol: {details.protocol}")


def _validate_query_token(token: str) -> None:
    expected = os.getenv("UADIB_AUTH_TOKEN", "changeme")
    if token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
