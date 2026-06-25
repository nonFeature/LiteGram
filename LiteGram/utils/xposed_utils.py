import time

from base_plugin import MethodHook


class BaseHook(MethodHook):
    def __init__(self, plugin, setting_key: str | None = None):
        self.plugin = plugin
        self.setting_key = setting_key
        self._cached_value: bool = False
        self._last_checked = 0.0

    def is_enabled(self) -> bool:
        if not self.setting_key:
            return True
        now = time.time()
        if now - self._last_checked > 2.0:
            self._cached_value = bool(self.plugin.get_setting(self.setting_key, False))
            self._last_checked = now
        return self._cached_value
