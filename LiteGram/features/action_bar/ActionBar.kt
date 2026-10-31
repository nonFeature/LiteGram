package non.feature.litegram.action_bar

import android.view.View
import android.view.ViewGroup
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object ActionBarHook {

    const val ADD_SHORTCUT_PROFILE = 14
    const val CALL_ITEM = 15
    const val GIFT_PREMIUM = 38
    const val CHANNEL_STORIES = 39
    const val REPORT_PROFILE = 24

    const val CLEAR_HISTORY_CHAT = 15
    const val REPORT_CHAT = 21
    const val ADD_SHORTCUT_CHAT = 24
    const val BOOST_GROUP = 29

    const val CLEAR_HISTORY_DIALOGS = 103

    @Volatile @JvmStatic var hideLiveStream: Boolean = false
    @Volatile @JvmStatic var hideClearHistory: Boolean = false
    @Volatile @JvmStatic var hideReport: Boolean = false
    @Volatile @JvmStatic var hideSendGift: Boolean = false
    @Volatile @JvmStatic var hideArchivedStories: Boolean = false
    @Volatile @JvmStatic var hideAddShortcut: Boolean = false
    @Volatile @JvmStatic var hideBoostGroup: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideActionBarLiveStream", "hide_action_bar_live_stream" -> hideLiveStream = enabled
            "hideActionBarClearHistory", "hide_action_bar_clear_history" -> hideClearHistory = enabled
            "hideActionBarReport", "hide_action_bar_report" -> hideReport = enabled
            "hideActionBarSendGift", "hide_action_bar_send_gift" -> hideSendGift = enabled
            "hideActionBarArchivedStories", "hide_action_bar_archived_stories" -> hideArchivedStories = enabled
            "hideActionBarAddShortcut", "hide_action_bar_add_shortcut" -> hideAddShortcut = enabled
            "hideActionBarBoostGroup", "hide_action_bar_boost_group" -> hideBoostGroup = enabled
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

        hideLiveStream = false
        hideClearHistory = false
        hideReport = false
        hideSendGift = false
        hideArchivedStories = false
        hideAddShortcut = false
        hideBoostGroup = false
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

    private fun toInt(value: Any?): Int {
        if (value == null) return -1
        if (value is Number) return value.toInt()
        try {
            return value.toString().toInt()
        } catch (_: Throwable) {}
        return -1
    }

    private fun hideItemOrView(target: Any?) {
        if (target == null) return
        if (target is View) {
            target.visibility = View.GONE
        }
        try {
            val clazz = target.javaClass
            ReflectionCache.getField(clazz, "visibility")?.setInt(target, View.GONE)
            val innerView = ReflectionCache.getField(clazz, "view")?.get(target) as? View
            innerView?.visibility = View.GONE
        } catch (_: Throwable) {}
    }

    private fun isClearHistory(args: Array<Any?>?): Boolean {
        if (args == null || args.isEmpty()) return false
        val itemId = toInt(args[0])
        return itemId == CLEAR_HISTORY_CHAT || itemId == CLEAR_HISTORY_DIALOGS
    }

    private fun shouldHideMenuItem(args: Array<Any?>?): Boolean {
        if (args == null || args.isEmpty()) return false
        val itemId = toInt(args[0])
        if (itemId < 0) return false

        if (isClearHistory(args) && hideClearHistory) return true

        if (itemId == 15) {
            return hideClearHistory || hideLiveStream
        }
        if (itemId == 24) {
            return hideReport || hideAddShortcut
        }
        if (itemId == REPORT_CHAT && hideReport) return true
        if (itemId == BOOST_GROUP && hideBoostGroup) return true
        if (itemId == GIFT_PREMIUM && hideSendGift) return true
        if (itemId == CHANNEL_STORIES && hideArchivedStories) return true
        if (itemId == ADD_SHORTCUT_PROFILE && hideAddShortcut) return true

        return false
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        val actionBarMenuItemClass = ReflectionCache.findClass("org.telegram.ui.ActionBar.ActionBarMenuItem", cl)
        val chatActivityClass = ReflectionCache.findClass("org.telegram.ui.ChatActivity", cl)
        val topicsFragmentClass = ReflectionCache.findClass("org.telegram.ui.TopicsFragment", cl)
        val itemOptionsClass = ReflectionCache.findClass("org.telegram.ui.Components.ItemOptions", cl)

        if (actionBarMenuItemClass != null) {
            val popupLayoutField = ReflectionCache.getField(actionBarMenuItemClass, "popupLayout")
            val lazyMapField = ReflectionCache.getField(actionBarMenuItemClass, "lazyMap")

            // 1. addSubItem & lazilyAddSubItem
            val addSubItemHook = object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val result = param.result ?: return
                    val args = param.args ?: return
                    if (shouldHideMenuItem(args)) {
                        hideItemOrView(result)
                    }
                }
            }
            hookAllMethods(actionBarMenuItemClass, "addSubItem", addSubItemHook, unhooksList)
            hookAllMethods(actionBarMenuItemClass, "lazilyAddSubItem", addSubItemHook, unhooksList)

            // 2. setSubItemShown
            hookAllMethods(actionBarMenuItemClass, "setSubItemShown", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    val args = param.args ?: return
                    if (shouldHideMenuItem(args)) {
                        if (args.size > 1) {
                            args[1] = false
                        }
                    }
                }
            }, unhooksList)

            // 3. toggleSubMenu
            hookAllMethods(actionBarMenuItemClass, "toggleSubMenu", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val item = param.thisObject ?: return
                    try {
                        val popupLayout = popupLayoutField?.get(item) as? ViewGroup
                        if (popupLayout != null) {
                            val childCount = popupLayout.childCount
                            for (i in 0 until childCount) {
                                val child = popupLayout.getChildAt(i) ?: continue
                                val tag = toInt(child.tag)
                                if (tag >= 0 && shouldHideMenuItem(arrayOf(tag))) {
                                    hideItemOrView(child)
                                }
                            }
                        }

                        val lazyMap = lazyMapField?.get(item) as? Map<*, *>
                        if (lazyMap != null) {
                            for (entry in lazyMap.entries) {
                                val pid = toInt(entry.key)
                                if (pid >= 0 && shouldHideMenuItem(arrayOf(pid))) {
                                    hideItemOrView(entry.value)
                                }
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 4. ChatActivity.checkActionBarMenu
        if (chatActivityClass != null) {
            val clearHistoryItemField = ReflectionCache.getField(chatActivityClass, "clearHistoryItem")

            hookAllMethods(chatActivityClass, "checkActionBarMenu", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hideClearHistory) return
                    val chatActivity = param.thisObject ?: return
                    try {
                        val item = clearHistoryItemField?.get(chatActivity)
                        if (item != null) {
                            hideItemOrView(item)
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 5. ItemOptions.add
        if (itemOptionsClass != null) {
            hookAllMethods(itemOptionsClass, "add", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideClearHistory) return
                    if (isClearHistory(param.args)) {
                        param.setResult(param.thisObject)
                    }
                }
            }, unhooksList)
        }

        // 6. TopicsFragment.updateChatInfo
        if (topicsFragmentClass != null) {
            val boostGroupSubmenuField = ReflectionCache.getField(topicsFragmentClass, "boostGroupSubmenu")
            val reportSubmenuField = ReflectionCache.getField(topicsFragmentClass, "reportSubmenu")

            hookAllMethods(topicsFragmentClass, "updateChatInfo", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val instance = param.thisObject ?: return
                    try {
                        if (hideBoostGroup) {
                            hideItemOrView(boostGroupSubmenuField?.get(instance))
                        }
                        if (hideReport) {
                            hideItemOrView(reportSubmenuField?.get(instance))
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }
    }
}
