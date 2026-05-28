from hook_utils import find_class
from ui.bulletin import BulletinHelper

from LegacyGram.data.constants import Keys
from LegacyGram.utils.utils import get_client_version, parse_version


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
        client_version = parse_version(get_client_version())

        if function_name == Keys.drawer_options:
            if client_version == (12, 1, 1):
                return "myProfileItem"
            if client_version >= (12, 4, 1):
                return "mainMenuSettings"

    except Exception:
        pass

    return function_name
