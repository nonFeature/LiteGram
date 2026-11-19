from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

MODERN_ROW_TO_KEY = {
    11: Keys.hide_premium_row,
    12: Keys.hide_stars_row,
    13: Keys.hide_wallet_row,
    15: Keys.hide_business_row,
    16: Keys.hide_send_a_gift_row,
    17: Keys.hide_help_section,
    18: Keys.hide_help_section,
    19: Keys.hide_help_section,
    23: Keys.hide_help_section,
    25: Keys.hide_wallet_row,
}
WALLET_BOT_ID = 1985737506

# Structural UItem view types used by SettingsActivity.fillItems:
# 0 = asHeader, 7/8 = asShadow separator, -4 = asCustomShadow anchor
# (wraps topView/versionView and is itself treated as a separator by the
# section renderer), 28 = asSpace search spacer.
VIEW_TYPE_HEADER = 0
VIEW_TYPE_SHADOW = 7
VIEW_TYPE_SHADOW_TEXT = 8
VIEW_TYPE_SPACE = 28
VIEW_TYPE_CUSTOM_SHADOW = -4

_CLASS_HEADER = 0
_CLASS_SEPARATOR = 1
_CLASS_ANCHOR = 2
_CLASS_CONTENT = 3


def get_uitem_id(item):
    if item is None:
        return None
    for field_name in ("id",):
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


def classify_view_type(view_type) -> int:
    if view_type == VIEW_TYPE_HEADER:
        return _CLASS_HEADER
    if view_type in (VIEW_TYPE_SHADOW, VIEW_TYPE_SHADOW_TEXT):
        return _CLASS_SEPARATOR
    if view_type == VIEW_TYPE_CUSTOM_SHADOW:
        return _CLASS_ANCHOR
    return _CLASS_CONTENT


def compute_layout_removals(class_list, dropped) -> set:
    removals = set()
    survivors = [i for i in range(len(class_list)) if i not in dropped]

    # 1. orphaned headers, right-to-left
    has_content_after = False
    for index in reversed(survivors):
        item_class = class_list[index]
        if item_class == _CLASS_CONTENT:
            has_content_after = True
        elif item_class == _CLASS_HEADER:
            if not has_content_after:
                removals.add(index)
            has_content_after = False

    survivors = [i for i in survivors if i not in removals]

    # 2. separator runs
    position = 0
    count = len(survivors)
    while position < count:
        if class_list[survivors[position]] != _CLASS_SEPARATOR:
            position += 1
            continue
        end = position
        while end < count and class_list[survivors[end]] == _CLASS_SEPARATOR:
            end += 1
        prev_class = class_list[survivors[position - 1]] if position > 0 else None
        next_class = class_list[survivors[end]] if end < count else None
        keep_one = prev_class in (_CLASS_HEADER, _CLASS_CONTENT) and next_class in (_CLASS_HEADER, _CLASS_CONTENT)
        for run_index in range(position + (1 if keep_one else 0), end):
            removals.add(survivors[run_index])
        position = end

    return removals


class SettingsActivityFillItemsHook(BaseHook):
    def after_hooked_method(self, param):
        items = param.args[0] if param.args else None
        if items is None:
            return

        try:
            size = items.size()
        except Exception:
            return
        if size <= 1:
            return

        # Search mode fills the list with an asSpace + result cells whose
        # ids are unrelated to settings rows — skip entirely.
        try:
            if get_uitem_view_type(items.get(0)) == VIEW_TYPE_SPACE:
                return
        except Exception:
            return

        class_list = []
        item_ids = []
        wallet_flags = []
        for index in range(size):
            item = items.get(index)
            class_list.append(classify_view_type(get_uitem_view_type(item)))
            item_ids.append(get_uitem_id(item))
            wallet_flags.append(is_wallet_item(item))

        setting_enabled = {key: bool(self.plugin.get_setting(key, False)) for key in set(MODERN_ROW_TO_KEY.values())}
        hide_wallet_row = setting_enabled.get(Keys.hide_wallet_row, False)

        indices_to_remove = set()
        for index in range(size):
            if class_list[index] == _CLASS_ANCHOR:
                continue
            setting_key = MODERN_ROW_TO_KEY.get(item_ids[index])
            if setting_key and setting_enabled.get(setting_key, False):
                indices_to_remove.add(index)
                continue
            if hide_wallet_row and wallet_flags[index]:
                indices_to_remove.add(index)

        if not indices_to_remove:
            return

        indices_to_remove |= compute_layout_removals(class_list, indices_to_remove)

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
        should_block = False
        if setting_key:
            if setting_key == Keys.hide_wallet_row and self.plugin.get_setting(Keys.hide_wallet_row, False):
                should_block = True
            elif self.plugin.get_setting(setting_key, False):
                should_block = True
        if should_block:
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
