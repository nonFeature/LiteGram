from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def init_premium_badge_dex(plugin: Any) -> None:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_premium_badge_dex_settings(plugin)


def update_premium_badge_dex_settings(plugin: Any) -> None:
    hide_badge = bool(plugin.get_setting(Keys.hide_premium_badge, False))
    hide_collectible = bool(plugin.get_setting(Keys.hide_collectible_status, False))
    dex_bridge.set_flag(Keys.hide_premium_badge, hide_badge)
    dex_bridge.set_flag(Keys.hide_collectible_status, hide_collectible)


def unload_premium_badge_dex() -> None:
    pass


def register_premium_badge(plugin: Any) -> None:
    init_premium_badge_dex(plugin)
