import json
from typing import Dict, Optional

class ModuleManager:
    DEFAULT_MODULE_PREFIX = "erispulse.module.data:"
    DEFAULT_STATUS_PREFIX = "erispulse.module.status:"

    def __init__(self):
        from .db import env
        self.env = env
        self._ensure_prefixes()

    def _ensure_prefixes(self):
        if not self.env.get("erispulse.system.module_prefix"):
            self.env.set("erispulse.system.module_prefix", self.DEFAULT_MODULE_PREFIX)
        if not self.env.get("erispulse.system.status_prefix"):
            self.env.set("erispulse.system.status_prefix", self.DEFAULT_STATUS_PREFIX)

    @property
    def module_prefix(self) -> str:
        return self.env.get("erispulse.system.module_prefix")

    @property
    def status_prefix(self) -> str:
        return self.env.get("erispulse.system.status_prefix")

    def set_module_status(self, module_name: str, status: bool) -> None:
        self.env.set(f"{self.status_prefix}{module_name}", bool(status))

    def get_module_status(self, module_name: str) -> bool:
        status = self.env.get(f"{self.status_prefix}{module_name}", True)
        if isinstance(status, str):
            return status.lower() == 'true'
        return bool(status)

    def set_module(self, module_name: str, module_info: dict) -> None:
        self.env.set(f"{self.module_prefix}{module_name}", module_info)
        self.set_module_status(module_name, module_info.get('status', True))

    def get_module(self, module_name: str) -> Optional[dict]:
        return self.env.get(f"{self.module_prefix}{module_name}")

    def set_all_modules(self, modules_info: Dict[str, dict]) -> None:
        for module_name, module_info in modules_info.items():
            self.set_module(module_name, module_info)

    def get_all_modules(self) -> dict:
        modules_info = {}
        all_keys = self.env.get_all_keys()
        prefix_len = len(self.module_prefix)

        for key in all_keys:
            if key.startswith(self.module_prefix):
                module_name = key[prefix_len:]
                module_info = self.get_module(module_name)
                if module_info:
                    status = self.get_module_status(module_name)
                    module_info['status'] = bool(status)
                    modules_info[module_name] = module_info
        return modules_info

    def update_module(self, module_name: str, module_info: dict) -> None:
        self.set_module(module_name, module_info)

    def remove_module(self, module_name: str) -> bool:
        module_key = f"{self.module_prefix}{module_name}"
        status_key = f"{self.status_prefix}{module_name}"

        if self.env.get(module_key) is not None:
            self.env.delete(module_key)
            self.env.delete(status_key)
            return True
        return False

    def update_prefixes(self, module_prefix: str = None, status_prefix: str = None) -> None:
        if module_prefix:
            if not module_prefix.endswith(':'):
                module_prefix += ':'
            self.env.set("erispulse.system.module_prefix", module_prefix)

        if status_prefix:
            if not status_prefix.endswith(':'):
                status_prefix += ':'
            self.env.set("erispulse.system.status_prefix", status_prefix)

mods = ModuleManager()