package non.feature.litegram.profile_actions

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object ProfileActionsHook {

    const val KEY_GIFT = 3
    const val KEY_VOICE_CHAT = 10
    const val KEY_STREAM = 11
    const val KEY_STORY = 12

    @Volatile @JvmStatic var hideGiftButton: Boolean = false
    @Volatile @JvmStatic var hideStoriesButton: Boolean = false
    @Volatile @JvmStatic var hideStreamButton: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideProfileActionsGiftButton", "hide_profile_actions_gift_button" -> hideGiftButton = enabled
            "hideProfileActionsStoriesButton", "hide_profile_actions_stories_button" -> hideStoriesButton = enabled
            "hideProfileActionsStreamButton", "hide_profile_actions_stream_button" -> hideStreamButton = enabled
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

        hideGiftButton = false
        hideStoriesButton = false
        hideStreamButton = false
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
        val profileActionsViewClass = ReflectionCache.findClass("org.telegram.ui.Components.ProfileActionsView", cl)
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)
        val profileGiftsContainerClass = ReflectionCache.findClass("org.telegram.ui.Gifts.ProfileGiftsContainer", cl)
        val profileGiftsContainerPageClass = ReflectionCache.findClass("org.telegram.ui.Gifts.ProfileGiftsContainer\$Page", cl)

        // 1. ProfileActionsView hooks
        if (profileActionsViewClass != null) {
            hookAllMethods(profileActionsViewClass, "set", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideGiftButton && !hideStoriesButton && !hideStreamButton) return
                    val args = param.args ?: return
                    if (args.isEmpty()) return
                    val currentKey = (args[0] as? Number)?.toInt() ?: return

                    val shouldHide = (hideGiftButton && currentKey == KEY_GIFT) ||
                            (hideStoriesButton && currentKey == KEY_STORY) ||
                            (hideStreamButton && (currentKey == KEY_VOICE_CHAT || currentKey == KEY_STREAM))

                    if (shouldHide) {
                        param.setResult(null)
                    }
                }
            }, unhooksList)

            val visibleActionsField = ReflectionCache.getField(profileActionsViewClass, "visibleActions")
            val actionsListField = ReflectionCache.getField(profileActionsViewClass, "actionsList")
            val allAvailableActionsField = ReflectionCache.getField(profileActionsViewClass, "allAvailableActions")

            hookAllMethods(profileActionsViewClass, "applyVisibleActions", object : XC_MethodHook(100) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hideGiftButton && !hideStoriesButton && !hideStreamButton) return
                    val obj = param.thisObject ?: return

                    val targetKeys = ArrayList<Int>(4)
                    if (hideGiftButton) targetKeys.add(KEY_GIFT)
                    if (hideStoriesButton) targetKeys.add(KEY_STORY)
                    if (hideStreamButton) {
                        targetKeys.add(KEY_VOICE_CHAT)
                        targetKeys.add(KEY_STREAM)
                    }

                    fun removeKeys(collection: Any?) {
                        if (collection is MutableCollection<*>) {
                            for (key in targetKeys) {
                                collection.remove(key)
                            }
                        }
                    }

                    try {
                        removeKeys(visibleActionsField?.get(obj))
                        removeKeys(actionsListField?.get(obj))
                        removeKeys(allAvailableActionsField?.get(obj))
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 2. ProfileActivity.updateBottomButtonY
        if (profileActivityClass != null) {
            val bottomButtonsContainerField = ReflectionCache.getField(profileActivityClass, "bottomButtonsContainer")

            hookAllMethods(profileActivityClass, "updateBottomButtonY", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideStoriesButton) return
                    param.setResult(null)
                    val instance = param.thisObject ?: return
                    try {
                        val container = bottomButtonsContainerField?.get(instance) as? View
                        container?.visibility = View.GONE
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 3. ProfileGiftsContainer hooks
        if (profileGiftsContainerClass != null) {
            val buttonContainerField = ReflectionCache.getField(profileGiftsContainerClass, "buttonContainer")

            hookAllMethods(profileGiftsContainerClass, "updateButton", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideGiftButton) return
                    param.setResult(null)
                    val instance = param.thisObject ?: return
                    try {
                        val container = buttonContainerField?.get(instance) as? View
                        container?.visibility = View.GONE
                    } catch (_: Throwable) {}
                }
            }, unhooksList)

            hookAllMethods(profileGiftsContainerClass, "getBottomOffset", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideGiftButton) {
                        param.setResult(0)
                    }
                }
            }, unhooksList)
        }

        // 4. ProfileGiftsContainer$Page.updateEmptyView
        if (profileGiftsContainerPageClass != null) {
            val emptyView1ButtonField = ReflectionCache.getField(profileGiftsContainerPageClass, "emptyView1Button")

            hookAllMethods(profileGiftsContainerPageClass, "updateEmptyView", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hideGiftButton) return
                    val instance = param.thisObject ?: return
                    try {
                        val button = emptyView1ButtonField?.get(instance) as? View
                        button?.visibility = View.GONE
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }
    }
}
