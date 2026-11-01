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
    if function_name == Keys.drawer_options:
        return "appNavigationSettings"
    return function_name


def resolve_icon(icon_name: str) -> str:
    if icon_name in ("extera_outline", "etg_settings"):
        return "extera_outline"
    return icon_name
