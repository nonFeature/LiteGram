package non.feature.litegram.premium_badge

import android.graphics.drawable.Drawable
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

    private fun hasExteraBadge(user: Any): Boolean {
        try {
            if (badgesControllerClass == null) return false
            val instance = badgesControllerInstanceField?.get(null) ?: return false
            if (badgesControllerHasBadgeMethod != null) {
                val res = badgesControllerHasBadgeMethod!!.invoke(instance, user)
                if (res is Boolean && res) return true
            }
            if (badgesControllerGetBadgeMethod != null) {
                val res = badgesControllerGetBadgeMethod!!.invoke(instance, user)
                if (res != null) return true
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

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        userClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$User", cl)
        if (userClass != null) {
            userVerifiedField = ReflectionCache.getField(userClass, "verified")
        }

        badgeDtoClass = ReflectionCache.findClass("com.exteragram.messenger.api.dto.BadgeDTO", cl)
        badgesControllerClass = ReflectionCache.findClass("com.exteragram.messenger.badges.BadgesController", cl)
        if (badgesControllerClass != null) {
            badgesControllerInstanceField = ReflectionCache.getField(badgesControllerClass, "INSTANCE")
            if (userClass != null) {
                badgesControllerHasBadgeMethod = ReflectionCache.getMethod(badgesControllerClass, "hasBadge", userClass!!)
                badgesControllerGetBadgeMethod = ReflectionCache.getMethod(badgesControllerClass, "getBadge", userClass!!)
            }
        }

        premiumGradientClass = findPremiumGradientClass(cl)

        val userObjectClass = ReflectionCache.findClass("org.telegram.messenger.UserObject", cl)
        val dialogObjectClass = ReflectionCache.findClass("org.telegram.messenger.DialogObject", cl)
        val messageObjectClass = ReflectionCache.findClass("org.telegram.messenger.MessageObject", cl)
        val messagesControllerClass = ReflectionCache.findClass("org.telegram.messenger.MessagesController", cl)
        val chatMessageCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.ChatMessageCell", cl)
        val swapAnimatedEmojiDrawableClass = ReflectionCache.findClass("org.telegram.ui.Components.AnimatedEmojiDrawable\$SwapAnimatedEmojiDrawable", cl)
        val statusBadgeComponentClass = findStatusBadgeComponentClass(cl)
        val drawerHeaderViewClass = ReflectionCache.findClass("com.exteragram.messenger.drawer.DrawerHeaderView", cl)
        val accountRowViewClass = ReflectionCache.findClass("com.exteragram.messenger.drawer.DrawerAccountPickerView\$AccountRowView", cl)
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)

        // 1. UserObject.getEmojiStatusDocumentId -> null
        hookAllMethods(userObjectClass, "getEmojiStatusDocumentId", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.result = null
            }
        }, unhooksList)

        // 2. DialogObject & MessageObject.getEmojiStatusDocumentId -> 0
        val zeroHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.result = 0L
            }
        }
        hookAllMethods(dialogObjectClass, "getEmojiStatusDocumentId", zeroHook, unhooksList)
        hookAllMethods(messageObjectClass, "getEmojiStatusDocumentId", zeroHook, unhooksList)

        // 3. isEmojiStatusCollectible -> false (when hidePremiumBadge OR hideCollectibleStatus)
        val isCollectibleHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hidePremiumBadge || hideCollectibleStatus) {
                    param.result = false
                }
            }
        }
        hookAllMethods(userObjectClass, "isEmojiStatusCollectible", isCollectibleHook, unhooksList)
        hookAllMethods(dialogObjectClass, "isEmojiStatusCollectible", isCollectibleHook, unhooksList)
        hookAllMethods(messageObjectClass, "isEmojiStatusCollectible", isCollectibleHook, unhooksList)

        // 4. MessagesController.isPremiumUser -> false
        hookAllMethods(messagesControllerClass, "isPremiumUser", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.result = false
            }
        }, unhooksList)

        // 5. ChatMessageCell.getAuthorStatus
        hookAllMethods(chatMessageCellClass, "getAuthorStatus", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val res = param.result ?: return
                if (badgeDtoClass != null && badgeDtoClass!!.isInstance(res)) {
                    return
                }
                if (res is Number) {
                    param.result = null
                    return
                }
                val clsName = res.javaClass.name
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

        // 7. StatusBadgeComponent.updateDrawable
        hookAllMethods(statusBadgeComponentClass, "updateDrawable", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val args = param.args ?: return
                var user: Any? = null
                if (userClass != null) {
                    for (arg in args) {
                        if (arg != null && userClass!!.isInstance(arg)) {
                            user = arg
                            break
                        }
                    }
                }
                if (user != null) {
                    try {
                        if (userVerifiedField != null && userVerifiedField!!.getBoolean(user)) {
                            return
                        }
                        if (hasExteraBadge(user)) {
                            return
                        }
                    } catch (_: Throwable) {}

                    val res = param.result ?: return
                    setDrawableNull(res)
                }
            }
        }, unhooksList)

        // 8. DrawerHeaderView.updateUserInfo & AccountRowView.bind
        val drawerHook = object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val obj = param.thisObject ?: return
                val drawable = ReflectionCache.getFieldValue(obj, "premiumStatusDrawable") ?: return
                setDrawableNull(drawable)
            }
        }
        hookAllMethods(drawerHeaderViewClass, "updateUserInfo", drawerHook, unhooksList)
        hookAllMethods(accountRowViewClass, "bind", drawerHook, unhooksList)

        // 9. ProfileActivity.setCollectibleGiftStatus
        hookAllMethods(profileActivityClass, "setCollectibleGiftStatus", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus) return
                val obj = param.thisObject ?: return
                try {
                    val hint = ReflectionCache.getFieldValue(obj, "collectibleHint")
                    if (hint != null) {
                        try {
                            hint.javaClass.getMethod("hide").invoke(hint)
                        } catch (_: Throwable) {}
                    }
                    ReflectionCache.setFieldValue(obj, "collectibleHint", null)
                    ReflectionCache.setFieldValue(obj, "collectibleHintVisible", false)
                    ReflectionCache.setFieldValue(obj, "collectibleStatus", null)
                    ReflectionCache.setFieldValue(obj, "emojiStatusGiftId", null)
                } catch (_: Throwable) {}
                param.result = null
            }
        }, unhooksList)

        // 10. ProfileActivity.getEmojiStatusDrawable
        hookAllMethods(profileActivityClass, "getEmojiStatusDrawable", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hidePremiumBadge) {
                    param.result = null
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus) return
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
