from hook_utils import find_class, get_private_field
from java import jint

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


class StarGiftPatternsDrawProfileAnimatedPatternHook(BaseHook):
    """
    We just skip drawing method lol
    """

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(None)


class ProfileGiftsViewConstructorHook(BaseHook):
    def after_hooked_method(self, param):
        if self.is_enabled():
            try:
                param.thisObject.setVisibility(8)  # GONE
            except Exception:
                pass


class ProfileGiftsViewUpdateHook(BaseHook):
    """
    ProfileGiftsView.update()
        -> StarsController.getProfileGiftsList()
        -> Creates Gift objects and adds to gifts ArrayList
        -> dispatchDraw() renders them around avatar

    If enabled, we immediately set visibility to GONE and skip update logic.
    """

    def before_hooked_method(self, param):
        if self.is_enabled():
            try:
                param.thisObject.setVisibility(8)  # GONE
            except Exception:
                pass
            param.setResult(None)


class ChatMessageCellSetMessageObjectInternalHook(BaseHook):
    """
    setMessageObjectInternal(MessageObject) -> read MessageObject.messageOwner.from_boosts_applied
    if boosts > 0: create BoostCounter
    just hook it and set to 0
    """

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        try:
            message_object = param.args[0]  # MessageObject messageObject
            message_object.messageOwner.from_boosts_applied = 0
        except (AttributeError, TypeError):
            pass


class MessagesControllerPeerColorFromCollectibleHook(BaseHook):
    """
    final MessagesController.PeerColor wasPeerColor = peerColor;
    peerColor = MessagesController.PeerColor.fromCollectible(user.emoji_status);
    if (peerColor == null) {
        final int colorId = UserObject.getProfileColorId(user);
        ...
    }
    """

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(None)


class UserObjectGetProfileColorIdHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(jint(-1))  # Return -1 color id


class ChatObjectGetProfileColorIdHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(jint(-1))  # Return -1 color id


class DialogObjectGetBotVerificationIconHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(0)  # Return no icon


class DialogObjectGetBotVerificationHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(None)  # return .bot_verification is null


class ProfileActivityGetBotVerificationDrawableHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(None)  # skip this method entirely


class ChatActivityUpdateTopPanelHook(BaseHook):
    """Remove a bot verification description in Top Panel by nullify bot_verification field"""

    def __init__(self, plugin, setting_key):
        super().__init__(plugin, setting_key)
        self._last_instance_hash = None

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        instance = param.thisObject
        instance_hash = instance.hashCode()
        if self._last_instance_hash == instance_hash:
            return

        user_info = get_private_field(instance, "userInfo")
        chat_info = get_private_field(instance, "chatInfo")
        if user_info:
            user_info.bot_verification = None
        if chat_info:
            chat_info.bot_verification = None

        self._last_instance_hash = instance_hash


class UserFullTLdeserializeHook(BaseHook):
    def after_hooked_method(self, param):
        from de.robv.android.xposed import XposedBridge  # type: ignore

        try:
            user_info = param.getResult()
            if not user_info:
                return

            if self.plugin.get_setting(Keys.hide_profile_music, False):
                try:
                    user_info.saved_music = None
                except Exception as e:
                    XposedBridge.log(f"LiteGram [UserFullHook] error setting saved_music: {e}")

            if self.plugin.get_setting(Keys.hide_profile_business, False):
                try:
                    user_info.business_work_hours = None
                    user_info.business_location = None
                except Exception as e:
                    XposedBridge.log(f"LiteGram [UserFullHook] error setting business fields: {e}")
        except Exception as e:
            XposedBridge.log(f"LiteGram [UserFullHook] error: {e}")


class NowPlayingControllerShouldShowCardHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(False)


def register_profile_appearance(plugin) -> None:
    # Profile Background Emoji
    StarGiftPatterns = find_class("org.telegram.ui.Stars.StarGiftPatterns")
    if StarGiftPatterns:
        try:
            plugin.hook_all_methods(
                StarGiftPatterns, "drawProfileAnimatedPattern", StarGiftPatternsDrawProfileAnimatedPatternHook(plugin, Keys.hide_profile_background_emoji)
            )
        except Exception:
            pass

    # Profile Pinned Gifts
    ProfileGiftsView = find_class("org.telegram.ui.Stars.ProfileGiftsView")
    if ProfileGiftsView:
        try:
            plugin.hook_all_constructors(ProfileGiftsView, ProfileGiftsViewConstructorHook(plugin, Keys.hide_profile_pinned_gifts))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(ProfileGiftsView, "update", ProfileGiftsViewUpdateHook(plugin, Keys.hide_profile_pinned_gifts))
        except Exception:
            pass

    # Boost Badge
    ChatMessageCell = find_class("org.telegram.ui.Cells.ChatMessageCell")
    if ChatMessageCell:
        try:
            plugin.hook_all_methods(ChatMessageCell, "setMessageObjectInternal", ChatMessageCellSetMessageObjectInternalHook(plugin, Keys.hide_boost_badge))
        except Exception:
            pass

    # Profile Colorful Background
    MessagesController = find_class("org.telegram.messenger.MessagesController$PeerColor")
    UserObject = find_class("org.telegram.messenger.UserObject")
    ChatObject = find_class("org.telegram.messenger.ChatObject")
    if MessagesController:
        try:
            plugin.hook_all_methods(
                MessagesController, "fromCollectible", MessagesControllerPeerColorFromCollectibleHook(plugin, Keys.hide_profile_colorful_background)
            )
        except Exception:
            pass
    if UserObject:
        try:
            plugin.hook_all_methods(UserObject, "getProfileColorId", UserObjectGetProfileColorIdHook(plugin, Keys.hide_profile_colorful_background))
        except Exception:
            pass
    if ChatObject:
        try:
            plugin.hook_all_methods(ChatObject, "getProfileColorId", ChatObjectGetProfileColorIdHook(plugin, Keys.hide_profile_colorful_background))
        except Exception:
            pass

    # Bot verification (Also see settings_menu UpdateRowsIds hook!)
    DialogObject = find_class("org.telegram.messenger.DialogObject")
    ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
    if DialogObject:
        try:
            plugin.hook_all_methods(DialogObject, "getBotVerificationIcon", DialogObjectGetBotVerificationIconHook(plugin, Keys.hide_bot_verification))
        except Exception:
            pass
        try:
            plugin.hook_all_methods(DialogObject, "getBotVerification", DialogObjectGetBotVerificationHook(plugin, Keys.hide_bot_verification))
        except Exception:
            pass
    if ProfileActivity:
        try:
            plugin.hook_all_methods(
                ProfileActivity, "getBotVerificationDrawable", ProfileActivityGetBotVerificationDrawableHook(plugin, Keys.hide_bot_verification)
            )
        except Exception:
            pass
    # UserFull fields (saved_music, business_work_hours, business_location)
    UserFull = find_class("org.telegram.tgnet.TLRPC$UserFull")
    if UserFull:
        try:
            plugin.hook_all_methods(UserFull, "TLdeserialize", UserFullTLdeserializeHook(plugin))
        except Exception:
            pass

    # Now Playing Card Hiding
    NowPlayingController = find_class("com.exteragram.messenger.nowplaying.NowPlayingController")
    if NowPlayingController:
        try:
            plugin.hook_all_methods(NowPlayingController, "shouldShowCard", NowPlayingControllerShouldShowCardHook(plugin, Keys.hide_profile_music))
        except Exception:
            pass

    ChatActivity = find_class("org.telegram.ui.ChatActivity")
    if ChatActivity:
        try:
            plugin.hook_all_methods(ChatActivity, "updateTopPanelView", ChatActivityUpdateTopPanelHook(plugin, Keys.hide_bot_verification))
        except Exception:
            pass
