from hook_utils import find_class, get_private_field

from LegacyGram.data.constants import Keys
from LegacyGram.utils.xposed_utils import BaseHook

# ============================================================
# Class resolution
# ============================================================

AnimatedEmojiDrawable = find_class("org.telegram.ui.Components.AnimatedEmojiDrawable")
Emoji = find_class("org.telegram.messenger.Emoji")
EmojiView = find_class("org.telegram.ui.Components.EmojiView")
EmojiGridAdapter = find_class("org.telegram.ui.Components.EmojiView$EmojiGridAdapter")
EmojiSearchAdapter = find_class("org.telegram.ui.Components.EmojiView$EmojiSearchAdapter")
SuggestEmojiView = find_class("org.telegram.ui.Components.SuggestEmojiView")
ArrayList = find_class("java.util.ArrayList")
MediaDataController = find_class("org.telegram.messenger.MediaDataController")
MessageObject = find_class("org.telegram.messenger.MessageObject")
ReactionsContainerLayout = find_class("org.telegram.ui.Components.ReactionsContainerLayout")
UserConfig = find_class("org.telegram.messenger.UserConfig")

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


def _is_premium(document) -> bool:
    """True if a document is premium (sticker/emoji locked behind subscription).

    Optimized: uses `premium` attr directly when available (stickers),
    only falls back to Java `isFreeEmoji` for emoji documents.
    """
    if document is None:
        return False
    try:
        prem = getattr(document, "premium", None)
        if prem is not None:
            return bool(prem)
    except Exception:
        pass
    if not _is_non_stock(document):
        return False
    if MessageObject:
        try:
            return not MessageObject.isFreeEmoji(document)
        except Exception:
            pass
    return False


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


def _current_account(account=None) -> int:
    if account is not None:
        return account
    if UserConfig:
        try:
            return int(UserConfig.selectedAccount)
        except Exception:
            pass
    return 0


# ============================================================
# Filtering primitives
# ============================================================


def _filter_list(container, *, sub=None, drop_empty=False, drop_non_stock=False):
    """Remove premium (and optionally non-stock) items from an ArrayList.

    sub=None           -> items are documents directly
    sub="documents"    -> each item has a .documents sublist
    drop_empty         -> remove items whose sublist becomes empty
    drop_non_stock     -> also remove non-stock custom emoji items
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
                # Emoji-пак: все документы — custom эмодзи → без проверок удаляем пак
                if drop_non_stock and getattr(getattr(item, "set", None), "emojis", False):
                    container.remove(i)
                    removed += 1
                    i -= 1
                    continue
                # Стикер-пак: только проверка premium
                j = docs.size() - 1
                while j >= 0:
                    if _is_premium(docs.get(j)):
                        docs.remove(j)
                        removed += 1
                    j -= 1
                if drop_empty and docs.size() == 0:
                    container.remove(i)
                    removed += 1
        else:
            obj = container.get(i)
            if _is_premium(obj) or (drop_non_stock and _is_non_stock(obj)):
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
    if cover and _is_premium(cover):
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


def _count_packs(packs):
    if not packs:
        return 0, 0
    total = 0
    for i in range(packs.size()):
        p = packs.get(i)
        if hasattr(p, "documents"):
            total += p.documents.size()
    return packs.size(), total


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
    changed = False
    for i in range(sets.size()):
        item = sets.get(i)
        if item and getattr(item, "title", None) is not None:
            continue
        if _is_premium(item) or _is_non_stock(item):
            changed = True
    if not changed:
        return
    rebuilt = ArrayList()
    buffer = ArrayList()
    for i in range(sets.size()):
        item = sets.get(i)
        if item and getattr(item, "title", None) is not None:
            if buffer.size() > 0:
                rebuilt.add(item)
                for d in range(buffer.size()):
                    rebuilt.add(buffer.get(d))
            buffer = ArrayList()
            continue
        if not _is_premium(item) and not _is_non_stock(item):
            buffer.add(item)
    for d in range(buffer.size()):
        rebuilt.add(buffer.get(d))
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
    "TL_messages_searchStickers": lambda r: _filter_list(r.documents),
    "TL_messages_getRecentReactions": lambda r: _filter_reactions_list(r.reactions),
    "TL_messages_getRecentStickers": lambda r: _filter_list(r.stickers),
    "TL_messages_getStickers": lambda r: _filter_list(getattr(r, "stickers", None)),
    "TL_messages_getStickerSet": lambda r: _filter_list(getattr(r, "documents", None)),
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
# UI hooks — pack lists
# ============================================================


class FilterStickerSetsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        sets = param.getResult()
        if not sets:
            return
        before = _count_packs(sets)
        _filter_list(sets, sub="documents", drop_empty=True, drop_non_stock=True)
        after = _count_packs(sets)
        if before != after:
            _log(f"sticker sets filtered: {before[0]}p/{before[1]}d -> {after[0]}p/{after[1]}d")


class FilterFeaturedSetsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        sets = param.getResult()
        if not sets:
            return
        before = sets.size()
        result = ArrayList() if ArrayList else sets
        changed = False
        for idx in range(sets.size()):
            pack = sets.get(idx)
            if _is_featured_premium(pack) or _is_featured_non_stock(pack):
                changed = True
                continue
            result.add(pack)
        if changed:
            param.setResult(result)
            _log(f"featured sets filtered: {before}->{result.size()}")


class FilterFeaturedStickerSetsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        sets = param.getResult()
        if not sets:
            return
        before = sets.size()
        n = _filter_featured_sticker_sets(sets)
        if n:
            _log(f"featured sticker sets filtered: {before}->{sets.size()}")


_last_frozen_size = 0


class FilterFrozenPacksHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        packs = get_private_field(param.thisObject, "frozenEmojiPacks")
        if not packs:
            return
        rebuild = param.args and len(param.args) > 0 and bool(param.args[0])
        global _last_frozen_size
        if not rebuild and packs.size() == _last_frozen_size:
            return
        before = _count_packs(packs)
        _filter_list(packs, sub="documents", drop_empty=True, drop_non_stock=True)
        after = _count_packs(packs)
        _last_frozen_size = packs.size()
        if before != after:
            _log(f"frozen packs filtered: {before[0]}p/{before[1]}d -> {after[0]}p/{after[1]}d")


# ============================================================
# UI hooks — recent stickers
# ============================================================


class FilterRecentStickersHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        stickers = param.getResult()
        if not stickers:
            return
        before = stickers.size()
        n = _filter_list(stickers)
        if n:
            _log(f"recent stickers filtered: {before}->{stickers.size()} ({n} premium)")


# ============================================================
# UI hooks — reactions
# ============================================================


class FilterReactionsListHook(BaseHook):
    def __init__(self, plugin, label):
        super().__init__(plugin, Keys.hide_premium_emoji)
        self._label = label

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        reactions = param.getResult()
        if not reactions:
            return
        before = reactions.size()
        n = _filter_reactions_list(reactions)
        if n:
            _log(f"reactions ({self._label}) filtered: {before}->{reactions.size()}")


class FilterVisibleReactionsHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 1:
            return
        if get_private_field(param.thisObject, "channelReactions"):
            return
        visible = param.args[0]
        if not visible:
            return
        before = visible.size()
        removed = 0
        i = visible.size() - 1
        while i >= 0:
            if getattr(visible.get(i), "documentId", 0) != 0:
                visible.remove(i)
                removed += 1
            i -= 1
        if removed:
            _log(f"reactions panel filtered: {before}->{visible.size()} ({removed} custom)")


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
        classes.append("EmojiView")

    if EmojiSearchAdapter:
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$5", FilterSearchResultsHook(plugin, Keys.hide_premium_emoji))
        classes.append("EmojiSearchAdapter")

    if SuggestEmojiView:
        plugin.hook_all_methods(SuggestEmojiView, "lambda$searchKeywords$3", FilterSuggestResultsHook(plugin, 4, "keywords"))
        plugin.hook_all_methods(SuggestEmojiView, "lambda$searchAnimated$5", FilterSuggestResultsHook(plugin, 2, "animated"))
        classes.append("SuggestEmojiView")

    if MediaDataController:
        plugin.hook_all_methods(MediaDataController, "getStickerSets", FilterStickerSetsHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(MediaDataController, "getFeaturedEmojiSets", FilterFeaturedSetsHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(MediaDataController, "getFeaturedStickerSets", FilterFeaturedStickerSetsHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(MediaDataController, "getRecentStickers", FilterRecentStickersHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(MediaDataController, "getRecentReactions", FilterReactionsListHook(plugin, "recent"))
        plugin.hook_all_methods(MediaDataController, "getTopReactions", FilterReactionsListHook(plugin, "top"))
        plugin.hook_all_methods(MediaDataController, "getSavedReactions", FilterReactionsListHook(plugin, "saved"))
        classes.append("MediaDataController")

    if EmojiGridAdapter:
        plugin.hook_all_methods(EmojiGridAdapter, "processEmoji", FilterFrozenPacksHook(plugin, Keys.hide_premium_emoji))
        classes.append("EmojiGridAdapter")

    if ReactionsContainerLayout:
        plugin.hook_all_methods(ReactionsContainerLayout, "setVisibleReactionsList", FilterVisibleReactionsHook(plugin, Keys.hide_premium_emoji))
        classes.append("ReactionsContainerLayout")

    _log(f"premium_emoji hooks: {', '.join(classes)}")
