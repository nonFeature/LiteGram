from hook_utils import find_class

from LegacyGram.data.constants import Keys
from LegacyGram.utils.xposed_utils import BaseHook

KEY_GIFT = 3
KEY_VOICE_CHAT = 10
KEY_STREAM = 11
KEY_STORY = 12


class ProfileActionsViewHook(BaseHook):
    def __init__(self, plugin, key_index: int):
        super().__init__(plugin)
        self.key_index = key_index

    def before_hooked_method(self, param):
        hide_gifts = self.plugin.get_setting(Keys.hide_profile_actions_gift_button, False)
        hide_stories = self.plugin.get_setting(Keys.hide_profile_actions_stories_button, False)
        hide_stream = self.plugin.get_setting(Keys.hide_profile_actions_stream_button, False)

        if not hide_gifts and not hide_stories and not hide_stream:
            return

        current_key = param.args[self.key_index]

        should_hide = (
            (hide_gifts and current_key == KEY_GIFT)
            or (hide_stories and current_key == KEY_STORY)
            or (hide_stream and current_key in (KEY_VOICE_CHAT, KEY_STREAM))
        )

        if should_hide:
            param.setResult(None)


class ProfileActionsApplyHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            for coll in ("visibleActions", "actionsList", "allAvailableActions"):
                actions = getattr(obj, coll, None)
                if actions is not None and hasattr(actions, "remove"):
                    try:
                        actions.remove(KEY_GIFT)
                    except Exception:
                        pass
        except Exception:
            pass


class ProfileActivityGiftBlockHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)


class BlockProfileGiftViewHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)


def register_profile_actions(plugin) -> None:
    ProfileActionsView = find_class("org.telegram.ui.Components.ProfileActionsView")
    if ProfileActionsView:
        plugin.hook_all_methods(ProfileActionsView, "set", ProfileActionsViewHook(plugin, 0))
        plugin.hook_all_methods(ProfileActionsView, "getOrCreate", ProfileActionsViewHook(plugin, 1))
        plugin.hook_all_methods(ProfileActionsView, "applyVisibleActions", ProfileActionsApplyHook(plugin, Keys.hide_profile_actions_gift_button), priority=100)

    ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
    if ProfileActivity:
        for m in ("showGifts", "openGifts", "openStarGifts", "onGiftClick", "onGiftPermiumClicked"):
            plugin.hook_all_methods(ProfileActivity, m, BlockProfileGiftViewHook(plugin, Keys.hide_profile_actions_gift_button))
        plugin.hook_all_methods(ProfileActivity, "updateGiftState", ProfileActivityGiftBlockHook(plugin, Keys.hide_profile_actions_gift_button))
