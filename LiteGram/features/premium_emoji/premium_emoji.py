from hook_utils import find_class, get_private_field

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
EmojiSearchAdapterRunnable = safe_find_class("org.telegram.ui.Components.EmojiView$EmojiSearchAdapter$5")
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


def _filter_search_results(results):
    if not results:
        return 0
    removed = 0
    i = results.size() - 1
    while i >= 0:
        r = results.get(i)
        emoji = getattr(r, "emoji", None)
        if emoji is None:
            try:
                emoji = str(r)
            except Exception:
                i -= 1
                continue
        if _is_non_stock(emoji):
            results.remove(i)
            removed += 1
            i -= 1
            continue
        try:
            if getattr(r, "premium", False):
                results.remove(i)
                removed += 1
        except Exception:
            pass
        i -= 1
    return removed


def _reindex_search_sets(sets):
    if not sets or not ArrayList:
        return
    rebuilt = ArrayList()
    buffer = ArrayList()
    dirty = False
    for i in range(sets.size()):
        item = sets.get(i)
        if item and getattr(item, "title", None) is not None:
            if buffer.size() > 0:
                rebuilt.add(item)
                for d in range(buffer.size()):
                    rebuilt.add(buffer.get(d))
            buffer = ArrayList()
            continue
        if _is_non_stock(item):
            dirty = True
        else:
            buffer.add(item)
    for d in range(buffer.size()):
        rebuilt.add(buffer.get(d))
    if dirty:
        sets.clear()
        sets.addAll(rebuilt)


def _filter_search_packs(packs_list):
    if not packs_list:
        return 0
    removed = 0
    i = packs_list.size() - 1
    while i >= 0:
        pack_info = packs_list.get(i)
        docs = getattr(pack_info, "documents", None)
        if docs:
            _filter_list(docs, drop_non_stock=True)
            if docs.size() == 0:
                packs_list.remove(i)
                removed += 1
        else:
            packs_list.remove(i)
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


class FilterSearchResultsHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 3:
            return
        _filter_search_results(param.args[1])
        _reindex_search_sets(param.args[2])


class FilterSearchV7Hook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_search)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 3:
            return
        _filter_search_results(param.args[1])
        _reindex_search_sets(param.args[2])


class FilterSearchV12_8_1Hook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 5:
            return

        runnable_instance = param.thisObject
        search_adapter = getattr(runnable_instance, "this$0", None)
        if search_adapter:
            result_pre = get_private_field(search_adapter, "resultPre")
            if result_pre:
                _filter_search_results(result_pre)

        _filter_search_results(param.args[1])
        _filter_search_packs(param.args[2])
        _filter_search_packs(param.args[3])


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
            plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$5", FilterSearchResultsHook(plugin, Keys.hide_premium_search))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$7", FilterSearchV7Hook(plugin))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$3", BlockGlobalSearchHook(plugin, Keys.hide_premium_search))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(EmojiSearchAdapter, "searchEmoji", BlockGlobalSearchHook(plugin, Keys.hide_premium_search))
        except Exception:
            pass

    if EmojiSearchAdapterRunnable:
        try:
            plugin.hook_all_methods(EmojiSearchAdapterRunnable, "lambda$run$7", FilterSearchV12_8_1Hook(plugin, Keys.hide_premium_search))
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
