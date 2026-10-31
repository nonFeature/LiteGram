package non.feature.litegram.media_layout

import android.util.SparseArray
import android.view.View
import android.view.ViewGroup
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList
import java.util.HashSet
import non.feature.litegram.core.ReflectionCache

object MediaLayoutHook {

    @Volatile @JvmStatic var hideGiftsTab: Boolean = false
    @Volatile @JvmStatic var hideStoriesTab: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideGiftsTab", "hide_gifts_tab" -> hideGiftsTab = enabled
            "hideStoriesTab", "hide_stories_tab" -> hideStoriesTab = enabled
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

        hideGiftsTab = false
        hideStoriesTab = false
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

    private fun removeGifts(obj: Any?, tabGiftsClass: Class<*>?) {
        if (obj == null) return
        try {
            val clazz = obj.javaClass
            ReflectionCache.getField(clazz, "stargifts_count")?.setInt(obj, 0)
            val mainTabField = ReflectionCache.getField(clazz, "main_tab")
            if (mainTabField != null && tabGiftsClass != null) {
                val mainTab = mainTabField.get(obj)
                if (mainTab != null && tabGiftsClass.isInstance(mainTab)) {
                    mainTabField.set(obj, null)
                }
            }
        } catch (_: Throwable) {}
    }

    private fun removeStories(obj: Any?, tabPostsClass: Class<*>?) {
        if (obj == null) return
        try {
            val clazz = obj.javaClass
            ReflectionCache.getField(clazz, "stories_pinned_available")?.setBoolean(obj, false)
            ReflectionCache.getField(clazz, "stories")?.set(obj, null)
            val mainTabField = ReflectionCache.getField(clazz, "main_tab")
            if (mainTabField != null && tabPostsClass != null) {
                val mainTab = mainTabField.get(obj)
                if (mainTab != null && tabPostsClass.isInstance(mainTab)) {
                    mainTabField.set(obj, null)
                }
            }
        } catch (_: Throwable) {}
    }

    private fun isSelfProfile(instance: Any): Boolean {
        try {
            val isSelfMethod = ReflectionCache.getMethod(instance.javaClass, "isSelf")
            if (isSelfMethod != null) {
                val res = isSelfMethod.invoke(instance)
                if (res is Boolean && res) return true
            }
        } catch (_: Throwable) {}

        try {
            val profileActivityField = ReflectionCache.getField(instance.javaClass, "profileActivity")
            val activity = profileActivityField?.get(instance)
            if (activity != null) {
                val myProfileField = ReflectionCache.getField(activity.javaClass, "myProfile")
                val res = myProfileField?.get(activity)
                if (res is Boolean && res) return true
            }
        } catch (_: Throwable) {}

        return false
    }

    @Suppress("UNCHECKED_CAST")
    private fun rebuildProfileTabs(tabStrip: Any?, removableIds: Set<Int>) {
        if (tabStrip == null || removableIds.isEmpty()) return
        try {
            val stripClass = tabStrip.javaClass
            val hasTabMethod = ReflectionCache.getMethod(stripClass, "hasTab", Int::class.javaPrimitiveType) ?: return

            var hasAny = false
            for (id in removableIds) {
                val res = hasTabMethod.invoke(tabStrip, id)
                if (res == true) {
                    hasAny = true
                    break
                }
            }
            if (!hasAny) return

            val getCurrentTabIdMethod = ReflectionCache.getMethod(stripClass, "getCurrentTabId")
            val currentTabId = (getCurrentTabIdMethod?.invoke(tabStrip) as? Number)?.toInt() ?: -1

            val getTabIdsMethod = ReflectionCache.getMethod(stripClass, "getTabIds")
            val rawTabIds = getTabIdsMethod?.invoke(tabStrip) ?: return
            val tabIdsList = ArrayList<Int>()

            when (rawTabIds) {
                is IntArray -> {
                    for (id in rawTabIds) tabIdsList.add(id)
                }
                is Iterable<*> -> {
                    for (item in rawTabIds) {
                        if (item is Number) tabIdsList.add(item.toInt())
                    }
                }
            }

            val removeTabsMethod = ReflectionCache.getMethod(stripClass, "removeTabs")
            val cachedTabs = removeTabsMethod?.invoke(tabStrip) as? SparseArray<View> ?: return

            var firstAvailable: Int? = null
            val addTextTabMethod = stripClass.methods.firstOrNull {
                it.name == "addTextTab" && it.parameterTypes.size == 3
            }

            for (tabId in tabIdsList) {
                if (removableIds.contains(tabId)) continue

                val view = cachedTabs.get(tabId)
                var tabText: CharSequence = ""
                try {
                    val getTextMethod = view?.javaClass?.getMethod("getText")
                    val res = getTextMethod?.invoke(view)
                    if (res is CharSequence) tabText = res
                } catch (_: Throwable) {}

                addTextTabMethod?.invoke(tabStrip, tabId, tabText, cachedTabs)
                if (firstAvailable == null) {
                    firstAvailable = tabId
                }
            }

            val finishAddingTabsMethod = ReflectionCache.getMethod(stripClass, "finishAddingTabs")
            finishAddingTabsMethod?.invoke(tabStrip)

            if (firstAvailable == null) return

            if (removableIds.contains(currentTabId)) {
                val scrollToMethod = ReflectionCache.getMethod(stripClass, "scrollTo", Int::class.javaPrimitiveType)
                scrollToMethod?.invoke(tabStrip, firstAvailable)
            } else {
                val selectTabWithIdMethod = ReflectionCache.getMethod(
                    stripClass,
                    "selectTabWithId",
                    Int::class.javaPrimitiveType,
                    Float::class.javaPrimitiveType
                )
                selectTabWithIdMethod?.invoke(tabStrip, currentTabId, 1.0f)
            }
        } catch (_: Throwable) {}
    }

    private fun clearEmptyMediaSelection(instance: Any, tabStrip: Any?) {
        try {
            if (tabStrip != null) {
                val setInitialTabIdMethod = ReflectionCache.getMethod(tabStrip.javaClass, "setInitialTabId", Int::class.javaPrimitiveType)
                setInitialTabIdMethod?.invoke(tabStrip, -1)
            }
        } catch (_: Throwable) {}

        try {
            val mediaPagesField = ReflectionCache.getField(instance.javaClass, "mediaPages")
            val mediaPages = mediaPagesField?.get(instance) as? Array<*>
            val savedContainerField = ReflectionCache.getField(instance.javaClass, "savedMessagesContainer")
            val savedContainer = savedContainerField?.get(instance) as? View

            if (mediaPages != null) {
                for (i in 0 until minOf(2, mediaPages.size)) {
                    val page = mediaPages[i] as? ViewGroup ?: continue
                    try {
                        ReflectionCache.getField(page.javaClass, "selectedType")?.setInt(page, -1)
                    } catch (_: Throwable) {}

                    if (savedContainer != null && savedContainer.parent == page) {
                        try {
                            val chatActivityField = ReflectionCache.getField(savedContainer.javaClass, "chatActivity")
                            val chatActivity = chatActivityField?.get(savedContainer)
                            if (chatActivity != null) {
                                ReflectionCache.getMethod(chatActivity.javaClass, "onRemoveFromParent")?.invoke(chatActivity)
                            }
                        } catch (_: Throwable) {}
                        page.removeView(savedContainer)
                    }
                    page.visibility = View.GONE
                }
            }
        } catch (_: Throwable) {}

        (instance as? View)?.visibility = View.GONE
    }

    private fun restoreMediaPageVisibility(instance: Any) {
        try {
            val mediaPagesField = ReflectionCache.getField(instance.javaClass, "mediaPages")
            val mediaPages = mediaPagesField?.get(instance) as? Array<*>
            if (mediaPages != null) {
                for (i in 0 until minOf(2, mediaPages.size)) {
                    (mediaPages[i] as? View)?.visibility = View.VISIBLE
                }
            }
            (instance as? View)?.visibility = View.VISIBLE
        } catch (_: Throwable) {}
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        val sharedMediaLayoutClass = ReflectionCache.findClass("org.telegram.ui.Components.SharedMediaLayout", cl)
        val profileStoriesTabsClass = ReflectionCache.findClass("org.telegram.ui.ProfileStoriesCollectionTabs", cl)
        val tabGiftsClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$TL_profileTabGifts", cl)
        val tabPostsClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$TL_profileTabPosts", cl)

        if (sharedMediaLayoutClass != null) {
            val infoField = ReflectionCache.getField(sharedMediaLayoutClass, "info")
            val userInfoField = ReflectionCache.getField(sharedMediaLayoutClass, "userInfo")
            val tabStripField = ReflectionCache.getField(sharedMediaLayoutClass, "scrollSlidingTextTabStrip")

            fun handleTabRebuild(instance: Any) {
                if (!hideStoriesTab) return
                if (!isSelfProfile(instance)) return

                val hideSavedTabs = hideGiftsTab
                val removable = HashSet<Int>()
                removable.add(8)
                removable.add(9)
                removable.add(13)
                if (hideSavedTabs) {
                    removable.add(11)
                    removable.add(12)
                }

                val tabStrip = tabStripField?.get(instance)
                rebuildProfileTabs(tabStrip, removable)

                if (tabStrip != null) {
                    val count = (ReflectionCache.getMethod(tabStrip.javaClass, "getTabsCount")?.invoke(tabStrip) as? Number)?.toInt() ?: -1
                    if (count == 0) {
                        clearEmptyMediaSelection(instance, tabStrip)
                    } else if (count > 0) {
                        restoreMediaPageVisibility(instance)
                    }
                }
            }

            // 1. Constructors
            hookAllConstructors(sharedMediaLayoutClass, object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideGiftsTab && !hideStoriesTab) return
                    val args = param.args ?: return
                    val chatInfo = if (args.size > 5) args[5] else null
                    val userInfo = if (args.size > 6) args[6] else null

                    if (hideGiftsTab) {
                        removeGifts(chatInfo, tabGiftsClass)
                        removeGifts(userInfo, tabGiftsClass)
                    }
                    if (hideStoriesTab) {
                        removeStories(chatInfo, tabPostsClass)
                        removeStories(userInfo, tabPostsClass)
                    }
                }

                override fun afterHookedMethod(param: MethodHookParam) {
                    val instance = param.thisObject ?: return
                    handleTabRebuild(instance)
                }
            }, unhooksList)

            // 2. updateTabs
            hookAllMethods(sharedMediaLayoutClass, "updateTabs", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideGiftsTab && !hideStoriesTab) return
                    val instance = param.thisObject ?: return
                    val chatInfo = infoField?.get(instance)
                    val userInfo = userInfoField?.get(instance)

                    if (hideGiftsTab) {
                        removeGifts(chatInfo, tabGiftsClass)
                        removeGifts(userInfo, tabGiftsClass)
                    }
                    if (hideStoriesTab) {
                        removeStories(chatInfo, tabPostsClass)
                        removeStories(userInfo, tabPostsClass)
                    }
                }

                override fun afterHookedMethod(param: MethodHookParam) {
                    val instance = param.thisObject ?: return
                    handleTabRebuild(instance)
                }
            }, unhooksList)

            // 3. setChatInfo and setUserInfo
            val setInfoHook = object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideGiftsTab && !hideStoriesTab) return
                    val args = param.args ?: return
                    if (args.isEmpty()) return
                    val infoObj = args[0]
                    if (hideGiftsTab) removeGifts(infoObj, tabGiftsClass)
                    if (hideStoriesTab) removeStories(infoObj, tabPostsClass)
                }
            }
            hookAllMethods(sharedMediaLayoutClass, "setChatInfo", setInfoHook, unhooksList)
            hookAllMethods(sharedMediaLayoutClass, "setUserInfo", setInfoHook, unhooksList)

            // 4. includeStories & isArchivedOnlyStoriesView
            val returnFalseHook = object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideStoriesTab) {
                        param.setResult(false)
                    }
                }
            }
            hookAllMethods(sharedMediaLayoutClass, "includeStories", returnFalseHook, unhooksList)
            hookAllMethods(sharedMediaLayoutClass, "isArchivedOnlyStoriesView", returnFalseHook, unhooksList)
        }

        // 5. ProfileStoriesCollectionTabs.setVisibility
        if (profileStoriesTabsClass != null) {
            hookAllMethods(profileStoriesTabsClass, "setVisibility", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideStoriesTab) return
                    val args = param.args ?: return
                    if (args.isNotEmpty()) {
                        if (args[0] == true) {
                            args[0] = false
                        }
                    }
                }
            }, unhooksList)
        }
    }
}
