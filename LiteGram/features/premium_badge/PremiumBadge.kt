package non.feature.litegram.premium_badge

import android.graphics.drawable.Drawable
import android.view.View
import android.view.ViewGroup
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object PremiumBadgeHook {

    @Volatile @JvmStatic var hidePremiumBadge: Boolean = false
    @Volatile @JvmStatic var hideCollectibleStatus: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    private var userClass: Class<*>? = null
    private var userVerifiedField: Field? = null
    private var chatClass: Class<*>? = null
    private var chatVerifiedField: Field? = null
    private var tlObjectClass: Class<*>? = null

    private var badgeDtoClass: Class<*>? = null
    private var badgesControllerClass: Class<*>? = null
    private var badgesControllerInstanceField: Field? = null
    private var badgesControllerHasBadgeMethod: Method? = null
    private var badgesControllerGetBadgeMethod: Method? = null

    private var premiumGradientClass: Class<*>? = null
    private var premiumGradientGetInstanceMethod: Method? = null
    private var premiumStarMiniField: Field? = null
    private var swapSetMethod: Method? = null

    @JvmStatic
    fun updateSettings(hideBadge: Boolean, hideCollectible: Boolean) {
        hidePremiumBadge = hideBadge
        hideCollectibleStatus = hideCollectible
    }

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hidePremiumBadge", "hide_premium_badge" -> hidePremiumBadge = enabled
            "hideCollectibleStatus", "hide_collectible_status" -> hideCollectibleStatus = enabled
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

        userClass = null
        userVerifiedField = null
        chatClass = null
        chatVerifiedField = null
        tlObjectClass = null
        badgeDtoClass = null
        badgesControllerClass = null
        badgesControllerInstanceField = null
        badgesControllerHasBadgeMethod = null
        badgesControllerGetBadgeMethod = null
        premiumGradientClass = null
        premiumGradientGetInstanceMethod = null
        premiumStarMiniField = null
        swapSetMethod = null
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

    private fun findPremiumGradientClass(cl: ClassLoader): Class<*>? {
        for (pkg in arrayOf(
            "com.exteragram.messenger.utils.PremiumGradient",
            "org.telegram.ui.Components.Premium.PremiumGradient"
        )) {
            val cls = ReflectionCache.findClass(pkg, cl)
            if (cls != null) return cls
        }
        return null
    }

    private fun findStatusBadgeComponentClass(cl: ClassLoader): Class<*>? {
        for (pkg in arrayOf(
            "org.telegram.ui.Components.StatusBadgeComponent",
            "com.exteragram.messenger.ui.StatusBadgeComponent",
            "org.telegram.ui.Components.Reactions.StatusBadgeComponent"
        )) {
            val cls = ReflectionCache.findClass(pkg, cl)
            if (cls != null) return cls
        }
        return null
    }

    private fun hasExteraBadge(obj: Any?): Boolean {
        if (obj == null) return false
        try {
            if (badgesControllerClass == null) return false
            val instance = badgesControllerInstanceField?.get(null) ?: return false
            if (badgesControllerHasBadgeMethod != null) {
                val res = badgesControllerHasBadgeMethod!!.invoke(instance, obj)
                if (res is Boolean && res) return true
            }
            if (badgesControllerGetBadgeMethod != null) {
                val res = badgesControllerGetBadgeMethod!!.invoke(instance, obj)
                if (res != null) return true
            }
        } catch (_: Throwable) {}
        return false
    }

    private fun isVerified(obj: Any?): Boolean {
        if (obj == null) return false
        try {
            if (userClass != null && userClass!!.isInstance(obj)) {
                if (userVerifiedField != null && userVerifiedField!!.getBoolean(obj)) return true
            }
            if (chatClass != null && chatClass!!.isInstance(obj)) {
                if (chatVerifiedField != null && chatVerifiedField!!.getBoolean(obj)) return true
            }
        } catch (_: Throwable) {}
        return false
    }

    private fun getPremiumStarMini(clazz: Class<*>): Any? {
        try {
            if (premiumGradientGetInstanceMethod == null) {
                premiumGradientGetInstanceMethod = ReflectionCache.getMethod(clazz, "getInstance")
            }
            val instance = premiumGradientGetInstanceMethod?.invoke(null) ?: return null
            if (premiumStarMiniField == null) {
                premiumStarMiniField = ReflectionCache.getField(clazz, "premiumStarDrawableMini")
            }
            return premiumStarMiniField?.get(instance)
        } catch (_: Throwable) {
            return null
        }
    }

    private fun setDrawableNull(drawable: Any) {
        try {
            if (swapSetMethod != null) {
                swapSetMethod!!.invoke(drawable, null, false)
                return
            }
        } catch (_: Throwable) {}
        try {
            val m = ReflectionCache.getMethod(drawable.javaClass, "set", Drawable::class.java, Boolean::class.javaPrimitiveType)
            if (m != null) {
                swapSetMethod = m
                m.invoke(drawable, null, false)
            }
        } catch (_: Throwable) {}
    }

    private fun cleanupCollectibleHint(activity: Any) {
        try {
            val hint = ReflectionCache.getFieldValue(activity, "collectibleHint")
            if (hint != null) {
                try {
                    hint.javaClass.getMethod("hide").invoke(hint)
                } catch (_: Throwable) {}
                try {
                    val container = ReflectionCache.getFieldValue(activity, "avatarContainer2")
                    if (container is ViewGroup && hint is View) {
                        hint.visibility = View.GONE
                        container.removeView(hint)
                    }
                } catch (_: Throwable) {}
            }
            val container = ReflectionCache.getFieldValue(activity, "avatarContainer2")
            if (container is ViewGroup) {
                for (i in container.childCount - 1 downTo 0) {
                    val child = container.getChildAt(i)
                    if (child != null && child.javaClass.name.contains("HintView")) {
                        child.visibility = View.GONE
                        container.removeViewAt(i)
                    }
                }
            }
            ReflectionCache.setFieldValue(activity, "collectibleHint", null)
            ReflectionCache.setFieldValue(activity, "collectibleHintVisible", false)
        } catch (_: Throwable) {}
    }

    private fun disableParticles(drawable: Any?) {
        if (drawable == null) return
        try {
            val m = ReflectionCache.getMethod(
                drawable.javaClass,
                "setParticles",
                Boolean::class.javaPrimitiveType,
                Boolean::class.javaPrimitiveType
            )
            if (m != null) {
                m.invoke(drawable, false, true)
                return
            }
        } catch (_: Throwable) {}
        try {
            for (m in drawable.javaClass.methods) {
                if (m.name == "setParticles") {
                    if (m.parameterTypes.size == 2) {
                        m.invoke(drawable, false, true)
                        return
                    } else if (m.parameterTypes.size == 1 && m.parameterTypes[0] == Boolean::class.javaPrimitiveType) {
                        m.invoke(drawable, false)
                        return
                    }
                }
            }
        } catch (_: Throwable) {}
        try {
            for (f in drawable.javaClass.declaredFields) {
                if (f.name.contains("particle", ignoreCase = true)) {
                    f.isAccessible = true
                    if (f.type == Boolean::class.javaPrimitiveType) {
                        f.setBoolean(drawable, false)
                    } else if (!f.type.isPrimitive) {
                        f.set(drawable, null)
                    }
                }
            }
        } catch (_: Throwable) {}
    }

    private fun clearRightDrawableFromView(view: Any?) {
        if (view == null) return
        try {
            val getRightMethod = ReflectionCache.getMethod(view.javaClass, "getRightDrawable")
            if (getRightMethod != null) {
                val right = getRightMethod.invoke(view)
                if (right != null) {
                    val rightClsName = right.javaClass.name
                    if (rightClsName.contains("SwapAnimatedEmojiDrawable") ||
                        rightClsName.contains("AnimatedEmojiDrawable") ||
                        rightClsName.contains("Status") ||
                        rightClsName.contains("Premium")
                    ) {
                        disableParticles(right)
                        setDrawableNull(right)

                        val setRightMethod = ReflectionCache.getMethod(
                            view.javaClass,
                            "setRightDrawable",
                            Drawable::class.java
                        )
                        if (setRightMethod != null) {
                            setRightMethod.invoke(view, null as Drawable?)
                        } else {
                            for (m in view.javaClass.methods) {
                                if (m.name == "setRightDrawable" && m.parameterTypes.size == 1) {
                                    m.invoke(view, null as Drawable?)
                                    break
                                }
                            }
                        }

                        val rf = ReflectionCache.getField(view.javaClass, "rightDrawable")
                        if (rf != null && rf.get(view) != null) {
                            (rf.get(view) as? Drawable)?.callback = null
                            rf.set(view, null)
                            (view as? View)?.invalidate()
                        }
                    }
                }
                return
            }
        } catch (_: Throwable) {}

        try {
            if (view is android.widget.TextView) {
                val drawables = view.compoundDrawables
                if (drawables.size > 2 && drawables[2] != null) {
                    val right = drawables[2]
                    val rightClsName = right.javaClass.name
                    if (rightClsName.contains("SwapAnimatedEmojiDrawable") ||
                        rightClsName.contains("AnimatedEmojiDrawable") ||
                        rightClsName.contains("Status") ||
                        rightClsName.contains("Premium")
                    ) {
                        disableParticles(right)
                        setDrawableNull(right)
                        view.setCompoundDrawablesWithIntrinsicBounds(drawables[0], drawables[1], null, drawables[3])
                    }
                }
            }
        } catch (_: Throwable) {}
    }

    private fun cleanDrawerItem(obj: Any?) {
        if (!hidePremiumBadge) return
        if (obj == null) return
        try {
            for (fName in arrayOf("premiumStatusDrawable", "emojiStatusDrawable", "statusDrawable")) {
                val drawable = ReflectionCache.getFieldValue(obj, fName)
                if (drawable != null) {
                    disableParticles(drawable)
                    setDrawableNull(drawable)
                }
            }

            for (f in obj.javaClass.declaredFields) {
                val fname = f.name
                if (fname.contains("statusDrawable", ignoreCase = true) ||
                    fname.contains("premiumStatus", ignoreCase = true) ||
                    fname.contains("emojiStatus", ignoreCase = true)
                ) {
                    try {
                        f.isAccessible = true
                        val drawable = f.get(obj)
                        if (drawable != null) {
                            disableParticles(drawable)
                            setDrawableNull(drawable)
                        }
                    } catch (_: Throwable) {}
                }
            }

            for (fName in arrayOf("nameTextView", "titleTextView", "textView", "nameView", "titleView")) {
                val tv = ReflectionCache.getFieldValue(obj, fName)
                if (tv != null) {
                    clearRightDrawableFromView(tv)
                }
            }

            if (obj is ViewGroup) {
                for (i in 0 until obj.childCount) {
                    val child = obj.getChildAt(i) ?: continue
                    clearRightDrawableFromView(child)
                }
            }
        } catch (_: Throwable) {}
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        userClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$User", cl)
        if (userClass != null) {
            userVerifiedField = ReflectionCache.getField(userClass, "verified")
        }
        chatClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$Chat", cl)
        if (chatClass != null) {
            chatVerifiedField = ReflectionCache.getField(chatClass, "verified")
        }
        tlObjectClass = ReflectionCache.findClass("org.telegram.tgnet.TLObject", cl)

        badgeDtoClass = ReflectionCache.findClass("com.exteragram.messenger.api.dto.BadgeDTO", cl)
        badgesControllerClass = ReflectionCache.findClass("com.exteragram.messenger.badges.BadgesController", cl)
        if (badgesControllerClass != null) {
            badgesControllerInstanceField = ReflectionCache.getField(badgesControllerClass, "INSTANCE")
            if (tlObjectClass != null) {
                badgesControllerHasBadgeMethod = ReflectionCache.getMethod(badgesControllerClass, "hasBadge", tlObjectClass!!)
                badgesControllerGetBadgeMethod = ReflectionCache.getMethod(badgesControllerClass, "getBadge", tlObjectClass!!)
            }
            if (badgesControllerHasBadgeMethod == null) {
                for (m in badgesControllerClass!!.methods) {
                    if (m.name == "hasBadge" && m.parameterTypes.size == 1) {
                        badgesControllerHasBadgeMethod = m
                        break
                    }
                }
            }
            if (badgesControllerGetBadgeMethod == null) {
                for (m in badgesControllerClass!!.methods) {
                    if (m.name == "getBadge" && m.parameterTypes.size == 1) {
                        badgesControllerGetBadgeMethod = m
                        break
                    }
                }
            }
        }

        premiumGradientClass = findPremiumGradientClass(cl)

        val userObjectClass = ReflectionCache.findClass("org.telegram.messenger.UserObject", cl)
        val dialogObjectClass = ReflectionCache.findClass("org.telegram.messenger.DialogObject", cl)
        val messagesControllerClass = ReflectionCache.findClass("org.telegram.messenger.MessagesController", cl)
        val chatMessageCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.ChatMessageCell", cl)
        val swapAnimatedEmojiDrawableClass = ReflectionCache.findClass("org.telegram.ui.Components.AnimatedEmojiDrawable\$SwapAnimatedEmojiDrawable", cl)
        val statusBadgeComponentClass = findStatusBadgeComponentClass(cl)
        val drawerHeaderViewClass = ReflectionCache.findClass("com.exteragram.messenger.drawer.DrawerHeaderView", cl)
        val accountRowViewClass = ReflectionCache.findClass("com.exteragram.messenger.drawer.DrawerAccountPickerView\$AccountRowView", cl)
        val drawerProfileCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.DrawerProfileCell", cl)
        val drawerUserCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.DrawerUserCell", cl)
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)

        // 1. UserObject.getEmojiStatusDocumentId -> null
        hookAllMethods(userObjectClass, "getEmojiStatusDocumentId", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.setResult(null)
            }
        }, unhooksList)

        // 2. DialogObject.getEmojiStatusDocumentId -> 0 (only for EmojiStatus, preserve dialogId routing)
        hookAllMethods(dialogObjectClass, "getEmojiStatusDocumentId", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val args = param.args
                if (args != null && args.isNotEmpty()) {
                    val first = args[0]
                    if (first is Long) return
                }
                param.setResult(0L)
            }
        }, unhooksList)

        // 3. DialogObject.isEmojiStatusCollectible -> false (only when hiding premium badges)
        hookAllMethods(dialogObjectClass, "isEmojiStatusCollectible", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val args = param.args
                if (args != null && args.isNotEmpty()) {
                    val first = args[0]
                    if (first is Long) return
                }
                param.setResult(false)
            }
        }, unhooksList)

        // 4. MessagesController.isPremiumUser -> false (exclude self to protect account capabilities/sync)
        hookAllMethods(messagesControllerClass, "isPremiumUser", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val user = param.args?.getOrNull(0) ?: return
                val isSelf = ReflectionCache.getFieldValue(user, "self")
                if (isSelf == true) return
                param.setResult(false)
            }
        }, unhooksList)

        // 5. ChatMessageCell.getAuthorStatus
        hookAllMethods(chatMessageCellClass, "getAuthorStatus", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (hideCollectibleStatus || hidePremiumBadge) {
                    val obj = param.thisObject
                    if (obj != null) {
                        try {
                            ReflectionCache.setFieldValue(obj, "nameStatusSlug", null)
                        } catch (_: Throwable) {}
                    }
                }
                if (!hidePremiumBadge) return
                val res = param.result ?: return
                if (badgeDtoClass != null && badgeDtoClass!!.isInstance(res)) {
                    return
                }
                val clsName = res.javaClass.name
                if (clsName.contains("Badge")) {
                    return
                }
                if (res is Number) {
                    param.result = null
                    return
                }
                if (clsName.contains("Drawable") || clsName.contains("Long") || clsName.contains("Integer") || clsName.contains("Number")) {
                    param.result = null
                }
            }
        }, unhooksList)

        // 6. SwapAnimatedEmojiDrawable.set
        hookAllMethods(swapAnimatedEmojiDrawableClass, "set", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val args = param.args ?: return
                if (args.isEmpty()) return
                val arg = args[0] ?: return
                val clsName = arg.javaClass.name
                if (clsName.contains("Drawable")) {
                    val lower = clsName.lowercase()
                    if (clsName.contains("Premium") || clsName.contains("Star") || lower.contains("liststar")) {
                        args[0] = null
                        return
                    }
                    if (premiumGradientClass != null) {
                        val star = getPremiumStarMini(premiumGradientClass!!)
                        if (star != null && (arg == star || (arg is Drawable && star is Drawable && arg.constantState != null && arg.constantState == star.constantState))) {
                            args[0] = null
                            return
                        }
                    }
                }
            }
        }, unhooksList)

        // 6.1 SwapAnimatedEmojiDrawable.setParticles
        hookAllMethods(swapAnimatedEmojiDrawableClass, "setParticles", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val args = param.args
                if (args != null && args.isNotEmpty() && args[0] == true) {
                    args[0] = false
                }
            }
        }, unhooksList)

        // 7. StatusBadgeComponent.updateDrawable
        hookAllMethods(statusBadgeComponentClass, "updateDrawable", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val args = param.args ?: return
                var targetObj: Any? = null
                for (arg in args) {
                    if (arg != null && ((userClass != null && userClass!!.isInstance(arg)) || (chatClass != null && chatClass!!.isInstance(arg)))) {
                        targetObj = arg
                        break
                    }
                }
                if (targetObj != null) {
                    if (isVerified(targetObj) || hasExteraBadge(targetObj)) {
                        return
                    }

                    val res = param.result ?: return
                    val resCls = res.javaClass.name
                    if (resCls.contains("Verified") || resCls.contains("Combined")) {
                        return
                    }
                    setDrawableNull(res)
                }
            }
        }, unhooksList)

        // 8. DrawerHeaderView & AccountRowView & DrawerProfileCell & DrawerUserCell
        val drawerHook = object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                val obj = param.thisObject ?: return
                cleanDrawerItem(obj)
            }
        }
        hookAllMethods(drawerHeaderViewClass, "updateUserInfo", drawerHook, unhooksList)
        hookAllMethods(drawerHeaderViewClass, "setUser", drawerHook, unhooksList)
        hookAllMethods(accountRowViewClass, "bind", drawerHook, unhooksList)
        hookAllMethods(accountRowViewClass, "setAccount", drawerHook, unhooksList)
        hookAllMethods(drawerProfileCellClass, "setUser", drawerHook, unhooksList)
        hookAllMethods(drawerUserCellClass, "setAccount", drawerHook, unhooksList)
        hookAllMethods(drawerUserCellClass, "didReceivedNotification", drawerHook, unhooksList)

        // 9. ProfileActivity.setCollectibleGiftStatus
        hookAllMethods(profileActivityClass, "setCollectibleGiftStatus", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus && !hidePremiumBadge) return
                val obj = param.thisObject ?: return
                cleanupCollectibleHint(obj)
                val statusArg = param.args?.getOrNull(0)
                try {
                    ReflectionCache.setFieldValue(obj, "collectibleStatus", statusArg)
                } catch (_: Throwable) {}
                param.setResult(null)
            }
        }, unhooksList)

        // 9.1 ProfileActivity.updateCollectibleHint
        hookAllMethods(profileActivityClass, "updateCollectibleHint", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus && !hidePremiumBadge) return
                val obj = param.thisObject ?: return
                cleanupCollectibleHint(obj)
                param.setResult(null)
            }
        }, unhooksList)

        // 9.2 ProfileActivity.updateProfileData
        hookAllMethods(profileActivityClass, "updateProfileData", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus && !hidePremiumBadge) return
                val obj = param.thisObject ?: return
                cleanupCollectibleHint(obj)
            }
        }, unhooksList)

        // 9.3 ProfileActivity onFragmentResume & onTransitionAnimationEnd
        val resumeHook = object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus && !hidePremiumBadge) return
                val obj = param.thisObject ?: return
                cleanupCollectibleHint(obj)
            }
        }
        hookAllMethods(profileActivityClass, "onFragmentResume", resumeHook, unhooksList)
        hookAllMethods(profileActivityClass, "onTransitionAnimationEnd", resumeHook, unhooksList)

        // 9.4 ProfileActivity$TopView.setBackgroundEmojiId
        val topViewClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity\$TopView", cl)
        if (topViewClass != null) {
            hookAllMethods(topViewClass, "setBackgroundEmojiId", object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumBadge) return
                    val args = param.args ?: return
                    if (args.size > 1 && args[1] is Boolean) {
                        args[1] = false
                    }
                }
            }, unhooksList)
        }

        // 10. ProfileActivity.getEmojiStatusDrawable
        hookAllMethods(profileActivityClass, "getEmojiStatusDrawable", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hidePremiumBadge) {
                    param.setResult(null)
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val obj = param.thisObject
                if (obj != null) {
                    try {
                        ReflectionCache.setFieldValue(obj, "emojiStatusGiftId", null)
                    } catch (_: Throwable) {}
                }
                val res = param.result ?: return
                try {
                    val m = ReflectionCache.getMethod(res.javaClass, "setParticles", Boolean::class.javaPrimitiveType, Boolean::class.javaPrimitiveType)
                    if (m != null) {
                        m.invoke(res, false, true)
                    } else {
                        val fallback = res.javaClass.getMethod("setParticles", Boolean::class.javaPrimitiveType, Boolean::class.javaPrimitiveType)
                        fallback.invoke(res, false, true)
                    }
                } catch (_: Throwable) {}
            }
        }, unhooksList)
    }
}
