package non.feature.litegram.premium_badge

import android.graphics.drawable.Drawable
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList

object PremiumBadgeHook {

    @Volatile @JvmStatic var hidePremiumBadge: Boolean = false
    @Volatile @JvmStatic var hideCollectibleStatus: Boolean = false

    private val unhooks = ArrayList<XC_MethodHook.Unhook>()

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
            "hidePremiumBadge" -> hidePremiumBadge = enabled
            "hideCollectibleStatus" -> hideCollectibleStatus = enabled
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

    private fun findField(clazz: Class<*>?, fieldName: String): Field? {
        var cls = clazz
        while (cls != null) {
            try {
                val f = cls.getDeclaredField(fieldName)
                f.isAccessible = true
                return f
            } catch (_: NoSuchFieldException) {
                cls = cls.superclass
            }
        }
        return null
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

    private fun setPrivateField(obj: Any?, fieldName: String, value: Any?) {
        if (obj == null) return
        try {
            var cls: Class<*>? = obj.javaClass
            while (cls != null) {
                try {
                    val field = cls.getDeclaredField(fieldName)
                    field.isAccessible = true
                    if (value is Int && field.type == Int::class.javaPrimitiveType) {
                        field.setInt(obj, value)
                    } else if (value is Boolean && field.type == Boolean::class.javaPrimitiveType) {
                        field.setBoolean(obj, value)
                    } else {
                        field.set(obj, value)
                    }
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

    private fun findStatusBadgeComponentClass(cl: ClassLoader): Class<*>? {
        for (pkg in arrayOf(
            "org.telegram.ui.Components.StatusBadgeComponent",
            "org.telegram.p035ui.Components.StatusBadgeComponent",
            "org.telegram.p022ui.Components.StatusBadgeComponent",
            "org.telegram.p031ui.Components.StatusBadgeComponent"
        )) {
            val cls = findClass(pkg, cl)
            if (cls != null) return cls
        }
        return null
    }

    private fun findPremiumGradientClass(cl: ClassLoader): Class<*>? {
        for (pkg in arrayOf(
            "org.telegram.ui.Components.Premium.PremiumGradient",
            "org.telegram.p035ui.Components.Premium.PremiumGradient",
            "org.telegram.p022ui.Components.Premium.PremiumGradient",
            "org.telegram.p031ui.Components.Premium.PremiumGradient"
        )) {
            val cls = findClass(pkg, cl)
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
                premiumGradientGetInstanceMethod = clazz.getMethod("getInstance")
            }
            val instance = premiumGradientGetInstanceMethod?.invoke(null) ?: return null
            if (premiumStarMiniField == null) {
                premiumStarMiniField = clazz.getField("premiumStarDrawableMini")
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
            var cls: Class<*>? = drawable.javaClass
            while (cls != null) {
                try {
                    val m = cls.getDeclaredMethod("set", Drawable::class.java, Boolean::class.javaPrimitiveType)
                    m.isAccessible = true
                    swapSetMethod = m
                    m.invoke(drawable, null, false)
                    return
                } catch (_: NoSuchMethodException) {
                    cls = cls.superclass
                }
            }
        } catch (_: Throwable) {}
    }

    @JvmStatic
    fun init(cl: ClassLoader) {
        userClass = findClass("org.telegram.tgnet.TLRPC\$User", cl)
        if (userClass != null) {
            try {
                userVerifiedField = userClass!!.getField("verified")
            } catch (_: Throwable) {
                userVerifiedField = findField(userClass, "verified")
            }
        }

        badgeDtoClass = findClass("com.exteragram.messenger.api.dto.BadgeDTO", cl)
        badgesControllerClass = findClass("com.exteragram.messenger.badges.BadgesController", cl)
        if (badgesControllerClass != null) {
            try {
                badgesControllerInstanceField = badgesControllerClass!!.getField("INSTANCE")
            } catch (_: Throwable) {}
            try {
                badgesControllerHasBadgeMethod = badgesControllerClass!!.getMethod("hasBadge", userClass)
            } catch (_: Throwable) {}
            try {
                badgesControllerGetBadgeMethod = badgesControllerClass!!.getMethod("getBadge", userClass)
            } catch (_: Throwable) {}
        }

        premiumGradientClass = findPremiumGradientClass(cl)

        val userObjectClass = findClass("org.telegram.messenger.UserObject", cl)
        val dialogObjectClass = findClass("org.telegram.messenger.DialogObject", cl)
        val messageObjectClass = findClass("org.telegram.messenger.MessageObject", cl)
        val messagesControllerClass = findClass("org.telegram.messenger.MessagesController", cl)
        val chatMessageCellClass = findClass("org.telegram.ui.Cells.ChatMessageCell", cl)
        val swapAnimatedEmojiDrawableClass = findClass("org.telegram.ui.Components.AnimatedEmojiDrawable\$SwapAnimatedEmojiDrawable", cl)
        val statusBadgeComponentClass = findStatusBadgeComponentClass(cl)
        val drawerHeaderViewClass = findClass("com.exteragram.messenger.drawer.DrawerHeaderView", cl)
        val accountRowViewClass = findClass("com.exteragram.messenger.drawer.DrawerAccountPickerView\$AccountRowView", cl)
        val profileActivityClass = findClass("org.telegram.ui.ProfileActivity", cl)

        // 1. UserObject.getEmojiStatusDocumentId -> null
        hookAllMethods(userObjectClass, "getEmojiStatusDocumentId", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.setResult(null)
            }
        })

        // 2. DialogObject & MessageObject.getEmojiStatusDocumentId -> 0
        val zeroHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.setResult(0L)
            }
        }
        hookAllMethods(dialogObjectClass, "getEmojiStatusDocumentId", zeroHook)
        hookAllMethods(messageObjectClass, "getEmojiStatusDocumentId", zeroHook)

        // 3. isEmojiStatusCollectible -> false (when hidePremiumBadge OR hideCollectibleStatus)
        val isCollectibleHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hidePremiumBadge || hideCollectibleStatus) {
                    param.setResult(false)
                }
            }
        }
        hookAllMethods(userObjectClass, "isEmojiStatusCollectible", isCollectibleHook)
        hookAllMethods(dialogObjectClass, "isEmojiStatusCollectible", isCollectibleHook)
        hookAllMethods(messageObjectClass, "isEmojiStatusCollectible", isCollectibleHook)

        // 4. MessagesController.isPremiumUser -> false
        hookAllMethods(messagesControllerClass, "isPremiumUser", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                param.setResult(false)
            }
        })

        // 5. ChatMessageCell.getAuthorStatus
        hookAllMethods(chatMessageCellClass, "getAuthorStatus", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val res = param.result ?: return
                if (badgeDtoClass != null && badgeDtoClass!!.isInstance(res)) {
                    return
                }
                if (res is Number) {
                    param.setResult(null)
                    return
                }
                val clsName = res.javaClass.name
                if (clsName.contains("Drawable") || clsName.contains("Long") || clsName.contains("Integer") || clsName.contains("Number")) {
                    param.setResult(null)
                }
            }
        })

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
        })

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
        })

        // 8. DrawerHeaderView.updateUserInfo & AccountRowView.bind
        val drawerHook = object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hidePremiumBadge) return
                val obj = param.thisObject ?: return
                val drawable = getPrivateField(obj, "premiumStatusDrawable") ?: return
                setDrawableNull(drawable)
            }
        }
        hookAllMethods(drawerHeaderViewClass, "updateUserInfo", drawerHook)
        hookAllMethods(accountRowViewClass, "bind", drawerHook)

        // 9. ProfileActivity.setCollectibleGiftStatus
        hookAllMethods(profileActivityClass, "setCollectibleGiftStatus", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus) return
                val obj = param.thisObject ?: return
                try {
                    val hint = getPrivateField(obj, "collectibleHint")
                    if (hint != null) {
                        try {
                            hint.javaClass.getMethod("hide").invoke(hint)
                        } catch (_: Throwable) {}
                    }
                    setPrivateField(obj, "collectibleHint", null)
                    setPrivateField(obj, "collectibleHintVisible", false)
                    setPrivateField(obj, "collectibleStatus", null)
                    setPrivateField(obj, "emojiStatusGiftId", null)
                } catch (_: Throwable) {}
                param.setResult(null)
            }
        })

        // 10. ProfileActivity.getEmojiStatusDrawable
        hookAllMethods(profileActivityClass, "getEmojiStatusDrawable", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hidePremiumBadge) {
                    param.setResult(null)
                }
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCollectibleStatus) return
                val res = param.result ?: return
                try {
                    val m = res.javaClass.getMethod("setParticles", Boolean::class.javaPrimitiveType, Boolean::class.javaPrimitiveType)
                    m.invoke(res, false, true)
                } catch (_: Throwable) {}
            }
        })
    }
}
