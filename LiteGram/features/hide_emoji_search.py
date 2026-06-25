from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

# ============================================================
# Class resolution
# ============================================================

EmojiView = find_class("org.telegram.ui.Components.EmojiView")


# ============================================================
# Hooks
# ============================================================


class EmojiViewInitHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin)

    def after_hooked_method(self, param):
        self_view = param.thisObject
        plugin = self.plugin

        try:
            # 1. Emoji search categories (quick reactions / recent emojis)
            if plugin.get_setting(Keys.hide_emoji_search, False):
                emoji_sf = get_private_field(self_view, "emojiSearchField")
                if emoji_sf:
                    categories_list = get_private_field(emoji_sf, "categoriesListView")
                    if categories_list:
                        categories_list.setVisibility(8)  # GONE

            # 2. Sticker search categories
            if plugin.get_setting(Keys.hide_sticker_search, False):
                sticker_sf = get_private_field(self_view, "stickersSearchField")
                if sticker_sf:
                    categories_list = get_private_field(sticker_sf, "categoriesListView")
                    if categories_list:
                        categories_list.setVisibility(8)  # GONE

            # 3. GIF search categories
            if plugin.get_setting(Keys.hide_gif_search, False):
                gif_sf = get_private_field(self_view, "gifSearchField")
                if gif_sf:
                    categories_list = get_private_field(gif_sf, "categoriesListView")
                    if categories_list:
                        categories_list.setVisibility(8)  # GONE
        except Exception:
            pass


# ============================================================
# Registration
# ============================================================


def register_hide_emoji_search(plugin):
    if EmojiView:
        try:
            plugin.hook_all_constructors(EmojiView, EmojiViewInitHook(plugin))
        except Exception:
            pass
