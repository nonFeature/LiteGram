from android.view import View  # ty: ignore
from hook_utils import find_class, get_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

"""
A LITTLE EXPLANATION
There's a separate code paths for addSubItem and lazilyAddSubItems
addSubItem(id, ...) -> creates view -> adds to popupLayout -> returns View
    If we return null: caller stores null -> later setVisibility() from showSubItem -> app crashed

lazilyAddSubItem(id, ...) -> stores in lazyList -> later layoutLazyItems() creates view
    If we return null: lazyMap has null -> ... -> crashed

So we just View.GONE, instead setResult(None)

We also hook setSubItemShown to remove some elements, that sets visibility to true
And hook for topics (boost group button)
"""

# from ProfileActivity class
CALL_ITEM = 15  # Start Live Stream / Video Chat | NOT CALLS IN DM!
GIFT_PREMIUM = 38
CHANNEL_STORIES = 39  # Archived Stories
ADD_SHORTCUT_PROFILE = 14  # Add to home screen

# from ChatActivity class
ADD_SHORTCUT_CHAT = 24
BOOST_GROUP = 29

# from TopicsFragment class
BOOST_GROUP_TOPIC = 14

_ITEM_KEY_MAP = {
    CALL_ITEM: Keys.hide_action_bar_live_stream,
    GIFT_PREMIUM: Keys.hide_action_bar_send_gift,
    CHANNEL_STORIES: Keys.hide_action_bar_archived_stories,
    ADD_SHORTCUT_PROFILE: Keys.hide_action_bar_add_shortcut,
    ADD_SHORTCUT_CHAT: Keys.hide_action_bar_add_shortcut,
    BOOST_GROUP: Keys.hide_action_bar_boost_group,
}


class ActionBarMenuItemAddSubItemHook(BaseHook):
    def after_hooked_method(self, param):
        result = param.getResult()
        if result is None:
            return
        if not param.args:
            return
        item_id = param.args[0]
        if item_id not in _ITEM_KEY_MAP or not self.plugin.get_setting(_ITEM_KEY_MAP[item_id], False):
            return
        result.setVisibility(View.GONE)


class ActionBarMenuItemLazilyAddSubItemHook(BaseHook):
    def after_hooked_method(self, param):
        result = param.getResult()
        if result is None:
            return
        if not param.args:
            return
        item_id = param.args[0]
        if item_id not in _ITEM_KEY_MAP or not self.plugin.get_setting(_ITEM_KEY_MAP[item_id], False):
            return
        result.setVisibility(View.GONE)


# calls showSubItem(id); if show is true
# public void setSubItemShown(int id, boolean show)
class ActionBarMenuItemSetSubItemShownHook(BaseHook):
    def before_hooked_method(self, param):
        if not param.args or len(param.args) < 2:
            return
        item_id = param.args[0]
        if item_id in _ITEM_KEY_MAP and self.plugin.get_setting(_ITEM_KEY_MAP[item_id], False):
            param.args[1] = False  # boolean show


class TopicsFragmentUpdateChatInfoHook(BaseHook):
    def after_hooked_method(self, param):
        if not self.is_enabled():
            return

        instance = param.thisObject
        boost_submenu_field = get_private_field(instance, "boostGroupSubmenu")

        if boost_submenu_field is not None:
            boost_submenu_field.setVisibility(8)


def register_action_bar(plugin) -> None:
    ActionBarMenuItem = find_class("org.telegram.ui.ActionBar.ActionBarMenuItem")
    TopicsFragment = find_class("org.telegram.ui.TopicsFragment")
    if ActionBarMenuItem:
        plugin.hook_all_methods(ActionBarMenuItem, "addSubItem", ActionBarMenuItemAddSubItemHook(plugin))
        plugin.hook_all_methods(ActionBarMenuItem, "lazilyAddSubItem", ActionBarMenuItemLazilyAddSubItemHook(plugin))
        plugin.hook_all_methods(ActionBarMenuItem, "setSubItemShown", ActionBarMenuItemSetSubItemShownHook(plugin))
    if TopicsFragment:
        plugin.hook_all_methods(TopicsFragment, "updateChatInfo", TopicsFragmentUpdateChatInfoHook(plugin, Keys.hide_action_bar_boost_group))
