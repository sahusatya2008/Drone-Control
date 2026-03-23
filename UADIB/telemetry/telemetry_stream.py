from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from core.runtime import UADIBRuntime


class TelemetryStream:
    def __init__(self, runtime: UADIBRuntime, interval_s: float = 0.5) -> None:
        self.runtime = runtime
        self.interval_s = interval_s

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        while True:
            yield self.runtime.telemetry()
            await asyncio.sleep(self.interval_s)
