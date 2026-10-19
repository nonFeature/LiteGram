from typing import Any

from base_plugin import MethodHook


class BaseHook(MethodHook):
    def __init__(self, plugin: Any = None, setting_key: str | None = None):
        super().__init__()
        self.plugin = plugin
        self.setting_key = setting_key

    def is_enabled(self) -> bool:
        if not self.setting_key or not self.plugin:
            return True
        return bool(self.plugin.get_setting(self.setting_key, False))
