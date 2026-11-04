package non.feature.litegram.hide_wallet

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.util.ArrayList
import java.util.Collections
import non.feature.litegram.core.ReflectionCache

object HideWalletHook {

    const val WALLET_BOT_ID = 1985737506L
    const val ACTION_SEND_MONEY = 117
    const val SUBITEM_PROFILE_SEND_MONEY = 48
    const val MAIN_MENU_WALLET_ID = 107
    const val SETTINGS_WALLET_ROW = 25
    const val SETTINGS_GRAM_ROW = 13

    @Volatile @JvmStatic var hideProfileBalance: Boolean = false
    @Volatile @JvmStatic var hideProfileSendMoney: Boolean = false
    @Volatile @JvmStatic var hideChatSendMoney: Boolean = false
    @Volatile @JvmStatic var hideWalletRow: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    val shouldHideDrawer: Boolean
        get() = hideWalletRow

    val shouldHideSettings: Boolean
        get() = hideWalletRow

    val shouldHideProfileBalance: Boolean
        get() = hideProfileBalance

    val shouldHideProfileSendMoney: Boolean
        get() = hideProfileSendMoney

    val shouldHideAttachMenuWallet: Boolean
        get() = false

    val shouldHideChatSendMoney: Boolean
        get() = hideChatSendMoney

    val shouldDisableWalletConfig: Boolean
        get() = hideProfileBalance || hideProfileSendMoney || hideChatSendMoney || hideWalletRow

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideProfileBalance", "hide_profile_balance" -> hideProfileBalance = enabled
            "hideProfileSendMoney", "hide_profile_send_money" -> hideProfileSendMoney = enabled
            "hideChatSendMoney", "hide_chat_send_money" -> hideChatSendMoney = enabled
            "hideWalletRow", "hide_wallet_row" -> hideWalletRow = enabled
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

        hideProfileBalance = false
        hideProfileSendMoney = false
        hideChatSendMoney = false
        hideWalletRow = false
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
        // 1. Hook AppGlobalConfig.ConfigBoolean.get(): global wallet availability kill switch
        val configBooleanClass = ReflectionCache.findClass("org.telegram.messenger.AppGlobalConfig\$ConfigBoolean", cl)
        if (configBooleanClass != null) {
            val handlerField = ReflectionCache.getField(configBooleanClass, "handler")
            val handlerClass = ReflectionCache.findClass("org.telegram.messenger.AppGlobalConfig\$ConfigBoolean\$Internal", cl)
            val nameField = if (handlerClass != null) ReflectionCache.getField(handlerClass, "name") else null

            hookAllMethods(configBooleanClass, "get", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!shouldDisableWalletConfig) return
                    try {
                        val handler = handlerField?.get(param.thisObject) ?: return
                        val name = nameField?.get(handler)?.toString() ?: return
                        if (name == "wallet_available" || name == "wallet_paid_message_recipient_message_amount_check") {
                            param.result = false
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 2. Hook MediaDataController.getAttachMenuBots(): purge Wallet bot from cached list
        val mediaDataControllerClass = ReflectionCache.findClass("org.telegram.messenger.MediaDataController", cl)
        if (mediaDataControllerClass != null) {
            hookAllMethods(mediaDataControllerClass, "getAttachMenuBots", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!shouldDisableWalletConfig && !shouldHideDrawer && !shouldHideAttachMenuWallet) return
                    val attachBotsObj = param.result ?: return
                    try {
                        val botsField = ReflectionCache.getField(attachBotsObj.javaClass, "bots")
                        val botsList = botsField?.get(attachBotsObj) as? MutableList<*> ?: return
                        val it = botsList.iterator()
                        while (it.hasNext()) {
                            val bot = it.next() ?: continue
                            val botId = (ReflectionCache.getField(bot.javaClass, "bot_id")?.get(bot) as? Number)?.toLong() ?: 0L
                            val shortName = ReflectionCache.getField(bot.javaClass, "short_name")?.get(bot)?.toString() ?: ""
                            if (botId == WALLET_BOT_ID || shortName.equals("wallet", ignoreCase = true)) {
                                it.remove()
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 3. Side menu / Drawer hooks
        val mainMenuHelperClass = ReflectionCache.findClass("com.exteragram.messenger.utils.chats.MainMenuHelper", cl)
        if (mainMenuHelperClass != null) {
            hookAllMethods(mainMenuHelperClass, "getAttachMenuBotItems", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!shouldHideDrawer) return
                    val list = param.result as? MutableList<*> ?: return
                    val it = list.iterator()
                    while (it.hasNext()) {
                        val item = it.next() ?: continue
                        try {
                            val bot = ReflectionCache.getField(item.javaClass, "bot")?.get(item)
                            val botId = (ReflectionCache.getField(bot?.javaClass, "bot_id")?.get(bot) as? Number)?.toLong() ?: 0L
                            val name = ReflectionCache.getField(item.javaClass, "name")?.get(item)?.toString() ?: ""
                            if (botId == WALLET_BOT_ID || name.contains("wallet", ignoreCase = true) || name.contains("кошелек", ignoreCase = true) || name.contains("кошелёк", ignoreCase = true)) {
                                it.remove()
                            }
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)

            hookAllMethods(mainMenuHelperClass, "resolveDrawerMenuItems", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!shouldHideDrawer) return
                    val itemId = (param.args?.getOrNull(0) as? Number)?.toInt() ?: return
                    if (itemId == MAIN_MENU_WALLET_ID || itemId == 3) {
                        param.result = Collections.emptyList<Any>()
                    }
                }
            }, unhooksList)
        }

        val itemOptionsClass = ReflectionCache.findClass("org.telegram.ui.Components.ItemOptions", cl)
        if (itemOptionsClass != null) {
            hookAllMethods(itemOptionsClass, "addBot", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!shouldHideDrawer) return
                    val bot = param.args?.getOrNull(0) ?: return
                    try {
                        val botId = (ReflectionCache.getField(bot.javaClass, "bot_id")?.get(bot) as? Number)?.toLong() ?: 0L
                        val shortName = ReflectionCache.getField(bot.javaClass, "short_name")?.get(bot)?.toString() ?: ""
                        if (botId == WALLET_BOT_ID || shortName.equals("wallet", ignoreCase = true)) {
                            param.result = param.thisObject
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 4. Settings: suppress addWalletItem (row 25)
        val settingsActivityClass = ReflectionCache.findClass("org.telegram.ui.SettingsActivity", cl)
        if (settingsActivityClass != null) {
            hookAllMethods(settingsActivityClass, "addWalletItem", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (shouldHideSettings) {
                        param.result = null
                    }
                }
            }, unhooksList)
        }

        // 5. ProfileActivity: balance view, wallet card, 3-dots send money, bot/channel balance rows
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)
        val actionBarMenuItemClass = ReflectionCache.findClass("org.telegram.ui.ActionBar.ActionBarMenuItem", cl)
        if (profileActivityClass != null) {
            val balanceViewField = ReflectionCache.getField(profileActivityClass, "balanceView")
            val hasBalanceField = ReflectionCache.getField(profileActivityClass, "hasBalance")
            val botStarsBalanceRowField = ReflectionCache.getField(profileActivityClass, "botStarsBalanceRow")
            val botTonBalanceRowField = ReflectionCache.getField(profileActivityClass, "botTonBalanceRow")
            val channelBalanceRowField = ReflectionCache.getField(profileActivityClass, "channelBalanceRow")
            val channelBalanceSectionRowField = ReflectionCache.getField(profileActivityClass, "channelBalanceSectionRow")
            val balanceDividerRowField = ReflectionCache.getField(profileActivityClass, "balanceDividerRow")

            hookAllMethods(profileActivityClass, "createView", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val act = param.thisObject ?: return
                    if (shouldHideProfileBalance) {
                        try {
                            (balanceViewField?.get(act) as? View)?.visibility = View.GONE
                            hasBalanceField?.setBoolean(act, false)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)

            hookAllMethods(profileActivityClass, "updateRows", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val act = param.thisObject ?: return
                    if (shouldHideProfileBalance) {
                        try {
                            (balanceViewField?.get(act) as? View)?.visibility = View.GONE
                            hasBalanceField?.setBoolean(act, false)
                            botStarsBalanceRowField?.setInt(act, -1)
                            botTonBalanceRowField?.setInt(act, -1)
                            channelBalanceRowField?.setInt(act, -1)
                            channelBalanceSectionRowField?.setInt(act, -1)
                            balanceDividerRowField?.setInt(act, -1)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)

            // Hide SubItem 48 (WalletSendMoney) in 3-dots menu
            if (actionBarMenuItemClass != null) {
                hookAllMethods(actionBarMenuItemClass, "addSubItem", object : XC_MethodHook(120) {
                    override fun beforeHookedMethod(param: MethodHookParam) {
                        if (!shouldHideProfileSendMoney) return
                        val id = (param.args?.getOrNull(0) as? Number)?.toInt() ?: return
                        if (id == SUBITEM_PROFILE_SEND_MONEY) {
                            param.result = null
                        }
                    }
                }, unhooksList)
            }

            hookAllMethods(profileActivityClass, "onItemClick", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!shouldHideProfileSendMoney) return
                    val id = (param.args?.getOrNull(0) as? Number)?.toInt() ?: return
                    if (id == SUBITEM_PROFILE_SEND_MONEY) {
                        param.result = null
                    }
                }
            }, unhooksList)
        }

        // 6. UserFull & ChatFull deserialization: clear wallet_card and revenue flags
        val userFullClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$UserFull", cl)
        if (userFullClass != null) {
            val walletCardField = ReflectionCache.getField(userFullClass, "wallet_card")
            val canViewRevenueField = ReflectionCache.getField(userFullClass, "can_view_revenue")

            hookAllMethods(userFullClass, "TLdeserialize", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val uf = param.result ?: return
                    if (shouldHideProfileBalance) {
                        try {
                            walletCardField?.set(uf, null)
                            canViewRevenueField?.setBoolean(uf, false)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)
        }

        val chatFullClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$ChatFull", cl)
        if (chatFullClass != null) {
            val canViewStarsRevenueField = ReflectionCache.getField(chatFullClass, "can_view_stars_revenue")
            val canViewRevenueChatField = ReflectionCache.getField(chatFullClass, "can_view_revenue")

            hookAllMethods(chatFullClass, "TLdeserialize", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val cf = param.result ?: return
                    if (shouldHideProfileBalance) {
                        try {
                            canViewStarsRevenueField?.setBoolean(cf, false)
                            canViewRevenueChatField?.setBoolean(cf, false)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)
        }

        // 7. ChatActivity: suppress message context menu action 117 (WalletSendMoney)
        val chatActivityClass = ReflectionCache.findClass("org.telegram.ui.ChatActivity", cl)
        if (chatActivityClass != null) {
            hookAllMethods(chatActivityClass, "onItemClick", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!shouldHideChatSendMoney) return
                    val id = (param.args?.getOrNull(0) as? Number)?.toInt() ?: return
                    if (id == ACTION_SEND_MONEY) {
                        param.result = null
                    }
                }
            }, unhooksList)
        }
    }
}
