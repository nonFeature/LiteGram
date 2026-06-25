from hook_utils import find_class

from LiteGram.utils.xposed_utils import BaseHook


class HideSavedMessagesTagsHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            if param.args:
                param.args[0] = False  # force show = False


def register_saved_tags(plugin) -> None:
    SearchTagsList = find_class("org.telegram.ui.Components.SearchTagsList")
    if SearchTagsList:
        try:
            plugin.hook_all_methods(SearchTagsList, "show", HideSavedMessagesTagsHook(plugin, "hide_saved_messages_tags"))
        except Exception:
            pass
