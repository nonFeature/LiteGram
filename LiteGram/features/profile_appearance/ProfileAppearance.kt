package non.feature.litegram.profile_appearance

import android.view.View
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.lang.reflect.Method
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object ProfileAppearanceHook {

    @Volatile @JvmStatic var hideProfileBackgroundEmoji: Boolean = false
    @Volatile @JvmStatic var hideProfilePinnedGifts: Boolean = false
    @Volatile @JvmStatic var hideBoostBadge: Boolean = false
    @Volatile @JvmStatic var hideProfileColorfulBackground: Boolean = false
    @Volatile @JvmStatic var hideBotVerification: Boolean = false
    @Volatile @JvmStatic var hideProfileMusic: Boolean = false
    @Volatile @JvmStatic var hideProfileBusiness: Boolean = false
    @Volatile @JvmStatic var hideProfileEditorGifts: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideProfileBackgroundEmoji", "hide_profile_background_emoji" -> hideProfileBackgroundEmoji = enabled
            "hideProfilePinnedGifts", "hide_profile_pinned_gifts" -> hideProfilePinnedGifts = enabled
            "hideBoostBadge", "hide_boost_badge" -> hideBoostBadge = enabled
            "hideProfileColorfulBackground", "hide_profile_colorful_background" -> hideProfileColorfulBackground = enabled
            "hideBotVerification", "hide_bot_verification" -> hideBotVerification = enabled
            "hideProfileMusic", "hide_profile_music" -> hideProfileMusic = enabled
            "hideProfileBusiness", "hide_profile_business" -> hideProfileBusiness = enabled
            "hideProfileEditorGifts", "hide_profile_editor_gifts" -> hideProfileEditorGifts = enabled
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

        hideProfileBackgroundEmoji = false
        hideProfilePinnedGifts = false
        hideBoostBadge = false
        hideProfileColorfulBackground = false
        hideBotVerification = false
        hideProfileMusic = false
        hideProfileBusiness = false
        hideProfileEditorGifts = false
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

    @JvmStatic
    fun init(cl: ClassLoader, unhooksList: MutableList<XC_MethodHook.Unhook> = localUnhooks) {
        // 1. Profile Background Emoji: StarGiftPatterns.drawProfileAnimatedPattern
        val starGiftPatternsClass = ReflectionCache.findClass("org.telegram.ui.Stars.StarGiftPatterns", cl)
        if (starGiftPatternsClass != null) {
            hookAllMethods(starGiftPatternsClass, "drawProfileAnimatedPattern", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfileBackgroundEmoji) {
                        param.setResult(null)
                    }
                }
            }, unhooksList)
        }

        // 2. Profile Pinned Gifts: ProfileGiftsView constructors & update
        val profileGiftsViewClass = ReflectionCache.findClass("org.telegram.ui.Stars.ProfileGiftsView", cl)
        if (profileGiftsViewClass != null) {
            hookAllConstructors(profileGiftsViewClass, object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (hideProfilePinnedGifts) {
                        try {
                            (param.thisObject as? View)?.visibility = View.GONE
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)

            hookAllMethods(profileGiftsViewClass, "update", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfilePinnedGifts) {
                        try {
                            (param.thisObject as? View)?.visibility = View.GONE
                        } catch (_: Throwable) {}
                        param.setResult(null)
                    }
                }
            }, unhooksList)
        }

        // 3. Boost Badge: ChatMessageCell.setMessageObjectInternal
        val chatMessageCellClass = ReflectionCache.findClass("org.telegram.ui.Cells.ChatMessageCell", cl)
        val messageObjectClass = ReflectionCache.findClass("org.telegram.messenger.MessageObject", cl)
        val messageOwnerField = if (messageObjectClass != null) ReflectionCache.getField(messageObjectClass, "messageOwner") else null
        val messageClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$Message", cl)
        val fromBoostsAppliedField = if (messageClass != null) ReflectionCache.getField(messageClass, "from_boosts_applied") else null

        if (chatMessageCellClass != null) {
            hookAllMethods(chatMessageCellClass, "setMessageObjectInternal", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideBoostBadge) return
                    val args = param.args
                    if (args == null || args.isEmpty()) return
                    val msgObj = args[0] ?: return
                    try {
                        val owner = messageOwnerField?.get(msgObj) ?: return
                        fromBoostsAppliedField?.setInt(owner, 0)
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 4. Profile Colorful Background: PeerColor.fromCollectible, UserObject.getProfileColorId, ChatObject.getProfileColorId
        val peerColorClass = ReflectionCache.findClass("org.telegram.messenger.MessagesController\$PeerColor", cl)
        if (peerColorClass != null) {
            hookAllMethods(peerColorClass, "fromCollectible", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfileColorfulBackground) {
                        param.setResult(null)
                    }
                }
            }, unhooksList)
        }

        val userObjectClass = ReflectionCache.findClass("org.telegram.messenger.UserObject", cl)
        if (userObjectClass != null) {
            hookAllMethods(userObjectClass, "getProfileColorId", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfileColorfulBackground) {
                        param.setResult(-1)
                    }
                }
            }, unhooksList)
        }

        val chatObjectClass = ReflectionCache.findClass("org.telegram.messenger.ChatObject", cl)
        if (chatObjectClass != null) {
            hookAllMethods(chatObjectClass, "getProfileColorId", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfileColorfulBackground) {
                        param.setResult(-1)
                    }
                }
            }, unhooksList)
        }

        // 5. Bot Verification: DialogObject.getBotVerification*, ProfileActivity.getBotVerificationDrawable, ChatActivity.updateTopPanelView
        val dialogObjectClass = ReflectionCache.findClass("org.telegram.messenger.DialogObject", cl)
        if (dialogObjectClass != null) {
            hookAllMethods(dialogObjectClass, "getBotVerificationIcon", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideBotVerification) {
                        param.setResult(0)
                    }
                }
            }, unhooksList)

            hookAllMethods(dialogObjectClass, "getBotVerification", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideBotVerification) {
                        param.setResult(null)
                    }
                }
            }, unhooksList)
        }

        val profileActivityClass = ReflectionCache.findClass("org.telegram.ui.ProfileActivity", cl)
        if (profileActivityClass != null) {
            hookAllMethods(profileActivityClass, "getBotVerificationDrawable", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideBotVerification) {
                        param.setResult(null)
                    }
                }
            }, unhooksList)
        }

        val chatActivityClass = ReflectionCache.findClass("org.telegram.ui.ChatActivity", cl)
        if (chatActivityClass != null) {
            val userInfoField = ReflectionCache.getField(chatActivityClass, "userInfo")
            val chatInfoField = ReflectionCache.getField(chatActivityClass, "chatInfo")
            val userFullClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$UserFull", cl)
            val chatFullClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$ChatFull", cl)
            val userBotVerificationField = if (userFullClass != null) ReflectionCache.getField(userFullClass, "bot_verification") else null
            val chatBotVerificationField = if (chatFullClass != null) ReflectionCache.getField(chatFullClass, "bot_verification") else null

            hookAllMethods(chatActivityClass, "updateTopPanelView", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideBotVerification) return
                    val instance = param.thisObject ?: return
                    try {
                        val uInfo = userInfoField?.get(instance)
                        if (uInfo != null) {
                            userBotVerificationField?.set(uInfo, null)
                        }
                        val cInfo = chatInfoField?.get(instance)
                        if (cInfo != null) {
                            chatBotVerificationField?.set(cInfo, null)
                        }
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }

        // 6. UserFull fields: saved_music, business_work_hours, business_location
        val userFullClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$UserFull", cl)
        if (userFullClass != null) {
            val savedMusicField = ReflectionCache.getField(userFullClass, "saved_music")
            val businessWorkHoursField = ReflectionCache.getField(userFullClass, "business_work_hours")
            val businessLocationField = ReflectionCache.getField(userFullClass, "business_location")

            hookAllMethods(userFullClass, "TLdeserialize", object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    val userFull = param.result ?: return
                    if (hideProfileMusic && savedMusicField != null) {
                        try {
                            savedMusicField.set(userFull, null)
                        } catch (_: Throwable) {}
                    }
                    if (hideProfileBusiness) {
                        try {
                            businessWorkHoursField?.set(userFull, null)
                            businessLocationField?.set(userFull, null)
                        } catch (_: Throwable) {}
                    }
                }
            }, unhooksList)
        }

        // 7. Now Playing Card: NowPlayingController.shouldShowCard
        val nowPlayingControllerClass = ReflectionCache.findClass(
            "com.exteragram.messenger.nowplaying.NowPlayingController", cl
        )
        if (nowPlayingControllerClass != null) {
            hookAllMethods(nowPlayingControllerClass, "shouldShowCard", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfileMusic) {
                        param.setResult(false)
                    }
                }
            }, unhooksList)
        }

        // 8. Profile Appearance Editor Gifts: PeerColorActivity & PeerColorActivity$Page.updateRows
        val peerColorActivityClass = ReflectionCache.findClass("org.telegram.ui.PeerColorActivity", cl)
        val peerColorActivityPageClass = ReflectionCache.findClass("org.telegram.ui.PeerColorActivity\$Page", cl)

        if (peerColorActivityClass != null) {
            val giftsField = ReflectionCache.getField(peerColorActivityClass, "gifts")
            val giftsWithPeerColorField = ReflectionCache.getField(peerColorActivityClass, "giftsWithPeerColor")

            fun cancelGifts(activity: Any?) {
                if (activity == null) return
                try {
                    val gifts = giftsField?.get(activity)
                    if (gifts != null) {
                        ReflectionCache.getMethod(gifts.javaClass, "cancel")?.invoke(gifts)
                        giftsField.set(activity, null)
                    }
                    val giftsColor = giftsWithPeerColorField?.get(activity)
                    if (giftsColor != null) {
                        ReflectionCache.getMethod(giftsColor.javaClass, "cancel")?.invoke(giftsColor)
                        giftsWithPeerColorField.set(activity, null)
                    }
                } catch (_: Throwable) {}
            }

            hookAllConstructors(peerColorActivityClass, object : XC_MethodHook(120) {
                override fun afterHookedMethod(param: MethodHookParam) {
                    if (hideProfileEditorGifts) {
                        cancelGifts(param.thisObject)
                    }
                }
            }, unhooksList)

            hookAllMethods(peerColorActivityClass, "createView", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (hideProfileEditorGifts) {
                        cancelGifts(param.thisObject)
                    }
                }
            }, unhooksList)

            if (peerColorActivityPageClass != null) {
                val outerThisField = ReflectionCache.getField(peerColorActivityPageClass, "this$0")
                val giftsHeaderRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsHeaderRow")
                val giftsStartRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsStartRow")
                val giftsLoadingStartRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsLoadingStartRow")
                val giftsLoadingEndRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsLoadingEndRow")
                val giftsEndRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsEndRow")
                val giftsInfoRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsInfoRow")
                val giftsTabsRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsTabsRow")
                val giftsEmptyRowField = ReflectionCache.getField(peerColorActivityPageClass, "giftsEmptyRow")
                val giftsEmptyRowGapField = ReflectionCache.getField(peerColorActivityPageClass, "giftsEmptyRowGap")
                val giftsCountField = ReflectionCache.getField(peerColorActivityPageClass, "giftsCount")
                val uniqueGiftsField = ReflectionCache.getField(peerColorActivityPageClass, "uniqueGifts")
                val giftTabsViewField = ReflectionCache.getField(peerColorActivityPageClass, "giftTabsView")

                val typeField = ReflectionCache.getField(peerColorActivityPageClass, "type")
                val selectedColorField = ReflectionCache.getField(peerColorActivityPageClass, "selectedColor")
                val selectedEmojiCollField = ReflectionCache.getField(peerColorActivityPageClass, "selectedEmojiCollectible")
                val selectedPeerCollField = ReflectionCache.getField(peerColorActivityPageClass, "selectedPeerCollectible")

                val colorPickerRowField = ReflectionCache.getField(peerColorActivityPageClass, "colorPickerRow")
                val iconRowField = ReflectionCache.getField(peerColorActivityPageClass, "iconRow")
                val infoRowField = ReflectionCache.getField(peerColorActivityPageClass, "infoRow")
                val clearRowField = ReflectionCache.getField(peerColorActivityPageClass, "clearRow")
                val shadowRowField = ReflectionCache.getField(peerColorActivityPageClass, "shadowRow")
                val buttonRowField = ReflectionCache.getField(peerColorActivityPageClass, "buttonRow")
                val rowCountField = ReflectionCache.getField(peerColorActivityPageClass, "rowCount")

                hookAllMethods(peerColorActivityPageClass, "updateRows", object : XC_MethodHook(120) {
                    override fun beforeHookedMethod(param: MethodHookParam) {
                        if (!hideProfileEditorGifts) return
                        val page = param.thisObject ?: return
                        try {
                            val outer = outerThisField?.get(page)
                            cancelGifts(outer)
                        } catch (_: Throwable) {}
                    }

                    override fun afterHookedMethod(param: MethodHookParam) {
                        if (!hideProfileEditorGifts) return
                        val page = param.thisObject ?: return
                        try {
                            giftsHeaderRowField?.setInt(page, -1)
                            giftsStartRowField?.setInt(page, -1)
                            giftsLoadingStartRowField?.setInt(page, -1)
                            giftsLoadingEndRowField?.setInt(page, -1)
                            giftsEndRowField?.setInt(page, -1)
                            giftsInfoRowField?.setInt(page, -1)
                            giftsTabsRowField?.setInt(page, -1)
                            giftsEmptyRowField?.setInt(page, -1)
                            giftsEmptyRowGapField?.setInt(page, -1)
                            giftsCountField?.setInt(page, 0)

                            val uniqueGifts = uniqueGiftsField?.get(page) as? ArrayList<*>
                            uniqueGifts?.clear()

                            (giftTabsViewField?.get(page) as? View)?.visibility = View.GONE

                            val typeVal = typeField?.getInt(page) ?: 0
                            val selectedColor = selectedColorField?.getInt(page) ?: -1
                            val selectedEmojiColl = selectedEmojiCollField?.get(page)
                            val selectedPeerColl = selectedPeerCollField?.get(page)

                            var rowCount = 0
                            colorPickerRowField?.setInt(page, rowCount++)
                            iconRowField?.setInt(page, rowCount++)
                            infoRowField?.setInt(page, rowCount++)

                            if (typeVal == 0 && (selectedColor >= 0 || selectedEmojiColl != null || selectedPeerColl != null)) {
                                clearRowField?.setInt(page, rowCount++)
                                shadowRowField?.setInt(page, rowCount++)
                            } else {
                                clearRowField?.setInt(page, -1)
                                shadowRowField?.setInt(page, -1)
                            }

                            buttonRowField?.setInt(page, rowCount++)
                            rowCountField?.setInt(page, rowCount)
                        } catch (_: Throwable) {}
                    }
                }, unhooksList)
            }
        }
    }
}
