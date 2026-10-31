from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge

_ACTION_BAR_KEYS = (
    Keys.hide_action_bar_live_stream,
    Keys.hide_action_bar_clear_history,
    Keys.hide_action_bar_report,
    Keys.hide_action_bar_send_gift,
    Keys.hide_action_bar_archived_stories,
    Keys.hide_action_bar_add_shortcut,
    Keys.hide_action_bar_boost_group,
)


def update_action_bar_dex_settings(plugin: Any) -> None:
    for key in _ACTION_BAR_KEYS:
        try:
            dex_bridge.set_flag(key, bool(plugin.get_setting(key, False)))
        except Exception:
            pass


def register_action_bar(plugin: Any) -> None:
    update_action_bar_dex_settings(plugin)
