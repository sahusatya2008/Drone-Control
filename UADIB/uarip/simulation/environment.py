from __future__ import annotations


class SimulationEnvironment:
    PROVIDERS = ["Gazebo", "PyBullet", "AirSim"]

    def available(self) -> list[str]:
        return list(self.PROVIDERS)

    def launch(self, provider: str, scenario: str = "default") -> dict[str, str]:
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")
        return {
            "status": "ready",
            "provider": provider,
            "scenario": scenario,
            "note": "This scaffold returns integration metadata. Attach provider runtime separately.",
        }
