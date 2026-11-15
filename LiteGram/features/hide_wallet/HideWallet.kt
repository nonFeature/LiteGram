package non.feature.litegram.hide_wallet

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

/**
 * Wallet hiding — one switch per surface:
 * - hideWalletRow         -> settings list row (SettingsActivity.addWalletItem)
 * - hideWalletDrawer      -> side menu WALLET entry + wallet bot in the drawer bots section
 * - hideWalletAttach      -> chat attachment panel: wallet bot + "Money" (send Gram) button
 * - hideProfileBalance    -> balance view / wallet card / revenue rows in profiles
 * - hideProfileSendMoney  -> "Send Money" in profile (3-dots menu + wallet card dialog)
 * - hideChatSendMoney     -> "Send Money" in chat (message context menu + TON address sheet)
 *
 * exteragram gates most wallet UI on config.wallet_available. The ConfigBoolean.get hook
 * answers it per-surface: the caller is identified by the innermost app frame in the
 * stack, so each switch kills exactly its own entry points.
 */
object HideWalletHook {

    const val WALLET_BOT_ID = 1985737506L

    @Volatile @JvmStatic var hideWalletRow: Boolean = false
    @Volatile @JvmStatic var hideWalletDrawer: Boolean = false
    @Volatile @JvmStatic var hideWalletAttach: Boolean = false
    @Volatile @JvmStatic var hideProfileBalance: Boolean = false
    @Volatile @JvmStatic var hideProfileSendMoney: Boolean = false
    @Volatile @JvmStatic var hideChatSendMoney: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideWalletRow", "hide_wallet_row" -> hideWalletRow = enabled
            "hideWalletDrawer", "hide_wallet_drawer" -> hideWalletDrawer = enabled
            "hideWalletAttach", "hide_wallet_attach" -> hideWalletAttach = enabled
            "hideProfileBalance", "hide_profile_balance" -> hideProfileBalance = enabled
            "hideProfileSendMoney", "hide_profile_send_money" -> hideProfileSendMoney = enabled
            "hideChatSendMoney", "hide_chat_send_money" -> hideChatSendMoney = enabled
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

        hideWalletRow = false
        hideWalletDrawer = false
        hideWalletAttach = false
        hideProfileBalance = false
        hideProfileSendMoney = false
        hideChatSendMoney = false
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

    private fun isWalletBot(bot: Any?): Boolean {
        bot ?: return false
        return try {
            val botId = (ReflectionCache.getField(bot.javaClass, "bot_id")?.get(bot) as? Number)?.toLong() ?: 0L
            val shortName = ReflectionCache.getField(bot.javaClass, "short_name")?.get(bot)?.toString()
            botId == WALLET_BOT_ID || shortName.equals("wallet", ignoreCase = true)
        } catch (_: Throwable) {
            false
        }
    }

    /** Innermost app frame of the stack — the class that actually reads the config value. */
    private fun nearestCaller(stack: Array<StackTraceElement>): String? {
        for (el in stack) {
            val cn = el.className
            if (cn.startsWith("org.telegram.ui.") || cn.startsWith("com.exteragram.messenger.")) {
                return cn
            }
        }
        return null
    }

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        // 1. Settings row: SettingsActivity.addWalletItem adds the wallet UItem
        val settingsActivityClass = ReflectionCache.findClass("org.telegram.ui.SettingsActivity", cl)
        if (settingsActivityClass != null) {
            hookAllMethods(settingsActivityClass, "addWalletItem", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideWalletRow) {
                        param.result = null
                    }
                }
            }, unhooksList)
        }

        // 2. Drawer bots section: purge the wallet bot from the list MainMenuHelper builds
        val mainMenuHelperClass = ReflectionCache.findClass("com.exteragram.messenger.utils.chats.MainMenuHelper", cl)
        if (mainMenuHelperClass != null) {
            hookAllMethods(mainMenuHelperClass, "getAttachMenuBotItems", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hideWalletDrawer) return
                    val list = param.result as? MutableList<*> ?: return
                    val it = list.iterator()
                    while (it.hasNext()) {
                        val item = it.next() ?: continue
                        try {
                            val botField = try {
                                ReflectionCache.getField(item.javaClass, "bot")?.get(item)
                            } catch (_: Throwable) {
                                null
                            }
                            val bot = botField ?: try {
                                ReflectionCache.getMethod(item.javaClass, "bot")?.invoke(item)
                            } catch (_: Throwable) {
                                null
                            }
                            if (isWalletBot(bot)) {
                                it.remove()
                            }
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)
        }

        // 3. Chat attachment panel: wallet bot shortcut (display-time filter per bot)
        val mediaDataControllerClass = ReflectionCache.findClass("org.telegram.messenger.MediaDataController", cl)
        if (mediaDataControllerClass != null) {
            hookAllMethods(mediaDataControllerClass, "canShowAttachMenuBot", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideWalletAttach) return
                    if (isWalletBot(param.args?.getOrNull(0))) {
                        param.result = false
                    }
                }
            }, unhooksList)
        }

        // 4. Per-surface answers for config.wallet_available
        val configBooleanClass = ReflectionCache.findClass("org.telegram.messenger.AppGlobalConfig\$ConfigBoolean", cl)
        if (configBooleanClass != null) {
            val handlerField = ReflectionCache.getField(configBooleanClass, "handler")
            val handlerClass = ReflectionCache.findClass("org.telegram.messenger.AppGlobalConfig\$ConfigBoolean\$Internal", cl)
            val nameField = if (handlerClass != null) ReflectionCache.getField(handlerClass, "name") else null

            hookAllMethods(configBooleanClass, "get", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideWalletDrawer && !hideProfileSendMoney && !hideChatSendMoney) return
                    try {
                        val handler = handlerField?.get(param.thisObject) ?: return
                        if (nameField?.get(handler)?.toString() != "wallet_available") return
                        val caller = nearestCaller(Thread.currentThread().stackTrace) ?: return
                        when {
                            // message context menu (id 117) + TON address sheet
                            caller.startsWith("org.telegram.ui.ChatActivity") -> {
                                if (hideChatSendMoney) param.result = false
                            }
                            // attach panel "Money" button (ChatAttachAlert$ButtonsAdapter) — belongs to the attach surface
                            caller.startsWith("org.telegram.ui.Components.ChatAttachAlert") -> {
                                if (hideWalletAttach) param.result = false
                            }
                            // profile 3-dots subitem, wallet card dialog "Send Money" button
                            caller.startsWith("org.telegram.ui.ProfileActivity") ||
                                caller.startsWith("org.telegram.ui.Wallet.ProfileWalletCardDialog") -> {
                                if (hideProfileSendMoney) param.result = false
                            }
                            // side menu WALLET entry (MainMenuHelper.resolveMenuItem)
                            caller.startsWith("com.exteragram.messenger.utils.chats.MainMenuHelper") -> {
                                if (hideWalletDrawer) param.result = false
                            }
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 5. Profile: hide the balance pill only, nothing else.
        // wallet_card is nulled just for the duration of updateRows*/createView so
        // hasBalance computes false natively (no flicker, no reserved space), then
        // restored — the wallet card dialog and revenue rows stay untouched.
        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)
        if (profileActivityClass != null) {
            val balanceViewField = ReflectionCache.getField(profileActivityClass, "balanceView")
            val hasBalanceField = ReflectionCache.getField(profileActivityClass, "hasBalance")
            val userInfoField = ReflectionCache.getField(profileActivityClass, "userInfo")
            val userFullClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$UserFull", cl)
            val walletCardField = if (userFullClass != null) ReflectionCache.getField(userFullClass, "wallet_card") else null
            val stash = ThreadLocal<Array<Any?>>()

            val pillHook = object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideProfileBalance || walletCardField == null) return
                    val act = param.thisObject ?: return
                    try {
                        val uf = userInfoField?.get(act) ?: return
                        stash.set(arrayOf(uf, walletCardField.get(uf)))
                        walletCardField.set(uf, null)
                    } catch (_: Throwable) {}
                }

                override fun afterHookedMethod(param: MethodHookParam) {
                    if (!hideProfileBalance) return
                    val act = param.thisObject ?: return
                    try {
                        val stashed = stash.get()
                        if (stashed != null) {
                            stash.remove()
                            try {
                                walletCardField?.set(stashed[0], stashed[1])
                            } catch (_: Throwable) {}
                        }
                        (balanceViewField?.get(act) as? View)?.visibility = View.GONE
                        hasBalanceField?.setBoolean(act, false)
                    } catch (_: Throwable) {}
                }
            }
            // exteragram calls it updateRows, ayugram renamed it to updateRowsIds — hook both
            hookAllMethods(profileActivityClass, "createView", pillHook, unhooksList)
            hookAllMethods(profileActivityClass, "updateRows", pillHook, unhooksList)
            hookAllMethods(profileActivityClass, "updateRowsIds", pillHook, unhooksList)
        }
    }
}
