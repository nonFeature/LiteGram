from hook_utils import find_class
from java import jint

from LiteGram.data.constants import Keys
from LiteGram.utils.xposed_utils import BaseHook

ALL_HIDDEN_TYPES = (18, 25, 30, 31, 33, 34)
ALL_HIDDEN_ACTION_CLASSES = (
    "org.telegram.tgnet.TLRPC$TL_messageActionGift",
    "org.telegram.tgnet.TLRPC$TL_messageActionGiftCode",
    "org.telegram.tgnet.TLRPC$TL_messageActionGiftPremium",
    "org.telegram.tgnet.TLRPC$TL_messageActionGiftStars",
    "org.telegram.tgnet.TLRPC$TL_messageActionGiftTon",
    "org.telegram.tgnet.TLRPC$TL_messageActionStarGift",
    "org.telegram.tgnet.TLRPC$TL_messageActionStarGiftUnique",
    "org.telegram.tgnet.TLRPC$TL_messageActionStarGiftPurchaseOffer",
    "org.telegram.tgnet.TLRPC$TL_messageActionStarGiftPurchaseOfferDeclined",
)
ALL_HIDDEN_MEDIA_CLASSES = (
    "org.telegram.tgnet.TLRPC$TL_messageMediaGiftStars",
    "org.telegram.tgnet.TLRPC$TL_messageMediaGiftPremium",
    "org.telegram.tgnet.TLRPC$TL_messageMediaStarGift",
    "org.telegram.tgnet.TLRPC$TL_messageMediaStarGiftUnique",
)
GIFT_OBJECT_CLASS_NAMES = (
    "org.telegram.tgnet.tl.TL_stars$TL_starGift",
    "org.telegram.tgnet.tl.TL_stars$TL_starGiftUnique",
)
GIFT_OBJECT_PREFIXES = (
    "org.telegram.tgnet.tl.TL_stars$TL_starGiftUnique_",
    "org.telegram.tgnet.tl.TL_stars$TL_starGiftUnique",
)


def _get_java_class_name(value) -> str:
    try:
        return str(value.getClass().getName() or "")
    except Exception:
        try:
            return str(type(value) or "")
        except Exception:
            return ""


def _has_gift_ids(obj) -> bool:
    if obj is None:
        return False
    for field in ("saved_id", "gift_msg_id"):
        try:
            val = getattr(obj, field, 0) or 0
            if int(val) != 0:
                return True
        except Exception:
            pass
    return False


def _has_gift_object_metadata(action_or_media) -> bool:
    if action_or_media is None:
        return False
    try:
        gift = getattr(action_or_media, "gift", None)
        if gift is None:
            return False
        cn = _get_java_class_name(gift)
        if cn in GIFT_OBJECT_CLASS_NAMES:
            return True
        if any(cn.startswith(p) for p in GIFT_OBJECT_PREFIXES):
            return True
        slug = getattr(gift, "slug", None)
        if slug:
            return True
    except Exception:
        pass
    return False


def _is_giveaway(item) -> bool:
    return "Giveaway" in _get_java_class_name(item)


def _is_gift(item) -> bool:
    cn = _get_java_class_name(item)
    return cn in ALL_HIDDEN_ACTION_CLASSES or cn in ALL_HIDDEN_MEDIA_CLASSES


def is_gift_message(msg) -> bool:
    try:
        if msg is None:
            return False
        try:
            msg_type = int(getattr(msg, "type", 0) or 0)
            if msg_type in ALL_HIDDEN_TYPES:
                return True
        except Exception:
            pass
        owner = getattr(msg, "messageOwner", None)
        if owner is None:
            return False
        media = getattr(owner, "media", None)
        action = getattr(owner, "action", None)
        for item in (media, action):
            if item is not None:
                if _is_gift(item):
                    return True
                if _has_gift_object_metadata(item):
                    return True
                if _has_gift_ids(item):
                    return True
        return False
    except Exception:
        return False


def is_giveaway_message(msg) -> bool:
    try:
        if msg is None:
            return False
        try:
            msg_type = int(getattr(msg, "type", 0) or 0)
            if msg_type in (26, 28):
                return True
        except Exception:
            pass
        owner = getattr(msg, "messageOwner", None)
        if owner is None:
            return False
        if getattr(owner, "via_giveaway", False):
            return True
        media = getattr(owner, "media", None)
        action = getattr(owner, "action", None)
        for item in (media, action):
            if item is not None:
                if _is_giveaway(item):
                    return True
        return False
    except Exception:
        return False


HIDDEN_VIEW_TYPE = -1000

View = find_class("android.view.View")
RecyclerViewLayoutParams = find_class("androidx.recyclerview.widget.RecyclerView$LayoutParams")
Holder = find_class("org.telegram.ui.Components.RecyclerListView$Holder")


class CollapseItemViewTypeHook(BaseHook):
    def before_hooked_method(self, param):
        hide_gifts = self.plugin.get_setting(Keys.hide_gift_cards, False)
        hide_giveaways = self.plugin.get_setting(Keys.hide_giveaway_cards, False)
        if not hide_gifts and not hide_giveaways:
            return
        if not param.args or len(param.args) < 1:
            return
        try:
            adapter = param.thisObject
            position = param.args[0]
            msg = get_msg(adapter, None, position)
            if msg is None:
                return
            if (hide_gifts and is_gift_message(msg)) or (hide_giveaways and is_giveaway_message(msg)):
                param.setResult(jint(HIDDEN_VIEW_TYPE))
        except Exception:
            pass


class CollapseCreateHook(BaseHook):
    def before_hooked_method(self, param):
        hide_gifts = self.plugin.get_setting(Keys.hide_gift_cards, False)
        hide_giveaways = self.plugin.get_setting(Keys.hide_giveaway_cards, False)
        if not hide_gifts and not hide_giveaways:
            return
        if not param.args or len(param.args) < 2:
            return
        viewType = param.args[1]
        if viewType != HIDDEN_VIEW_TYPE:
            return
        try:
            parent = param.args[0]
            context = parent.getContext()
            if View and RecyclerViewLayoutParams and Holder:
                empty = View(context)
                empty.setLayoutParams(RecyclerViewLayoutParams(-1, 0))
                empty.setMinimumHeight(0)
                param.setResult(Holder(empty))
        except Exception:
            pass


class CollapseBindHook(BaseHook):
    def before_hooked_method(self, param):
        hide_gifts = self.plugin.get_setting(Keys.hide_gift_cards, False)
        hide_giveaways = self.plugin.get_setting(Keys.hide_giveaway_cards, False)
        if not hide_gifts and not hide_giveaways:
            return
        if not param.args or len(param.args) < 2:
            return
        try:
            adapter = param.thisObject
            position = param.args[1]
            if not isinstance(position, int):
                return
            msg = get_msg(adapter, None, position)
            if msg is None:
                return
            if (hide_gifts and is_gift_message(msg)) or (hide_giveaways and is_giveaway_message(msg)):
                param.setResult(None)
        except Exception:
            pass


def get_msg(adapter, holder, position):
    start_row = getattr(adapter, "messagesStartRow", -1)
    if start_row < 0 or position < start_row:
        return None
    messages = adapter.getMessages() if hasattr(adapter, "getMessages") else None
    if messages is None:
        return None
    index = position - start_row
    if index < 0:
        return None
    return messages.get(index) if hasattr(messages, "get") else messages[index]


def register_gift_cards(plugin) -> None:
    ChatActivityAdapter = find_class("org.telegram.ui.ChatActivity$ChatActivityAdapter")
    if ChatActivityAdapter:
        plugin.hook_all_methods(ChatActivityAdapter, "getItemViewType", CollapseItemViewTypeHook(plugin), priority=120)
        plugin.hook_all_methods(ChatActivityAdapter, "onCreateViewHolder", CollapseCreateHook(plugin), priority=120)
        plugin.hook_all_methods(ChatActivityAdapter, "onBindViewHolder", CollapseBindHook(plugin), priority=120)
