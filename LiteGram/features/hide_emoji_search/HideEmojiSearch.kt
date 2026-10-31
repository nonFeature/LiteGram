package non.feature.litegram.hide_emoji_search

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object HideEmojiSearchHook {

    @Volatile @JvmStatic var hideEmojiSearch: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    private var stickerCategoriesListViewClass: Class<*>? = null

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideEmojiSearch", "hide_emoji_search" -> hideEmojiSearch = enabled
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

        hideEmojiSearch = false
        stickerCategoriesListViewClass = null
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
        stickerCategoriesListViewClass = ReflectionCache.findClass(
            "org.telegram.ui.Components.StickerCategoriesListView", cl
        )
        if (stickerCategoriesListViewClass == null) return

        // 1. Hook updateCategoriesShown: force first argument (shown) to false
        hookAllMethods(stickerCategoriesListViewClass, "updateCategoriesShown", object : XC_MethodHook(120) {
            override fun beforeHookedMethod(param: MethodHookParam) {
                if (!hideEmojiSearch) return
                val args = param.args
                if (args != null && args.isNotEmpty()) {
                    args[0] = false
                }
            }
        }, unhooksList)

        // 2. Hook onLayout: force view visibility to GONE
        hookAllMethods(stickerCategoriesListViewClass, "onLayout", object : XC_MethodHook(120) {
            override fun afterHookedMethod(param: MethodHookParam) {
                if (!hideEmojiSearch) return
                val view = param.thisObject as? View ?: return
                if (view.visibility != View.GONE) {
                    view.visibility = View.GONE
                }
            }
        }, unhooksList)
    }
}
