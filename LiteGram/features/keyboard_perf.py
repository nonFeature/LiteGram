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


def register_keyboard_perf(plugin):
    if EmojiGridAdapter:
        plugin.hook_all_methods(EmojiGridAdapter, "processEmoji", SkipEmojiPacksHook(plugin))

    if EmojiView:
        plugin.hook_all_methods(EmojiView, "getEmojipacks", EmptyEmojiPacksHook(plugin))

    if EmojiSearchAdapter:
        plugin.hook_all_methods(EmojiSearchAdapter, "lambda$search$7", FilterSearchV7Hook(plugin))
