package non.feature.litegram.hide_premium_features

import android.view.View
import android.view.ViewGroup
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Modifier
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object HidePremiumFeaturesHook {

    @Volatile @JvmStatic var hidePremiumFeatures: Boolean = false
    @Volatile @JvmStatic var inFilterCreate: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hidePremiumFeatures", "hide_premium_features" -> hidePremiumFeatures = enabled
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

        hidePremiumFeatures = false
        inFilterCreate = false
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

    private fun hideRow(clazz: Class<*>, instance: Any?, fieldName: String) {
        if (instance == null) return
        try {
            val field = ReflectionCache.getField(clazz, fieldName) ?: return
            val rowIdx = field.getInt(instance)
            if (rowIdx != -1) {
                val rowCountField = ReflectionCache.getField(clazz, "rowCount") ?: return
                val rowCount = rowCountField.getInt(instance)

                field.setInt(instance, -1)
                for (f in clazz.declaredFields) {
                    if (f.type == Int::class.javaPrimitiveType && f.name.contains("row", ignoreCase = true) && !Modifier.isStatic(f.modifiers)) {
                        f.isAccessible = true
                        val v = f.getInt(instance)
                        if (v in (rowIdx + 1) until rowCount) {
                            f.setInt(instance, v - 1)
                        }
                    }
                }
                rowCountField.setInt(instance, rowCount - 1)
            }
        } catch (_: Throwable) {}
    }

    private fun getItemViewType(item: Any?): Int {
        if (item == null) return -1
        try {
            val field = ReflectionCache.getField(item.javaClass, "viewType")
            if (field != null) return field.getInt(item)
        } catch (_: Throwable) {}
        return -1
    }

    private fun getItemText(item: Any?): String {
        if (item == null) return ""
        try {
            val field = ReflectionCache.getField(item.javaClass, "text")
            val v = field?.get(item)
            if (v != null) return v.toString()
        } catch (_: Throwable) {}
        return ""
    }

    private fun removeExteraSettingEntry(registry: Any?, alias: String) {
        if (registry == null) return
        try {
            val entriesField = ReflectionCache.getField(registry.javaClass, "entriesStringAlias")
            val map = entriesField?.get(registry) as? MutableMap<*, *>
            map?.remove(alias)
        } catch (_: Throwable) {}

        try {
            val preparedField = ReflectionCache.getField(registry.javaClass, "preparedEntries")
            val prepared = preparedField?.get(registry) ?: return

            if (prepared is MutableMap<*, *>) {
                val keys = ArrayList(prepared.keys)
                for (k in keys) {
                    val v = prepared[k]
                    if (v is MutableList<*>) {
                        val it = v.iterator()
                        while (it.hasNext()) {
                            val entry = it.next() ?: continue
                            val guid = ReflectionCache.getField(entry.javaClass, "guid")?.get(entry)?.toString()
                            if (guid == alias) {
                                it.remove()
                            }
                        }
                    } else if (v != null) {
                        val guid = ReflectionCache.getField(v.javaClass, "guid")?.get(v)?.toString()
                        if (guid == alias) {
                            prepared.remove(k)
                        }
                    }
                }
            } else if (prepared is MutableList<*>) {
                val it = prepared.iterator()
                while (it.hasNext()) {
                    val entry = it.next() ?: continue
                    val guid = ReflectionCache.getField(entry.javaClass, "guid")?.get(entry)?.toString()
                    if (guid == alias) {
                        it.remove()
                    }
                }
            }
        } catch (_: Throwable) {}
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        val privacySettingsClass = ReflectionCache.findClass("org.telegram.ui.PrivacySettingsActivity", cl)
        val privacyControlClass = ReflectionCache.findClass("org.telegram.ui.PrivacyControlActivity", cl)
        val textInfoPrivacyCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.TextInfoPrivacyCell", cl)
        val filtersSetupClass = ReflectionCache.findClass("org.telegram.ui.FiltersSetupActivity", cl)
        val messagesControllerClass = ReflectionCache.findClass("org.telegram.messenger.MessagesController", cl)
        val userConfigClass = ReflectionCache.findClass("org.telegram.messenger.UserConfig", cl)
        val generalPrefsClass = ReflectionCache.findClass("com.exteragram.messenger.preferences.GeneralPreferencesActivity", cl)
        val settingsRegistryClass = ReflectionCache.findClass("com.exteragram.messenger.preferences.utils.SettingsRegistry", cl)
        val filterCreateClass = ReflectionCache.findClass("org.telegram.ui.FilterCreateActivity", cl)
        val filterCreateListAdapterClass = ReflectionCache.findClass("org.telegram.ui.FilterCreateActivity\$ListAdapter", cl)
        val dialogCellTagsClass = ReflectionCache.findClass("org.telegram.ui.Components.DialogCellTags", cl)

        // 1. PrivacySettingsActivity: voice messages & premium star
        if (privacySettingsClass != null) {
            hookAllMethods(privacySettingsClass, "updateRows", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val instance = param.thisObject ?: return
                    hideRow(instance.javaClass, instance, "voicesRow")
                }
            }, unhooksList)

            hookAllMethods(privacySettingsClass, "addPremiumStar", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val args = param.args ?: return
                    if (args.isNotEmpty() && args[0] != null) {
                        param.setResult(args[0])
                    }
                }
            }, unhooksList)
        }

        // 2. PrivacyControlActivity: payRow & priceButtonRow
        if (privacyControlClass != null) {
            val rulesTypeField = ReflectionCache.getField(privacyControlClass, "rulesType")

            hookAllMethods(privacyControlClass, "setMessageText", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val instance = param.thisObject ?: return
                    val rulesType = rulesTypeField?.getInt(instance) ?: -1
                    if (rulesType == 10) {
                        hideRow(instance.javaClass, instance, "payRow")
                        hideRow(instance.javaClass, instance, "priceButtonRow")
                    }
                }
            }, unhooksList)
        }

        // 2.1 TextInfoPrivacyCell.setText
        if (textInfoPrivacyCellClass != null) {
            hookAllMethods(textInfoPrivacyCellClass, "setText", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val args = param.args ?: return
                    if (args.isEmpty()) return
                    val text = args[0] ?: return
                    var textStr = text.toString()
                    if (textStr.contains("Вы можете запретить входящие сообщения") || textStr.contains("You can restrict who can send you messages")) {
                        if (textStr.contains("\n")) {
                            textStr = textStr.substringBefore("\n").trim()
                        } else if (textStr.contains("**")) {
                            textStr = textStr.substringBefore("**").trim()
                        } else if (textStr.contains("Premium")) {
                            val parts = textStr.split(".")
                            if (parts.size > 1) {
                                textStr = parts[0].trim() + "."
                            }
                        }
                        args[0] = textStr
                    }
                }
            }, unhooksList)
        }

        // 3. FiltersSetupActivity: folder tags
        if (filtersSetupClass != null) {
            val showTagsRowField = ReflectionCache.getField(filtersSetupClass, "showTagsRow")
            val folderTagsPositionField = ReflectionCache.getField(filtersSetupClass, "folderTagsPosition")
            val itemsField = ReflectionCache.getField(filtersSetupClass, "items")
            val adapterField = ReflectionCache.getField(filtersSetupClass, "adapter")

            hookAllMethods(filtersSetupClass, "updateRows", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val instance = param.thisObject ?: return
                    try {
                        val showTagsRow = showTagsRowField?.getInt(instance) ?: -1
                        if (showTagsRow != -1) {
                            val items = itemsField?.get(instance) as? MutableList<*>
                            if (items != null && showTagsRow < items.size) {
                                items.removeAt(showTagsRow)
                                if (showTagsRow < items.size) {
                                    items.removeAt(showTagsRow)
                                }
                                showTagsRowField?.setInt(instance, -1)
                                folderTagsPositionField?.setInt(instance, -1)
                                adapterField?.get(instance)?.let { ad ->
                                    ReflectionCache.getMethod(ad.javaClass, "notifyDataSetChanged")?.invoke(ad)
                                }
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 4. MessagesController
        if (messagesControllerClass != null) {
            val folderTagsField = ReflectionCache.getField(messagesControllerClass, "folderTags")

            hookAllMethods(messagesControllerClass, "isTranslationsAutoEnabled", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hidePremiumFeatures) {
                        param.setResult(false)
                    }
                }
            }, unhooksList)

            hookAllConstructors(messagesControllerClass, object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (hidePremiumFeatures) {
                        val inst = param.thisObject ?: return
                        try {
                            folderTagsField?.setBoolean(inst, false)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)

            hookAllMethods(messagesControllerClass, "setFolderTags", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hidePremiumFeatures) {
                        param.args?.let { if (it.isNotEmpty()) it[0] = false }
                        val inst = param.thisObject ?: return
                        try {
                            folderTagsField?.setBoolean(inst, false)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)
        }

        // 4.1 UserConfig.isPremium
        if (userConfigClass != null) {
            hookAllMethods(userConfigClass, "isPremium", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hidePremiumFeatures && inFilterCreate) {
                        param.setResult(true)
                    }
                }
            }, unhooksList)
        }

        // 4.2 GeneralPreferencesActivity.fillItems
        if (generalPrefsClass != null) {
            hookAllMethods(generalPrefsClass, "fillItems", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val list = param.args?.getOrNull(0) as? MutableList<*> ?: return
                    for (i in list.indices.reversed()) {
                        val item = list[i] ?: continue
                        try {
                            val idVal = (ReflectionCache.getField(item.javaClass, "id")?.get(item) as? Number)?.toInt()
                                ?: (ReflectionCache.getField(item.javaClass, "f1708id")?.get(item) as? Number)?.toInt()
                                ?: -1
                            if (idVal == 2) {
                                list.removeAt(i)
                            }
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)
        }

        // 5. SettingsRegistry
        if (settingsRegistryClass != null) {
            hookAllMethods(settingsRegistryClass, "createEntriesIfNeeded", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (hidePremiumFeatures) {
                        removeExteraSettingEntry(param.thisObject, "showTranslateChatButton")
                    }
                }
            }, unhooksList)
        }

        // 6. FilterCreateActivity & ListAdapter
        if (filterCreateClass != null) {
            hookAllConstructors(filterCreateClass, object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    inFilterCreate = true
                }
            }, unhooksList)

            hookAllMethods(filterCreateClass, "onFragmentDestroy", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    inFilterCreate = false
                }
            }, unhooksList)

            val itemsField = ReflectionCache.getField(filterCreateClass, "items")
            val adapterField = ReflectionCache.getField(filterCreateClass, "adapter")

            hookAllMethods(filterCreateClass, "updateRows", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val instance = param.thisObject ?: return
                    try {
                        val items = itemsField?.get(instance) as? MutableList<*> ?: return
                        for (i in items.indices.reversed()) {
                            val item = items[i] ?: continue
                            val vt = getItemViewType(item)
                            if (vt == 9 || vt == 10) {
                                items.removeAt(i)
                            } else if (vt == 0 || vt == 3 || vt == 6) {
                                val text = getItemText(item).lowercase()
                                if (text.contains("цвет тега") || text.contains("tag color") || text.contains("folder tag")) {
                                    items.removeAt(i)
                                }
                            }
                        }
                        adapterField?.get(instance)?.let { ad ->
                            ReflectionCache.getMethod(ad.javaClass, "notifyDataSetChanged")?.invoke(ad)
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        if (filterCreateListAdapterClass != null) {
            hookAllMethods(filterCreateListAdapterClass, "onCreateViewHolder", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val holder = param.result ?: return
                    val itemViewField = ReflectionCache.getField(holder.javaClass, "itemView")
                    val view = itemViewField?.get(holder) as? View ?: return
                    val clsName = view.javaClass.name
                    if (clsName.contains("HeaderCellColorPreview") || clsName.contains("PeerColorGrid")) {
                        view.visibility = View.GONE
                        val lp = view.layoutParams
                        if (lp != null) {
                            lp.height = 0
                            lp.width = 0
                            view.layoutParams = lp
                        }
                    }
                }
            }, unhooksList)

            hookAllMethods(filterCreateListAdapterClass, "onBindViewHolder", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val holder = param.args?.getOrNull(0) ?: return
                    val itemViewField = ReflectionCache.getField(holder.javaClass, "itemView")
                    val view = itemViewField?.get(holder) as? View ?: return
                    val clsName = view.javaClass.name
                    val vt = (ReflectionCache.getMethod(holder.javaClass, "getItemViewType")?.invoke(holder) as? Number)?.toInt() ?: -1
                    if (vt == 9 || vt == 10 || clsName.contains("HeaderCellColorPreview") || clsName.contains("PeerColorGrid")) {
                        view.visibility = View.GONE
                        val lp = view.layoutParams
                        if (lp != null) {
                            lp.height = 0
                            lp.width = 0
                            view.layoutParams = lp
                        }
                    }
                }
            }, unhooksList)
        }

        // 7. DialogCellTags.update
        if (dialogCellTagsClass != null) {
            val tagsField = ReflectionCache.getField(dialogCellTagsClass, "tags")

            hookAllMethods(dialogCellTagsClass, "update", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hidePremiumFeatures) return
                    val obj = param.thisObject ?: return
                    try {
                        val tags = tagsField?.get(obj) as? MutableCollection<*>
                        tags?.clear()
                    } catch (_: Throwable) {}
                    param.setResult(false)
                }
            }, unhooksList)
        }
    }
}
