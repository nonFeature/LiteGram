from hook_utils import find_class, set_private_field

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

TL_reactionPaid = find_class("org.telegram.tgnet.TLRPC$TL_reactionPaid")


class ReactionsLayoutInBubbleSetMessageHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        try:
            message_object = param.args[0]  # MessageObject messageObject
            results = message_object.messageOwner.reactions.results
        except (AttributeError, TypeError):
            return

        to_remove = None

        for i in range(results.size()):
            reaction_count = results.get(i)  # class ReactionCount
            reaction = reaction_count.reaction  # class Reaction
            # org.telegram.tgnet.TLRPC$TL_reactionEmoji, reactionCustomEmoji, reactionEmpty or reactionPaid
            if TL_reactionPaid and isinstance(reaction, TL_reactionPaid):
                to_remove = reaction_count
                break

        if to_remove:
            results.remove(to_remove)


class ReactionsContainerLayoutSetVisibleReactionsListHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        try:
            visible_reactions_list = param.args[0]  # List<ReactionsLayoutInBubble.VisibleReaction> visibleReactionsList
        except IndexError:
            return

        i = visible_reactions_list.size() - 1
        while i >= 0:
            if visible_reactions_list.get(i).isStar:  # public boolean isStar;
                visible_reactions_list.remove(i)
            i -= 1


class ReactionsContainerLayoutDrawHook(BaseHook):
    """Remove gold gradient"""

    def before_hooked_method(self, param):
        if not self.is_enabled():
            return

        instance = param.thisObject
        set_private_field(instance, "hasStar", False)


def register_star_reaction(plugin) -> None:
    ReactionsLayoutInBubble = find_class("org.telegram.ui.Components.Reactions.ReactionsLayoutInBubble")
    if ReactionsLayoutInBubble:
        plugin.hook_all_methods(ReactionsLayoutInBubble, "setMessage", ReactionsLayoutInBubbleSetMessageHook(plugin, Keys.hide_star_reaction))

    ReactionsContainerLayout = find_class("org.telegram.ui.Components.ReactionsContainerLayout")
    if ReactionsContainerLayout:
        plugin.hook_all_methods(
            ReactionsContainerLayout, "setVisibleReactionsList", ReactionsContainerLayoutSetVisibleReactionsListHook(plugin, Keys.hide_star_reaction)
        )
        plugin.hook_all_methods(ReactionsContainerLayout, "dispatchDraw", ReactionsContainerLayoutDrawHook(plugin, Keys.hide_star_reaction))
