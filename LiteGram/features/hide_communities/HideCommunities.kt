package non.feature.litegram.hide_communities

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object HideCommunitiesHook {

    @Volatile @JvmStatic var hideCommunitiesBadges: Boolean = false
    @Volatile @JvmStatic var hideCommunitiesProfile: Boolean = false

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

    private val origDrawChatComm = ThreadLocal<Long>()
    private val origDrawUserComm = ThreadLocal<Long>()
    private val origProfileChatComm = ThreadLocal<Long>()
    private val origProfileUserComm = ThreadLocal<Long>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        if (name == "hideCommunitiesBadges" || name == "hide_communities_badges") {
            hideCommunitiesBadges = enabled
        } else if (name == "hideCommunitiesProfile" || name == "hide_communities_profile") {
            hideCommunitiesProfile = enabled
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

        origDrawChatComm.remove()
        origDrawUserComm.remove()
        origProfileChatComm.remove()
        origProfileUserComm.remove()
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

        val chatAvatarContainerClass = ReflectionCache.findClass("org.telegram.ui.Components.ChatAvatarContainer", cl)
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)
        val dialogCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.DialogCell", cl)
        val avatarStoryParamsClass = ReflectionCache.findClass("org.telegram.ui.Stories.StoriesUtilities\$AvatarStoryParams", cl)

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

        // ==================== 1. BADGES (DialogCell & ChatAvatarContainer) ====================

        // 1.1 Chat header community badge
        hookAllMethods(chatAvatarContainerClass, "setCommunityItemVisible", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesBadges) return
                val args = param.args ?: return
                if (args.isNotEmpty() && args[0] is Boolean) {
                    args[0] = false
                }
            }
        }, unhooksList)

        // 1.2 DialogCell layout updates: force drawCommunityAvatar = false
        val dialogCellUpdateHook = object : XC_MethodHook() {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesBadges) return
                val cell = param.thisObject ?: return
                try {
                    if (dialogCellDrawCommunityAvatarField != null) {
                        dialogCellDrawCommunityAvatarField!!.setBoolean(cell, false)
                    } else {
                        ReflectionCache.setFieldValue(cell, "drawCommunityAvatar", false)
                    }
                } catch (_: Throwable) {}
            }
        }
        hookAllMethods(dialogCellClass, "setDialog", dialogCellUpdateHook, unhooksList)
        hookAllMethods(dialogCellClass, "update", dialogCellUpdateHook, unhooksList)
        hookAllMethods(dialogCellClass, "buildLayout", dialogCellUpdateHook, unhooksList)

        // 1.3 DialogCell onDraw: temporarily suppress linked_community_id during drawing so community badge isn't rendered
        hookAllMethods(dialogCellClass, "onDraw", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesBadges) return
                val cell = param.thisObject ?: return
                try {
                    if (dialogCellDrawCommunityAvatarField != null) {
                        dialogCellDrawCommunityAvatarField!!.setBoolean(cell, false)
                    }
                    val chat = if (dialogCellChatField != null) dialogCellChatField!!.get(cell) else null
                    if (chat != null && chatLinkedCommunityField != null) {
                        val orig = chatLinkedCommunityField!!.getLong(chat)
                        if (orig != 0L) {
                            origDrawChatComm.set(orig)
                            chatLinkedCommunityField!!.setLong(chat, 0L)
                        }
                    }
                    val user = if (dialogCellUserField != null) dialogCellUserField!!.get(cell) else null
                    if (user != null && userLinkedCommunityField != null) {
                        val orig = userLinkedCommunityField!!.getLong(user)
                        if (orig != 0L) {
                            origDrawUserComm.set(orig)
                            userLinkedCommunityField!!.setLong(user, 0L)
                        }
                    }
                } catch (_: Throwable) {}
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesBadges) return
                val cell = param.thisObject ?: return
                try {
                    val origChat = origDrawChatComm.get()
                    if (origChat != null && origChat != 0L) {
                        origDrawChatComm.remove()
                        val chat = if (dialogCellChatField != null) dialogCellChatField!!.get(cell) else null
                        if (chat != null && chatLinkedCommunityField != null) {
                            chatLinkedCommunityField!!.setLong(chat, origChat)
                        }
                    }
                    val origUser = origDrawUserComm.get()
                    if (origUser != null && origUser != 0L) {
                        origDrawUserComm.remove()
                        val user = if (dialogCellUserField != null) dialogCellUserField!!.get(cell) else null
                        if (user != null && userLinkedCommunityField != null) {
                            userLinkedCommunityField!!.setLong(user, origUser)
                        }
                    }
                } catch (_: Throwable) {}
            }
        }, unhooksList)

        // 1.4 Prevent clicking the community badge on the avatar in chat list
        val avatarClickHook = object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (hideCommunitiesBadges) {
                    param.setResult(false)
                }
            }
        }
        if (dialogCellClass != null) {
            try {
                for (inner in dialogCellClass.declaredClasses) {
                    if (avatarStoryParamsClass != null && avatarStoryParamsClass.isAssignableFrom(inner)) {
                        hookAllMethods(inner, "isAvatarClickable", avatarClickHook, unhooksList)
                        hookAllMethods(inner, "onAvatarClick", avatarClickHook, unhooksList)
                    }
                }
            } catch (_: Throwable) {}
        }
        if (avatarStoryParamsClass != null) {
            hookAllMethods(avatarStoryParamsClass, "isAvatarClickable", avatarClickHook, unhooksList)
            hookAllMethods(avatarStoryParamsClass, "onAvatarClick", avatarClickHook, unhooksList)
        }

        // ==================== 2. PROFILE (ProfileActivity) ====================

        // 2.1 Profile community banner item
        hookAllMethods(profileActivityClass, "updateCommunityArrowItem", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesProfile) return
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
                param.setResult(null)
            }
        }, unhooksList)

        // 2.2 Profile list rows: exclude linked community row and divider
        hookAllMethods(profileActivityClass, "updateRowsIds", object : XC_MethodHook() {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesProfile) return
                val activity = param.thisObject ?: return
                try {
                    val currentChat = if (profileCurrentChatField != null) {
                        profileCurrentChatField!!.get(activity)
                    } else {
                        ReflectionCache.getFieldValue(activity, "currentChat")
                    }
                    if (currentChat != null && chatLinkedCommunityField != null) {
                        val orig = chatLinkedCommunityField!!.getLong(currentChat)
                        if (orig != 0L) {
                            origProfileChatComm.set(orig)
                            chatLinkedCommunityField!!.setLong(currentChat, 0L)
                        }
                    }

                    val currentUser = if (profileCurrentUserField != null) {
                        profileCurrentUserField!!.get(activity)
                    } else {
                        ReflectionCache.getFieldValue(activity, "currentUser")
                    }
                    if (currentUser != null && userLinkedCommunityField != null) {
                        val orig = userLinkedCommunityField!!.getLong(currentUser)
                        if (orig != 0L) {
                            origProfileUserComm.set(orig)
                            userLinkedCommunityField!!.setLong(currentUser, 0L)
                        }
                    }
                } catch (_: Throwable) {}
            }

            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideCommunitiesProfile) return
                val activity = param.thisObject ?: return
                try {
                    val origChat = origProfileChatComm.get()
                    if (origChat != null && origChat != 0L) {
                        origProfileChatComm.remove()
                        val currentChat = if (profileCurrentChatField != null) {
                            profileCurrentChatField!!.get(activity)
                        } else {
                            ReflectionCache.getFieldValue(activity, "currentChat")
                        }
                        if (currentChat != null && chatLinkedCommunityField != null) {
                            chatLinkedCommunityField!!.setLong(currentChat, origChat)
                        }
                    }

                    val origUser = origProfileUserComm.get()
                    if (origUser != null && origUser != 0L) {
                        origProfileUserComm.remove()
                        val currentUser = if (profileCurrentUserField != null) {
                            profileCurrentUserField!!.get(activity)
                        } else {
                            ReflectionCache.getFieldValue(activity, "currentUser")
                        }
                        if (currentUser != null && userLinkedCommunityField != null) {
                            userLinkedCommunityField!!.setLong(currentUser, origUser)
                        }
                    }

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
    }
}
