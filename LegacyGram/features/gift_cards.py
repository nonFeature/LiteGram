from hook_utils import find_class

from LegacyGram.data.constants import Keys
from LegacyGram.utils.xposed_utils import BaseHook

GIFT_MESSAGE_TYPES = (18, 25, 30, 31, 33, 34)
GIFT_ACTION_CLASS_NAMES = (
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
GIFT_MEDIA_CLASS_NAMES = (
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


def is_gift_card_message(msg) -> bool:
    try:
        if msg is None:
            return False
        try:
            msg_type = int(getattr(msg, "type", 0) or 0)
            if msg_type in GIFT_MESSAGE_TYPES:
                return True
        except Exception:
            pass
        owner = getattr(msg, "messageOwner", None)
        media = getattr(owner, "media", None) if owner else None
        action = getattr(owner, "action", None) if owner else None
        for item in (media, action):
            if item is not None:
                if _is_gift_class(_get_java_class_name(item)):
                    return True
                if _has_gift_object_metadata(item):
                    return True
                if _has_gift_ids(item):
                    return True
        return False
    except Exception:
        return False


def _is_gift_class(class_name: str) -> bool:
    return class_name in GIFT_ACTION_CLASS_NAMES or class_name in GIFT_MEDIA_CLASS_NAMES


class ChatActivityGiftBindHook(BaseHook):
    def before_hooked_method(self, param):
        if not self.is_enabled():
            return
        if not param.args or len(param.args) < 2:
            return
        try:
            holder = param.args[0]
            position = param.args[1]
            if not isinstance(position, int):
                return
            adapter = param.thisObject
            start_row = getattr(adapter, "messagesStartRow", -1)
            if start_row < 0 or position < start_row:
                return
            messages = adapter.getMessages() if hasattr(adapter, "getMessages") else None
            if messages is None:
                return
            index = position - start_row
            if index < 0:
                return
            msg = messages.get(index) if hasattr(messages, "get") else messages[index]
            if is_gift_card_message(msg):
                view = getattr(holder, "itemView", None)
                if view is not None:
                    view.setVisibility(8)
                param.setResult(None)
        except Exception:
            pass


def register_gift_cards(plugin) -> None:
    ChatActivityAdapter = find_class("org.telegram.ui.ChatActivity$ChatActivityAdapter")
    if ChatActivityAdapter:
        plugin.hook_all_methods(ChatActivityAdapter, "onBindViewHolder", ChatActivityGiftBindHook(plugin, Keys.hide_gift_cards), priority=120)
