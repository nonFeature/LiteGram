package non.feature.litegram.hide_communities

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.util.ArrayList

object HideCommunitiesHook {

    @Volatile @JvmStatic var hideCommunities: Boolean = false

    private val unhooks = ArrayList<XC_MethodHook.Unhook>()

    private var chatClass: Class<*>? = null
    private var userClass: Class<*>? = null
    private var chatLinkedCommunityField: Field? = null
    private var userLinkedCommunityField: Field? = null

    private var profileCommunityItemField: Field? = null
    private var profileCurrentChatField: Field? = null
    private var profileCurrentUserField: Field? = null
    private var profileLinkedCommunityRowField: Field? = null
    private var profileLinkedCommunityDividerRowField: Field? = null

    private var dialogCellChatField: Field? = null
    private var dialogCellUserField: Field? = null
    private var dialogCellDrawCommunityAvatarField: Field? = null

    @JvmStatic
    fun updateSettings(enabled: Boolean) {
        hideCommunities = enabled
    }

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        if (name == "hideCommunities") {
            hideCommunities = enabled
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

    private fun setFieldZero(field: Field, obj: Any) {
        val t = field.type
        if (t == Long::class.javaPrimitiveType) {
            field.setLong(obj, 0L)
        } else if (t == Int::class.javaPrimitiveType) {
            field.setInt(obj, 0)
        } else if (t == java.lang.Long::class.java) {
            field.set(obj, java.lang.Long.valueOf(0L))
        } else if (t == java.lang.Integer::class.java) {
            field.set(obj, java.lang.Integer.valueOf(0))
        } else {
            field.set(obj, 0L)
        }
    }

    private fun neutralize(obj: Any?) {
        if (obj == null) return
        try {
            if (chatClass != null && chatClass!!.isInstance(obj)) {
                if (chatLinkedCommunityField != null) {
                    setFieldZero(chatLinkedCommunityField!!, obj)
                    return
                }
            }
            if (userClass != null && userClass!!.isInstance(obj)) {
                if (userLinkedCommunityField != null) {
                    setFieldZero(userLinkedCommunityField!!, obj)
                    return
                }
            }
            var cls: Class<*>? = obj.javaClass
            while (cls != null) {
                try {
                    val f = cls.getDeclaredField("linked_community_id")
                    f.isAccessible = true
                    if (chatClass != null && chatClass!!.isInstance(obj)) {
                        chatLinkedCommunityField = f
                    } else if (userClass != null && userClass!!.isInstance(obj)) {
                        userLinkedCommunityField = f
                    }
                    setFieldZero(f, obj)
                    return
                } catch (_: NoSuchFieldException) {
                    cls = cls.superclass
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

    private fun applyToDialogCell(cell: Any?) {
        if (cell == null) return
        try {
            val chat = if (dialogCellChatField != null) {
                dialogCellChatField!!.get(cell)
            } else {
                getPrivateField(cell, "chat")
            }
            neutralize(chat)

            val user = if (dialogCellUserField != null) {
                dialogCellUserField!!.get(cell)
            } else {
                getPrivateField(cell, "user")
            }
            neutralize(user)

            if (dialogCellDrawCommunityAvatarField != null) {
                dialogCellDrawCommunityAvatarField!!.setBoolean(cell, false)
            } else {
                setPrivateField(cell, "drawCommunityAvatar", false)
            }
        } catch (_: Throwable) {}
    }

    @JvmStatic
    fun init(cl: ClassLoader) {
        chatClass = findClass("org.telegram.tgnet.TLRPC\$Chat", cl)
        userClass = findClass("org.telegram.tgnet.TLRPC\$User", cl)

        if (chatClass != null) {
            chatLinkedCommunityField = findField(chatClass, "linked_community_id")
        }
        if (userClass != null) {
            userLinkedCommunityField = findField(userClass, "linked_community_id")
        }

        val messagesControllerClass = findClass("org.telegram.messenger.MessagesController", cl)
        val chatAvatarContainerClass = findClass("org.telegram.ui.Components.ChatAvatarContainer", cl)
        val profileActivityClass = findClass("org.telegram.ui.ProfileActivity", cl)
        val dialogCellClass = findClass("org.telegram.ui.Cells.DialogCell", cl)

        if (profileActivityClass != null) {
            profileCommunityItemField = findField(profileActivityClass, "communityItem")
            profileCurrentChatField = findField(profileActivityClass, "currentChat")
            profileCurrentUserField = findField(profileActivityClass, "currentUser")
            profileLinkedCommunityRowField = findField(profileActivityClass, "linkedCommunityRow")
            profileLinkedCommunityDividerRowField = findField(profileActivityClass, "linkedCommunityDividerRow")
        }

        if (dialogCellClass != null) {
            dialogCellChatField = findField(dialogCellClass, "chat")
            dialogCellUserField = findField(dialogCellClass, "user")
            dialogCellDrawCommunityAvatarField = findField(dialogCellClass, "drawCommunityAvatar")
        }

        // 1. TLRPC.Chat.TLdeserialize
        hookAllMethods(chatClass, "TLdeserialize", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                neutralize(param.result)
            }
        })

        // 2. TLRPC.User.TLdeserialize
        hookAllMethods(userClass, "TLdeserialize", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                neutralize(param.result)
            }
        })

        // 3. MessagesController.putChat & putUser
        hookAllMethods(messagesControllerClass, "putChat", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val args = param.args ?: return
                if (args.isNotEmpty()) {
                    neutralize(args[0])
                }
            }
        })
        hookAllMethods(messagesControllerClass, "putUser", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val args = param.args ?: return
                if (args.isNotEmpty()) {
                    neutralize(args[0])
                }
            }
        })

        // 4. ChatAvatarContainer.setCommunityItemVisible
        hookAllMethods(chatAvatarContainerClass, "setCommunityItemVisible", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val args = param.args ?: return
                if (args.isNotEmpty() && args[0] is Boolean) {
                    args[0] = false
                }
            }
        })

        // 5. ProfileActivity.updateCommunityArrowItem
        hookAllMethods(profileActivityClass, "updateCommunityArrowItem", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val activity = param.thisObject ?: return
                try {
                    val communityItem = if (profileCommunityItemField != null) {
                        profileCommunityItemField!!.get(activity) as? View
                    } else {
                        getPrivateField(activity, "communityItem") as? View
                    }
                    if (communityItem != null) {
                        communityItem.visibility = View.GONE
                    }
                } catch (_: Throwable) {}
                param.setResult(null)
            }
        })

        // 6. ProfileActivity.updateRowsIds
        hookAllMethods(profileActivityClass, "updateRowsIds", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val activity = param.thisObject ?: return
                try {
                    val currentChat = if (profileCurrentChatField != null) {
                        profileCurrentChatField!!.get(activity)
                    } else {
                        getPrivateField(activity, "currentChat")
                    }
                    neutralize(currentChat)

                    val currentUser = if (profileCurrentUserField != null) {
                        profileCurrentUserField!!.get(activity)
                    } else {
                        getPrivateField(activity, "currentUser")
                    }
                    neutralize(currentUser)
                } catch (_: Throwable) {}
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val activity = param.thisObject ?: return
                try {
                    if (profileLinkedCommunityRowField != null) {
                        profileLinkedCommunityRowField!!.setInt(activity, -1)
                    } else {
                        setPrivateField(activity, "linkedCommunityRow", -1)
                    }
                    if (profileLinkedCommunityDividerRowField != null) {
                        profileLinkedCommunityDividerRowField!!.setInt(activity, -1)
                    } else {
                        setPrivateField(activity, "linkedCommunityDividerRow", -1)
                    }
                } catch (_: Throwable) {}
            }
        })

        // 7. DialogCell setDialog, update, buildLayout
        val dialogCellHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                applyToDialogCell(param.thisObject)
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                applyToDialogCell(param.thisObject)
            }
        }
        hookAllMethods(dialogCellClass, "setDialog", dialogCellHook)
        hookAllMethods(dialogCellClass, "update", dialogCellHook)
        hookAllMethods(dialogCellClass, "buildLayout", dialogCellHook)
    }
}
