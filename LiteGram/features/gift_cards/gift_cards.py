from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def init_gift_cards_dex(plugin: Any) -> None:
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_gift_cards_dex_settings(plugin)


def update_gift_cards_dex_settings(plugin: Any) -> None:
    hide_gifts = bool(plugin.get_setting(Keys.hide_gift_cards, False))
    hide_giveaways = bool(plugin.get_setting(Keys.hide_giveaway_cards, False))
    hide_transfers = bool(plugin.get_setting(Keys.hide_transfer_cards, False))
    dex_bridge.set_flag(Keys.hide_gift_cards, hide_gifts)
    dex_bridge.set_flag(Keys.hide_giveaway_cards, hide_giveaways)
    dex_bridge.set_flag(Keys.hide_transfer_cards, hide_transfers)


def unload_gift_cards_dex() -> None:
    pass


def register_gift_cards(plugin: Any) -> None:
    init_gift_cards_dex(plugin)
