package non.feature.litegram.hide_communities

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object HideCommunitiesHook {

    @Volatile @JvmStatic var hideCommunities: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

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
        if (name == "hideCommunities" || name == "hide_communities") {
            hideCommunities = enabled
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
        chatClass = null
        userClass = null
        chatLinkedCommunityField = null
        userLinkedCommunityField = null
        profileCommunityItemField = null
        profileCurrentChatField = null
        profileCurrentUserField = null
        profileLinkedCommunityRowField = null
        profileLinkedCommunityDividerRowField = null
        dialogCellChatField = null
        dialogCellUserField = null
        dialogCellDrawCommunityAvatarField = null
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
            val f = ReflectionCache.getField(obj.javaClass, "linked_community_id")
            if (f != null) {
                setFieldZero(f, obj)
            }
        } catch (_: Throwable) {}
    }

    private fun applyToDialogCell(cell: Any?) {
        if (cell == null) return
        try {
            val chat = if (dialogCellChatField != null) {
                dialogCellChatField!!.get(cell)
            } else {
                ReflectionCache.getFieldValue(cell, "chat")
            }
            neutralize(chat)

            val user = if (dialogCellUserField != null) {
                dialogCellUserField!!.get(cell)
            } else {
                ReflectionCache.getFieldValue(cell, "user")
            }
            neutralize(user)

            if (dialogCellDrawCommunityAvatarField != null) {
                dialogCellDrawCommunityAvatarField!!.setBoolean(cell, false)
            } else {
                ReflectionCache.setFieldValue(cell, "drawCommunityAvatar", false)
            }
        } catch (_: Throwable) {}
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        chatClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$Chat", cl)
        userClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$User", cl)

        if (chatClass != null) {
            chatLinkedCommunityField = ReflectionCache.getField(chatClass, "linked_community_id")
        }
        if (userClass != null) {
            userLinkedCommunityField = ReflectionCache.getField(userClass, "linked_community_id")
        }

        // If Telegram does not have linked_community_id field, communities feature is absent (< 12.9.0)
        if (chatClass == null || chatLinkedCommunityField == null) {
            return
        }

        val messagesControllerClass = ReflectionCache.findClass("org.telegram.messenger.MessagesController", cl)
        val chatAvatarContainerClass = ReflectionCache.findClass("org.telegram.ui.Components.ChatAvatarContainer", cl)
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)
        val dialogCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.DialogCell", cl)

        if (profileActivityClass != null) {
            profileCommunityItemField = ReflectionCache.getField(profileActivityClass, "communityItem")
            profileCurrentChatField = ReflectionCache.getField(profileActivityClass, "currentChat")
            profileCurrentUserField = ReflectionCache.getField(profileActivityClass, "currentUser")
            profileLinkedCommunityRowField = ReflectionCache.getField(profileActivityClass, "linkedCommunityRow")
            profileLinkedCommunityDividerRowField = ReflectionCache.getField(profileActivityClass, "linkedCommunityDividerRow")
        }

        if (dialogCellClass != null) {
            dialogCellChatField = ReflectionCache.getField(dialogCellClass, "chat")
            dialogCellUserField = ReflectionCache.getField(dialogCellClass, "user")
            dialogCellDrawCommunityAvatarField = ReflectionCache.getField(dialogCellClass, "drawCommunityAvatar")
        }

        // 1. TLRPC.Chat.TLdeserialize
        hookAllMethods(chatClass, "TLdeserialize", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                neutralize(param.result)
            }
        }, unhooksList)

        // 2. TLRPC.User.TLdeserialize
        hookAllMethods(userClass, "TLdeserialize", object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                neutralize(param.result)
            }
        }, unhooksList)

        // 3. MessagesController.putChat & putUser
        hookAllMethods(messagesControllerClass, "putChat", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val args = param.args ?: return
                if (args.isNotEmpty()) {
                    neutralize(args[0])
                }
            }
        }, unhooksList)
        hookAllMethods(messagesControllerClass, "putUser", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val args = param.args ?: return
                if (args.isNotEmpty()) {
                    neutralize(args[0])
                }
            }
        }, unhooksList)

        // 4. ChatAvatarContainer.setCommunityItemVisible
        hookAllMethods(chatAvatarContainerClass, "setCommunityItemVisible", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val args = param.args ?: return
                if (args.isNotEmpty() && args[0] is Boolean) {
                    args[0] = false
                }
            }
        }, unhooksList)

        // 5. ProfileActivity.updateCommunityArrowItem
        hookAllMethods(profileActivityClass, "updateCommunityArrowItem", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val activity = param.thisObject ?: return
                try {
                    val communityItem = if (profileCommunityItemField != null) {
                        profileCommunityItemField!!.get(activity) as? View
                    } else {
                        ReflectionCache.getFieldValue(activity, "communityItem") as? View
                    }
                    if (communityItem != null) {
                        communityItem.visibility = View.GONE
                    }
                } catch (_: Throwable) {}
                param.result = null
            }
        }, unhooksList)

        // 6. ProfileActivity.updateRowsIds
        hookAllMethods(profileActivityClass, "updateRowsIds", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunities) return
                val activity = param.thisObject ?: return
                try {
                    val currentChat = if (profileCurrentChatField != null) {
                        profileCurrentChatField!!.get(activity)
                    } else {
                        ReflectionCache.getFieldValue(activity, "currentChat")
                    }
                    neutralize(currentChat)

                    val currentUser = if (profileCurrentUserField != null) {
                        profileCurrentUserField!!.get(activity)
                    } else {
                        ReflectionCache.getFieldValue(activity, "currentUser")
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
                        ReflectionCache.setFieldValue(activity, "linkedCommunityRow", -1)
                    }
                    if (profileLinkedCommunityDividerRowField != null) {
                        profileLinkedCommunityDividerRowField!!.setInt(activity, -1)
                    } else {
                        ReflectionCache.setFieldValue(activity, "linkedCommunityDividerRow", -1)
                    }
                } catch (_: Throwable) {}
            }
        }, unhooksList)

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
        hookAllMethods(dialogCellClass, "setDialog", dialogCellHook, unhooksList)
        hookAllMethods(dialogCellClass, "update", dialogCellHook, unhooksList)
        hookAllMethods(dialogCellClass, "buildLayout", dialogCellHook, unhooksList)
    }
}
