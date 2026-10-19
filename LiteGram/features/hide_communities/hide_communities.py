from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def init_hide_communities_dex(plugin: Any) -> None:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_hide_communities_dex_settings(plugin)


def update_hide_communities_dex_settings(plugin: Any) -> None:
    val = bool(plugin.get_setting(Keys.hide_communities, False))
    dex_bridge.set_flag(Keys.hide_communities, val)


def unload_hide_communities_dex() -> None:
    pass


def register_hide_communities(plugin: Any) -> None:
    init_hide_communities_dex(plugin)
