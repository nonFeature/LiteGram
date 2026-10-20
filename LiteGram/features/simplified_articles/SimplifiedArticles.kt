package non.feature.litegram.simplified_articles

import android.graphics.drawable.Drawable
import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object SimplifiedArticlesHook {

    @Volatile @JvmStatic var simplifiedArticlesEditor: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    private var buttonClass: Class<*>? = null
    private var requiresPremiumDrawableClass: Class<*>? = null
    private var showPremiumIconField: Field? = null
    private var toolbarPremiumButtonsField: Field? = null

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        if (name == "simplifiedArticlesEditor" || name == "simplified_articles_editor") {
            simplifiedArticlesEditor = enabled
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
        buttonClass = null
        requiresPremiumDrawableClass = null
        showPremiumIconField = null
        toolbarPremiumButtonsField = null
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
        buttonClass = ReflectionCache.findClass("org.telegram.ui.iv.RichEditor\$Button", cl)
        requiresPremiumDrawableClass = ReflectionCache.findClass("org.telegram.ui.iv.RichEditor\$RequiresPremiumDrawable", cl)
        val richEditorToolbarClass = ReflectionCache.findClass("org.telegram.ui.iv.RichEditorToolbar", cl)
        val itemOptionsClass = ReflectionCache.findClass("org.telegram.ui.Components.ItemOptions", cl)

        if (requiresPremiumDrawableClass != null) {
            showPremiumIconField = ReflectionCache.getField(requiresPremiumDrawableClass, "showPremiumIcon")
        }
        if (richEditorToolbarClass != null) {
            toolbarPremiumButtonsField = ReflectionCache.getField(richEditorToolbarClass, "premiumButtons")
        }

        // 1. Hook RichEditor.Button.setPremiumLocked: hide premium/advanced buttons in simplified mode
        if (buttonClass != null) {
            hookAllMethods(buttonClass, "setPremiumLocked", object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val view = param.thisObject as? View ?: return
                    try {
                        val parent = view.parent as? android.view.ViewGroup
                        if (simplifiedArticlesEditor) {
                            view.visibility = View.GONE
                            if (parent != null && parent.childCount == 1) {
                                parent.visibility = View.GONE
                            }
                        } else {
                            view.visibility = View.VISIBLE
                            if (parent != null && parent.childCount == 1) {
                                parent.visibility = View.VISIBLE
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 2. Hook RichEditorToolbar.setPremiumLocked: ensure all toolbar premium buttons are toggled
        if (richEditorToolbarClass != null) {
            hookAllMethods(richEditorToolbarClass, "setPremiumLocked", object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val toolbar = param.thisObject ?: return
                    try {
                        val list = toolbarPremiumButtonsField?.get(toolbar) as? List<*> ?: return
                        for (item in list) {
                            val view = item as? View ?: continue
                            val parent = view.parent as? android.view.ViewGroup
                            if (simplifiedArticlesEditor) {
                                view.visibility = View.GONE
                                if (parent != null && parent.childCount == 1) {
                                    parent.visibility = View.GONE
                                }
                            } else {
                                view.visibility = View.VISIBLE
                                if (parent != null && parent.childCount == 1) {
                                    parent.visibility = View.VISIBLE
                                }
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 3. Hook ItemOptions.addChecked: hide advanced/premium items (headings, pullquote, footer) from menus
        if (itemOptionsClass != null) {
            hookAllMethods(itemOptionsClass, "addChecked", object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!simplifiedArticlesEditor) return
                    val args = param.args ?: return
                    for (arg in args) {
                        if (arg is Drawable && requiresPremiumDrawableClass != null && requiresPremiumDrawableClass!!.isInstance(arg)) {
                            param.result = param.thisObject
                            return
                        }
                    }
                }
            }, unhooksList)
        }
    }
}
