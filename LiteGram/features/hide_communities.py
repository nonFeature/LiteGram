from hook_utils import find_class, get_private_field, set_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


class ChatTLdeserializeHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            chat = param.getResult()
            if chat is not None and hasattr(chat, "linked_community_id"):
                chat.linked_community_id = 0
        except Exception:
            pass


class UserTLdeserializeHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            user = param.getResult()
            if user is not None and hasattr(user, "linked_community_id"):
                user.linked_community_id = 0
        except Exception:
            pass


class ChatAvatarContainerSetCommunityItemVisibleHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if param.args:
            param.args[0] = False


class ProfileActivityUpdateCommunityArrowItemHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            community_item = get_private_field(param.thisObject, "communityItem")
            if community_item:
                community_item.setVisibility(8)
        except Exception:
            pass
        param.setResult(None)


class ProfileActivityUpdateRowsIdsHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            activity = param.thisObject
            chat = get_private_field(activity, "currentChat")
            if chat and hasattr(chat, "linked_community_id"):
                chat.linked_community_id = 0
            user = get_private_field(activity, "currentUser")
            if user and hasattr(user, "linked_community_id"):
                user.linked_community_id = 0
        except Exception:
            pass

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            set_private_field(param.thisObject, "linkedCommunityRow", -1)
            set_private_field(param.thisObject, "linkedCommunityDividerRow", -1)
        except Exception:
            pass


class DialogCellHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            cell = param.thisObject
            chat = getattr(cell, "chat", None)
            if chat and hasattr(chat, "linked_community_id"):
                chat.linked_community_id = 0
            user = getattr(cell, "user", None)
            if user and hasattr(user, "linked_community_id"):
                user.linked_community_id = 0
            set_private_field(cell, "drawCommunityAvatar", False)
        except Exception:
            pass

    def after_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            set_private_field(param.thisObject, "drawCommunityAvatar", False)
        except Exception:
            pass


class CommunityArrowDrawableDrawHook(BaseHook):
    def __init__(self, plugin):
        super().__init__(plugin, Keys.hide_communities)

    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)


def register_hide_communities(plugin) -> None:
    try:
        TLRPC_Chat = find_class("org.telegram.tgnet.TLRPC$Chat")
        if TLRPC_Chat:
            try:
                plugin.hook_all_methods(TLRPC_Chat, "TLdeserialize", ChatTLdeserializeHook(plugin))
            except Exception:
                pass

        TLRPC_User = find_class("org.telegram.tgnet.TLRPC$User")
        if TLRPC_User:
            try:
                plugin.hook_all_methods(TLRPC_User, "TLdeserialize", UserTLdeserializeHook(plugin))
            except Exception:
                pass

        ChatAvatarContainer = find_class("org.telegram.ui.Components.ChatAvatarContainer")
        if ChatAvatarContainer:
            try:
                plugin.hook_all_methods(
                    ChatAvatarContainer,
                    "setCommunityItemVisible",
                    ChatAvatarContainerSetCommunityItemVisibleHook(plugin),
                )
            except Exception:
                pass

        ProfileActivity = find_class("org.telegram.ui.ProfileActivity")
        if ProfileActivity:
            try:
                plugin.hook_all_methods(
                    ProfileActivity,
                    "updateCommunityArrowItem",
                    ProfileActivityUpdateCommunityArrowItemHook(plugin),
                )
            except Exception:
                pass
            try:
                plugin.hook_all_methods(
                    ProfileActivity,
                    "updateRowsIds",
                    ProfileActivityUpdateRowsIdsHook(plugin),
                )
            except Exception:
                pass

        DialogCell = find_class("org.telegram.ui.Cells.DialogCell")
        if DialogCell:
            hook = DialogCellHook(plugin)
            try:
                plugin.hook_all_methods(DialogCell, "buildLayout", hook)
            except Exception:
                pass
            try:
                plugin.hook_all_methods(DialogCell, "onDraw", hook)
            except Exception:
                pass

        CommunityArrowDrawable = find_class("org.telegram.ui.community.CommunityArrowDrawable")
        if CommunityArrowDrawable:
            try:
                plugin.hook_all_methods(
                    CommunityArrowDrawable,
                    "draw",
                    CommunityArrowDrawableDrawHook(plugin),
                )
            except Exception:
                pass
    except Exception:
        pass
