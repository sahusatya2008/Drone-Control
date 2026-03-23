from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from uarip.protocol_ai.protocol_reverse_engine import ProtocolReverseEngineer
from uarip.robot_graph.capability_graph import CapabilityGraph
from uarip.security.anomaly_monitor import AnomalyMonitor
from uarip.simulation.environment import SimulationEnvironment
from uarip.swarm_ai.swarm_coordinator import Agent, SwarmCoordinator
from uarip.ui_generator.dynamic_panel_generator import generate_control_panel

router = APIRouter(prefix="/uarip", tags=["uarip"])

rev_engine = ProtocolReverseEngineer()
swarm = SwarmCoordinator()
sim = SimulationEnvironment()
anomaly = AnomalyMonitor()


class PacketSample(BaseModel):
    packets_hex: list[str] = Field(default_factory=list)


class CapabilityInput(BaseModel):
    navigation: bool = True
    camera_control: bool = True
    waypoint_navigation: bool = True
    obstacle_avoidance: bool = False
    payload_control: bool = False


class SwarmAgentInput(BaseModel):
    id: str
    pos: list[float]
    vel: list[float]
    goal: list[float]


class SwarmRequest(BaseModel):
    agents: list[SwarmAgentInput]


class SimLaunchRequest(BaseModel):
    provider: str
    scenario: str = "default"


class AnomalyRequest(BaseModel):
    signal: list[float]


@router.get("/overview")
def overview() -> dict[str, Any]:
    return {
        "name": "UARIP",
        "objective": "Universal Autonomous Robotics Intelligence Platform",
        "layers": [
            "User Interface Layer",
            "AI Intelligence Layer",
            "Robotics Abstraction Layer",
            "Communication Layer",
            "Hardware Interface Layer",
        ],
        "supported_domains": ["drones", "rovers", "robotic_arms", "underwater_robots"],
    }


@router.post("/protocol/infer")
def protocol_infer(body: PacketSample) -> dict[str, Any]:
    packets = []
    for hex_packet in body.packets_hex:
        cleaned = hex_packet.replace(" ", "")
        packets.append(bytes.fromhex(cleaned))
    schema = rev_engine.infer_schema(packets)
    return {"schema": schema}


@router.post("/capability/graph")
def capability_graph(body: CapabilityInput) -> dict[str, Any]:
    graph = CapabilityGraph.from_capabilities(body.model_dump())
    panel = generate_control_panel(graph.to_dict())
    return {"graph": graph.to_dict(), "panel": panel}


@router.post("/swarm/step")
def swarm_step(body: SwarmRequest) -> dict[str, Any]:
    agents = [
        Agent(
            id=a.id,
            pos=np.array(a.pos, dtype=np.float64),
            vel=np.array(a.vel, dtype=np.float64),
            goal=np.array(a.goal, dtype=np.float64),
        )
        for a in body.agents
    ]
    return {"agents": swarm.step(agents)}


@router.get("/simulation/providers")
def sim_providers() -> dict[str, list[str]]:
    return {"providers": sim.available()}


@router.post("/simulation/launch")
def sim_launch(body: SimLaunchRequest) -> dict[str, str]:
    return sim.launch(provider=body.provider, scenario=body.scenario)


@router.post("/security/anomaly")
def security_anomaly(body: AnomalyRequest) -> dict[str, Any]:
    return {
        "score": round(anomaly.score(body.signal), 4),
        "classification": anomaly.classify(body.signal),
    }
