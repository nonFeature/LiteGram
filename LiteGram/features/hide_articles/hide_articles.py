from typing import Any

from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge
from LiteGram.utils.xposed_utils import BaseHook


class MessagesControllerRichEditorAvailableHook(BaseHook):
    def __init__(self, plugin: Any):
        super().__init__(plugin, Keys.hide_articles_editor)

    def before_hooked_method(self, param: Any) -> None:
        if not self.is_enabled():
            return
        param.setResult(False)


def update_simplified_articles_settings(plugin: Any) -> None:
    val = bool(plugin.get_setting(Keys.simplified_articles_editor, False))
    dex_bridge.set_flag(Keys.simplified_articles_editor, val)


def register_hide_articles(plugin: Any) -> None:
    try:
        from LiteGram.utils.utils import get_client_version, parse_version

        if parse_version(get_client_version()) < (12, 9, 0):
            return

        update_simplified_articles_settings(plugin)

        MessagesController = find_class("org.telegram.messenger.MessagesController")
        if MessagesController is not None:
            plugin.hook_all_methods(MessagesController, "richEditorAvailable", MessagesControllerRichEditorAvailableHook(plugin))
    except Exception:
        pass
