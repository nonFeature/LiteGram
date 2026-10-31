from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge

_PROFILE_ACTIONS_KEYS = (
    Keys.hide_profile_actions_gift_button,
    Keys.hide_profile_actions_stories_button,
    Keys.hide_profile_actions_stream_button,
)


def update_profile_actions_dex_settings(plugin: Any) -> None:
    for key in _PROFILE_ACTIONS_KEYS:
        try:
            dex_bridge.set_flag(key, bool(plugin.get_setting(key, False)))
        except Exception:
            pass


def register_profile_actions(plugin: Any) -> None:
    update_profile_actions_dex_settings(plugin)
