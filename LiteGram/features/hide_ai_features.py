from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


# спизжено у @kvucoPlugins, извините 👉👈  # noqa: RUF003
class AiControllerCanUseAIHook(BaseHook):
    def before_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_ai_summarize, False):
            param.setResult(False)


class ChatActivityShowAiButtonHook(BaseHook):
    def before_hooked_method(self, param):
        if self.plugin.get_setting(Keys.hide_ai_button, False):
            from java.lang import Boolean

            try:
                if param.args:
                    param.args[0] = Boolean(False)  # ty: ignore
            except Exception:
                pass


def register_hide_ai_features(plugin) -> None:
    # 1. AI settings
    try:
        AiController = find_class("com.exteragram.messenger.ai.AiController")
        if AiController is not None:
            plugin.hook_all_methods(AiController, "canUseAI", AiControllerCanUseAIHook(plugin))
    except Exception:
        pass

    # 2. AI input button: showAiButton hooks
    ai_classes = (
        "org.telegram.ui.Components.ChatActivityEnterView",
        "org.telegram.ui.Components.ChatAttachAlert",
        "org.telegram.ui.Components.CaptionPhotoViewer",
    )
    for class_name in ai_classes:
        try:
            clazz = find_class(class_name)
            if clazz is not None:
                plugin.hook_all_methods(clazz, "showAiButton", ChatActivityShowAiButtonHook(plugin))
        except Exception:
            pass
