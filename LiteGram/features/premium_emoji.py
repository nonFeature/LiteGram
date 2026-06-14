from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

# ============================================================
# Class resolution
# ============================================================

Emoji = find_class("org.telegram.messenger.Emoji")
EmojiView = find_class("org.telegram.ui.Components.EmojiView")
EmojiGridAdapter = find_class("org.telegram.ui.Components.EmojiView$EmojiGridAdapter")
EmojiSearchAdapter = find_class("org.telegram.ui.Components.EmojiView$EmojiSearchAdapter")
SuggestEmojiView = find_class("org.telegram.ui.Components.SuggestEmojiView")
ArrayList = find_class("java.util.ArrayList")
MessageObject = find_class("org.telegram.messenger.MessageObject")
StickerEmojiCell = find_class("org.telegram.ui.Cells.StickerEmojiCell")
ChatActivityEnterView = find_class("org.telegram.ui.Components.ChatActivityEnterView")
MediaDataController = find_class("org.telegram.messenger.MediaDataController")

# ============================================================
# Module state & logging
# ============================================================

_logger = None


def _init(plugin):
    global _logger
    _logger = plugin.log


def _log(msg):
    if _logger:
        try:
            _logger(msg)
        except Exception:
            pass


# ============================================================
# Core checks
# ============================================================


def _is_non_stock(item) -> bool:
    """True if item is a custom (non-stock) emoji.

    Stock emoji = standard Unicode emoji that existed before Telegram Premium.
    Custom emoji = everything else (from emoji packs, stored with document IDs).

    Works for both string entries (recent emoji, search) and TL documents.
    """
    if isinstance(item, str):
        return item.startswith("animated_")
    if MessageObject:
        try:
            return bool(MessageObject.isAnimatedEmoji(item))
        except Exception:
            pass
    return False


def _is_premium_sticker(document) -> bool:
    """True if a sticker document has premium-only animation (video_thumbs type 'f').

    Pure Python — 0 Java calls for normal (free) stickers.
    Falls back to MessageObject.isPremiumSticker only if attr access fails.
    """
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
# Filtering primitives
# ============================================================


def _filter_list(container, *, sub=None, drop_empty=False, drop_non_stock=False, is_sticker=False):
    """Remove premium (and optionally non-stock) items from an ArrayList.

    sub=None           -> items are documents directly
    sub="documents"    -> each item has a .documents sublist
    drop_empty         -> remove items whose sublist becomes empty
    drop_non_stock     -> also remove non-stock custom emoji items
    is_sticker         -> use _is_premium_sticker check (video_thumbs) for leaf docs
    """
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


def _filter_reactions_list(container):
    """Remove custom emoji reactions (any with document_id)."""
    if not container:
        return 0
    removed = 0
    i = container.size() - 1
    while i >= 0:
        if getattr(container.get(i), "document_id", 0) != 0:
            container.remove(i)
            removed += 1
        i -= 1
    return removed


def _is_featured_premium(pack):
    """Check if a StickerSetCovered is a premium pack."""
    if not pack or not MessageObject:
        return False
    try:
        return bool(MessageObject.isPremiumEmojiPack(pack))
    except Exception:
        pass
    for attr in ("documents", "covers"):
        docs = getattr(pack, attr, None)
        if docs:
            for j in range(docs.size()):
                try:
                    if getattr(docs.get(j), "premium", False):
                        return True
                except Exception:
                    pass
    return False


def _is_featured_non_stock(pack):
    """Check if a StickerSetCovered is a custom emoji pack (no stock emoji)."""
    if not pack:
        return False
    sticker_set = getattr(pack, "set", None)
    if sticker_set:
        try:
            return bool(sticker_set.emojis)
        except Exception:
            pass
    return False


def _filter_featured_sets(sets):
    """Remove premium emoji packs AND custom emoji packs from featured sets."""
    if not sets:
        return 0
    removed = 0
    i = sets.size() - 1
    while i >= 0:
        pack = sets.get(i)
        if _is_featured_premium(pack) or _is_featured_non_stock(pack):
            sets.remove(i)
            removed += 1
        i -= 1
    return removed


def _is_premium_sticker_pack(pack):
    """Check if a StickerSetCovered is a premium sticker pack by its cover."""
    if not pack:
        return False
    cover = getattr(pack, "cover", None)
    if cover and _is_premium_sticker(cover):
        return True
    return False


def _filter_featured_sticker_sets(sets):
    """Remove premium packs from featured sticker sets."""
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
# Search-specific filtering
# ============================================================


def _filter_search_results(results):
    """Filter non-stock emoji and premium items from search results."""
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
    """Rebuild search sets keeping header-group structure, dropping non-stock + premium."""
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


# ============================================================
# TL response handlers
# ============================================================

HANDLERS = {
    "TL_messages_getEmojiStickers": lambda r: _filter_list(r.sets, sub="documents", drop_empty=True, drop_non_stock=True),
    "TL_messages_getFeaturedEmojiStickers": lambda r: _filter_featured_sets(r.sets),
    "TL_messages_getFeaturedStickers": lambda r: _filter_featured_sticker_sets(r.sets),
    "TL_messages_searchEmojiStickerSets": lambda r: _filter_list(r.sets, drop_non_stock=True),
    "TL_messages_searchStickers": lambda r: _filter_list(r.stickers, is_sticker=True),
    "TL_messages_getRecentReactions": lambda r: _filter_reactions_list(r.reactions),
    "TL_messages_getRecentStickers": lambda r: _filter_list(r.stickers, is_sticker=True),
    "TL_messages_getStickers": lambda r: _filter_list(getattr(r, "stickers", None), is_sticker=True),
    "TL_messages_getStickerSet": lambda r: _filter_list(getattr(r, "documents", None), is_sticker=True),
}


def filter_response(request_name, response):
    handler = HANDLERS.get(request_name)
    if handler is None:
        return
    try:
        n = handler(response)
        if n:
            _log(f"TL {request_name}: removed {n}")
    except Exception as e:
        _log(f"TL {request_name} error: {e}")


# ============================================================
# UI hooks — recent emoji
# ============================================================


class BlockNonStockHook(BaseHook):
    """Prevent custom emoji from being added to recents."""

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args:
            return
        source = param.args[0]
        if _is_non_stock(source):
            param.setResult(None)


class FilterRecentEmojiHook(BaseHook):
    """Remove custom emoji from recent emoji list."""

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        recent = param.getResult()
        if not recent:
            return
        before = recent.size()
        i = recent.size() - 1
        while i >= 0:
            if _is_non_stock(recent.get(i)):
                recent.remove(i)
            i -= 1
        if recent.size() != before:
            _log(f"recent emoji filtered: {before}->{recent.size()}")


# ============================================================
# UI hooks — search
# ============================================================


class FilterSearchResultsHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 3:
            return
        n1 = param.args[1].size() if param.args[1] else 0
        s1 = param.args[2].size() if param.args[2] else 0
        _filter_search_results(param.args[1])
        _reindex_search_sets(param.args[2])
        n2 = param.args[1].size() if param.args[1] else 0
        s2 = param.args[2].size() if param.args[2] else 0
        if n1 != n2 or s1 != s2:
            _log(f"search filtered: results {n1}->{n2}, sets {s1}->{s2}")


class FilterSuggestResultsHook(BaseHook):
    def __init__(self, plugin, arg_index, label):
        super().__init__(plugin, Keys.hide_premium_emoji)
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
        before = target.size()
        removed = 0
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
                removed += 1
            i -= 1
        if removed:
            _log(f"suggest {self._label} filtered: {before}->{target.size()}")


# ============================================================
# UI hooks — premium stickers
# ============================================================


def _hide_view(view) -> None:
    try:
        view.setVisibility(8)
    except Exception:
        pass
    try:
        lp = view.getLayoutParams()
        if lp:
            lp.height = 0
            lp.width = 0
            view.setLayoutParams(lp)
    except Exception:
        pass


def _restore_view(view) -> None:
    try:
        view.setVisibility(0)
    except Exception:
        pass
    try:
        lp = view.getLayoutParams()
        if lp and getattr(lp, "height", None) == 0:
            lp.height = -2
            lp.width = -2
            view.setLayoutParams(lp)
    except Exception:
        pass


class CheckDocumentsHook(BaseHook):
    """Remove premium stickers from recentStickers and favouriteStickers in EmojiView."""

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        obj = param.thisObject
        for field in ("favouriteStickers", "recentStickers"):
            lst = get_private_field(obj, field)
            if not lst:
                continue
            before = lst.size()
            i = lst.size() - 1
            while i >= 0:
                if _is_premium_sticker(lst.get(i)):
                    lst.remove(i)
                i -= 1
            if lst.size() != before:
                _log(f"EmojiView.{field}: {before}->{lst.size()}")


class HidePremiumStickerCellHook(BaseHook):
    """Hide StickerEmojiCell if document is premium; restore visibility otherwise (recycling fix)."""

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args:
            return
        doc = param.args[0]
        view = param.thisObject
        if _is_premium_sticker(doc):
            _hide_view(view)
            param.setResult(None)
        else:
            _restore_view(view)


# ============================================================
# UI hooks — keyboard performance
# ============================================================


class SkipEmojiPacksHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(None)


class EmptyEmojiPacksHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if ArrayList:
            param.setResult(ArrayList())


class FilterSearchV7Hook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 3:
            return
        _filter_search_results(param.args[1])
        _reindex_search_sets(param.args[2])


class DisableNotificationsLockerHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        locker = get_private_field(param.thisObject, "notificationsLocker")
        if locker:
            locker.disabled = True


class SetAllowAnimatedEmojiFalseHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.thisObject.allowAnimatedEmoji = False


class FilterReactionsListHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        reactions = param.getResult()
        if not reactions:
            return
        i = reactions.size() - 1
        while i >= 0:
            if getattr(reactions.get(i), "document_id", 0) != 0:
                reactions.remove(i)
            i -= 1


class ClearStickerSetsType5Hook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or param.args[0] != 5:
            return
        sets = param.getResult()
        if sets:
            sets.clear()


class ClearFeaturedEmojiSetsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        sets = param.getResult()
        if sets:
            sets.clear()


# ============================================================
# Registration
# ============================================================


def register_premium_emoji(plugin):
    _init(plugin)
    classes = []

    if Emoji:
        plugin.hook_all_methods(Emoji, "addRecentEmoji", BlockNonStockHook(plugin, Keys.hide_premium_emoji))
        classes.append("Emoji")

    if EmojiView:
        plugin.hook_all_methods(EmojiView, "getRecentEmoji", FilterRecentEmojiHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(EmojiView, "checkDocuments", CheckDocumentsHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(EmojiView, "getEmojipacks", EmptyEmojiPacksHook(plugin))
        plugin.hook_all_methods(EmojiView, "<init>", SetAllowAnimatedEmojiFalseHook(plugin))
        classes.append("EmojiView")

    if EmojiGridAdapter:
        plugin.hook_all_methods(EmojiGridAdapter, "processEmoji", SkipEmojiPacksHook(plugin))
        classes.append("EmojiGridAdapter")

    if EmojiSearchAdapter:
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$5", FilterSearchResultsHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$7", FilterSearchV7Hook(plugin))
        classes.append("EmojiSearchAdapter")

    if SuggestEmojiView:
        plugin.hook_all_methods(SuggestEmojiView, "lambda$searchKeywords$3", FilterSuggestResultsHook(plugin, 4, "keywords"))
        plugin.hook_all_methods(SuggestEmojiView, "lambda$searchAnimated$5", FilterSuggestResultsHook(plugin, 2, "animated"))
        classes.append("SuggestEmojiView")

    if StickerEmojiCell:
        plugin.hook_all_methods(StickerEmojiCell, "setSticker", HidePremiumStickerCellHook(plugin, Keys.hide_premium_emoji))
        classes.append("StickerEmojiCell")

    if ChatActivityEnterView:
        plugin.hook_all_methods(ChatActivityEnterView, "<init>", DisableNotificationsLockerHook(plugin))
        classes.append("ChatActivityEnterView")

    if MediaDataController:
        plugin.hook_all_methods(MediaDataController, "getRecentReactions", FilterReactionsListHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getTopReactions", FilterReactionsListHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getSavedReactions", FilterReactionsListHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getStickerSets", ClearStickerSetsType5Hook(plugin))
        plugin.hook_all_methods(MediaDataController, "getFeaturedEmojiSets", ClearFeaturedEmojiSetsHook(plugin))
        classes.append("MediaDataController")

    _log(f"premium_emoji hooks: {', '.join(classes)}")
