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


class ProfileGiftsViewUpdateHook(BaseHook):
    """
    ProfileGiftsView.update()
        -> StarsController.getProfileGiftsList()
        -> Creates Gift objects and adds to gifts ArrayList
        -> dispatchDraw() renders them around avatar

    so we just clear an array with gifts and redraw View
    """

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        instance = param.thisObject
        instance.gifts.clear()

        # redraw the view
        instance.invalidate()


class ChatMessageCellSetMessageObjectInternalHook(BaseHook):
    """
    setMessageObjectInternal(MessageObject) -> read MessageObject.messageOwner.from_boosts_applied
    if boosts > 0: create BoostCounter
    just hook it and set to 0
    """

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        message_object = param.args[0]  # MessageObject messageObject
        message_object.messageOwner.from_boosts_applied = 0


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

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        instance = param.thisObject
        user_info = get_private_field(instance, "userInfo")
        chat_info = get_private_field(instance, "chatInfo")
        if user_info:
            user_info.bot_verification = None
        if chat_info:
            chat_info.bot_verification = None


def register_profile_appearance(plugin) -> None:
    # Profile Background Emoji
    StarGiftPatterns = find_class("org.telegram.ui.Stars.StarGiftPatterns")
    if StarGiftPatterns:
        plugin.hook_all_methods(
            StarGiftPatterns, "drawProfileAnimatedPattern", StarGiftPatternsDrawProfileAnimatedPatternHook(plugin, Keys.hide_profile_background_emoji)
        )

    # Profile Pinned Gifts
    ProfileGiftsView = find_class("org.telegram.ui.Stars.ProfileGiftsView")
    if ProfileGiftsView:
        plugin.hook_all_methods(ProfileGiftsView, "update", ProfileGiftsViewUpdateHook(plugin, Keys.hide_profile_pinned_gifts))

    # Boost Badge
    ChatMessageCell = find_class("org.telegram.ui.Cells.ChatMessageCell")
    if ChatMessageCell:
        plugin.hook_all_methods(ChatMessageCell, "setMessageObjectInternal", ChatMessageCellSetMessageObjectInternalHook(plugin, Keys.hide_boost_badge))

    # Profile Colorful Background
    MessagesController = find_class("org.telegram.messenger.MessagesController$PeerColor")
    UserObject = find_class("org.telegram.messenger.UserObject")
    ChatObject = find_class("org.telegram.messenger.ChatObject")
    if MessagesController:
        plugin.hook_all_methods(
            MessagesController, "fromCollectible", MessagesControllerPeerColorFromCollectibleHook(plugin, Keys.hide_profile_colorful_background)
        )
    if UserObject:
        plugin.hook_all_methods(UserObject, "getProfileColorId", UserObjectGetProfileColorIdHook(plugin, Keys.hide_profile_colorful_background))
    if ChatObject:
        plugin.hook_all_methods(ChatObject, "getProfileColorId", ChatObjectGetProfileColorIdHook(plugin, Keys.hide_profile_colorful_background))

    # Bot verification (Also see settings_menu UpdateRowsIds hook!)
    DialogObject = find_class("org.telegram.messenger.DialogObject")
    ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
    if DialogObject:
        plugin.hook_all_methods(DialogObject, "getBotVerificationIcon", DialogObjectGetBotVerificationIconHook(plugin, Keys.hide_bot_verification))
        plugin.hook_all_methods(DialogObject, "getBotVerification", DialogObjectGetBotVerificationHook(plugin, Keys.hide_bot_verification))
    if ProfileActivity:
        plugin.hook_all_methods(
            ProfileActivity, "getBotVerificationDrawable", ProfileActivityGetBotVerificationDrawableHook(plugin, Keys.hide_bot_verification)
        )
    ChatActivity = find_class("org.telegram.ui.ChatActivity")
    if ChatActivity:
        plugin.hook_all_methods(ChatActivity, "updateTopPanelView", ChatActivityUpdateTopPanelHook(plugin, Keys.hide_bot_verification))
