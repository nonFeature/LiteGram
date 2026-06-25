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
            search_fields_config = [
                ("emojiSearchField", Keys.hide_emoji_search),
                ("stickersSearchField", Keys.hide_sticker_search),
                ("gifSearchField", Keys.hide_gif_search),
            ]

            for field_name, setting_key in search_fields_config:
                if plugin.get_setting(setting_key, False):
                    sf = get_private_field(self_view, field_name)
                    if sf:
                        categories_list = get_private_field(sf, "categoriesListView")
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
