package non.feature.litegram.premium_emoji

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object PremiumEmojiHook {

    @Volatile @JvmStatic var hidePremiumEmojiKeyboard: Boolean = false
    @Volatile @JvmStatic var hidePremiumStickersRecent: Boolean = false
    @Volatile @JvmStatic var hidePremiumStickersGrid: Boolean = false
    @Volatile @JvmStatic var hidePremiumEmojiReactions: Boolean = false
    @Volatile @JvmStatic var hideGroupStickers: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()
    private val isSuppressingReactionPacks = ThreadLocal<Boolean>()

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
            "hidePremiumEmojiKeyboard", "hide_premium_emoji_keyboard" -> hidePremiumEmojiKeyboard = enabled
            "hidePremiumStickersRecent", "hide_premium_stickers_recent" -> hidePremiumStickersRecent = enabled
            "hidePremiumStickersGrid", "hide_premium_stickers_grid" -> hidePremiumStickersGrid = enabled
            "hidePremiumEmojiReactions", "hide_premium_emoji_reactions" -> hidePremiumEmojiReactions = enabled
            "hideGroupStickers", "hide_group_stickers" -> hideGroupStickers = enabled
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
        try {
            isSuppressingReactionPacks.remove()
        } catch (_: Throwable) {}

        messageObjectClass = null
        isPremiumStickerMethod = null
        isAnimatedEmojiMethod = null
        videoThumbsField = null
        thumbTypeField = null
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

    private fun hookAllConstructors(
        clazz: Class<*>?,
        hook: XC_MethodHook,
        targetList: MutableList<XC_MethodHook.Unhook>
    ) {
        if (clazz == null) return
        try {
            val result = XposedBridge.hookAllConstructors(clazz, hook)
            if (result != null) {
                synchronized(targetList) {
                    targetList.addAll(result)
                }
            }
        } catch (_: Throwable) {}
    }

    private fun setPrivateField(obj: Any?, fieldName: String, value: Any?) {
        ReflectionCache.setFieldValue(obj, fieldName, value)
    }

    private fun getPrivateField(obj: Any?, fieldName: String): Any? {
        return ReflectionCache.getFieldValue(obj, fieldName)
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
                videoThumbsField = ReflectionCache.getField(doc.javaClass, "video_thumbs")
            }
            val thumbs = videoThumbsField?.get(doc) as? List<*> ?: return false
            val size = thumbs.size
            for (i in 0 until size) {
                val thumb = thumbs[i] ?: continue
                if (thumbTypeField == null) {
                    thumbTypeField = ReflectionCache.getField(thumb.javaClass, "type")
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
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        messageObjectClass = ReflectionCache.findClass("org.telegram.messenger.MessageObject", cl)
        if (messageObjectClass != null) {
            try {
                val docClz = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$Document", cl)
                if (docClz != null) {
                    isPremiumStickerMethod = ReflectionCache.getMethod(messageObjectClass, "isPremiumSticker", docClz)
                    isAnimatedEmojiMethod = ReflectionCache.getMethod(messageObjectClass, "isAnimatedEmoji", docClz)
                }
            } catch (_: Throwable) {}
        }

        val emojiViewClass = ReflectionCache.findClass("org.telegram.ui.Components.EmojiView", cl)
        val emojiGridAdapterClass = ReflectionCache.findClass("org.telegram.ui.Components.EmojiView\$EmojiGridAdapter", cl)
        val emojiTabsStripClass = ReflectionCache.findClass("org.telegram.ui.Components.EmojiTabsStrip", cl)
        val stickerEmojiCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.StickerEmojiCell", cl)
        val mediaDataControllerClass = ReflectionCache.findClass("org.telegram.messenger.MediaDataController", cl)
        val selectAnimatedEmojiDialogClass = ReflectionCache.findClass("org.telegram.ui.SelectAnimatedEmojiDialog", cl)
        val reactionsContainerLayoutClass = ReflectionCache.findClass("org.telegram.ui.Components.ReactionsContainerLayout", cl)

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
        }, unhooksList)

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
        }, unhooksList)

        // 3. EmojiView.getEmojipacks
        hookAllMethods(emojiViewClass, "getEmojipacks", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                param.setResult(ArrayList<Any>())
            }
        }, unhooksList)

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
        }, unhooksList)

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
        }, unhooksList)

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
        }, unhooksList)

        // 7. EmojiTabsStrip Constructors
        hookAllConstructors(emojiTabsStripClass, object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val args = param.args ?: return
                val isKeyboard = (args.size > 4 && args[4] == true)
                if (isKeyboard && args.size > 5 && args[5] is Boolean) {
                    args[5] = false
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val strip = param.thisObject ?: return
                val emojiTabsField = getPrivateField(strip, "emojiTabs")
                if (emojiTabsField != null) {
                    setPrivateField(strip, "includeAnimated", false)
                }
            }
        }, unhooksList)

        // 8. EmojiTabsStrip.updateEmojiPacks
        hookAllMethods(emojiTabsStripClass, "updateEmojiPacks", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val strip = param.thisObject ?: return
                val emojiTabsField = getPrivateField(strip, "emojiTabs")
                if (emojiTabsField != null) {
                    setPrivateField(strip, "includeAnimated", false)
                    val args = param.args
                    if (args != null && args.isNotEmpty()) {
                        args[0] = ArrayList<Any>()
                    }
                }
            }
        }, unhooksList)

        // 9. EmojiView.addEmojiToRecent (block animated from being saved from keyboard)
        hookAllMethods(emojiViewClass, "addEmojiToRecent", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiKeyboard) return
                val args = param.args ?: return
                if (args.isNotEmpty()) {
                    val item = args[0]
                    if (item is String && item.startsWith("animated_")) {
                        param.setResult(null)
                    }
                }
            }
        }, unhooksList)

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
                    param.setResult(null)
                } else {
                    if (view.visibility != View.VISIBLE) {
                        view.visibility = View.VISIBLE
                    }
                }
            }
        }, unhooksList)

        // 11. MediaDataController.getStickerSets & getFeaturedEmojiSets
        hookAllMethods(mediaDataControllerClass, "getStickerSets", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                val args = param.args ?: return
                if (args.isNotEmpty() && args[0] is Int) {
                    val type = args[0] as Int
                    if (type == 5 && isSuppressingReactionPacks.get() == true) {
                        // TYPE_EMOJIPACKS = 5, ONLY suppressed when updating reaction dialog rows
                        param.setResult(ArrayList<Any>())
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
        }, unhooksList)

        hookAllMethods(mediaDataControllerClass, "getFeaturedEmojiSets", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (isSuppressingReactionPacks.get() == true) {
                    param.setResult(ArrayList<Any>())
                }
            }
        }, unhooksList)

        // 12. SelectAnimatedEmojiDialog.updateRows (reactions window category bar & packs suppression)
        hookAllMethods(selectAnimatedEmojiDialogClass, "updateRows", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiReactions) return
                val dialog = param.thisObject ?: return
                val dtype = getPrivateField(dialog, "type")
                if (dtype is Int && (dtype == 1 || dtype == 8 || dtype == 11)) {
                    isSuppressingReactionPacks.set(true)
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                try {
                    if (!hidePremiumEmojiReactions) return
                    val dialog = param.thisObject ?: return
                    val dtype = getPrivateField(dialog, "type")
                    if (dtype is Int && (dtype == 1 || dtype == 8 || dtype == 11)) {
                        val tabs = getPrivateField(dialog, "emojiTabs") as? View
                        if (tabs != null && tabs.visibility != View.GONE) {
                            tabs.visibility = View.GONE
                        }
                        val shadow = getPrivateField(dialog, "emojiTabsShadow") as? View
                        if (shadow != null && shadow.visibility != View.GONE) {
                            shadow.visibility = View.GONE
                        }
                    }
                } finally {
                    isSuppressingReactionPacks.remove()
                }
            }
        }, unhooksList)

        // 13. ReactionsContainerLayout (quick bar custom emoji reactions)
        val reactionsFilterHook = object : XC_MethodHook() {
            private fun filterReactions(list: ArrayList<*>?) {
                if (list == null) return
                for (i in list.size - 1 downTo 0) {
                    val item = list[i] ?: continue
                    val docId1 = getPrivateField(item, "documentId") as? Long ?: 0L
                    val docId2 = getPrivateField(item, "document_id") as? Long ?: 0L
                    if (docId1 != 0L || docId2 != 0L) {
                        list.removeAt(i)
                    }
                }
            }

            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumEmojiReactions) return
                val layout = param.thisObject ?: return
                filterReactions(getPrivateField(layout, "allReactionsList") as? ArrayList<*>)
                filterReactions(getPrivateField(layout, "visibleReactionsList") as? ArrayList<*>)
            }
        }
        hookAllMethods(reactionsContainerLayoutClass, "showCustomEmojiReactionDialog", reactionsFilterHook, unhooksList)
        hookAllMethods(reactionsContainerLayoutClass, "setMessage", reactionsFilterHook, unhooksList)
        hookAllMethods(reactionsContainerLayoutClass, "setVisibleReactionsList", reactionsFilterHook, unhooksList)
        hookAllConstructors(reactionsContainerLayoutClass, reactionsFilterHook, unhooksList)
    }
}
