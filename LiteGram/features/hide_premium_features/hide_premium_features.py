from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def update_hide_premium_features_dex_settings(plugin: Any) -> None:
    enabled = bool(plugin.get_setting(Keys.hide_premium_features, False))
    try:
        dex_bridge.set_flag(Keys.hide_premium_features, enabled)
    except Exception:
        pass

    if enabled:
        try:
            from hook_utils import find_class

            MessagesController = find_class("org.telegram.messenger.MessagesController")
            if MessagesController:
                for i in range(4):
                    try:
                        instance = MessagesController.getInstance(i)
                        if instance:
                            field = instance.getClass().getDeclaredField("folderTags")
                            field.setAccessible(True)
                            field.setBoolean(instance, False)
                    except Exception:
                        pass
        except Exception:
            pass


def register_hide_premium_features(plugin: Any) -> None:
    update_hide_premium_features_dex_settings(plugin)
