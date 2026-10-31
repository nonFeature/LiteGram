from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge

_MEDIA_LAYOUT_KEYS = (
    Keys.hide_gifts_tab,
    Keys.hide_stories_tab,
)


def update_media_layout_dex_settings(plugin: Any) -> None:
    for key in _MEDIA_LAYOUT_KEYS:
        try:
            dex_bridge.set_flag(key, bool(plugin.get_setting(key, False)))
        except Exception:
            pass


def register_media_layout(plugin: Any) -> None:
    update_media_layout_dex_settings(plugin)
