from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.runtime import UADIBRuntime
from security.authentication import validate_api_token
from security.permission_manager import PermissionManager

router = APIRouter(prefix="/drone", tags=["drone"])
permission_manager = PermissionManager()


class CommandPayload(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class WaypointRequest(BaseModel):
    lat: float
    lon: float
    alt: float


class GeofenceRequest(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


class SpeedRequest(BaseModel):
    speed_mps: float


class YawRequest(BaseModel):
    yaw_deg: float


class MoveRequest(BaseModel):
    delta_lat: float = 0.0
    delta_lon: float = 0.0
    delta_alt: float = 0.0


class GenericCommandRequest(BaseModel):
    command: str
    payload: dict[str, Any] = Field(default_factory=dict)


def get_runtime() -> UADIBRuntime:
    from api.server import runtime

    return runtime


def _run_command(rt: UADIBRuntime, command: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        permission_manager.ensure_allowed(command)
        critical = command in {"takeoff", "land", "move", "set_waypoint", "rtl"}
        return rt.safe_command(command, payload, retries=3, require_preflight=critical)
    except (PermissionError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/profile")
def get_profile(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    if not rt.profile:
        raise HTTPException(status_code=400, detail="No connected drone")
    return asdict(rt.profile)


@router.get("/capabilities")
def get_capabilities(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    if not rt.capabilities:
        raise HTTPException(status_code=400, detail="No connected drone")
    return asdict(rt.capabilities)


@router.get("/telemetry")
def get_telemetry(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return rt.telemetry()


@router.post("/takeoff")
def takeoff(body: CommandPayload, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "takeoff", body.payload)


@router.post("/land")
def land(body: CommandPayload, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "land", body.payload)


@router.post("/set_waypoint")
def set_waypoint(body: WaypointRequest, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "set_waypoint", body.model_dump())


@router.post("/camera/start")
def camera_start(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "camera_start", {})


@router.post("/camera/stop")
def camera_stop(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "camera_stop", {})


@router.post("/set_speed")
def set_speed(body: SpeedRequest, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "set_speed", body.model_dump())


@router.post("/yaw")
def set_yaw(body: YawRequest, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "yaw", body.model_dump())


@router.post("/move")
def move(body: MoveRequest, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "move", body.model_dump())


@router.post("/hover")
def hover(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "hover", {})


@router.post("/rtl")
def rtl(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, "rtl", {})


@router.post("/geofence")
def set_geofence(body: GeofenceRequest, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, float]:
    return rt.configure_geofence(
        min_lat=body.min_lat,
        max_lat=body.max_lat,
        min_lon=body.min_lon,
        max_lon=body.max_lon,
    )


@router.post("/command")
def command(body: GenericCommandRequest, _: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return _run_command(rt, body.command, body.payload)


@router.get("/preflight")
def preflight(_: str = Depends(validate_api_token), rt: UADIBRuntime = Depends(get_runtime)) -> dict[str, Any]:
    return rt.preflight_check()
