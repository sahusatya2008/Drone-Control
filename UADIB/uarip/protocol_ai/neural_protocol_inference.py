from __future__ import annotations

from dataclasses import dataclass
import os

import numpy as np

@dataclass(slots=True)
class InferenceResult:
    message_type: int
    confidence: float
    boundary_candidates: list[int]


class NeuralProtocolInference:
    """Lightweight NPI facade.

    Torch path is disabled by default for runtime safety.
    Enable with UARIP_ENABLE_TORCH=1 in environments with validated torch install.
    """

    def __init__(self) -> None:
        self._torch_enabled = os.getenv("UARIP_ENABLE_TORCH", "0") == "1"
        self.model = None
        self.torch = None
        if self._torch_enabled:
            self._try_init_torch_model()

    def _try_init_torch_model(self) -> None:
        try:
            import torch
            import torch.nn as nn
        except Exception:  # pragma: no cover
            self._torch_enabled = False
            return

        class ProtocolTransformer(nn.Module):
            def __init__(self, vocab: int = 256, d: int = 128) -> None:
                super().__init__()
                self.embed = nn.Embedding(vocab, d)
                encoder_layer = nn.TransformerEncoderLayer(d_model=d, nhead=8)
                self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
                self.classifier = nn.Linear(d, 32)

            def forward(self, packet):
                x = self.embed(packet)
                x = self.encoder(x)
                return self.classifier(x.mean(0))

        self.torch = torch
        self.model = ProtocolTransformer()

    def infer(self, packet: bytes) -> InferenceResult:
        if not packet:
            return InferenceResult(message_type=0, confidence=0.0, boundary_candidates=[])

        arr = np.frombuffer(packet, dtype=np.uint8)
        boundaries = [i for i in range(1, len(arr)) if arr[i] in {0x00, 0xFE, 0xFF}]

        if self.model is not None and self.torch is not None:
            with self.torch.no_grad():
                tensor = self.torch.tensor(arr, dtype=self.torch.long).unsqueeze(1)
                logits = self.model(tensor).mean(0)
                probs = self.torch.softmax(logits, dim=0)
                message_type = int(self.torch.argmax(probs).item())
                confidence = float(self.torch.max(probs).item())
        else:
            message_type = int(arr.mean() % 8)
            confidence = float(min(0.95, 0.4 + (arr.std() / 255.0)))

        return InferenceResult(
            message_type=message_type,
            confidence=round(confidence, 4),
            boundary_candidates=boundaries[:16],
        )
