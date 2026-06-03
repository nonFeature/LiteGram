from typing import Any, Optional

from base_plugin import BasePlugin, HookResult
from ui.bulletin import BulletinHelper

from LegacyGram.data.constants import Keys
from LegacyGram.features.action_bar import register_action_bar
from LegacyGram.features.gift_button import register_gift_button
from LegacyGram.features.gift_cards import register_gift_cards
from LegacyGram.features.gift_dialogs import register_gift_dialogs
from LegacyGram.features.greeting_button import register_greeting_button
from LegacyGram.features.media_layout import register_media_layout
from LegacyGram.features.premium_badge import register_premium_badge
from LegacyGram.features.premium_emoji import filter_response, register_premium_emoji
from LegacyGram.features.profile_actions import register_profile_actions
from LegacyGram.features.profile_appearance import register_profile_appearance
from LegacyGram.features.settings_menu import register_settings_menu
from LegacyGram.features.star_rating import register_star_rating
from LegacyGram.features.star_reaction import register_star_reaction
from LegacyGram.ui.settings import get_main_settings_list
from LegacyGram.ui.settings_header import create_header

_PROFILE_GIFT_REQUEST_HOOKS = {
    "TL_users_getFullUser",
    "TL_channels_getFullChannel",
    "TL_messages_getFullChat",
    "TL_contacts_resolveUsername",
    "TL_messages_getDialogs",
    "TL_messages_getPeerDialogs",
    "TL_users_getUsers",
}

_GIFT_SUBSTRING_HOOKS = {"StarGift", "Gifts", "StarGiftUnique"}


class LegacyGramPlugin(BasePlugin):
    _instance: Optional["LegacyGramPlugin"] = None

    def on_plugin_load(self) -> None:
        LegacyGramPlugin._instance = self
        tl_hooks = [
            "TL_messages_getEmojiStickers",
            "TL_messages_getFeaturedEmojiStickers",
            "TL_messages_getFeaturedStickers",
            "TL_messages_searchEmojiStickerSets",
            "TL_messages_searchStickers",
            "TL_messages_getRecentReactions",
            "TL_messages_getRecentStickers",
            "TL_messages_getStickers",
            "TL_messages_getStickerSet",
        ]
        for name in tl_hooks:
            try:
                self.add_hook(name)
                self.log(f"TL add_hook: {name}")
            except Exception as e:
                self.log(f"TL add_hook failed: {name} {e}")
        for name in _PROFILE_GIFT_REQUEST_HOOKS:
            try:
                self.add_hook(name)
            except Exception:
                pass
        for name in _GIFT_SUBSTRING_HOOKS:
            try:
                self.add_hook(name, match_substring=True)
            except Exception:
                pass
        self.register_hooks()
        self._setup_settings_header()

    def post_request_hook(self, request_name: str, account: int, response: Any, error: Any) -> HookResult:
        if error is not None or response is None:
            return HookResult()
        if self.get_setting(Keys.hide_premium_emoji, False):
            filter_response(request_name, response)
        if self.get_setting(Keys.hide_gifts_tab, False) or self.get_setting(Keys.hide_profile_pinned_gifts, False):
            if self._is_gift_request(request_name):
                self._sanitize_gifts_payload(response)
        return HookResult()

    def on_update_hook(self, update_name: str, account: int, update: Any) -> HookResult:
        if self.get_setting(Keys.hide_profile_pinned_gifts, False) and update is not None:
            self._sanitize_gifts_payload(update)
        return HookResult()

    def on_updates_hook(self, container_name: str, account: int, updates: Any) -> HookResult:
        if self.get_setting(Keys.hide_profile_pinned_gifts, False) and updates is not None:
            self._sanitize_gifts_payload(updates)
        return HookResult()

    def _is_gift_request(self, name: str) -> bool:
        if name in _PROFILE_GIFT_REQUEST_HOOKS:
            return True
        name_lower = str(name).lower()
        return "gift" in name_lower or "stargift" in name_lower

    @staticmethod
    def _sanitize_gifts_payload(obj, visited=None, depth=0):
        if obj is None or depth > 4:
            return
        if visited is None:
            visited = set()
        try:
            oid = id(obj)
            if oid in visited:
                return
            visited.add(oid)
        except Exception:
            pass
        try:
            for field in ("gifts", "saved_gifts", "profileGifts", "profile_gifts", "profileTabs"):
                container = getattr(obj, field, None)
                if container is not None and hasattr(container, "clear"):
                    container.clear()
            tabs = getattr(obj, "tabs", None)
            if tabs is not None:
                try:
                    if hasattr(tabs, "size") and hasattr(tabs, "remove"):
                        i = tabs.size() - 1
                        while i >= 0:
                            tab = tabs.get(i)
                            if hasattr(tab, "id") and tab.id == 14:
                                tabs.remove(i)
                            i -= 1
                    elif hasattr(tabs, "__iter__"):
                        to_remove = [t for t in tabs if hasattr(t, "id") and t.id == 14]
                        for t in to_remove:
                            try:
                                tabs.remove(t)
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass
        for key in ("users", "chats", "list", "items"):
            try:
                val = getattr(obj, key, None)
                if val is not None and hasattr(val, "__iter__"):
                    for item in val:
                        LegacyGramPlugin._sanitize_gifts_payload(item, visited, depth + 1)
            except Exception:
                pass
        for key in ("user", "chat", "full_user", "full_chat", "peer", "data", "result"):
            try:
                LegacyGramPlugin._sanitize_gifts_payload(getattr(obj, key, None), visited, depth + 1)
            except Exception:
                pass

    def create_settings(self) -> list[Any]:
        return get_main_settings_list()

    def _setup_settings_header(self):
        try:
            from base_plugin import MethodHook
            from hook_utils import find_class, get_private_field
            from org.telegram.ui.Components import UItem

            class LegacyGramSettingsHeaderHook(MethodHook):
                def after_hooked_method(inner_self, param):
                    try:
                        activity = param.thisObject
                        items = param.args[0]
                        if not items or items.size() == 0:
                            return
                        plugin_obj = get_private_field(activity, "plugin")
                        if not plugin_obj or str(plugin_obj.getId()) != "legacygram":
                            return
                        if get_private_field(activity, "createSubFragmentCallback") is not None:
                            return
                        searching = get_private_field(activity, "searching")
                        if searching:
                            return
                        header = create_header(activity.getContext())
                        if header:
                            item = UItem.asCustom(header)
                            try:
                                item.setTransparent(True)
                            except Exception:
                                pass
                            items.add(0, item)
                            items.add(1, UItem.asShadow())
                    except Exception:
                        pass

            PluginSettingsActivity = find_class("com.exteragram.messenger.plugins.ui.PluginSettingsActivity")
            if PluginSettingsActivity:
                method = PluginSettingsActivity.getClass().getDeclaredMethod(
                    "fillItems",
                    find_class("java.util.ArrayList"),
                    find_class("org.telegram.ui.Components.UniversalAdapter"),
                )
                method.setAccessible(True)
                self.hook_method(method, LegacyGramSettingsHeaderHook())
                self.log("settings header hook registered")
        except Exception:
            pass

    def register_hooks(self) -> None:
        register_action_bar(self)
        register_star_rating(self)
        register_media_layout(self)
        register_settings_menu(self)
        register_gift_button(self)
        register_gift_cards(self)
        register_gift_dialogs(self)
        register_greeting_button(self)
        register_profile_appearance(self)
        register_profile_actions(self)
        register_premium_emoji(self)
        register_premium_badge(self)
        register_star_reaction(self)

    @classmethod
    def get_instance(cls) -> "LegacyGramPlugin":
        if cls._instance is None:
            BulletinHelper.show_error("Error while getting LegacyGramPlugin Instance!")
            raise RuntimeError("Error while getting LegacyGramPlugin Instance!")
        return cls._instance
