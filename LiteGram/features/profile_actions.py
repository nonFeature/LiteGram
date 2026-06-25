from hook_utils import find_class, get_private_field
from java import jint

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

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

        try:
            current_key = int(param.args[self.key_index])
        except (IndexError, ValueError, TypeError):
            return

        should_hide = (
            (hide_gifts and current_key == KEY_GIFT)
            or (hide_stories and current_key == KEY_STORY)
            or (hide_stream and current_key in (KEY_VOICE_CHAT, KEY_STREAM))
        )

        if should_hide:
            param.setResult(None)


class ProfileActionsApplyHook(BaseHook):
    def after_hooked_method(self, param):
        try:
            obj = param.thisObject
            for coll in ("visibleActions", "actionsList", "allAvailableActions"):
                actions = getattr(obj, coll, None)
                if actions is not None and hasattr(actions, "remove"):
                    settings_map = [
                        (Keys.hide_profile_actions_gift_button, (KEY_GIFT,)),
                        (Keys.hide_profile_actions_stories_button, (KEY_STORY,)),
                        (Keys.hide_profile_actions_stream_button, (KEY_VOICE_CHAT, KEY_STREAM)),
                    ]
                    for setting_key, target_keys in settings_map:
                        if self.plugin.get_setting(setting_key, False):
                            for key in target_keys:
                                for k in (key, jint(key)):
                                    try:
                                        actions.remove(k)
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


class ProfileActivityUpdateBottomButtonYHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            try:
                instance = param.thisObject
                bottom_buttons_container = get_private_field(instance, "bottomButtonsContainer")
                if bottom_buttons_container:
                    bottom_buttons_container.setVisibility(8)  # GONE
            except Exception:
                pass
            param.setResult(None)


class ProfileGiftsContainerUpdateButtonHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            try:
                instance = param.thisObject
                button_container = get_private_field(instance, "buttonContainer")
                if button_container:
                    button_container.setVisibility(8)  # GONE
            except Exception:
                pass
            param.setResult(None)


class ProfileGiftsContainerGetBottomOffsetHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(jint(0))


class ProfileGiftsContainerPageUpdateEmptyViewHook(BaseHook):
    def after_hooked_method(self, param):
        if self.is_enabled():
            try:
                instance = param.thisObject
                empty_view_button = get_private_field(instance, "emptyView1Button")
                if empty_view_button:
                    empty_view_button.setVisibility(8)  # GONE
            except Exception:
                pass


def register_profile_actions(plugin) -> None:
    ProfileActionsView = find_class("org.telegram.ui.Components.ProfileActionsView")
    if ProfileActionsView:
        try:
            plugin.hook_all_methods(ProfileActionsView, "set", ProfileActionsViewHook(plugin, 0))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(ProfileActionsView, "applyVisibleActions", ProfileActionsApplyHook(plugin), priority=100)
        except Exception:
            pass

    ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
    if ProfileActivity:
        for m in ("showGifts", "openGifts", "openStarGifts", "onGiftClick", "onGiftPermiumClicked"):
            try:
                plugin.hook_all_methods(ProfileActivity, m, BlockProfileGiftViewHook(plugin, Keys.hide_profile_actions_gift_button))
            except Exception:
                pass
        try:
            plugin.hook_all_methods(
                ProfileActivity,
                "updateGiftState",
                ProfileActivityGiftBlockHook(plugin, Keys.hide_profile_actions_gift_button),
            )
        except Exception:
            pass
        try:
            plugin.hook_all_methods(
                ProfileActivity,
                "updateBottomButtonY",
                ProfileActivityUpdateBottomButtonYHook(plugin, Keys.hide_profile_actions_stories_button),
            )
        except Exception:
            pass

    ProfileGiftsContainer = find_class("org.telegram.ui.Gifts.ProfileGiftsContainer")
    if ProfileGiftsContainer:
        try:
            plugin.hook_all_methods(
                ProfileGiftsContainer,
                "updateButton",
                ProfileGiftsContainerUpdateButtonHook(plugin, Keys.hide_profile_actions_gift_button),
            )
        except Exception:
            pass
        try:
            plugin.hook_all_methods(
                ProfileGiftsContainer,
                "getBottomOffset",
                ProfileGiftsContainerGetBottomOffsetHook(plugin, Keys.hide_profile_actions_gift_button),
            )
        except Exception:
            pass

    ProfileGiftsContainerPage = find_class("org.telegram.ui.Gifts.ProfileGiftsContainer$Page")
    if ProfileGiftsContainerPage:
        try:
            plugin.hook_all_methods(
                ProfileGiftsContainerPage,
                "updateEmptyView",
                ProfileGiftsContainerPageUpdateEmptyViewHook(plugin, Keys.hide_profile_actions_gift_button),
            )
        except Exception:
            pass
