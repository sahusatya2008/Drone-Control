from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

import cv2


@dataclass(slots=True)
class CameraState:
    source: str
    opened: bool
    width: int
    height: int


class CameraStreamManager:
    def __init__(self) -> None:
        self._source = ""
        self._capture: cv2.VideoCapture | None = None
        self._lock = threading.Lock()

    def configure(self, source: str) -> None:
        with self._lock:
            if source != self._source:
                self._source = source
                self._release_locked()

    def health(self) -> CameraState:
        with self._lock:
            cap = self._ensure_open_locked()
            if cap is None:
                return CameraState(source=self._source, opened=False, width=0, height=0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            return CameraState(source=self._source, opened=cap.isOpened(), width=width, height=height)

    def read_jpeg(self) -> bytes:
        with self._lock:
            cap = self._ensure_open_locked()
            if cap is None or not cap.isOpened():
                raise RuntimeError("Camera stream is not available. Configure a valid camera source.")

            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError("Unable to read frame from camera source")

            ok, encoded = cv2.imencode(".jpg", frame)
            if not ok:
                raise RuntimeError("Unable to encode camera frame")
            return encoded.tobytes()

    def close(self) -> None:
        with self._lock:
            self._release_locked()

    def _ensure_open_locked(self) -> cv2.VideoCapture | None:
        if self._capture is not None and self._capture.isOpened():
            return self._capture

        if not self._source:
            return None

        source: Any = self._source
        if self._source.isdigit():
            source = int(self._source)

        self._capture = cv2.VideoCapture(source)
        if not self._capture.isOpened():
            self._release_locked()
            return None
        return self._capture

    def _release_locked(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
