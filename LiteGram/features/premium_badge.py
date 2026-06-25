from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

"""
EXPLANATION
MessageCell.GetAuthorStatus() # Works only in chats!
    -> if user not null -> call UserObject.GetEmojiStatusDocumentId & exteraBadge
        -> if EmojiStatusDocumentId not null -> return it
        -> if exteraBadge not null -> return badge
        -> if user.premium -> return msg_premium_liststar
    else logic for chat / channels (or idk)
    not checked for exteraBadge

UserObject.GetEmojiStatusDocumentIdHook()  # Only 5 calls
    called in ChatMessageCell, DrawerUserCell, DrawerProfileCell
    so it's removes emoji status from (you will see msg_premium_liststar):
        messages in chats, drawer menu, chat list, title in chat list (search is not effected)

DialogObject.GetEmojiStatusDocumentIdHook() has over than 52 calls

Some Solution: instead remove premium badge in all places, just hook isPremiumUser

If you want to go without isPremiumUser hook:
hook ProfileActivityGetEmojiStatusDrawable for Hide Premium Badge in Profile (setResult(None) before_hooked)
hook ChatAvatarContainerSetTitleHook for hide premium badge in chat header (param.args[4] = False before_hooked)
"""


class UserObjectGetEmojiStatusDocumentIdHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(None)


class DialogObjectGetEmojiStatusDocumentIdHook(BaseHook):
    """
    Also fixes the issue when you click on badge in chat, you got wrong logic
    ref: see didPressUserStatus in ChatActivity using JADX
    if (!user.premium || DialogObject.getEmojiStatusDocumentId(user.emoji_status) == 0) {
        BadgesController badgesController = BadgesController.INSTANCE;
        BadgeDTO badge = badgesController.getBadge(user);
        if (badge != null) {
            // We are showing here stuff
            return;
        }
        return;
    }
    """

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(0)


class ChatMessageCellGetAuthorStatusHook(BaseHook):
    _BadgesController = None

    def __init__(self, plugin, setting_key):
        super().__init__(plugin, setting_key)
        self._badge_cache = {}

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        current_user = get_private_field(param.thisObject, "currentUser")

        if current_user:
            user_id = getattr(current_user, "id", None)
            if user_id is not None and user_id in self._badge_cache:
                param.setResult(self._badge_cache[user_id])
                return

            if self._BadgesController is None:
                self._BadgesController = find_class("com.exteragram.messenger.badges.BadgesController")

            if not self._BadgesController:
                return

            badge = self._BadgesController.INSTANCE.getBadge(current_user)
            if user_id is not None:
                self._badge_cache[user_id] = badge
            param.setResult(badge)
        else:
            param.setResult(None)


class MessagesControllerIsPremiumUserHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(False)


def register_premium_badge(plugin) -> None:
    ProfileActivity = find_class("org.telegram.ui.ProfileActivity")


    ChatMessageCell = find_class("org.telegram.ui.Cells.ChatMessageCell")
    if ChatMessageCell:
        try:
            plugin.hook_all_methods(ChatMessageCell, "getAuthorStatus", ChatMessageCellGetAuthorStatusHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    DialogObject = find_class("org.telegram.messenger.DialogObject")
    UserObject = find_class("org.telegram.messenger.UserObject")
    if DialogObject:
        try:
            plugin.hook_all_methods(DialogObject, "getEmojiStatusDocumentId", DialogObjectGetEmojiStatusDocumentIdHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass
    if UserObject:
        try:
            plugin.hook_all_methods(UserObject, "getEmojiStatusDocumentId", UserObjectGetEmojiStatusDocumentIdHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    MessagesController = find_class("org.telegram.messenger.MessagesController")
    if MessagesController:
        try:
            plugin.hook_all_methods(MessagesController, "isPremiumUser", MessagesControllerIsPremiumUserHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    # === Collectible status ===
    _hook_collectible_status(plugin)
    _hook_particles(plugin)


def _disable_particles(drawable) -> None:
    try:
        if drawable and hasattr(drawable, "setParticles"):
            drawable.setParticles(False, True)
    except Exception:
        pass


class IsEmojiStatusCollectibleHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(False)


class ProfileEmojiStatusDrawableHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        _disable_particles(param.getResult())


class DialogsStatusNeutralizeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            if hasattr(obj, "statusDrawableGiftId"):
                obj.statusDrawableGiftId = None
            _disable_particles(getattr(obj, "statusDrawable", None))
        except Exception:
            pass


class DialogCellStatusNeutralizeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            for field in ("statusDrawableGiftId", "emojiStatusGiftId"):
                if hasattr(obj, field):
                    setattr(obj, field, None)
            _disable_particles(getattr(obj, "statusDrawable", None))
            _disable_particles(getattr(obj, "emojiStatus", None))
        except Exception:
            pass


class DrawerProfileStatusNeutralizeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            if hasattr(obj, "statusGiftId"):
                obj.statusGiftId = None
            _disable_particles(getattr(obj, "status", None))
        except Exception:
            pass


class DrawerUserStatusNeutralizeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            for field in ("statusGiftId", "statusDrawableGiftId", "emojiStatusGiftId"):
                try:
                    if hasattr(obj, field):
                        setattr(obj, field, None)
                except Exception:
                    pass
            _disable_particles(getattr(obj, "status", None))
        except Exception:
            pass


class DrawerHeaderViewStatusNeutralizeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            _disable_particles(getattr(obj, "premiumStatusDrawable", None))
            _disable_particles(getattr(obj, "exteraBadgeDrawable", None))
        except Exception:
            pass


class ForceParticlesOffHook(BaseHook):
    _active = False

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if ForceParticlesOffHook._active:
            return
        if param.args and len(param.args) > 0 and isinstance(param.args[0], bool):
            if not param.args[0]:
                return
            ForceParticlesOffHook._active = True
            param.args[0] = False

    def after_hooked_method(self, param):
        ForceParticlesOffHook._active = False


def _hook_collectible_status(plugin) -> None:
    DialogObject = find_class("org.telegram.messenger.DialogObject")
    if DialogObject:
        try:
            plugin.hook_all_methods(DialogObject, "isEmojiStatusCollectible", IsEmojiStatusCollectibleHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass

    ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
    if ProfileActivity:
        try:
            plugin.hook_all_methods(ProfileActivity, "getEmojiStatusDrawable", ProfileEmojiStatusDrawableHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass

    DialogsActivity = find_class("org.telegram.ui.DialogsActivity")
    if DialogsActivity:
        try:
            plugin.hook_all_methods(DialogsActivity, "updateStatus", DialogsStatusNeutralizeHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass

    DialogCell = find_class("org.telegram.ui.Cells.DialogCell")
    if DialogCell:
        for m in ("buildLayout", "update"):
            try:
                plugin.hook_all_methods(DialogCell, m, DialogCellStatusNeutralizeHook(plugin, Keys.hide_collectible_status))
            except Exception:
                pass

    DrawerProfileCell = find_class("org.telegram.ui.Cells.DrawerProfileCell")
    if DrawerProfileCell:
        try:
            plugin.hook_all_methods(DrawerProfileCell, "setUser", DrawerProfileStatusNeutralizeHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass

    DrawerUserCell = find_class("org.telegram.ui.Cells.DrawerUserCell")
    if DrawerUserCell:
        for m in ("setAccount", "didReceivedNotification"):
            try:
                plugin.hook_all_methods(DrawerUserCell, m, DrawerUserStatusNeutralizeHook(plugin, Keys.hide_collectible_status))
            except Exception:
                pass

    DrawerHeaderView = find_class("com.exteragram.messenger.drawer.DrawerHeaderView")
    if DrawerHeaderView:
        try:
            plugin.hook_all_methods(DrawerHeaderView, "updateUserInfo", DrawerHeaderViewStatusNeutralizeHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass


def _hook_particles(plugin) -> None:
    SwapAnimatedEmojiDrawable = find_class("org.telegram.ui.Components.AnimatedEmojiDrawable$SwapAnimatedEmojiDrawable")
    if SwapAnimatedEmojiDrawable:
        try:
            plugin.hook_all_methods(SwapAnimatedEmojiDrawable, "setParticles", ForceParticlesOffHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass
