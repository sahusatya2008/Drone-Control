from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Waypoint:
    lat: float
    lon: float
    alt: float


class MissionBuilder:
    """Build, optimize and simulate waypoint missions."""

    def optimize_path(self, waypoints: list[Waypoint]) -> list[Waypoint]:
        if len(waypoints) <= 2:
            return waypoints
        points = np.array([[w.lat, w.lon, w.alt] for w in waypoints], dtype=np.float64)
        centroid = points.mean(axis=0)
        ordering = np.argsort(np.linalg.norm(points - centroid, axis=1))
        return [waypoints[i] for i in ordering]

    def simulate(self, waypoints: list[Waypoint], speed_mps: float = 5.0) -> dict[str, float]:
        if len(waypoints) < 2:
            return {"distance_m": 0.0, "eta_s": 0.0}
        distance = 0.0
        for a, b in zip(waypoints, waypoints[1:]):
            d_lat = (b.lat - a.lat) * 111_111
            d_lon = (b.lon - a.lon) * 111_111
            d_alt = b.alt - a.alt
            distance += float(np.sqrt(d_lat**2 + d_lon**2 + d_alt**2))
        return {"distance_m": round(distance, 2), "eta_s": round(distance / max(speed_mps, 0.5), 2)}
