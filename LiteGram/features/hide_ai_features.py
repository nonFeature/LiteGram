from typing import Any

from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge
from LiteGram.utils.xposed_utils import BaseHook


class TranslateControllerIsSummarizableHook(BaseHook):
    def before_hooked_method(self, param: Any) -> None:
        if self.plugin.get_setting(Keys.hide_ai_summarize, False):
            param.setResult(False)


class ChatActivityShowAiButtonHook(BaseHook):
    def before_hooked_method(self, param: Any) -> None:
        if self.plugin.get_setting(Keys.hide_ai_button, False):
            from java.lang import Boolean

            try:
                if param.args:
                    param.args[0] = Boolean(False)  # type: ignore
                obj = param.thisObject
                if obj is not None:
                    try:
                        obj.shownAiButton = False
                    except Exception:
                        pass
                    ai_btn = getattr(obj, "aiButton", None)
                    if ai_btn is not None:
                        ai_btn.setVisibility(8)
                param.setResult(None)
            except Exception:
                pass


class AiControllerCanUseAiHook(BaseHook):
    def before_hooked_method(self, param: Any) -> None:
        if self.plugin.get_setting(Keys.hide_ai_button, False):
            param.setResult(False)


def update_hide_ai_button_dex_settings(plugin: Any) -> None:
    try:
        dex_bridge.set_flag(Keys.hide_ai_button, bool(plugin.get_setting(Keys.hide_ai_button, False)))
    except Exception:
        pass


def register_hide_ai_features(plugin: Any) -> None:
    update_hide_ai_button_dex_settings(plugin)

    # 1. Summarize button inside message bubble
    try:
        TranslateController = find_class("org.telegram.messenger.TranslateController")
        if TranslateController is not None:
            plugin.hook_all_methods(TranslateController, "isSummarizable", TranslateControllerIsSummarizableHook(plugin))
    except Exception:
        pass

    # 2. AI input button: showAiButton hooks (keyboards, attach alert, caption viewer)
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

    # 3. Modern ExteraGram AI gating hook (AiController.canUseAI)
    try:
        AiController = find_class("com.exteragram.messenger.ai.AiController")
        if AiController is not None:
            plugin.hook_all_methods(AiController, "canUseAI", AiControllerCanUseAiHook(plugin))
    except Exception:
        pass
