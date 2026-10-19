package non.feature.litegram.premium_emoji

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList

object PremiumEmojiHook {

    @Volatile @JvmStatic var hidePremiumEmojiKeyboard: Boolean = false
    @Volatile @JvmStatic var hidePremiumStickersRecent: Boolean = false
    @Volatile @JvmStatic var hidePremiumStickersGrid: Boolean = false
    @Volatile @JvmStatic var hidePremiumEmojiReactions: Boolean = false
    @Volatile @JvmStatic var hideGroupStickers: Boolean = false

    private val unhooks = ArrayList<XC_MethodHook.Unhook>()

    private var messageObjectClass: Class<*>? = null
    private var isPremiumStickerMethod: Method? = null
    private var isAnimatedEmojiMethod: Method? = null

    private var videoThumbsField: Field? = null
    private var thumbTypeField: Field? = null

    @JvmStatic
    fun updateSettings(
        hideEmojiKeyboard: Boolean,
        hideStickersRecent: Boolean,
        hideStickersGrid: Boolean,
        hideEmojiReactions: Boolean,
        hideGroup: Boolean
    ) {
        hidePremiumEmojiKeyboard = hideEmojiKeyboard
        hidePremiumStickersRecent = hideStickersRecent
        hidePremiumStickersGrid = hideStickersGrid
        hidePremiumEmojiReactions = hideEmojiReactions
        hideGroupStickers = hideGroup
    }

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hidePremiumEmojiKeyboard" -> hidePremiumEmojiKeyboard = enabled
            "hidePremiumStickersRecent" -> hidePremiumStickersRecent = enabled
            "hidePremiumStickersGrid" -> hidePremiumStickersGrid = enabled
            "hidePremiumEmojiReactions" -> hidePremiumEmojiReactions = enabled
            "hideGroupStickers" -> hideGroupStickers = enabled
        }
    }

    @JvmStatic
    fun unload() {
        synchronized(unhooks) {
            for (u in unhooks) {
                try {
                    u.unhook()
                } catch (_: Throwable) {}
            }
            unhooks.clear()
        }
    }

    private fun findClass(name: String, cl: ClassLoader): Class<*>? {
        return try {
            Class.forName(name, false, cl)
        } catch (_: Throwable) {
            null
        }
    }

    private fun hookAllMethods(clazz: Class<*>?, methodName: String, hook: XC_MethodHook) {
        if (clazz == null) return
        try {
            val result = XposedBridge.hookAllMethods(clazz, methodName, hook)
            if (result != null) {
                synchronized(unhooks) {
                    unhooks.addAll(result)
                }
            }
        } catch (_: Throwable) {}
    }

    private fun hookAllConstructors(clazz: Class<*>?, hook: XC_MethodHook) {
        if (clazz == null) return
        try {
            val result = XposedBridge.hookAllConstructors(clazz, hook)
            if (result != null) {
                synchronized(unhooks) {
                    unhooks.addAll(result)
                }
            }
        } catch (_: Throwable) {}
    }

    private fun setPrivateField(obj: Any?, fieldName: String, value: Any?) {
        if (obj == null) return
        try {
            var cls: Class<*>? = obj.javaClass
            while (cls != null) {
                try {
                    val field = cls.getDeclaredField(fieldName)
                    field.isAccessible = true
                    field.set(obj, value)
                    return
                } catch (_: NoSuchFieldException) {
                    cls = cls.superclass
                }
            }
        } catch (_: Throwable) {}
    }

    private fun getPrivateField(obj: Any?, fieldName: String): Any? {
        if (obj == null) return null
        try {
            var cls: Class<*>? = obj.javaClass
            while (cls != null) {
                try {
                    val field = cls.getDeclaredField(fieldName)
                    field.isAccessible = true
                    return field.get(obj)
                } catch (_: NoSuchFieldException) {
                    cls = cls.superclass
                }
            }
        } catch (_: Throwable) {}
        return null
    }

    fun isPremiumSticker(doc: Any?): Boolean {
        if (doc == null) return false
        try {
            if (isPremiumStickerMethod != null) {
                val res = isPremiumStickerMethod!!.invoke(null, doc)
                if (res is Boolean) return res
            }
        } catch (_: Throwable) {}

        try {
            if (videoThumbsField == null) {
                videoThumbsField = doc.javaClass.getField("video_thumbs")
            }
            val thumbs = videoThumbsField?.get(doc) as? List<*> ?: return false
            val size = thumbs.size
            for (i in 0 until size) {
                val thumb = thumbs[i] ?: continue
                if (thumbTypeField == null) {
                    thumbTypeField = thumb.javaClass.getField("type")
                }
                val type = thumbTypeField?.get(thumb)
                if ("f" == type) {
                    return true
                }
            }
        } catch (_: Throwable) {}
        return false
    }

    fun isNonStockEmoji(item: Any?): Boolean {
        if (item == null) return false
        if (item is String) {
            return item.startsWith("animated_")
        }
        try {
            if (isAnimatedEmojiMethod != null) {
                val res = isAnimatedEmojiMethod!!.invoke(null, item)
                if (res is Boolean) return res
            }
        } catch (_: Throwable) {}
        return false
    }

    @JvmStatic
    fun init(cl: ClassLoader) {
        messageObjectClass = findClass("org.telegram.messenger.MessageObject", cl)
        if (messageObjectClass != null) {
            try {
                val docClz = findClass("org.telegram.tgnet.TLRPC\$Document", cl)
                if (docClz != null) {
                    isPremiumStickerMethod = messageObjectClass!!.getMethod("isPremiumSticker", docClz)
                    isAnimatedEmojiMethod = messageObjectClass!!.getMethod("isAnimatedEmoji", docClz)
                }
            } catch (_: Throwable) {}
        }

        val emojiViewClass = findClass("org.telegram.ui.Components.EmojiView", cl)
        val emojiGridAdapterClass = findClass("org.telegram.ui.Components.EmojiView\$EmojiGridAdapter", cl)
        val emojiTabsStripClass = findClass("org.telegram.ui.Components.EmojiTabsStrip", cl)
        val emojiClass = findClass("org.telegram.messenger.Emoji", cl)
        val stickerEmojiCellClass = findClass("org.telegram.ui.Cells.StickerEmojiCell", cl)
        val mediaDataControllerClass = findClass("org.telegram.messenger.MediaDataController", cl)
        val selectAnimatedEmojiDialogClass = findClass("org.telegram.ui.SelectAnimatedEmojiDialog", cl)
        val reactionsContainerLayoutClass = findClass("org.telegram.ui.Components.ReactionsContainerLayout", cl)

        // 1. EmojiView Constructor Hook
        hookAllConstructors(emojiViewClass, object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val args = param.args ?: return
                if (args.size > 1 && args[1] is Boolean) {
                    args[1] = false
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val view = param.thisObject ?: return
                setPrivateField(view, "allowAnimatedEmoji", false)
                setPrivateField(view, "allowEmojisForNonPremium", false)
            }
        })

        // 2. EmojiView.getRecentEmoji
        hookAllMethods(emojiViewClass, "getRecentEmoji", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val recent = param.result as? ArrayList<*> ?: return
                val size = recent.size
                if (size == 0) return
                var hasCustom = false
                for (i in 0 until size) {
                    val item = recent[i]
                    if (item is String && item.startsWith("animated_")) {
                        hasCustom = true
                        break
                    }
                }
                if (!hasCustom) return
                val filtered = ArrayList<Any>(size)
                for (i in 0 until size) {
                    val item = recent[i] ?: continue
                    if (item is String && item.startsWith("animated_")) continue
                    filtered.add(item)
                }
                param.result = filtered
            }
        })

        // 3. EmojiView.getEmojipacks
        hookAllMethods(emojiViewClass, "getEmojipacks", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                param.result = ArrayList<Any>()
            }
        })

        // 4. EmojiView.checkDocuments (clean recent/favourite stickers)
        hookAllMethods(emojiViewClass, "checkDocuments", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumStickersRecent) return
                val view = param.thisObject ?: return
                for (field in arrayOf("favouriteStickers", "recentStickers")) {
                    val list = getPrivateField(view, field) as? ArrayList<*> ?: continue
                    for (i in list.size - 1 downTo 0) {
                        if (isPremiumSticker(list[i])) {
                            list.removeAt(i)
                        }
                    }
                }
            }
        })

        // 5. EmojiGridAdapter.processEmoji
        hookAllMethods(emojiGridAdapterClass, "processEmoji", object : XC_MethodHook() {
            private fun clean(adapter: Any?) {
                if (adapter == null) return
                val emojiView = getPrivateField(adapter, "this$0")
                if (emojiView != null) {
                    setPrivateField(emojiView, "allowAnimatedEmoji", false)
                    setPrivateField(emojiView, "allowEmojisForNonPremium", false)
                    val packs = getPrivateField(emojiView, "emojipacksProcessed") as? ArrayList<*>
                    packs?.clear()
                }
                val frozen = getPrivateField(adapter, "frozenEmojiPacks") as? ArrayList<*>
                frozen?.clear()
            }

            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                clean(param.thisObject)
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                clean(param.thisObject)
            }
        })

        // 6. EmojiGridAdapter.updateRows
        hookAllMethods(emojiGridAdapterClass, "updateRows", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val adapter = param.thisObject ?: return
                setPrivateField(adapter, "trendingHeaderRow", -1)
                setPrivateField(adapter, "trendingRow", -1)
                setPrivateField(adapter, "recentlyUsedHeaderRow", -1)
                val emojiView = getPrivateField(adapter, "this$0")
                if (emojiView != null) {
                    val packs = getPrivateField(emojiView, "emojipacksProcessed") as? ArrayList<*>
                    packs?.clear()
                }
            }
        })

        // 7. EmojiTabsStrip Constructors
        hookAllConstructors(emojiTabsStripClass, object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val args = param.args ?: return
                var isKeyboard = false
                if (args.size > 6 && args[6] is Int) {
                    isKeyboard = (args[6] as Int) == 0
                } else if (args.size > 4 && args[4] == true) {
                    isKeyboard = true
                }
                if (isKeyboard && args.size > 5 && args[5] is Boolean) {
                    args[5] = false
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val strip = param.thisObject ?: return
                val currentType = getPrivateField(strip, "currentType")
                if (currentType is Int && currentType == 0) {
                    setPrivateField(strip, "includeAnimated", false)
                }
            }
        })

        // 8. EmojiTabsStrip.updateEmojiPacks
        hookAllMethods(emojiTabsStripClass, "updateEmojiPacks", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val strip = param.thisObject ?: return
                val currentType = getPrivateField(strip, "currentType")
                if (currentType is Int && currentType == 0) {
                    setPrivateField(strip, "includeAnimated", false)
                    val args = param.args
                    if (args != null && args.isNotEmpty()) {
                        args[0] = ArrayList<Any>()
                    }
                }
            }
        })

        // 9. Emoji.addRecentEmoji (block animated from being saved)
        hookAllMethods(emojiClass, "addRecentEmoji", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val args = param.args ?: return
                if (args.isNotEmpty()) {
                    val item = args[0]
                    if (item is String && item.startsWith("animated_")) {
                        param.result = null
                    }
                }
            }
        })

        // 10. StickerEmojiCell.setSticker (ZERO-LAG high performance recycling cell hook)
        hookAllMethods(stickerEmojiCellClass, "setSticker", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumStickersGrid) return
                val args = param.args ?: return
                if (args.isEmpty()) return
                val doc = args[0]
                val view = param.thisObject as? View ?: return
                if (isPremiumSticker(doc)) {
                    if (view.visibility != View.GONE) {
                        view.visibility = View.GONE
                    }
                    param.result = null
                } else {
                    if (view.visibility != View.VISIBLE) {
                        view.visibility = View.VISIBLE
                    }
                }
            }
        })

        // 11. MediaDataController.getStickerSets & getFeaturedEmojiSets
        hookAllMethods(mediaDataControllerClass, "getStickerSets", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                val args = param.args ?: return
                if (args.isNotEmpty() && args[0] is Int) {
                    val type = args[0] as Int
                    if (type == 5 && hidePremiumEmojiKeyboard) {
                        // TYPE_EMOJIPACKS = 5
                        param.result = ArrayList<Any>()
                    }
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                val args = param.args ?: return
                if (args.isNotEmpty() && args[0] is Int) {
                    val type = args[0] as Int
                    if (type == 3 && hidePremiumStickersGrid) {
                        // TYPE_FEATURED = 3
                        val list = param.result as? ArrayList<*> ?: return
                        for (i in list.size - 1 downTo 0) {
                            val pack = list[i] ?: continue
                            val cover = getPrivateField(pack, "cover")
                            if (cover != null && isPremiumSticker(cover)) {
                                list.removeAt(i)
                            }
                        }
                    }
                }
            }
        })

        hookAllMethods(mediaDataControllerClass, "getFeaturedEmojiSets", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hidePremiumEmojiKeyboard) {
                    param.result = ArrayList<Any>()
                }
            }
        })

        // 12. SelectAnimatedEmojiDialog.updateRows (reactions window category bar)
        hookAllMethods(selectAnimatedEmojiDialogClass, "updateRows", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                val dialog = param.thisObject ?: return
                val dtype = getPrivateField(dialog, "type")
                if (dtype is Int && (dtype == 1 || dtype == 8 || dtype == 11) && hidePremiumEmojiReactions) {
                    val tabs = getPrivateField(dialog, "emojiTabs") as? View
                    if (tabs != null && tabs.visibility != View.GONE) {
                        tabs.visibility = View.GONE
                    }
                    val shadow = getPrivateField(dialog, "emojiTabsShadow") as? View
                    if (shadow != null && shadow.visibility != View.GONE) {
                        shadow.visibility = View.GONE
                    }
                    val packs = getPrivateField(dialog, "packs") as? ArrayList<*>
                    packs?.clear()
                }
            }
        })

        // 13. ReactionsContainerLayout (quick bar custom emoji reactions)
        val reactionsFilterHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiReactions) return
                val layout = param.thisObject ?: return
                val allReactions = getPrivateField(layout, "allReactionsList") as? ArrayList<*> ?: return
                for (i in allReactions.size - 1 downTo 0) {
                    val item = allReactions[i] ?: continue
                    val docId1 = getPrivateField(item, "documentId") as? Long ?: 0L
                    val docId2 = getPrivateField(item, "document_id") as? Long ?: 0L
                    if (docId1 != 0L || docId2 != 0L) {
                        allReactions.removeAt(i)
                    }
                }
            }
        }
        hookAllMethods(reactionsContainerLayoutClass, "showCustomEmojiReactionDialog", reactionsFilterHook)
        hookAllConstructors(reactionsContainerLayoutClass, reactionsFilterHook)
    }
}
