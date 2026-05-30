from hook_utils import find_class, get_private_field

from LegacyGram.data.constants import Keys
from LegacyGram.utils.xposed_utils import BaseHook

AnimatedEmojiDrawable = find_class("org.telegram.ui.Components.AnimatedEmojiDrawable")
Emoji = find_class("org.telegram.messenger.Emoji")
EmojiView = find_class("org.telegram.ui.Components.EmojiView")
EmojiGridAdapter = find_class("org.telegram.ui.Components.EmojiView$EmojiGridAdapter")
EmojiSearchAdapter = find_class("org.telegram.ui.Components.EmojiView$EmojiSearchAdapter")
SuggestEmojiView = find_class("org.telegram.ui.Components.SuggestEmojiView")
ArrayList = find_class("java.util.ArrayList")
MediaDataController = find_class("org.telegram.messenger.MediaDataController")
MessageObject = find_class("org.telegram.messenger.MessageObject")
UserConfig = find_class("org.telegram.messenger.UserConfig")

_plugin = None


def _log(msg: str) -> None:
    global _plugin
    if _plugin is not None:
        try:
            _plugin.log(msg)
        except Exception:
            pass


def _is_keep_document(document) -> bool:
    if document is None:
        return False
    try:
        prem = bool(getattr(document, "premium", False))
        if prem:
            return False
    except Exception:
        pass
    if MessageObject:
        try:
            return bool(MessageObject.isFreeEmoji(document))
        except Exception:
            pass
    return True


# ========== TL API handlers ==========


def _filter_documents_in_place(documents) -> bool:
    if not documents or not ArrayList:
        return False
    changed = False
    try:
        keep = []
        for idx in range(documents.size()):
            doc = documents.get(idx)
            if _is_keep_document(doc):
                keep.append(doc)
            else:
                changed = True
        if changed:
            documents.clear()
            for doc in keep:
                documents.add(doc)
    except Exception:
        return False
    return changed


def _is_premium_featured_pack(sticker_set_covered) -> bool:
    if not sticker_set_covered or not MessageObject:
        return False
    try:
        return bool(MessageObject.isPremiumEmojiPack(sticker_set_covered))
    except Exception:
        pass
    documents = getattr(sticker_set_covered, "documents", None)
    if documents is None:
        documents = getattr(sticker_set_covered, "covers", None)
    if not documents:
        return False
    for idx in range(documents.size()):
        doc = documents.get(idx)
        try:
            if bool(getattr(doc, "premium", False)):
                return True
        except Exception:
            pass
    return False


def _filter_packs_in_response(response) -> None:
    if not hasattr(response, "sets"):
        return
    idx = response.sets.size() - 1
    while idx >= 0:
        pack = response.sets.get(idx)
        if hasattr(pack, "documents"):
            _filter_documents_in_place(pack.documents)
        removed = False
        if hasattr(pack, "documents") and pack.documents.size() == 0:
            response.sets.remove(idx)
            removed = True
        if not removed:
            idx -= 1


def _filter_featured_packs(response) -> None:
    if not hasattr(response, "sets"):
        return
    idx = response.sets.size() - 1
    while idx >= 0:
        pack = response.sets.get(idx)
        if _is_premium_featured_pack(pack):
            response.sets.remove(idx)
        idx -= 1


def _filter_search_packs(response) -> None:
    if hasattr(response, "sets"):
        idx = response.sets.size() - 1
        while idx >= 0:
            item = response.sets.get(idx)
            if hasattr(item, "title") and item.title:
                idx -= 1
                continue
            if not _is_keep_document(item):
                response.sets.remove(idx)
            idx -= 1


def _filter_documents_response(response) -> None:
    if hasattr(response, "documents"):
        idx = response.documents.size() - 1
        while idx >= 0:
            doc = response.documents.get(idx)
            if not _is_keep_document(doc):
                response.documents.remove(idx)
            idx -= 1


def _filter_pack_list_in_place(packs) -> bool:
    if not packs or not ArrayList:
        return False
    changed = False
    idx = packs.size() - 1
    while idx >= 0:
        pack = packs.get(idx)
        if hasattr(pack, "documents"):
            if _filter_documents_in_place(pack.documents):
                changed = True
        if hasattr(pack, "documents") and pack.documents.size() == 0:
            packs.remove(idx)
            changed = True
        idx -= 1
    return changed


def _filter_reactions_response(response) -> None:
    if not hasattr(response, "reactions"):
        return
    account = _resolve_current_account(None)
    if account is None or not AnimatedEmojiDrawable:
        return
    removed = 0
    idx = response.reactions.size() - 1
    while idx >= 0:
        reaction = response.reactions.get(idx)
        document_id = getattr(reaction, "document_id", None)
        if document_id is not None:
            try:
                document = AnimatedEmojiDrawable.findDocument(account, document_id)
                if document and not _is_keep_document(document):
                    response.reactions.remove(idx)
                    removed += 1
                    idx -= 1
                    continue
            except Exception:
                pass
        idx -= 1
    if removed:
        _log(f"reactions filtered: removed {removed} premium")


HANDLERS = {
    "TL_messages_getEmojiStickers": _filter_packs_in_response,
    "TL_messages_getFeaturedEmojiStickers": _filter_featured_packs,
    "TL_messages_searchEmojiStickerSets": _filter_search_packs,
    "TL_messages_searchStickers": _filter_documents_response,
    "TL_messages_getRecentReactions": _filter_reactions_response,
}


def filter_response(request_name: str, response) -> None:
    handler = HANDLERS.get(request_name)
    if handler is not None:
        _log(f"TL handler: {request_name}")
        try:
            handler(response)
        except Exception as e:
            _log(f"TL handler error: {request_name} {e}")


# ========== Lightweight Java hooks (search + recent) ==========


def _resolve_current_account(current_account: int | None) -> int | None:
    if current_account is not None:
        return current_account
    if UserConfig:
        try:
            return int(UserConfig.selectedAccount)
        except Exception:
            return None
    return None


def _animated_emoji_document_id(emoji_source) -> int | None:
    if not isinstance(emoji_source, str) or not emoji_source.startswith("animated_"):
        return None
    try:
        return int(emoji_source.removeprefix("animated_"))
    except ValueError:
        return None


def _is_premium_animated_emoji(emoji_source, current_account: int | None) -> bool:
    document_id = _animated_emoji_document_id(emoji_source)
    if document_id is None:
        return False
    account = _resolve_current_account(current_account)
    if account is None or not AnimatedEmojiDrawable:
        return False
    try:
        document = AnimatedEmojiDrawable.findDocument(account, document_id)
    except Exception:
        return False
    if not document:
        return False
    return not _is_keep_document(document)


def _filter_animated_emoji_string_list_in_place(emoji_list, current_account: int | None) -> bool:
    if not emoji_list:
        return False
    changed = False
    for idx in range(emoji_list.size() - 1, -1, -1):
        emoji = emoji_list.get(idx)
        if _is_premium_animated_emoji(emoji, current_account):
            emoji_list.remove(idx)
            changed = True
    return changed


def _filter_keyword_results_in_place(keyword_results, current_account: int | None) -> bool:
    if not keyword_results:
        return False
    changed = False
    for idx in range(keyword_results.size() - 1, -1, -1):
        result = keyword_results.get(idx)
        emoji = getattr(result, "emoji", None)
        if emoji is None:
            try:
                emoji = str(result)
            except Exception:
                continue
        if _is_premium_animated_emoji(emoji, current_account):
            keyword_results.remove(idx)
            changed = True
    return changed


def _filter_recent_emoji(recent_emoji, current_account: int | None) -> None:
    current_account = _resolve_current_account(current_account)
    if not recent_emoji:
        return
    _filter_animated_emoji_string_list_in_place(recent_emoji, current_account)


def _filter_search_results(search_results, current_account: int | None) -> None:
    current_account = _resolve_current_account(current_account)
    if not search_results:
        return
    for idx in range(search_results.size() - 1, -1, -1):
        result = search_results.get(idx)
        emoji = getattr(result, "emoji", None)
        if emoji is None:
            try:
                emoji = str(result)
            except Exception:
                continue
        if _is_premium_animated_emoji(emoji, current_account):
            search_results.remove(idx)
            continue
        try:
            if bool(getattr(result, "premium", False)):
                search_results.remove(idx)
        except Exception:
            pass


def _filter_search_sets_in_place(search_sets) -> None:
    if not search_sets or not ArrayList:
        return
    changed = False
    for idx in range(search_sets.size()):
        item = search_sets.get(idx)
        if bool(item) and getattr(item, "title", None) is not None:
            continue
        if not _is_keep_document(item):
            changed = True
    if not changed:
        return
    rebuild = ArrayList()
    current_docs = ArrayList()
    for idx in range(search_sets.size()):
        item = search_sets.get(idx)
        if bool(item) and getattr(item, "title", None) is not None:
            if current_docs.size() > 0:
                rebuild.add(item)
                for di in range(current_docs.size()):
                    rebuild.add(current_docs.get(di))
            current_docs = ArrayList()
            continue
        if _is_keep_document(item):
            current_docs.add(item)
    if current_docs.size() > 0:
        for di in range(current_docs.size()):
            rebuild.add(current_docs.get(di))
    search_sets.clear()
    search_sets.addAll(rebuild)


# ========== Hook classes ==========


class EmojiSearchAdapterSearchResultsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 3:
            return
        emoji_view = get_private_field(param.thisObject, "this$0")
        current_account = get_private_field(emoji_view, "currentAccount") if emoji_view else None
        before_n = param.args[1].size() if param.args[1] else 0
        before_s = param.args[2].size() if param.args[2] else 0
        _filter_search_results(param.args[1], current_account)
        _filter_search_sets_in_place(param.args[2])
        after_n = param.args[1].size() if param.args[1] else 0
        after_s = param.args[2].size() if param.args[2] else 0
        if before_n != after_n or before_s != after_s:
            _log(f"search filtered: results {before_n}->{after_n}, sets {before_s}->{after_s}")


class SuggestEmojiViewSearchKeywordsResultsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 5:
            return
        target = param.args[4]
        before = target.size() if target else 0
        _filter_keyword_results_in_place(target, get_private_field(param.thisObject, "currentAccount"))
        after = target.size() if target else 0
        if before != after:
            _log(f"keywords filtered: {before}->{after}")


class SuggestEmojiViewSearchAnimatedResultsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 3:
            return
        target = param.args[2]
        before = target.size() if target else 0
        _filter_keyword_results_in_place(target, get_private_field(param.thisObject, "currentAccount"))
        after = target.size() if target else 0
        if before != after:
            _log(f"animated keywords filtered: {before}->{after}")


class EmojiAddRecentEmojiHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args:
            return
        emoji_source = param.args[0]
        if not _is_premium_animated_emoji(emoji_source, None):
            return
        _log(f"blocked premium addRecentEmoji: {emoji_source}")
        param.setResult(None)


class EmojiViewGetRecentEmojiHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        recent_emoji = param.getResult()
        if not recent_emoji:
            return
        current_account = get_private_field(param.thisObject, "currentAccount")
        before = recent_emoji.size()
        _filter_recent_emoji(recent_emoji, current_account)
        after = recent_emoji.size()
        if before != after:
            _log(f"recent emoji filtered: {before}->{after}")


# ========== Pack filtering Java hooks ==========


def _count_packs(packs) -> tuple[int, int]:
    if not packs:
        return 0, 0
    total_docs = 0
    for i in range(packs.size()):
        pack = packs.get(i)
        if hasattr(pack, "documents"):
            total_docs += pack.documents.size()
    return packs.size(), total_docs


class MediaDataControllerGetStickerSetsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        sticker_sets = param.getResult()
        if not sticker_sets:
            return
        packs_before, docs_before = _count_packs(sticker_sets)
        _filter_pack_list_in_place(sticker_sets)
        packs_after, docs_after = _count_packs(sticker_sets)
        if packs_before != packs_after or docs_before != docs_after:
            _log(f"packs filtered: {packs_before}p/{docs_before}d -> {packs_after}p/{docs_after}d")


class MediaDataControllerGetFeaturedEmojiSetsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        featured_sets = param.getResult()
        if not featured_sets:
            return
        before = featured_sets.size()
        filtered = ArrayList() if ArrayList else featured_sets
        changed = False
        for index in range(featured_sets.size()):
            pack = featured_sets.get(index)
            if _is_premium_featured_pack(pack):
                changed = True
                continue
            filtered.add(pack)
        after = filtered.size()
        if changed:
            param.setResult(filtered)
            _log(f"featured packs filtered: {before}->{after}")


class EmojiGridAdapterProcessEmojiHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        frozen_emoji_packs = get_private_field(param.thisObject, "frozenEmojiPacks")
        if not frozen_emoji_packs:
            return
        packs_before, docs_before = _count_packs(frozen_emoji_packs)
        _filter_pack_list_in_place(frozen_emoji_packs)
        packs_after, docs_after = _count_packs(frozen_emoji_packs)
        if packs_before != packs_after or docs_before != docs_after:
            _log(f"frozen packs filtered: {packs_before}p/{docs_before}d -> {packs_after}p/{docs_after}d")


class MediaDataControllerGetRecentReactionsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_premium_emoji)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        reactions = param.getResult()
        if not reactions:
            return
        account = _resolve_current_account(None)
        if account is None or not AnimatedEmojiDrawable:
            return
        before = reactions.size()
        removed = 0
        idx = reactions.size() - 1
        while idx >= 0:
            reaction = reactions.get(idx)
            document_id = getattr(reaction, "document_id", None)
            if document_id is not None:
                try:
                    document = AnimatedEmojiDrawable.findDocument(account, document_id)
                    if document and not _is_keep_document(document):
                        reactions.remove(idx)
                        removed += 1
                except Exception:
                    pass
            idx -= 1
        if removed:
            _log(f"reactions recent filtered: {before}->{reactions.size()} ({removed} premium)")


def _scrub_cached_data():
    try:
        account = _resolve_current_account(None)
        if account is None or not MediaDataController:
            return
        controller = MediaDataController.getInstance(account)
    except Exception:
        return

    for pack_type in range(8):
        try:
            controller.getStickerSets(pack_type)
        except Exception:
            pass

    try:
        controller.getFeaturedEmojiSets()
    except Exception:
        pass

    try:
        controller.getRecentReactions()
    except Exception:
        pass

    _log("scrub: done")


def register_premium_emoji(plugin) -> None:
    global _plugin
    _plugin = plugin

    found = []
    if Emoji:
        plugin.hook_all_methods(Emoji, "addRecentEmoji", EmojiAddRecentEmojiHook(plugin))
        found.append("Emoji")

    if EmojiView:
        plugin.hook_all_methods(EmojiView, "getRecentEmoji", EmojiViewGetRecentEmojiHook(plugin))
        found.append("EmojiView")

    if EmojiSearchAdapter:
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$5", EmojiSearchAdapterSearchResultsHook(plugin))
        found.append("EmojiSearchAdapter")

    if SuggestEmojiView:
        plugin.hook_all_methods(
            SuggestEmojiView,
            "lambda$searchKeywords$3",
            SuggestEmojiViewSearchKeywordsResultsHook(plugin),
        )
        plugin.hook_all_methods(
            SuggestEmojiView,
            "lambda$searchAnimated$5",
            SuggestEmojiViewSearchAnimatedResultsHook(plugin),
        )
        found.append("SuggestEmojiView")

    if MediaDataController:
        plugin.hook_all_methods(MediaDataController, "getStickerSets", MediaDataControllerGetStickerSetsHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getFeaturedEmojiSets", MediaDataControllerGetFeaturedEmojiSetsHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getRecentReactions", MediaDataControllerGetRecentReactionsHook(plugin))
        found.append("MediaDataController")

    if EmojiGridAdapter:
        plugin.hook_all_methods(EmojiGridAdapter, "processEmoji", EmojiGridAdapterProcessEmojiHook(plugin))
        found.append("EmojiGridAdapter")

    _log(f"premium_emoji hooks registered: {', '.join(found)}")

    _scrub_cached_data()
