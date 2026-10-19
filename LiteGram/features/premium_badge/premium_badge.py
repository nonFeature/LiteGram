from typing import Any

from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import load_dex_class

_premium_badge_dex: Any = None


def init_premium_badge_dex(plugin: Any) -> None:
    global _premium_badge_dex
    if _premium_badge_dex is not None:
        update_premium_badge_dex_settings(plugin)
        return

    dex_cls = load_dex_class("non.feature.litegram.premium_badge.PremiumBadgeHook", plugin)
    if not dex_cls:
        return

    try:
        ApplicationLoader = find_class("org.telegram.messenger.ApplicationLoader")
        if not ApplicationLoader:
            return
        context = getattr(ApplicationLoader, "applicationContext", None)
        if not context:
            return
        parent_cl = context.getClassLoader()

        init_method = dex_cls.getMethod("init", find_class("java.lang.ClassLoader"))
        init_method.invoke(None, parent_cl)

        _premium_badge_dex = dex_cls
        update_premium_badge_dex_settings(plugin)
        plugin.log("[LiteGram] PremiumBadge Kotlin DEX loaded.")
    except Exception as e:
        plugin.log(f"[LiteGram] Failed to init PremiumBadge DEX: {e}")


def update_premium_badge_dex_settings(plugin: Any) -> None:
    if _premium_badge_dex is None:
        return
    try:
        BooleanClz = find_class("java.lang.Boolean")
        bool_type = getattr(BooleanClz, "TYPE", None)
        hide_badge = bool(plugin.get_setting(Keys.hide_premium_badge, False))
        hide_collectible = bool(plugin.get_setting(Keys.hide_collectible_status, False))

        try:
            update_method = _premium_badge_dex.getMethod("updateSettings", bool_type, bool_type)
            update_method.invoke(None, hide_badge, hide_collectible)
        except Exception:
            StringClz = find_class("java.lang.String")
            set_flag_method = _premium_badge_dex.getMethod("setFlag", StringClz, bool_type)
            set_flag_method.invoke(None, "hidePremiumBadge", hide_badge)
            set_flag_method.invoke(None, "hideCollectibleStatus", hide_collectible)
    except Exception as e:
        plugin.log(f"[LiteGram] Failed to update PremiumBadge DEX settings: {e}")


def unload_premium_badge_dex() -> None:
    global _premium_badge_dex
    if _premium_badge_dex is not None:
        try:
            _premium_badge_dex.getMethod("unload").invoke(None)
        except Exception:
            pass
        _premium_badge_dex = None


def register_premium_badge(plugin: Any) -> None:
    init_premium_badge_dex(plugin)
