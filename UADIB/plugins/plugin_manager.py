from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

from core.models import DroneCapabilities, DroneProfile
from plugins.base import UADIBPlugin


class PluginManager:
    def __init__(self) -> None:
        self.registry: list[UADIBPlugin] = self._discover_plugins()
        self.active: dict[str, dict[str, Any]] = {}

    def autoload(self, profile: DroneProfile, capabilities: DroneCapabilities) -> None:
        self.active.clear()
        for plugin in self.registry:
            if plugin.supports(profile, capabilities):
                self.active[plugin.name] = plugin.activate()

    def loaded_plugin_names(self) -> list[str]:
        return list(self.active.keys())

    @staticmethod
    def _discover_plugins() -> list[UADIBPlugin]:
        discovered: list[UADIBPlugin] = []
        import plugins as plugin_pkg

        for modinfo in pkgutil.iter_modules(plugin_pkg.__path__):
            if modinfo.name in {"base", "plugin_manager"}:
                continue
            module = importlib.import_module(f"plugins.{modinfo.name}")
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls is UADIBPlugin or not issubclass(cls, UADIBPlugin):
                    continue
                discovered.append(cls())
        return discovered
