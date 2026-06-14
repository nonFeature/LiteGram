from hook_utils import find_class
from ui.bulletin import BulletinHelper

from LiteGram.data.constants import Keys
from LiteGram.utils.utils import get_client_version, parse_version

_cached_parsed_version = None


def _parsed_version():
    global _cached_parsed_version
    if _cached_parsed_version is None:
        _cached_parsed_version = parse_version(get_client_version())
    return _cached_parsed_version


# thx jadx
def open_extera_setting(alias: str, plugin_id: str | None = None) -> None:
    try:
        SettingsRegistry = find_class("com.exteragram.messenger.preferences.utils.SettingsRegistry")

        if not SettingsRegistry:
            return

        alias = resolve_extera_function(alias)
        registry_instance = SettingsRegistry.getInstance()
        registry_instance.handleLink(alias, plugin_id)
    except Exception as e:
        BulletinHelper.show_error(f"Failed to open extera setting: {e}")


def resolve_extera_function(function_name: str) -> str:
    try:
        v = _parsed_version()
        if function_name == Keys.drawer_options:
            if v >= (12, 4, 1):
                return "appNavigationSettings"
            return "myProfileItem"
    except Exception:
        pass
    return function_name


def resolve_icon(icon_name: str) -> str:
    try:
        v = _parsed_version()
        if icon_name == "extera_outline" and v < (12, 4, 1):
            return "etg_settings"
        if icon_name == "etg_settings" and v >= (12, 4, 1):
            return "extera_outline"
    except Exception:
        pass
    return icon_name
