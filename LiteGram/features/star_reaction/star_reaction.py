from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def init_star_reaction_dex(plugin: Any) -> None:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_star_reaction_dex_settings(plugin)


def update_star_reaction_dex_settings(plugin: Any) -> None:
    hide_star = bool(plugin.get_setting(Keys.hide_star_reaction, False))
    dex_bridge.set_flag(Keys.hide_star_reaction, hide_star)


def unload_star_reaction_dex() -> None:
    pass


def register_star_reaction(plugin: Any) -> None:
    init_star_reaction_dex(plugin)
