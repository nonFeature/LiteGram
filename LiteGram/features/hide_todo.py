from hook_utils import find_class, get_private_field, set_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


class ButtonsAdapterNotifyDataSetChangedHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_todo_button)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        adapter = param.thisObject
        if not adapter:
            return
        alert = getattr(adapter, "this$0", None)
        if not alert:
            alert = get_private_field(adapter, "this$0")
        if alert:
            set_private_field(alert, "todoEnabled", False)


class ChatAttachAlertInitHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_todo_button)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        set_private_field(param.thisObject, "todoEnabled", False)


def register_hide_todo(plugin) -> None:
    try:
        from LiteGram.utils.utils import get_client_version, parse_version

        if parse_version(get_client_version()) < (12, 9, 0):
            return

        ChatAttachAlert = find_class("org.telegram.ui.Components.ChatAttachAlert")
        if ChatAttachAlert is not None:
            try:
                plugin.hook_all_methods(ChatAttachAlert, "init", ChatAttachAlertInitHook(plugin))
            except Exception:
                pass

            ButtonsAdapter = find_class("org.telegram.ui.Components.ChatAttachAlert$ButtonsAdapter")
            if ButtonsAdapter is None:
                try:
                    for declared in ChatAttachAlert.getDeclaredClasses():
                        if declared.getSimpleName() == "ButtonsAdapter":
                            ButtonsAdapter = declared
                            break
                except Exception:
                    pass

            if ButtonsAdapter is not None:
                try:
                    plugin.hook_all_methods(
                        ButtonsAdapter,
                        "notifyDataSetChanged",
                        ButtonsAdapterNotifyDataSetChangedHook(plugin),
                    )
                except Exception:
                    pass
    except Exception:
        pass
