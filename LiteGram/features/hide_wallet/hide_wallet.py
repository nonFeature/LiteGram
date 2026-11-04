from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def update_hide_wallet_dex_settings(plugin: Any) -> None:
    for key in (
        Keys.hide_profile_balance,
        Keys.hide_profile_send_money,
        Keys.hide_chat_send_money,
        Keys.hide_wallet_row,
    ):
        try:
            val = bool(plugin.get_setting(key, False))
            dex_bridge.set_flag(key, val)
        except Exception:
            pass


def register_hide_wallet(plugin: Any) -> None:
    update_hide_wallet_dex_settings(plugin)
