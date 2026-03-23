from __future__ import annotations

from collections import defaultdict

try:
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None


class CapabilityGraph:
    def __init__(self) -> None:
        self._adj: dict[str, set[str]] = defaultdict(set)
        self._nx = nx.DiGraph() if nx is not None else None

    def add_capability(self, name: str) -> None:
        self._adj.setdefault(name, set())
        if self._nx is not None:
            self._nx.add_node(name)

    def link(self, parent: str, child: str) -> None:
        self.add_capability(parent)
        self.add_capability(child)
        self._adj[parent].add(child)
        if self._nx is not None:
            self._nx.add_edge(parent, child)

    def to_dict(self) -> dict[str, list[str]]:
        return {k: sorted(v) for k, v in self._adj.items()}

    @classmethod
    def from_capabilities(cls, capabilities: dict[str, bool]) -> "CapabilityGraph":
        g = cls()
        g.add_capability("Robot")

        movement = ["Takeoff", "Land", "MoveXYZ", "Hover"]
        sensors = ["Camera", "GPS", "Lidar", "Barometer"]
        actuators = ["Motor", "Gimbal", "Payload"]

        if capabilities.get("navigation", False):
            g.link("Robot", "Movement")
            for item in movement:
                g.link("Movement", item)

        g.link("Robot", "Sensors")
        if capabilities.get("camera_control", False):
            g.link("Sensors", "Camera")
        if capabilities.get("navigation", False):
            g.link("Sensors", "GPS")
        if capabilities.get("obstacle_avoidance", False):
            g.link("Sensors", "Lidar")
        g.link("Sensors", "Barometer")

        g.link("Robot", "Actuators")
        g.link("Actuators", "Motor")
        if capabilities.get("camera_control", False):
            g.link("Actuators", "Gimbal")
        if capabilities.get("payload_control", False):
            g.link("Actuators", "Payload")

        return g
