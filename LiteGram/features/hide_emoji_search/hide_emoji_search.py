from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def init_hide_emoji_search_dex(plugin: Any) -> None:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_hide_emoji_search_dex_settings(plugin)


def update_hide_emoji_search_dex_settings(plugin: Any) -> None:
    hide = bool(plugin.get_setting(Keys.hide_emoji_search, False))
    dex_bridge.set_flag(Keys.hide_emoji_search, hide)


def unload_hide_emoji_search_dex() -> None:
    pass


def register_hide_emoji_search(plugin: Any) -> None:
    init_hide_emoji_search_dex(plugin)
