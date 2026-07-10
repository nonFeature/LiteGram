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
        gifts = bool(self.plugin.get_setting(Keys.hide_profile_actions_gift_button, False))
        stories = bool(self.plugin.get_setting(Keys.hide_profile_actions_stories_button, False))
        stream = bool(self.plugin.get_setting(Keys.hide_profile_actions_stream_button, False))

        if not gifts and not stories and not stream:
            return

        try:
            current_key = int(param.args[self.key_index])
        except (IndexError, ValueError, TypeError):
            return

        should_hide = (gifts and current_key == KEY_GIFT) or (stories and current_key == KEY_STORY) or (stream and current_key in (KEY_VOICE_CHAT, KEY_STREAM))

        if should_hide:
            param.setResult(None)


class ProfileActionsApplyHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin)

    def after_hooked_method(self, param):
        try:
            gifts = bool(self.plugin.get_setting(Keys.hide_profile_actions_gift_button, False))
            stories = bool(self.plugin.get_setting(Keys.hide_profile_actions_stories_button, False))
            stream = bool(self.plugin.get_setting(Keys.hide_profile_actions_stream_button, False))

            if not gifts and not stories and not stream:
                return

            obj = param.thisObject

            # Pre-filter target keys to remove
            target_keys = []
            if gifts:
                target_keys.append(KEY_GIFT)
            if stories:
                target_keys.append(KEY_STORY)
            if stream:
                target_keys.extend((KEY_VOICE_CHAT, KEY_STREAM))

            for coll in ("visibleActions", "actionsList", "allAvailableActions"):
                actions = getattr(obj, coll, None)
                if actions is not None and hasattr(actions, "remove"):
                    for key in target_keys:
                        for k in (key, jint(key)):
                            try:
                                actions.remove(k)
                            except Exception:
                                pass
        except Exception:
            pass


class ProfileActivityUpdateBottomButtonYHook(BaseHook):
    def __init__(self, plugin, setting_key):
        super().__init__(plugin, setting_key)
        self._last_instance_hash = None

    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)
            try:
                instance = param.thisObject
                instance_hash = instance.hashCode()
                if self._last_instance_hash == instance_hash:
                    return
                bottom_buttons_container = get_private_field(instance, "bottomButtonsContainer")
                if bottom_buttons_container:
                    bottom_buttons_container.setVisibility(8)  # GONE
                    self._last_instance_hash = instance_hash
            except Exception:
                pass


class ProfileGiftsContainerUpdateButtonHook(BaseHook):
    def __init__(self, plugin, setting_key):
        super().__init__(plugin, setting_key)
        self._last_instance_hash = None

    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)
            try:
                instance = param.thisObject
                instance_hash = instance.hashCode()
                if self._last_instance_hash == instance_hash:
                    return
                button_container = get_private_field(instance, "buttonContainer")
                if button_container:
                    button_container.setVisibility(8)  # GONE
                    self._last_instance_hash = instance_hash
            except Exception:
                pass


class ProfileGiftsContainerGetBottomOffsetHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(jint(0))


class ProfileGiftsContainerPageUpdateEmptyViewHook(BaseHook):
    def __init__(self, plugin, setting_key):
        super().__init__(plugin, setting_key)
        self._last_instance_hash = None

    def after_hooked_method(self, param):
        if self.is_enabled():
            try:
                instance = param.thisObject
                instance_hash = instance.hashCode()
                if self._last_instance_hash == instance_hash:
                    return
                empty_view_button = get_private_field(instance, "emptyView1Button")
                if empty_view_button:
                    empty_view_button.setVisibility(8)  # GONE
                    self._last_instance_hash = instance_hash
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
