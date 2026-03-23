from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Agent:
    id: str
    pos: np.ndarray
    vel: np.ndarray
    goal: np.ndarray


class SwarmCoordinator:
    def __init__(self, neighbor_radius: float = 25.0) -> None:
        self.neighbor_radius = neighbor_radius

    def step(self, agents: list[Agent]) -> list[dict[str, object]]:
        if not agents:
            return []

        out: list[dict[str, object]] = []
        for agent in agents:
            neighbors = [n for n in agents if n.id != agent.id and np.linalg.norm(agent.pos - n.pos) <= self.neighbor_radius]
            if not neighbors:
                new_vel = agent.vel + 0.1 * (agent.goal - agent.pos)
            else:
                vel_stack = np.array([n.vel for n in neighbors], dtype=np.float64)
                pos_stack = np.array([n.pos for n in neighbors], dtype=np.float64)

                align = vel_stack.mean(axis=0) - agent.vel
                cohesion = pos_stack.mean(axis=0) - agent.pos
                sep_terms = []
                for n in neighbors:
                    dist = np.linalg.norm(agent.pos - n.pos)
                    if dist > 1e-6:
                        sep_terms.append((agent.pos - n.pos) / dist)
                separation = np.sum(sep_terms, axis=0) if sep_terms else np.zeros(3)
                goal = agent.goal - agent.pos

                new_vel = agent.vel + 0.5 * align + 0.3 * cohesion + 0.7 * separation + 0.2 * goal

            new_pos = agent.pos + new_vel * 0.1
            out.append({
                "id": agent.id,
                "pos": new_pos.round(4).tolist(),
                "vel": new_vel.round(4).tolist(),
            })
        return out
