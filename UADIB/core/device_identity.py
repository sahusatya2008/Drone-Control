from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class DeviceIdentity:
    device_id: str
    created_at: str
    host_fingerprint: str


class DeviceIdentityManager:
    def __init__(self, id_file: Path | None = None) -> None:
        env_override = os.getenv("UADIB_DEVICE_ID_FILE")
        if id_file is not None:
            self.id_file = id_file
        elif env_override:
            self.id_file = Path(env_override)
        else:
            self.id_file = Path.home() / ".uadib" / "device_identity.json"
        self._volatile_identity: DeviceIdentity | None = None

    def get_or_create(self) -> DeviceIdentity:
        if self._volatile_identity is not None:
            return self._volatile_identity

        existing = self._read_existing()
        if existing:
            return existing

        self._ensure_parent_dir()
        identity = self._create_identity()
        try:
            self.id_file.write_text(json.dumps(asdict(identity), indent=2), encoding="utf-8")
        except PermissionError:
            # Sandbox-safe fallback path.
            self.id_file = Path("/tmp/.uadib/device_identity.json")
            try:
                self._ensure_parent_dir()
                self.id_file.write_text(json.dumps(asdict(identity), indent=2), encoding="utf-8")
            except PermissionError:
                # Final fallback: runtime-only identity (stable for process lifetime).
                self._volatile_identity = identity
                return identity
        try:
            self.id_file.chmod(0o444)
        except Exception:
            # Non-fatal on filesystems that do not support chmod semantics.
            pass
        return identity

    def device_config(self) -> dict[str, str | int]:
        return {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count() or 1,
        }

    def _read_existing(self) -> DeviceIdentity | None:
        if not self.id_file.exists():
            return None
        try:
            data = json.loads(self.id_file.read_text(encoding="utf-8"))
            return DeviceIdentity(
                device_id=str(data["device_id"]),
                created_at=str(data["created_at"]),
                host_fingerprint=str(data["host_fingerprint"]),
            )
        except Exception:
            return None

    def _ensure_parent_dir(self) -> None:
        try:
            self.id_file.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.id_file = Path("/tmp/.uadib/device_identity.json")
            self.id_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _host_fingerprint() -> str:
        raw = f"{socket.gethostname()}::{platform.machine()}::{platform.system()}::{uuid.getnode()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def _create_identity(self) -> DeviceIdentity:
        fingerprint = self._host_fingerprint()
        seed = f"UADIB::{fingerprint}::{uuid.uuid4()}"
        device_id = "UADIB-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16].upper()
        return DeviceIdentity(
            device_id=device_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            host_fingerprint=fingerprint,
        )
