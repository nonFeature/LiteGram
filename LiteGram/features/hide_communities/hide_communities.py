from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def init_hide_communities_dex(plugin: Any) -> None:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_hide_communities_dex_settings(plugin)


def update_hide_communities_dex_settings(plugin: Any) -> None:
    mode = int(plugin.get_setting(Keys.hide_communities, 0) or 0)
    dex_bridge.set_flag(Keys.hide_communities_badges, mode in (1, 2))
    dex_bridge.set_flag(Keys.hide_communities_profile, mode in (1, 3))


def unload_hide_communities_dex() -> None:
    pass


def register_hide_communities(plugin: Any) -> None:
    init_hide_communities_dex(plugin)
