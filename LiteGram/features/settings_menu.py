from hook_utils import find_class, get_private_field, set_private_field
from java import jint
from java.lang.reflect import Modifier

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

"""
EXPLANATION
1. Get list of row field names to hide
2. For each row to hide:
    Set its index to -1
    Decrement all row indices that come after it
3. Update total row count
"""

# from ProfileActivity Class
PROFILE_SETTINGS_ROW_FIELDS = {
    Keys.hide_premium_row: "premiumRow",
    Keys.hide_stars_row: "starsRow",
    Keys.hide_ton_row: "tonRow",
    Keys.hide_business_row: "businessRow",
    Keys.hide_send_a_gift_row: "premiumGiftingRow",
}
PROFILE_HELP_ROW_FIELDS = ["helpHeaderRow", "questionRow", "policyRow"]

# when all rows hidden, there's are invisible "header"
PREMIUM_SECTIONS_ROW = "premiumSectionsRow"
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


class ProfileActivityUpdateRowsIdsHook(BaseHook):
    def get_rows_to_remove(self) -> list[str]:
        rows_to_remove = []

        hidden_premium_rows_count = 0
        for key, row_name in PROFILE_SETTINGS_ROW_FIELDS.items():
            if self.plugin.get_setting(key, False):
                rows_to_remove.append(row_name)
                hidden_premium_rows_count += 1

        # if all is hide -> also remove header
        if hidden_premium_rows_count == len(PROFILE_SETTINGS_ROW_FIELDS):
            rows_to_remove.append(PREMIUM_SECTIONS_ROW)

        if self.plugin.get_setting(Keys.hide_help_section, False):
            rows_to_remove.extend(PROFILE_HELP_ROW_FIELDS)

        return rows_to_remove

    def before_hooked_method(self, param):
        """Remove a bot verification description in Profile by nullify bot_verification field"""
        if not self.plugin.get_setting(Keys.hide_bot_verification, False):
            return

        instance = param.thisObject
        user_info = get_private_field(instance, "userInfo")
        chat_info = get_private_field(instance, "chatInfo")
        if user_info:
            user_info.bot_verification = None
        if chat_info:
            chat_info.bot_verification = None

    def after_hooked_method(self, param):
        rows_to_remove = self.get_rows_to_remove()
        if not rows_to_remove:
            return

        instance = param.thisObject

        row_count = get_private_field(instance, "rowCount")
        if not isinstance(row_count, int):
            return

        # Get all fields in ProfileActivity
        fields = instance.getClass().getDeclaredFields()
        valid_row_fields = []
        for field in fields:
            # only int, with "row" in lowercase name and not statics
            if field.getType().toString() == "int" and "row" in field.getName().lower() and not (field.getModifiers() & Modifier.STATIC):
                field.setAccessible(True)  # since all values is private
                valid_row_fields.append(field)

        rows_removed = 0

        for row_name in rows_to_remove:
            target_index = get_private_field(instance, row_name)  # e.g private int premiumRow
            if target_index is not None and target_index != -1:  # -1 not displayed
                rows_removed += 1
                set_private_field(instance, row_name, jint(-1))  # row will not be displayed, cuz set to 0. Instead, will be displayed versionRow

                for field in valid_row_fields:
                    current_val = field.getInt(instance)

                    if target_index < current_val < row_count:
                        field.setInt(instance, jint(current_val - 1))

                row_count -= 1
        if rows_removed > 0:
            set_private_field(instance, "rowCount", jint(row_count))


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
    ProfileActivityClass = find_class("org.telegram.ui.ProfileActivity")
    if ProfileActivityClass:
        plugin.hook_all_methods(ProfileActivityClass, "updateRowsIds", ProfileActivityUpdateRowsIdsHook(plugin))

    SettingsActivity = find_class("org.telegram.ui.SettingsActivity")
    if SettingsActivity:
        plugin.hook_all_methods(SettingsActivity, "fillItems", SettingsActivityFillItemsHook(plugin))
        plugin.hook_all_methods(SettingsActivity, "onClick", SettingsActivityOnClickHook(plugin))
