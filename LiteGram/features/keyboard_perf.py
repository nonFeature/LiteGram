from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.features.premium_emoji import (
    ArrayList,
    EmojiGridAdapter,
    EmojiSearchAdapter,
    EmojiView,
    _filter_search_results,
    _reindex_search_sets,
)
from LiteGram.utils.xposed_utils import BaseHook


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


ChatActivityEnterView = find_class("org.telegram.ui.Components.ChatActivityEnterView")
MediaDataController = find_class("org.telegram.messenger.MediaDataController")


def register_keyboard_perf(plugin):
    if EmojiGridAdapter:
        plugin.hook_all_methods(EmojiGridAdapter, "processEmoji", SkipEmojiPacksHook(plugin))

    if EmojiView:
        plugin.hook_all_methods(EmojiView, "getEmojipacks", EmptyEmojiPacksHook(plugin))
        plugin.hook_all_methods(EmojiView, "<init>", SetAllowAnimatedEmojiFalseHook(plugin))

    if EmojiSearchAdapter:
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$7", FilterSearchV7Hook(plugin))

    if ChatActivityEnterView:
        plugin.hook_all_methods(ChatActivityEnterView, "<init>", DisableNotificationsLockerHook(plugin))

    if MediaDataController:
        plugin.hook_all_methods(MediaDataController, "getRecentReactions", FilterReactionsListHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getTopReactions", FilterReactionsListHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getSavedReactions", FilterReactionsListHook(plugin))
        plugin.hook_all_methods(MediaDataController, "getStickerSets", ClearStickerSetsType5Hook(plugin))
        plugin.hook_all_methods(MediaDataController, "getFeaturedEmojiSets", ClearFeaturedEmojiSetsHook(plugin))
