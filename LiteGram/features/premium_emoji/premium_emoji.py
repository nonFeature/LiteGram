from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.main import LiteGramPlugin
from LiteGram.utils.dex_utils import dex_bridge
from LiteGram.utils.xposed_utils import BaseHook


def safe_find_class(class_name):
    try:
        return find_class(class_name)
    except Exception:
        return None


# ============================================================
# Class resolution
# ============================================================

EmojiSearchAdapter = safe_find_class("org.telegram.ui.Components.EmojiView$EmojiSearchAdapter")
SuggestEmojiView = safe_find_class("org.telegram.ui.Components.SuggestEmojiView")
ArrayList = safe_find_class("java.util.ArrayList")
MessageObject = safe_find_class("org.telegram.messenger.MessageObject")

# ============================================================
# Core checks
# ============================================================


def _is_non_stock(item) -> bool:
    if isinstance(item, str):
        return item.startswith("animated_")
    if MessageObject:
        try:
            return bool(MessageObject.isAnimatedEmoji(item))
        except Exception:
            pass
    return False


def _is_premium_sticker(document) -> bool:
    if document is None:
        return False
    try:
        vthumbs = getattr(document, "video_thumbs", None)
        if vthumbs:
            for j in range(vthumbs.size()):
                try:
                    if getattr(vthumbs.get(j), "type", None) == "f":
                        return True
                except Exception:
                    pass
        return False
    except Exception:
        pass
    if MessageObject:
        try:
            return bool(MessageObject.isPremiumSticker(document))
        except Exception:
            pass
    return False


# ============================================================
# Filtering primitives for TL responses and search
# ============================================================


def _filter_list(container, *, sub=None, drop_empty=False, drop_non_stock=False, is_sticker=False):
    if not container or not ArrayList:
        return 0
    removed = 0
    i = container.size() - 1
    while i >= 0:
        item = container.get(i)
        if sub:
            docs = getattr(item, sub, None)
            if docs is not None:
                _set = getattr(item, "set", None)
                is_emoji_pack = drop_non_stock and _set and getattr(_set, "emojis", False)
                if is_emoji_pack:
                    container.remove(i)
                    removed += 1
                    i -= 1
                    continue
                j = docs.size() - 1
                while j >= 0:
                    doc = docs.get(j)
                    if is_sticker:
                        if _is_premium_sticker(doc):
                            docs.remove(j)
                            removed += 1
                    else:
                        prem = getattr(doc, "premium", None)
                        if prem is not None and bool(prem):
                            docs.remove(j)
                            removed += 1
                    j -= 1
                if drop_empty and docs.size() == 0:
                    container.remove(i)
                    removed += 1
        else:
            obj = container.get(i)
            if drop_non_stock and _is_non_stock(obj):
                container.remove(i)
                removed += 1
            elif is_sticker:
                if _is_premium_sticker(obj):
                    container.remove(i)
                    removed += 1
            elif not drop_non_stock:
                prem = getattr(obj, "premium", None)
                if prem is not None and bool(prem):
                    container.remove(i)
                    removed += 1
        i -= 1
    return removed


def _is_premium_sticker_pack(pack):
    if not pack:
        return False
    cover = getattr(pack, "cover", None)
    return bool(cover and _is_premium_sticker(cover))


def _filter_featured_sticker_sets(sets):
    if not sets:
        return 0
    removed = 0
    i = sets.size() - 1
    while i >= 0:
        if _is_premium_sticker_pack(sets.get(i)):
            sets.remove(i)
            removed += 1
        i -= 1
    return removed


# ============================================================
# TL response handlers
# ============================================================

HANDLERS = {
    "TL_messages_getFeaturedStickers": lambda r, p: (
        _filter_featured_sticker_sets(getattr(r, "sets", None)) if p.get_setting(Keys.hide_premium_stickers_grid, False) else None
    ),
    "TL_messages_searchStickers": lambda r, p: (
        _filter_list(getattr(r, "stickers", None), is_sticker=True) if p.get_setting(Keys.hide_premium_stickers_search, False) else None
    ),
    "TL_messages_getRecentStickers": lambda r, p: (
        _filter_list(getattr(r, "stickers", None), is_sticker=True) if p.get_setting(Keys.hide_premium_stickers_recent, False) else None
    ),
    "TL_messages_getStickers": lambda r, p: (
        _filter_list(getattr(r, "stickers", None), is_sticker=True) if p.get_setting(Keys.hide_premium_stickers_search, False) else None
    ),
    "TL_messages_getStickerSet": lambda r, p: (
        _filter_list(getattr(r, "documents", None), is_sticker=True) if p.get_setting(Keys.hide_premium_stickers_search, False) else None
    ),
}


def filter_response(request_name, response):
    handler = HANDLERS.get(request_name)
    if handler is None:
        return
    try:
        plugin = LiteGramPlugin.get_instance()
        handler(response, plugin)
    except Exception:
        pass


# ============================================================
# Search hooks
# ============================================================


class BlockGlobalSearchHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args:
            return
        method_name = param.method.getName()
        if method_name == "searchEmoji":
            runnable = param.args[0]
        else:
            runnable = param.args[-1]
        if runnable:
            runnable.run()
        param.setResult(None)


class FilterSuggestResultsHook(BaseHook):
    def __init__(self, plugin, arg_index, label):
        super().__init__(plugin, Keys.hide_premium_suggestions)
        self._arg_index = arg_index
        self._label = label

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) <= self._arg_index:
            return
        target = param.args[self._arg_index]
        if not target:
            return
        i = target.size() - 1
        while i >= 0:
            item = target.get(i)
            emoji = getattr(item, "emoji", None)
            if emoji is None:
                try:
                    emoji = str(item)
                except Exception:
                    i -= 1
                    continue
            if _is_non_stock(emoji):
                target.remove(i)
            i -= 1


# ============================================================
# DEX Management
# ============================================================

_premium_emoji_dex = None


def init_premium_emoji_dex(plugin):
    if not dex_bridge.is_loaded():
        dex_bridge.load(plugin)
    update_premium_emoji_dex_settings(plugin)


def update_premium_emoji_dex_settings(plugin):
    for key in (
        Keys.hide_premium_emoji_keyboard,
        Keys.hide_premium_stickers_recent,
        Keys.hide_premium_stickers_grid,
        Keys.hide_premium_emoji_reactions,
        Keys.hide_group_stickers,
    ):
        val = bool(plugin.get_setting(key, False))
        dex_bridge.set_flag(key, val)


def unload_premium_emoji_dex():
    pass


# ============================================================
# Registration
# ============================================================


def register_premium_emoji(plugin):
    init_premium_emoji_dex(plugin)

    if EmojiSearchAdapter:
        try:
            plugin.hook_all_methods(EmojiSearchAdapter, "searchEmoji", BlockGlobalSearchHook(plugin, Keys.hide_premium_search))
        except Exception:
            pass

    if SuggestEmojiView:
        try:
            plugin.hook_all_methods(SuggestEmojiView, "lambda$searchKeywords$3", FilterSuggestResultsHook(plugin, 4, "keywords"))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(SuggestEmojiView, "lambda$searchAnimated$5", FilterSuggestResultsHook(plugin, 2, "animated"))
        except Exception:
            pass
