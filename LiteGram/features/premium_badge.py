from base_plugin import MethodReplacement
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
            if hasattr(obj, "emojiStatusGiftId"):
                obj.emojiStatusGiftId = None
        except Exception:
            pass
        param.setResult(None)


class ProfileEmojiStatusDrawableHook(BaseHook):
    def before_hooked_method(self, param):
        # If premium badge hiding is fully enabled, hide the drawable completely
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


class SmartEmojiStatusHook(BaseHook):
    def before_hooked_method(self, param):
        arg = param.args[0] if param.args else None
        if arg is None:
            param.setResult(0)
            return

        class_name = str(arg.getClass().getName()).lower()
        if "user" in class_name or "chat" in class_name:
            try:
                BadgesController = find_class("com.exteragram.messenger.badges.BadgesController")
                if BadgesController and BadgesController.INSTANCE.hasBadge(arg):
                    # Let it fall through to BadgesController
                    param.setResult(None)
                    return
            except Exception:
                pass

        # Hide standard premium/custom emoji statuses
        param.setResult(0)


class ZeroHook(BaseHook):
    def before_hooked_method(self, param):
        param.setResult(0)


class FalseMethodReplacement(MethodReplacement):
    def replace_hooked_method(self, param):
        return False


class NullMethodReplacement(MethodReplacement):
    def replace_hooked_method(self, param):
        return None


def register_premium_badge(plugin) -> None:
    if plugin.get_setting(Keys.hide_premium_badge, False):
        try:
            smart_hook = SmartEmojiStatusHook(plugin)
            zero_hook = ZeroHook(plugin)
            UserObject = find_class("org.telegram.messenger.UserObject")
            if UserObject:
                plugin.hook_all_methods(UserObject, "getEmojiStatusDocumentId", smart_hook)

            DialogObject = find_class("org.telegram.messenger.DialogObject")
            if DialogObject:
                plugin.hook_all_methods(DialogObject, "getEmojiStatusDocumentId", zero_hook)
        except Exception:
            pass

    # === Collectible status ===
    _hook_collectible_status(plugin)


def _hook_collectible_status(plugin) -> None:
    if plugin.get_setting(Keys.hide_collectible_status, False):
        try:
            return_false = FalseMethodReplacement()
            for class_name in ["org.telegram.messenger.UserObject", "org.telegram.messenger.DialogObject", "org.telegram.messenger.MessageObject"]:
                try:
                    cls = find_class(class_name)
                    if cls:
                        plugin.hook_all_methods(cls, "isEmojiStatusCollectible", return_false)
                except Exception:
                    pass
        except Exception:
            pass

    try:
        ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
        plugin.hook_all_methods(ProfileActivity, "setCollectibleGiftStatus", ProfileCollectibleHintBlockHook(plugin, Keys.hide_collectible_status))
        plugin.hook_all_methods(ProfileActivity, "getEmojiStatusDrawable", ProfileEmojiStatusDrawableHook(plugin, Keys.hide_collectible_status))
    except Exception:
        pass
