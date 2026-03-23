from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DroneAdapter(ABC):
    def __init__(self, source: str) -> None:
        self.source = source

    @abstractmethod
    def fetch_metadata(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def read_telemetry(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def send_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
