package non.feature.litegram.gift_cards

import android.os.Trace
import android.view.View
import android.view.ViewGroup
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Constructor
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList
import java.util.Collections
import java.util.concurrent.ConcurrentHashMap
import non.feature.litegram.core.ReflectionCache

object GiftCardsHook {

    @Volatile @JvmStatic var hideGiftCards: Boolean = false
    @Volatile @JvmStatic var hideGiveawayCards: Boolean = false

    private const val HIDDEN_VIEW_TYPE = -1000

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    private var chatActivityAdapterClass: Class<*>? = null
    private var messagesStartRowField: Field? = null
    private var getMessagesMethod: Method? = null
    private var messagesField: Field? = null

    private var recyclerListViewHolderConstructor: Constructor<*>? = null
    private var recyclerViewLayoutParamsConstructor: Constructor<*>? = null

    private var messageObjectClass: Class<*>? = null
    private var messageTypeField: Field? = null
    private var messageOwnerField: Field? = null

    private var messageClass: Class<*>? = null
    private var mediaField: Field? = null
    private var actionField: Field? = null
    private var viaGiveawayField: Field? = null

    // Fast O(1) class checks
    private val hiddenActionAndMediaClasses = Collections.newSetFromMap(ConcurrentHashMap<Class<*>, Boolean>())
    private val giftObjectClasses = Collections.newSetFromMap(ConcurrentHashMap<Class<*>, Boolean>())

    private val HIDDEN_ACTION_CLASS_NAMES = arrayOf(
        "org.telegram.tgnet.TLRPC\$TL_messageActionGift",
        "org.telegram.tgnet.TLRPC\$TL_messageActionGiftCode",
        "org.telegram.tgnet.TLRPC\$TL_messageActionGiftPremium",
        "org.telegram.tgnet.TLRPC\$TL_messageActionGiftStars",
        "org.telegram.tgnet.TLRPC\$TL_messageActionGiftTon",
        "org.telegram.tgnet.TLRPC\$TL_messageActionStarGift",
        "org.telegram.tgnet.TLRPC\$TL_messageActionStarGiftUnique",
        "org.telegram.tgnet.TLRPC\$TL_messageActionStarGiftPurchaseOffer",
        "org.telegram.tgnet.TLRPC\$TL_messageActionStarGiftPurchaseOfferDeclined"
    )

    private val HIDDEN_MEDIA_CLASS_NAMES = arrayOf(
        "org.telegram.tgnet.TLRPC\$TL_messageMediaGiftStars",
        "org.telegram.tgnet.TLRPC\$TL_messageMediaGiftPremium",
        "org.telegram.tgnet.TLRPC\$TL_messageMediaStarGift",
        "org.telegram.tgnet.TLRPC\$TL_messageMediaStarGiftUnique"
    )

    private val GIFT_OBJECT_CLASS_NAMES = arrayOf(
        "org.telegram.tgnet.tl.TL_stars\$TL_starGift",
        "org.telegram.tgnet.tl.TL_stars\$TL_starGiftUnique"
    )

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideGiftCards", "hide_gift_cards" -> hideGiftCards = enabled
            "hideGiveawayCards", "hide_giveaway_cards" -> hideGiveawayCards = enabled
        }
    }

    @JvmStatic
    fun unload() {
        synchronized(localUnhooks) {
            for (u in localUnhooks) {
                try {
                    u.unhook()
                } catch (_: Throwable) {}
            }
            localUnhooks.clear()
        }

        hideGiftCards = false
        hideGiveawayCards = false

        chatActivityAdapterClass = null
        messagesStartRowField = null
        getMessagesMethod = null
        messagesField = null
        recyclerListViewHolderConstructor = null
        recyclerViewLayoutParamsConstructor = null
        messageObjectClass = null
        messageTypeField = null
        messageOwnerField = null
        messageClass = null
        mediaField = null
        actionField = null
        viaGiveawayField = null
        hiddenActionAndMediaClasses.clear()
        giftObjectClasses.clear()
    }

    private fun hookAllMethods(
        clazz: Class<*>?,
        methodName: String,
        hook: XC_MethodHook,
        targetList: MutableList<XC_MethodHook.Unhook>
    ) {
        if (clazz == null) return
        try {
            val result = XposedBridge.hookAllMethods(clazz, methodName, hook)
            if (result != null) {
                synchronized(targetList) {
                    targetList.addAll(result)
                }
            }
        } catch (_: Throwable) {}
    }

    private fun getMessage(adapter: Any, position: Int): Any? {
        val startRow = messagesStartRowField?.getInt(adapter) ?: -1
        if (startRow < 0 || position < startRow) return null

        val messages = if (getMessagesMethod != null) {
            try {
                getMessagesMethod?.invoke(adapter)
            } catch (_: Throwable) {
                messagesField?.get(adapter)
            }
        } else {
            messagesField?.get(adapter)
        } ?: return null

        val index = position - startRow
        if (index < 0) return null

        return when (messages) {
            is List<*> -> if (index < messages.size) messages[index] else null
            is Array<*> -> if (index < messages.size) messages[index] else null
            else -> {
                try {
                    ReflectionCache.getMethod(messages.javaClass, "get", Int::class.javaPrimitiveType)?.invoke(messages, index)
                } catch (_: Throwable) {
                    null
                }
            }
        }
    }

    private fun isGiftActionOrMedia(item: Any?): Boolean {
        if (item == null) return false
        val cls = item.javaClass
        if (hiddenActionAndMediaClasses.contains(cls)) return true
        val name = cls.name
        if (name.startsWith("org.telegram.tgnet.TLRPC\$TL_messageActionGift") ||
            name.startsWith("org.telegram.tgnet.TLRPC\$TL_messageActionStarGift") ||
            name.startsWith("org.telegram.tgnet.TLRPC\$TL_messageMediaGift") ||
            name.startsWith("org.telegram.tgnet.TLRPC\$TL_messageMediaStarGift")
        ) {
            hiddenActionAndMediaClasses.add(cls)
            return true
        }
        return false
    }

    private fun hasGiftObjectMetadata(actionOrMedia: Any?): Boolean {
        if (actionOrMedia == null) return false
        try {
            val giftField = ReflectionCache.getField(actionOrMedia.javaClass, "gift") ?: return false
            val gift = giftField.get(actionOrMedia) ?: return false
            val giftCls = gift.javaClass
            if (giftObjectClasses.contains(giftCls)) return true
            val giftName = giftCls.name
            if (giftName.startsWith("org.telegram.tgnet.tl.TL_stars\$TL_starGift")) {
                giftObjectClasses.add(giftCls)
                return true
            }
            val slugField = ReflectionCache.getField(giftCls, "slug")
            if (slugField != null && slugField.get(gift) != null) return true
        } catch (_: Throwable) {}
        return false
    }

    private fun hasGiftIds(obj: Any?): Boolean {
        if (obj == null) return false
        try {
            val cls = obj.javaClass
            val savedIdField = ReflectionCache.getField(cls, "saved_id")
            if (savedIdField != null) {
                val v = (savedIdField.get(obj) as? Number)?.toLong() ?: 0L
                if (v != 0L) return true
            }
            val giftMsgIdField = ReflectionCache.getField(cls, "gift_msg_id")
            if (giftMsgIdField != null) {
                val v = (giftMsgIdField.get(obj) as? Number)?.toLong() ?: 0L
                if (v != 0L) return true
            }
        } catch (_: Throwable) {}
        return false
    }

    private fun isGiftMessage(msg: Any): Boolean {
        try {
            val type = messageTypeField?.getInt(msg) ?: 0
            when (type) {
                18, 25, 30, 31, 33, 34 -> return true
            }
            val owner = messageOwnerField?.get(msg) ?: return false
            val media = mediaField?.get(owner)
            if (media != null && (isGiftActionOrMedia(media) || hasGiftObjectMetadata(media) || hasGiftIds(media))) {
                return true
            }
            val action = actionField?.get(owner)
            if (action != null && (isGiftActionOrMedia(action) || hasGiftObjectMetadata(action) || hasGiftIds(action))) {
                return true
            }
        } catch (_: Throwable) {}
        return false
    }

    private fun isGiveawayMessage(msg: Any): Boolean {
        try {
            val type = messageTypeField?.getInt(msg) ?: 0
            when (type) {
                26, 28 -> return true
            }
            val owner = messageOwnerField?.get(msg) ?: return false
            if (viaGiveawayField?.getBoolean(owner) == true) return true

            val media = mediaField?.get(owner)
            if (media != null && media.javaClass.name.contains("Giveaway")) return true

            val action = actionField?.get(owner)
            if (action != null && action.javaClass.name.contains("Giveaway")) return true
        } catch (_: Throwable) {}
        return false
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        chatActivityAdapterClass = ReflectionCache.findClass("org.telegram.ui.ChatActivity\$ChatActivityAdapter", cl)
        if (chatActivityAdapterClass == null) return

        messagesStartRowField = ReflectionCache.getField(chatActivityAdapterClass, "messagesStartRow")
        getMessagesMethod = ReflectionCache.getMethod(chatActivityAdapterClass, "getMessages")
        messagesField = ReflectionCache.getField(chatActivityAdapterClass, "messages")

        val recyclerListViewHolderClass = ReflectionCache.findClass("org.telegram.ui.Components.RecyclerListView\$Holder", cl)
        recyclerListViewHolderConstructor = try {
            recyclerListViewHolderClass?.getConstructor(View::class.java)
        } catch (_: Throwable) { null }

        val recyclerViewLayoutParamsClass = ReflectionCache.findClass("androidx.recyclerview.widget.RecyclerView\$LayoutParams", cl)
        recyclerViewLayoutParamsConstructor = try {
            recyclerViewLayoutParamsClass?.getConstructor(Int::class.javaPrimitiveType, Int::class.javaPrimitiveType)
        } catch (_: Throwable) { null }

        messageObjectClass = ReflectionCache.findClass("org.telegram.messenger.MessageObject", cl)
        messageTypeField = ReflectionCache.getField(messageObjectClass, "type")
        messageOwnerField = ReflectionCache.getField(messageObjectClass, "messageOwner")

        messageClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$Message", cl)
        mediaField = ReflectionCache.getField(messageClass, "media")
        actionField = ReflectionCache.getField(messageClass, "action")
        viaGiveawayField = ReflectionCache.getField(messageClass, "via_giveaway")

        for (cn in HIDDEN_ACTION_CLASS_NAMES) {
            ReflectionCache.findClass(cn, cl)?.let { hiddenActionAndMediaClasses.add(it) }
        }
        for (cn in HIDDEN_MEDIA_CLASS_NAMES) {
            ReflectionCache.findClass(cn, cl)?.let { hiddenActionAndMediaClasses.add(it) }
        }
        for (cn in GIFT_OBJECT_CLASS_NAMES) {
            ReflectionCache.findClass(cn, cl)?.let { giftObjectClasses.add(it) }
        }

        // 1. Hook getItemViewType(int position)
        hookAllMethods(chatActivityAdapterClass, "getItemViewType", object : XC_MethodHook(120) {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideGiftCards && !hideGiveawayCards) return
                val args = param.args
                if (args == null || args.isEmpty()) return
                val position = args[0] as? Int ?: return
                val adapter = param.thisObject ?: return

                Trace.beginSection("LiteGram::gift_cards:getItemViewType")
                try {
                    val msg = getMessage(adapter, position) ?: return
                    val isGift = hideGiftCards && isGiftMessage(msg)
                    val isGiveaway = hideGiveawayCards && isGiveawayMessage(msg)
                    if (isGift || isGiveaway) {
                        param.setResult(HIDDEN_VIEW_TYPE)
                    }
                } finally {
                    Trace.endSection()
                }
            }
        }, unhooksList)

        // 2. Hook onCreateViewHolder(ViewGroup parent, int viewType)
        hookAllMethods(chatActivityAdapterClass, "onCreateViewHolder", object : XC_MethodHook(120) {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideGiftCards && !hideGiveawayCards) return
                val args = param.args
                if (args == null || args.size < 2) return
                val viewType = args[1] as? Int ?: return
                if (viewType != HIDDEN_VIEW_TYPE) return

                val parent = args[0] as? ViewGroup ?: return
                Trace.beginSection("LiteGram::gift_cards:onCreateViewHolder")
                try {
                    val lp = try {
                        recyclerViewLayoutParamsConstructor?.newInstance(-1, 0) as? ViewGroup.LayoutParams
                    } catch (_: Throwable) { null } ?: ViewGroup.LayoutParams(-1, 0)

                    val empty = View(parent.context).apply {
                        layoutParams = lp
                        minimumHeight = 0
                        visibility = View.GONE
                    }

                    val holder = try {
                        recyclerListViewHolderConstructor?.newInstance(empty)
                    } catch (_: Throwable) { null }

                    if (holder != null) {
                        param.setResult(holder)
                    }
                } finally {
                    Trace.endSection()
                }
            }
        }, unhooksList)

        // 3. Hook onBindViewHolder(ViewHolder holder, int position)
        hookAllMethods(chatActivityAdapterClass, "onBindViewHolder", object : XC_MethodHook(120) {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideGiftCards && !hideGiveawayCards) return
                val args = param.args
                if (args == null || args.size < 2) return
                val position = args[1] as? Int ?: return
                val adapter = param.thisObject ?: return

                Trace.beginSection("LiteGram::gift_cards:onBindViewHolder")
                try {
                    val msg = getMessage(adapter, position) ?: return
                    val isGift = hideGiftCards && isGiftMessage(msg)
                    val isGiveaway = hideGiveawayCards && isGiveawayMessage(msg)
                    if (isGift || isGiveaway) {
                        param.setResult(null)
                    }
                } finally {
                    Trace.endSection()
                }
            }
        }, unhooksList)
    }
}
