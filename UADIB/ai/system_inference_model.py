from __future__ import annotations

import numpy as np


class SystemInferenceModel:
    """Simple scoring model; replace with a trained model in production."""

    def predict(self, features: np.ndarray) -> dict[str, float]:
        # Sigmoid-like bounded score for each capability channel.
        logits = np.clip(features, -8.0, 8.0)
        probs = 1 / (1 + np.exp(-logits))
        return {
            "camera_available": float(probs[0]),
            "gps_available": float(probs[1]),
            "lidar_available": float(probs[2]),
            "payload_system": float(probs[3]),
        }
