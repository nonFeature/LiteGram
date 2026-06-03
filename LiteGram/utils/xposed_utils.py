from base_plugin import MethodHook


class BaseHook(MethodHook):
    def __init__(self, plugin, setting_key: str | None = None):
        self.plugin = plugin
        self.setting_key = setting_key

    def is_enabled(self) -> bool:
        if not self.setting_key:
            return True
        return self.plugin.get_setting(self.setting_key, False)
