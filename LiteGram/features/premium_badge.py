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
        if not self.is_enabled():
            return
        param.setResult(None)


class ZeroHook(BaseHook):
    def before_hooked_method(self, param):
        param.setResult(0)


class MessagesControllerIsPremiumUserHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        param.setResult(False)


class DrawerMenuHidePremiumHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            obj = param.thisObject
            if hasattr(obj, "premiumStatusDrawable"):
                drawable = obj.premiumStatusDrawable
                if drawable and hasattr(drawable, "set"):
                    drawable.set(None, False)
        except Exception:
            pass


_premium_gradient_class = None
_status_badge_component_class = None
_badge_dto_class = None
_tlrpc_user_class = None
_badges_controller_class = None


def find_premium_gradient_class():
    global _premium_gradient_class
    if _premium_gradient_class is not None:
        return _premium_gradient_class
    for pkg in [
        "org.telegram.ui.Components.Premium.PremiumGradient",
        "org.telegram.p035ui.Components.Premium.PremiumGradient",
        "org.telegram.p022ui.Components.Premium.PremiumGradient",
        "org.telegram.p031ui.Components.Premium.PremiumGradient",
    ]:
        try:
            cls = find_class(pkg)
            if cls:
                _premium_gradient_class = cls
                return cls
        except Exception:
            pass
    return None


def find_status_badge_component_class():
    global _status_badge_component_class
    if _status_badge_component_class is not None:
        return _status_badge_component_class
    for pkg in [
        "org.telegram.ui.Components.StatusBadgeComponent",
        "org.telegram.p035ui.Components.StatusBadgeComponent",
        "org.telegram.p022ui.Components.StatusBadgeComponent",
        "org.telegram.p031ui.Components.StatusBadgeComponent",
    ]:
        try:
            cls = find_class(pkg)
            if cls:
                _status_badge_component_class = cls
                return cls
        except Exception:
            pass
    return None


class ChatMessageCellGetAuthorStatusHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        res = param.getResult()
        if res is not None:
            if isinstance(res, (int, float)):
                param.setResult(None)
                return
            if hasattr(res, "getClass"):
                try:
                    global _badge_dto_class
                    if _badge_dto_class is None:
                        _badge_dto_class = find_class("com.exteragram.messenger.api.dto.BadgeDTO")
                    if _badge_dto_class and _badge_dto_class.isInstance(res):
                        return
                except Exception:
                    pass

                try:
                    clazz_name = res.getClass().getName()
                    if "Drawable" in clazz_name or "Long" in clazz_name or "Integer" in clazz_name or "Number" in clazz_name:
                        param.setResult(None)
                except Exception:
                    pass


class SwapAnimatedEmojiDrawableSetHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        arg = param.args[0] if param.args else None
        if arg is not None and hasattr(arg, "getClass"):
            try:
                clazz_name = arg.getClass().getName()
                if "Drawable" in clazz_name:
                    if "Premium" in clazz_name or "Star" in clazz_name or "liststar" in clazz_name.lower():
                        param.args[0] = None
                        return
                    PremiumGradient_cls = find_premium_gradient_class()
                    if PremiumGradient_cls:
                        instance = PremiumGradient_cls.getInstance()
                        if instance:
                            star_drawable = instance.premiumStarDrawableMini
                            if arg == star_drawable or (
                                hasattr(arg, "getConstantState")
                                and hasattr(star_drawable, "getConstantState")
                                and arg.getConstantState() == star_drawable.getConstantState()
                            ):
                                param.args[0] = None
                                return
            except Exception:
                pass


class StatusBadgeComponentUpdateDrawableHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        global _tlrpc_user_class
        if _tlrpc_user_class is None:
            try:
                _tlrpc_user_class = find_class("org.telegram.tgnet.TLRPC$User")
            except Exception:
                pass

        if _tlrpc_user_class is None:
            return

        user = None
        for arg in param.args:
            if arg is not None and _tlrpc_user_class.isInstance(arg):
                user = arg
                break

        if user:
            try:
                if hasattr(user, "verified") and user.verified:
                    return
                global _badges_controller_class
                if _badges_controller_class is None:
                    _badges_controller_class = find_class("com.exteragram.messenger.badges.BadgesController")
                if _badges_controller_class:
                    has_badge = False
                    try:
                        if _badges_controller_class.INSTANCE.getBadge(user) is not None:
                            has_badge = True
                    except Exception:
                        pass
                    try:
                        if _badges_controller_class.INSTANCE.hasBadge(user):
                            has_badge = True
                    except Exception:
                        pass
                    if has_badge:
                        return
            except Exception:
                pass

            res = param.getResult()
            if res is not None:
                try:
                    res.set(None, False)
                except Exception:
                    pass


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

            MessageObject = find_class("org.telegram.messenger.MessageObject")
            if MessageObject:
                plugin.hook_all_methods(MessageObject, "getEmojiStatusDocumentId", zero_hook)

            MessagesController = find_class("org.telegram.messenger.MessagesController")
            if MessagesController:
                is_premium_hook = MessagesControllerIsPremiumUserHook(plugin, Keys.hide_premium_badge)
                plugin.hook_all_methods(MessagesController, "isPremiumUser", is_premium_hook)

            ChatMessageCell = find_class("org.telegram.ui.Cells.ChatMessageCell")
            if ChatMessageCell:
                get_author_status_hook = ChatMessageCellGetAuthorStatusHook(plugin, Keys.hide_premium_badge)
                plugin.hook_all_methods(ChatMessageCell, "getAuthorStatus", get_author_status_hook)

            SwapAnimatedEmojiDrawable = find_class("org.telegram.ui.Components.AnimatedEmojiDrawable$SwapAnimatedEmojiDrawable")
            if SwapAnimatedEmojiDrawable:
                swap_set_hook = SwapAnimatedEmojiDrawableSetHook(plugin, Keys.hide_premium_badge)
                plugin.hook_all_methods(SwapAnimatedEmojiDrawable, "set", swap_set_hook)

            StatusBadgeComponent = find_status_badge_component_class()
            if StatusBadgeComponent:
                status_badge_hook = StatusBadgeComponentUpdateDrawableHook(plugin, Keys.hide_premium_badge)
                plugin.hook_all_methods(StatusBadgeComponent, "updateDrawable", status_badge_hook)

            DrawerHeaderView = find_class("com.exteragram.messenger.drawer.DrawerHeaderView")
            AccountRowView = find_class("com.exteragram.messenger.drawer.DrawerAccountPickerView$AccountRowView")

            drawer_hook = DrawerMenuHidePremiumHook(plugin, Keys.hide_premium_badge)
            if DrawerHeaderView:
                plugin.hook_all_methods(DrawerHeaderView, "updateUserInfo", drawer_hook)
            if AccountRowView:
                plugin.hook_all_methods(AccountRowView, "bind", drawer_hook)

            # Also block collectible emoji statuses when premium badge is hidden
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
