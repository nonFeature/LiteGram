from hook_utils import find_class

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

hook ProfileActivityGetEmojiStatusDrawable for Hide Premium Badge in Profile (setResult(None) before_hooked)
hook ChatAvatarContainerSetTitleHook for hide premium badge in chat header (param.args[4] = False before_hooked)
"""


class ProfileCollectibleHintBlockHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            hint = getattr(obj, "collectibleHint", None)
            if hint:
                try:
                    hint.hide()
                except Exception:
                    pass
            if hasattr(obj, "collectibleHint"):
                obj.collectibleHint = None
            if hasattr(obj, "collectibleHintVisible"):
                obj.collectibleHintVisible = False
            if hasattr(obj, "collectibleStatus"):
                obj.collectibleStatus = None
        except Exception:
            pass
        param.setResult(None)


class ProfileEmojiStatusDrawableHook(BaseHook):
    def before_hooked_method(self, param):
        # If premium badge hiding is fully enabled, hide the drawable completely
        # Since this hook uses hide_collectible_status setting, we need to check the premium setting manually
        if self.plugin.get_setting(Keys.hide_premium_badge, False):
            param.setResult(None)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            res = param.getResult()
            if res and hasattr(res, "setParticles"):
                res.setParticles(False, True)
        except Exception:
            pass
        try:
            obj = param.thisObject
            if hasattr(obj, "emojiStatusGiftId"):
                obj.emojiStatusGiftId = None
        except Exception:
            pass


def register_premium_badge(plugin) -> None:
    UserObject = find_class("org.telegram.messenger.UserObject")
    if UserObject:
        try:
            plugin.hook_all_methods(UserObject, "getEmojiStatusDocumentId", EmojiStatusDocumentIdHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    DialogObject = find_class("org.telegram.messenger.DialogObject")
    if DialogObject:
        try:
            plugin.hook_all_methods(DialogObject, "getEmojiStatusDocumentId", EmojiStatusDocumentIdHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    # === Collectible status ===
    _hook_collectible_status(plugin)
    _hook_particles(plugin)


class ForceParticlesOffHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled() and param.args:
            param.args[0] = False


class IsEmojiStatusCollectibleHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(False)


class EmojiStatusDocumentIdHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(0)


def _hook_collectible_status(plugin) -> None:
    hook = IsEmojiStatusCollectibleHook(plugin, Keys.hide_collectible_status)
    try:
        UserObject = find_class("org.telegram.messenger.UserObject")
        plugin.hook_all_methods(UserObject, "isEmojiStatusCollectible", hook)
    except Exception:
        pass

    try:
        DialogObject = find_class("org.telegram.messenger.DialogObject")
        plugin.hook_all_methods(DialogObject, "isEmojiStatusCollectible", hook)
    except Exception:
        pass

    try:
        MessageObject = find_class("org.telegram.messenger.MessageObject")
        plugin.hook_all_methods(MessageObject, "isEmojiStatusCollectible", hook)
    except Exception:
        pass

    try:
        ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
        plugin.hook_all_methods(ProfileActivity, "setCollectibleGiftStatus", ProfileCollectibleHintBlockHook(plugin, Keys.hide_collectible_status))
        plugin.hook_all_methods(ProfileActivity, "getEmojiStatusDrawable", ProfileEmojiStatusDrawableHook(plugin, Keys.hide_collectible_status))
    except Exception:
        pass


def _hook_particles(plugin) -> None:
    SwapAnimatedEmojiDrawable = find_class("org.telegram.ui.Components.AnimatedEmojiDrawable$SwapAnimatedEmojiDrawable")
    if SwapAnimatedEmojiDrawable:
        try:
            plugin.hook_all_methods(SwapAnimatedEmojiDrawable, "setParticles", ForceParticlesOffHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass
