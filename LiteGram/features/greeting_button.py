from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


class ChatActivityShowGreetInfoHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.args[0] = False  # boolean show


def register_greeting_button(plugin) -> None:
    ChatActivity = find_class("org.telegram.ui.ChatActivity")
    if ChatActivity:
        plugin.hook_all_methods(ChatActivity, "showGreetInfo", ChatActivityShowGreetInfoHook(plugin, Keys.hide_greeting_button))
