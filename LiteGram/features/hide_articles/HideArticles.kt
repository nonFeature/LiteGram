package non.feature.litegram.hide_articles

import android.graphics.drawable.Drawable
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.HorizontalScrollView
import android.widget.PopupWindow
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object HideArticlesHook {

    @Volatile @JvmStatic var hideArticlesEditor: Boolean = false
    @Volatile @JvmStatic var simplifiedArticlesEditor: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    private var buttonClass: Class<*>? = null
    private var requiresPremiumDrawableClass: Class<*>? = null
    private var showPremiumIconField: Field? = null
    private var toolbarPremiumButtonsField: Field? = null

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideArticlesEditor", "hide_articles_editor" -> hideArticlesEditor = enabled
            "simplifiedArticlesEditor", "simplified_articles_editor" -> simplifiedArticlesEditor = enabled
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
        hideArticlesEditor = false
        simplifiedArticlesEditor = false
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

    private fun isRichEditorBottomButton(scrimView: View?, fragment: Any?): Boolean {
        if (scrimView == null) return false
        val isButton = buttonClass != null && buttonClass!!.isInstance(scrimView)
        val isRichEditor = fragment != null && fragment.javaClass.name.contains("RichEditor")
        if (!isButton && !isRichEditor) return false

        var p = scrimView.parent
        while (p != null) {
            if (p is HorizontalScrollView) {
                return true
            }
            p = p.parent
        }
        return false
    }

    private fun clampPopupPosition(
        itemOptions: Any,
        containerField: Field?,
        pointContainerField: Field?,
        layoutField: Field?,
        offsetXField: Field?,
        offsetYField: Field?,
        popupWindowField: Field?
    ) {
        try {
            val popup = popupWindowField?.get(itemOptions) as? PopupWindow ?: return
            if (!popup.isShowing) return
            val container = (containerField?.get(itemOptions) as? ViewGroup)
                ?: (pointContainerField?.get(itemOptions) as? ViewGroup) ?: return
            val layout = layoutField?.get(itemOptions) as? View ?: return
            val currentX = (offsetXField?.get(itemOptions) as? Number)?.toFloat() ?: return
            val currentY = (offsetYField?.get(itemOptions) as? Number)?.toFloat() ?: return
            val containerWidth = container.width
            val layoutWidth = layout.measuredWidth
            if (containerWidth > 0 && layoutWidth > 0) {
                val pad = container.resources.displayMetrics.density * 8f
                val minX = pad
                val maxX = (containerWidth - layoutWidth - pad).coerceAtLeast(minX)
                val clampedX = currentX.coerceIn(minX, maxX)
                if (Math.abs(clampedX - currentX) > 1f) {
                    offsetXField.set(itemOptions, clampedX)
                    popup.update(clampedX.toInt(), currentY.toInt(), -1, -1)
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
        val richEditorListViewClass = ReflectionCache.findClass("org.telegram.ui.iv.RichEditorListView", cl)
        val blockRowClass = ReflectionCache.findClass("org.telegram.ui.iv.BlockRow", cl)

        if (requiresPremiumDrawableClass != null) {
            showPremiumIconField = ReflectionCache.getField(requiresPremiumDrawableClass, "showPremiumIcon")
        }
        if (richEditorToolbarClass != null) {
            toolbarPremiumButtonsField = ReflectionCache.getField(richEditorToolbarClass, "premiumButtons")
        }

        // 0. Hook MessagesController.richEditorAvailable & richEditorAllowed: completely hide rich/articles editor
        val messagesControllerClass = ReflectionCache.findClass("org.telegram.messenger.MessagesController", cl)
        if (messagesControllerClass != null) {
            val hideHook = object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideArticlesEditor) {
                        param.setResult(false)
                    }
                }
            }
            hookAllMethods(messagesControllerClass, "richEditorAvailable", hideHook, unhooksList)
            hookAllMethods(messagesControllerClass, "richEditorAllowed", hideHook, unhooksList)
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
                            param.setResult(param.thisObject)
                            return
                        }
                    }
                }
            }, unhooksList)

            // 4. Hook ItemOptions.show and reposition: center toolbar formatting menus horizontally above the button
            val scrimViewField = ReflectionCache.getField(itemOptionsClass, "scrimView")
            val fragmentField = ReflectionCache.getField(itemOptionsClass, "fragment")
            val gravityField = ReflectionCache.getField(itemOptionsClass, "gravity")
            val containerField = ReflectionCache.getField(itemOptionsClass, "container")
            val pointContainerField = ReflectionCache.getField(itemOptionsClass, "pointContainer")
            val layoutField = ReflectionCache.getField(itemOptionsClass, "layout")
            val offsetXField = ReflectionCache.getField(itemOptionsClass, "offsetX")
            val offsetYField = ReflectionCache.getField(itemOptionsClass, "offsetY")
            val popupWindowField = ReflectionCache.getField(itemOptionsClass, "actionBarPopupWindow")
            val setGravityMethod = ReflectionCache.getMethod(itemOptionsClass, "setGravity", Int::class.javaPrimitiveType)

            hookAllMethods(itemOptionsClass, "show", object : XC_MethodHook() {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!simplifiedArticlesEditor) return
                    val itemOptions = param.thisObject ?: return
                    val scrimView = scrimViewField?.get(itemOptions) as? View
                    val fragment = fragmentField?.get(itemOptions)
                    if (isRichEditorBottomButton(scrimView, fragment)) {
                        if (setGravityMethod != null) {
                            try {
                                setGravityMethod.invoke(itemOptions, Gravity.CENTER_HORIZONTAL)
                            } catch (_: Throwable) {
                                gravityField?.setInt(itemOptions, Gravity.CENTER_HORIZONTAL)
                            }
                        } else {
                            gravityField?.setInt(itemOptions, Gravity.CENTER_HORIZONTAL)
                        }
                    }
                }

                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!simplifiedArticlesEditor) return
                    val itemOptions = param.thisObject ?: return
                    val scrimView = scrimViewField?.get(itemOptions) as? View
                    val fragment = fragmentField?.get(itemOptions)
                    if (isRichEditorBottomButton(scrimView, fragment)) {
                        clampPopupPosition(itemOptions, containerField, pointContainerField, layoutField, offsetXField, offsetYField, popupWindowField)
                    }
                }
            }, unhooksList)

            hookAllMethods(itemOptionsClass, "reposition", object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!simplifiedArticlesEditor) return
                    val itemOptions = param.thisObject ?: return
                    val scrimView = scrimViewField?.get(itemOptions) as? View
                    val fragment = fragmentField?.get(itemOptions)
                    if (isRichEditorBottomButton(scrimView, fragment)) {
                        clampPopupPosition(itemOptions, containerField, pointContainerField, layoutField, offsetXField, offsetYField, popupWindowField)
                    }
                }
            }, unhooksList)
        }

        // 5. Hook RichEditorListView.seedEmptyArticle: remove default Heading 1 so new article preset starts with plain text only
        if (richEditorListViewClass != null) {
            val rowsField = ReflectionCache.getField(richEditorListViewClass, "rows")
            val adapterField = ReflectionCache.getField(richEditorListViewClass, "adapter")
            val blockField = if (blockRowClass != null) ReflectionCache.getField(blockRowClass, "block") else null

            hookAllMethods(richEditorListViewClass, "seedEmptyArticle", object : XC_MethodHook() {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!simplifiedArticlesEditor) return
                    val listView = param.thisObject ?: return
                    try {
                        val rows = rowsField?.get(listView) as? ArrayList<*> ?: return
                        if (rows.isNotEmpty()) {
                            val first = rows[0] ?: return
                            val block = blockField?.get(first)
                            if (block != null && block.javaClass.name.contains("pageBlockHeading")) {
                                rows.removeAt(0)
                                val adapter = adapterField?.get(listView)
                                if (adapter != null) {
                                    val updateMethod = ReflectionCache.getMethod(adapter.javaClass, "update", Boolean::class.javaPrimitiveType)
                                    updateMethod?.invoke(adapter, false)
                                }
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }
    }
}
