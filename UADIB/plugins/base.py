from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.models import DroneCapabilities, DroneProfile


class UADIBPlugin(ABC):
    name = "unnamed-plugin"

    @abstractmethod
    def supports(self, profile: DroneProfile, capabilities: DroneCapabilities) -> bool:
        raise NotImplementedError

    @abstractmethod
    def activate(self) -> dict[str, Any]:
        raise NotImplementedError
