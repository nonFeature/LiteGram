from hook_utils import find_class, get_private_field, set_private_field

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
TL_messages_stickerSet = find_class("org.telegram.tgnet.TLRPC$TL_messages_stickerSet")
System = find_class("java.lang.System")
UserConfig = find_class("org.telegram.messenger.UserConfig")

EMOJI_PACKS_TYPE = None
if MediaDataController:
    try:
        EMOJI_PACKS_TYPE = MediaDataController.TYPE_EMOJIPACKS
    except Exception:
        pass

_FILTERED_PACK_LIST_IDENTITIES: set[int] = set()
_PREMIUM_DOC_IDS: set[int] = set()
_FREE_DOC_IDS: set[int] = set()


def _document_id(document) -> int | None:
    if not document:
        return None

    document_id = getattr(document, "id", None)
    if document_id is None:
        return None

    try:
        return int(document_id)
    except Exception:
        return None


def _remember_document_status(document, is_free: bool) -> None:
    document_id = _document_id(document)
    if document_id is None:
        return

    if is_free:
        _PREMIUM_DOC_IDS.discard(document_id)
        _FREE_DOC_IDS.add(document_id)
    else:
        _FREE_DOC_IDS.discard(document_id)
        _PREMIUM_DOC_IDS.add(document_id)


def _is_premium_custom_emoji_document(document) -> bool:
    if not document:
        return False

    try:
        if bool(getattr(document, "premium", False)):
            return True
    except Exception:
        pass

    if not MessageObject:
        return False

    try:
        return not bool(MessageObject.isFreeEmoji(document))
    except Exception:
        return False


def _cache_custom_emoji_document_status(document) -> None:
    if not document:
        return

    _remember_document_status(document, not _is_premium_custom_emoji_document(document))


def _resolve_current_account(current_account: int | None) -> int | None:
    if current_account is not None:
        return current_account

    if UserConfig:
        try:
            return int(UserConfig.selectedAccount)
        except Exception:
            return None

    return None


def _is_free_document(document) -> bool:
    if not document or not MessageObject:
        return False

    try:
        is_free = bool(MessageObject.isFreeEmoji(document))
    except Exception:
        return False

    _remember_document_status(document, is_free)
    return is_free


def _is_keep_document(document) -> bool:
    return _is_free_document(document)


def _clone_filtered_documents(documents):
    if not documents or not ArrayList:
        return None, False

    filtered_documents = ArrayList()
    touched = False
    for index in range(documents.size()):
        document = documents.get(index)
        if _is_keep_document(document):
            filtered_documents.add(document)
        else:
            touched = True

    if not touched:
        return documents, False

    return filtered_documents, True


def _cache_documents(documents) -> None:
    if not documents:
        return

    for index in range(documents.size()):
        document = documents.get(index)
        _cache_custom_emoji_document_status(document)


def _cache_emoji_pack_documents(sticker_sets) -> None:
    if not sticker_sets:
        return

    for index in range(sticker_sets.size()):
        pack = sticker_sets.get(index)
        documents = getattr(pack, "documents", None)
        _cache_documents(documents)


def _clone_filtered_emoji_pack(pack):
    if not TL_messages_stickerSet or not ArrayList:
        return None, False

    documents = getattr(pack, "documents", None)
    if documents is None:
        return None, False

    filtered_documents, changed = _clone_filtered_documents(documents)
    if filtered_documents is None:
        return None, False

    if not changed:
        return pack, False

    try:
        cloned_pack = TL_messages_stickerSet()
    except Exception:
        try:
            cloned_pack = pack.__class__()
        except Exception:
            try:
                cloned_pack = pack.getClass().newInstance()
            except Exception:
                return None, False

    cloned_pack.set = getattr(pack, "set", None)
    cloned_pack.documents = filtered_documents

    return cloned_pack, True


def _clone_filtered_emoji_pack_list(sticker_sets) -> tuple[object | None, bool]:
    if not sticker_sets or not ArrayList:
        return None, False

    filtered_sticker_sets = ArrayList()
    touched = False

    for index in range(sticker_sets.size()):
        pack = sticker_sets.get(index)
        cloned_pack, changed = _clone_filtered_emoji_pack(pack)
        if cloned_pack is None:
            filtered_sticker_sets.add(pack)
            continue

        if changed:
            touched = True

        cloned_documents = getattr(cloned_pack, "documents", None)
        if cloned_documents is not None and cloned_documents.size() == 0:
            touched = True
            continue

        filtered_sticker_sets.add(cloned_pack)

    if not touched:
        return sticker_sets, False

    return filtered_sticker_sets, True


def _filter_search_sets_in_place(search_sets, current_account: int | None) -> bool:
    array_list_cls = ArrayList
    if not search_sets or array_list_cls is None:
        return False

    filtered = array_list_cls()
    changed = False
    current_header = None
    current_docs = array_list_cls()

    def flush_section():
        nonlocal current_header, current_docs, changed
        if current_header is None:
            if current_docs.size() > 0:
                for i in range(current_docs.size()):
                    filtered.add(current_docs.get(i))
            current_docs = array_list_cls()
            return

        if current_docs.size() > 0:
            filtered.add(current_header)
            for i in range(current_docs.size()):
                filtered.add(current_docs.get(i))
        else:
            changed = True
        current_header = None
        current_docs = array_list_cls()

    for index in range(search_sets.size()):
        item = search_sets.get(index)
        if bool(item) and getattr(item, "title", None) is not None:
            flush_section()
            current_header = item
            continue

        if _is_free_document(item):
            if current_header is None:
                filtered.add(item)
            else:
                current_docs.add(item)
        else:
            changed = True

    flush_section()

    if not changed:
        return False

    search_sets.clear()
    search_sets.addAll(filtered)
    return True


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

    for index in range(documents.size()):
        document = documents.get(index)
        if _is_premium_custom_emoji_document(document):
            return True

    return False


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

    if document_id in _FREE_DOC_IDS:
        return False

    if document_id in _PREMIUM_DOC_IDS:
        return True

    account = _resolve_current_account(current_account)
    if account is None or not AnimatedEmojiDrawable:
        return False

    try:
        document = AnimatedEmojiDrawable.findDocument(account, document_id)
    except Exception:
        return False

    if not document:
        return False

    return not _is_free_document(document)


def _filter_animated_emoji_string_list_in_place(emoji_list, current_account: int | None) -> bool:
    if not emoji_list:
        return False

    changed = False
    for index in range(emoji_list.size() - 1, -1, -1):
        emoji = emoji_list.get(index)
        if _is_premium_animated_emoji(emoji, current_account):
            emoji_list.remove(index)
            changed = True

    return changed


def _filter_keyword_results_in_place(keyword_results, current_account: int | None) -> bool:
    if not keyword_results:
        return False

    changed = False
    for index in range(keyword_results.size() - 1, -1, -1):
        result = keyword_results.get(index)
        emoji = getattr(result, "emoji", None)
        if emoji is None:
            try:
                emoji = str(result)
            except Exception:
                continue

        if _is_premium_animated_emoji(emoji, current_account):
            keyword_results.remove(index)
            changed = True

    return changed


def _list_identity(obj) -> int | None:
    if obj is None:
        return None

    try:
        if System:
            return int(System.identityHashCode(obj))
    except Exception:
        pass

    try:
        return hash(obj)
    except Exception:
        return None


def _filter_recent_emoji(recent_emoji, current_account: int | None) -> None:
    current_account = _resolve_current_account(current_account)
    if not recent_emoji:
        return

    _filter_animated_emoji_string_list_in_place(recent_emoji, current_account)


def _filter_search_results(search_results, current_account: int | None) -> None:
    current_account = _resolve_current_account(current_account)
    if not search_results:
        return

    for index in range(search_results.size() - 1, -1, -1):
        result = search_results.get(index)
        emoji = getattr(result, "emoji", None)
        if emoji is None:
            try:
                emoji = str(result)
            except Exception:
                continue

        if _is_premium_animated_emoji(emoji, current_account):
            search_results.remove(index)


class MediaDataControllerGetStickerSetsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        if not param.args:
            return

        try:
            arg0 = int(param.args[0])
        except Exception:
            return

        if EMOJI_PACKS_TYPE is None or arg0 != int(EMOJI_PACKS_TYPE):
            return

        sticker_sets = param.getResult()
        if not sticker_sets:
            return

        _cache_emoji_pack_documents(sticker_sets)

        filtered_sticker_sets, touched = _clone_filtered_emoji_pack_list(sticker_sets)
        if filtered_sticker_sets is None:
            return

        if touched:
            param.setResult(filtered_sticker_sets)


class MediaDataControllerGetFeaturedEmojiSetsHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        featured_sets = param.getResult()
        if not featured_sets:
            return

        filtered_featured_sets = ArrayList() if ArrayList else featured_sets
        changed = False
        for index in range(featured_sets.size()):
            pack = featured_sets.get(index)
            if _is_premium_featured_pack(pack):
                changed = True
                continue
            filtered_featured_sets.add(pack)

        if changed:
            param.setResult(filtered_featured_sets)


class EmojiSearchAdapterSearchResultsHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        if not param.args or len(param.args) < 3:
            return

        emoji_view = get_private_field(param.thisObject, "this$0")
        current_account = get_private_field(emoji_view, "currentAccount") if emoji_view else None
        _filter_search_results(param.args[1], current_account)
        _filter_search_sets_in_place(param.args[2], current_account)


class SuggestEmojiViewSearchKeywordsResultsHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        if not param.args or len(param.args) < 5:
            return

        _filter_keyword_results_in_place(param.args[4], get_private_field(param.thisObject, "currentAccount"))


class SuggestEmojiViewSearchAnimatedResultsHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        if not param.args or len(param.args) < 3:
            return

        _filter_keyword_results_in_place(param.args[2], get_private_field(param.thisObject, "currentAccount"))


class EmojiAddRecentEmojiHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        if not param.args:
            return

        emoji_source = param.args[0]
        if not _is_premium_animated_emoji(emoji_source, None):
            return

        param.setResult(None)


class EmojiGridAdapterProcessEmojiHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        try:
            update_emojipacks = bool(param.args[0])
        except Exception:
            update_emojipacks = False

        if update_emojipacks:
            return

        frozen_emoji_packs = get_private_field(param.thisObject, "frozenEmojiPacks")
        if not frozen_emoji_packs:
            return

        list_identity = _list_identity(frozen_emoji_packs)
        if list_identity is not None and list_identity in _FILTERED_PACK_LIST_IDENTITIES:
            return

        filtered_frozen_packs, touched = _clone_filtered_emoji_pack_list(frozen_emoji_packs)
        if touched and filtered_frozen_packs is not None:
            set_private_field(param.thisObject, "frozenEmojiPacks", filtered_frozen_packs)
            list_identity = _list_identity(filtered_frozen_packs)

        if list_identity is not None:
            _FILTERED_PACK_LIST_IDENTITIES.add(list_identity)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        frozen_emoji_packs = get_private_field(param.thisObject, "frozenEmojiPacks")
        list_identity = _list_identity(frozen_emoji_packs)
        if list_identity is not None:
            _FILTERED_PACK_LIST_IDENTITIES.add(list_identity)


class EmojiViewGetRecentEmojiHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        recent_emoji = param.getResult()
        if not recent_emoji:
            return

        current_account = get_private_field(param.thisObject, "currentAccount")
        _filter_recent_emoji(recent_emoji, current_account)


def register_premium_emoji(plugin) -> None:
    if Emoji:
        plugin.hook_all_methods(Emoji, "addRecentEmoji", EmojiAddRecentEmojiHook(plugin, Keys.hide_premium_emoji))

    if MediaDataController:
        plugin.hook_all_methods(MediaDataController, "getStickerSets", MediaDataControllerGetStickerSetsHook(plugin, Keys.hide_premium_emoji))
        plugin.hook_all_methods(MediaDataController, "getFeaturedEmojiSets", MediaDataControllerGetFeaturedEmojiSetsHook(plugin, Keys.hide_premium_emoji))

    if EmojiGridAdapter:
        plugin.hook_all_methods(EmojiGridAdapter, "processEmoji", EmojiGridAdapterProcessEmojiHook(plugin, Keys.hide_premium_emoji))

    if EmojiView:
        plugin.hook_all_methods(EmojiView, "getRecentEmoji", EmojiViewGetRecentEmojiHook(plugin, Keys.hide_premium_emoji))

    if EmojiSearchAdapter:
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$5", EmojiSearchAdapterSearchResultsHook(plugin, Keys.hide_premium_emoji))

    if SuggestEmojiView:
        plugin.hook_all_methods(
            SuggestEmojiView,
            "lambda$searchKeywords$3",
            SuggestEmojiViewSearchKeywordsResultsHook(plugin, Keys.hide_premium_emoji),
        )
        plugin.hook_all_methods(
            SuggestEmojiView,
            "lambda$searchAnimated$5",
            SuggestEmojiViewSearchAnimatedResultsHook(plugin, Keys.hide_premium_emoji),
        )
