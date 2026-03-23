from __future__ import annotations

import numpy as np

from ai.system_inference_model import SystemInferenceModel
from core.models import DroneProfile


class CapabilityClassifier:
    def __init__(self, model: SystemInferenceModel | None = None) -> None:
        self.model = model or SystemInferenceModel()

    def infer_from_profile(self, profile: DroneProfile) -> dict[str, float]:
        sensors = {s.upper() for s in profile.sensors}
        features = np.array(
            [
                2.0 if profile.camera else -1.2,
                2.5 if "GPS" in sensors else -1.5,
                1.8 if profile.lidar else -1.3,
                0.8 if profile.motors >= 6 else -0.4,
            ],
            dtype=np.float32,
        )
        return self.model.predict(features)
