from __future__ import annotations

import numpy as np


class AnomalyMonitor:
    def score(self, values: list[float]) -> float:
        if not values:
            return 0.0
        arr = np.array(values, dtype=np.float64)
        z = np.abs((arr - arr.mean()) / (arr.std() + 1e-6))
        return float(np.clip(z.mean() / 3.0, 0.0, 1.0))

    def classify(self, values: list[float]) -> str:
        score = self.score(values)
        if score >= 0.75:
            return "critical"
        if score >= 0.4:
            return "warning"
        return "normal"
