from hook_utils import find_class
from java import jlong

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


class TLUserDeserializeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        user = param.getResult()
        if user:
            try:
                user.premium = False
                user.emoji_status = None
            except Exception:
                pass


class TLChatDeserializeHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        chat = param.getResult()
        if chat:
            try:
                chat.emoji_status = None
            except Exception:
                pass


def register_premium_badge(plugin) -> None:
    TLRPC_User = find_class("org.telegram.tgnet.TLRPC$User")
    if TLRPC_User:
        try:
            plugin.hook_all_methods(TLRPC_User, "TLdeserialize", TLUserDeserializeHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    TLRPC_Chat = find_class("org.telegram.tgnet.TLRPC$Chat")
    if TLRPC_Chat:
        try:
            plugin.hook_all_methods(TLRPC_Chat, "TLdeserialize", TLChatDeserializeHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

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

    ChatAvatarContainer = find_class("org.telegram.ui.ActionBar.ChatAvatarContainer")
    if ChatAvatarContainer:
        try:
            plugin.hook_all_methods(ChatAvatarContainer, "setTitle", ChatAvatarContainerSetTitleHook(plugin, Keys.hide_premium_badge))
        except Exception:
            pass

    # === Collectible status ===
    _hook_collectible_status(plugin)
    _hook_particles(plugin)


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


class IsEmojiStatusCollectibleHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(False)


class EmojiStatusDocumentIdHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(jlong(0))


class ChatAvatarContainerSetTitleHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        # We look for the showPremiumBadge boolean.
        # In 8.7.4 it was arg[4]. In modern it's arg[1].
        # The safest approach is to set all booleans up to arg[4] to False ONLY if we know it's exactly the premium one.
        # But wait, we can just forcefully remove the premium star from the user object right before the call?
        # Actually, let's just set param.args[1] = False and param.args[4] = False if they are booleans!
        args = param.args
        if args and len(args) >= 2 and isinstance(args[1], bool):
            args[1] = False
        if args and len(args) >= 5 and isinstance(args[4], bool):
            args[4] = False


def _hook_collectible_status(plugin) -> None:
    DialogObject = find_class("org.telegram.messenger.DialogObject")
    if DialogObject:
        try:
            plugin.hook_all_methods(DialogObject, "isEmojiStatusCollectible", IsEmojiStatusCollectibleHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass


def _hook_particles(plugin) -> None:
    SwapAnimatedEmojiDrawable = find_class("org.telegram.ui.Components.AnimatedEmojiDrawable$SwapAnimatedEmojiDrawable")
    if SwapAnimatedEmojiDrawable:
        try:
            plugin.hook_all_methods(SwapAnimatedEmojiDrawable, "setParticles", ForceParticlesOffHook(plugin, Keys.hide_collectible_status))
        except Exception:
            pass
