from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

MODERN_ROW_TO_KEY = {
    11: Keys.hide_premium_row,
    12: Keys.hide_stars_row,
    13: Keys.hide_ton_row,
    15: Keys.hide_business_row,
    16: Keys.hide_send_a_gift_row,
    17: Keys.hide_help_section,
    18: Keys.hide_help_section,
    19: Keys.hide_help_section,
    23: Keys.hide_help_section,
}
MODERN_HELP_ROW_IDS = {17, 18, 19, 23}
WALLET_BOT_ID = 1985737506


def get_uitem_id(item):
    if item is None:
        return None
    for field_name in ("id", "f2205id"):
        try:
            value = getattr(item, field_name, None)
            if value is not None:
                return int(value)
        except Exception:
            pass
        try:
            value = get_private_field(item, field_name)
            if value is not None:
                return int(value)
        except Exception:
            pass
    return None


def get_uitem_view_type(item):
    if item is None:
        return None
    for field_name in ("viewType",):
        try:
            value = getattr(item, field_name, None)
            if value is not None:
                return int(value)
        except Exception:
            pass
        try:
            value = get_private_field(item, field_name)
            if value is not None:
                return int(value)
        except Exception:
            pass
    return None


def is_wallet_item(item) -> bool:
    item_id = get_uitem_id(item)
    if item_id == WALLET_BOT_ID:
        return True

    try:
        attached_bot = getattr(item, "object", None)
    except Exception:
        attached_bot = None

    if attached_bot is None:
        try:
            attached_bot = get_private_field(item, "object")
        except Exception:
            attached_bot = None

    return bool(attached_bot and getattr(attached_bot, "bot_id", None) == WALLET_BOT_ID)


class SettingsActivityFillItemsHook(BaseHook):
    def after_hooked_method(self, param):
        items = param.args[0] if param.args else None
        if items is None:
            return

        try:
            size = items.size()
        except Exception:
            return

        hide_help_section = self.plugin.get_setting(Keys.hide_help_section, False)
        hide_wallet_row = self.plugin.get_setting(Keys.hide_wallet_row, False)
        indices_to_remove = set()
        help_row_indices = []

        for index in range(size):
            item = items.get(index)
            item_id = get_uitem_id(item)
            setting_key = MODERN_ROW_TO_KEY.get(item_id)

            if setting_key and self.plugin.get_setting(setting_key, False):
                indices_to_remove.add(index)

            if hide_help_section and item_id in MODERN_HELP_ROW_IDS:
                help_row_indices.append(index)

            if hide_wallet_row and is_wallet_item(item):
                indices_to_remove.add(index)

        if hide_help_section and help_row_indices:
            header_index = min(help_row_indices) - 1
            while header_index >= 0 and get_uitem_view_type(items.get(header_index)) in (0, 7):
                indices_to_remove.add(header_index)
                header_index -= 1

        for index in sorted(indices_to_remove, reverse=True):
            try:
                items.remove(index)
            except Exception:
                pass


class SettingsActivityOnClickHook(BaseHook):
    def before_hooked_method(self, param):
        if not param.args:
            return

        item = param.args[0]
        item_id = get_uitem_id(item)
        setting_key = MODERN_ROW_TO_KEY.get(item_id)
        if setting_key and self.plugin.get_setting(setting_key, False):
            param.setResult(None)
            return

        if self.plugin.get_setting(Keys.hide_wallet_row, False) and is_wallet_item(item):
            param.setResult(None)


def register_settings_menu(plugin) -> None:
    SettingsActivity = find_class("org.telegram.ui.SettingsActivity")
    if SettingsActivity:
        try:
            plugin.hook_all_methods(SettingsActivity, "fillItems", SettingsActivityFillItemsHook(plugin))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(SettingsActivity, "onClick", SettingsActivityOnClickHook(plugin))
        except Exception:
            pass
