from typing import Any

from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import load_dex_class

_hide_communities_dex: Any = None


def init_hide_communities_dex(plugin: Any) -> None:
    global _hide_communities_dex
    if _hide_communities_dex is not None:
        update_hide_communities_dex_settings(plugin)
        return

    dex_cls = load_dex_class("non.feature.litegram.hide_communities.HideCommunitiesHook", plugin)
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

        _hide_communities_dex = dex_cls
        update_hide_communities_dex_settings(plugin)
        plugin.log("[LiteGram] HideCommunities Kotlin DEX loaded.")
    except Exception as e:
        plugin.log(f"[LiteGram] Failed to init HideCommunities DEX: {e}")


def update_hide_communities_dex_settings(plugin: Any) -> None:
    if _hide_communities_dex is None:
        return
    try:
        BooleanClz = find_class("java.lang.Boolean")
        StringClz = find_class("java.lang.String")
        bool_type = getattr(BooleanClz, "TYPE", None)
        val = bool(plugin.get_setting(Keys.hide_communities, False))

        try:
            update_method = _hide_communities_dex.getMethod("updateSettings", bool_type)
            update_method.invoke(None, val)
        except Exception:
            set_flag_method = _hide_communities_dex.getMethod("setFlag", StringClz, bool_type)
            set_flag_method.invoke(None, "hideCommunities", val)
    except Exception as e:
        plugin.log(f"[LiteGram] Failed to update HideCommunities DEX settings: {e}")


def unload_hide_communities_dex() -> None:
    global _hide_communities_dex
    if _hide_communities_dex is not None:
        try:
            _hide_communities_dex.getMethod("unload").invoke(None)
        except Exception:
            pass
        _hide_communities_dex = None


def register_hide_communities(plugin: Any) -> None:
    init_hide_communities_dex(plugin)
