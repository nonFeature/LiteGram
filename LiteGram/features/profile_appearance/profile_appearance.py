from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge

_PROFILE_APPEARANCE_KEYS = (
    Keys.hide_profile_background_emoji,
    Keys.hide_profile_pinned_gifts,
    Keys.hide_boost_badge,
    Keys.hide_profile_colorful_background,
    Keys.hide_bot_verification,
    Keys.hide_profile_music,
    Keys.hide_profile_business,
    Keys.hide_profile_editor_gifts,
)


def update_profile_appearance_dex_settings(plugin: Any) -> None:
    for key in _PROFILE_APPEARANCE_KEYS:
        try:
            dex_bridge.set_flag(key, bool(plugin.get_setting(key, False)))
        except Exception:
            pass


def register_profile_appearance(plugin: Any) -> None:
    update_profile_appearance_dex_settings(plugin)
