from hook_utils import find_class

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook


class BlockSheetHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)


class UserSelectorBottomSheetOpenHook(BaseHook):
    def before_hooked_method(self, param):
        if self.is_enabled():
            param.setResult(None)


class BaseFragmentShowDialogBlockHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 1:
            return
        try:
            dialog = param.args[0]
            if dialog is None or not hasattr(dialog, "getClass"):
                return
            name = str(dialog.getClass().getName() or "")
            if "UserSelectorBottomSheet" in name:
                param.setResult(None)
        except Exception:
            pass


def register_gift_dialogs(plugin) -> None:
    SendGiftSheet = find_class("org.telegram.ui.Gifts.SendGiftSheet")
    GiftSheet = find_class("org.telegram.ui.Gifts.GiftSheet")
    GiftOfferSheet = find_class("org.telegram.ui.Stars.GiftOfferSheet")
    UserSelectorBottomSheet = find_class("org.telegram.ui.Components.Premium.boosts.UserSelectorBottomSheet")
    BaseFragment = find_class("org.telegram.ui.ActionBar.BaseFragment")

    if SendGiftSheet:
        plugin.hook_all_methods(SendGiftSheet, "show", BlockSheetHook(plugin, Keys.hide_gift_dialogs_send))
    if GiftSheet:
        plugin.hook_all_methods(GiftSheet, "show", BlockSheetHook(plugin, Keys.hide_gift_dialogs_send))
    if GiftOfferSheet:
        plugin.hook_all_methods(GiftOfferSheet, "show", BlockSheetHook(plugin, Keys.hide_gift_dialogs_send))
    if UserSelectorBottomSheet:
        plugin.hook_all_methods(UserSelectorBottomSheet, "open", UserSelectorBottomSheetOpenHook(plugin, Keys.hide_gift_dialogs_send))
        plugin.hook_all_methods(UserSelectorBottomSheet, "show", BlockSheetHook(plugin, Keys.hide_gift_dialogs_send))
    if BaseFragment:
        plugin.hook_all_methods(BaseFragment, "showDialog", BaseFragmentShowDialogBlockHook(plugin, Keys.hide_gift_dialogs_send), priority=120)

    StarGiftSheet = find_class("org.telegram.ui.Stars.StarGiftSheet")
    StarGiftPreviewSheet = find_class("org.telegram.ui.Stars.StarGiftPreviewSheet")
    if StarGiftSheet:
        plugin.hook_all_methods(StarGiftSheet, "show", BlockSheetHook(plugin, Keys.hide_gift_dialogs_view))
    if StarGiftPreviewSheet:
        plugin.hook_all_methods(StarGiftPreviewSheet, "show", BlockSheetHook(plugin, Keys.hide_gift_dialogs_view))
