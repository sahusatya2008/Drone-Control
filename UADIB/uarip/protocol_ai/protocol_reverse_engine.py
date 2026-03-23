from __future__ import annotations

from collections import Counter
from dataclasses import asdict

from uarip.protocol_ai.neural_protocol_inference import NeuralProtocolInference


class ProtocolReverseEngineer:
    def __init__(self) -> None:
        self.npi = NeuralProtocolInference()

    def infer_schema(self, packets: list[bytes]) -> dict[str, object]:
        if not packets:
            return {"message_types": {}, "field_boundaries": [], "commands": []}

        results = [self.npi.infer(packet) for packet in packets]
        type_count = Counter(str(r.message_type) for r in results)

        boundaries = sorted({b for r in results for b in r.boundary_candidates})
        command_candidates = [f"cmd_{k}" for k, _ in type_count.most_common(4)]

        return {
            "message_types": dict(type_count),
            "field_boundaries": boundaries,
            "commands": command_candidates,
            "samples": [asdict(r) for r in results[:3]],
        }
