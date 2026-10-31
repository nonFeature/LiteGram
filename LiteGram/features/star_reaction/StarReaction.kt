package non.feature.litegram.star_reaction

import android.os.Trace
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import java.lang.reflect.Field
import java.util.ArrayList
import non.feature.litegram.core.ReflectionCache

object StarReactionHook {

    @Volatile @JvmStatic var hideStarReaction: Boolean = false

    private val localUnhooks = ArrayList<XC_MethodHook.Unhook>()

    private var reactionsLayoutInBubbleClass: Class<*>? = null
    private var reactionsContainerLayoutClass: Class<*>? = null
    private var hasStarField: Field? = null

    private var messageObjectClass: Class<*>? = null
    private var messageOwnerField: Field? = null
    private var messageClass: Class<*>? = null
    private var reactionsField: Field? = null
    private var resultsField: Field? = null
    private var reactionPaidClass: Class<*>? = null
    private var reactionField: Field? = null

    private var visibleReactionClass: Class<*>? = null
    private var isStarField: Field? = null

    @JvmStatic
    fun setFlag(name: String, enabled: Boolean) {
        when (name) {
            "hideStarReaction", "hide_star_reaction" -> hideStarReaction = enabled
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

        hideStarReaction = false
        reactionsLayoutInBubbleClass = null
        reactionsContainerLayoutClass = null
        hasStarField = null
        messageObjectClass = null
        messageOwnerField = null
        messageClass = null
        reactionsField = null
        resultsField = null
        reactionPaidClass = null
        reactionField = null
        visibleReactionClass = null
        isStarField = null
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
        reactionsLayoutInBubbleClass = ReflectionCache.findClass(
            "org.telegram.ui.Components.Reactions.ReactionsLayoutInBubble", cl
        )
        reactionsContainerLayoutClass = ReflectionCache.findClass(
            "org.telegram.ui.Components.ReactionsContainerLayout", cl
        )
        if (reactionsContainerLayoutClass != null) {
            hasStarField = ReflectionCache.getField(reactionsContainerLayoutClass, "hasStar")
        }

        messageObjectClass = ReflectionCache.findClass("org.telegram.messenger.MessageObject", cl)
        messageOwnerField = ReflectionCache.getField(messageObjectClass, "messageOwner")

        messageClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$Message", cl)
        reactionsField = ReflectionCache.getField(messageClass, "reactions")

        val messageReactionsClass = ReflectionCache.findClass(
            "org.telegram.tgnet.TLRPC\$TL_messageReactions", cl
        ) ?: ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$MessageReactions", cl)
        if (messageReactionsClass != null) {
            resultsField = ReflectionCache.getField(messageReactionsClass, "results")
        }

        reactionPaidClass = ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$TL_reactionPaid", cl)

        val reactionCountClass = ReflectionCache.findClass(
            "org.telegram.tgnet.TLRPC\$TL_reactionCount", cl
        ) ?: ReflectionCache.findClass("org.telegram.tgnet.TLRPC\$ReactionCount", cl)
        if (reactionCountClass != null) {
            reactionField = ReflectionCache.getField(reactionCountClass, "reaction")
        }

        visibleReactionClass = ReflectionCache.findClass(
            "org.telegram.ui.Components.Reactions.ReactionsLayoutInBubble\$VisibleReaction", cl
        )
        if (visibleReactionClass != null) {
            isStarField = ReflectionCache.getField(visibleReactionClass, "isStar")
        }

        // 1. Hook ReactionsLayoutInBubble.setMessage: remove TL_reactionPaid from results
        if (reactionsLayoutInBubbleClass != null) {
            hookAllMethods(reactionsLayoutInBubbleClass, "setMessage", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideStarReaction) return
                    val args = param.args
                    if (args == null || args.isEmpty()) return
                    val messageObject = args[0] ?: return

                    Trace.beginSection("LiteGram::star_reaction:setMessage")
                    try {
                        val owner = messageOwnerField?.get(messageObject) ?: return
                        val reactions = reactionsField?.get(owner) ?: return
                        val results = (resultsField?.get(reactions) ?: ReflectionCache.getFieldValue(reactions, "results")) as? ArrayList<*> ?: return

                        var i = results.size - 1
                        while (i >= 0) {
                            val rc = results[i]
                            if (rc != null) {
                                val r = reactionField?.get(rc) ?: ReflectionCache.getFieldValue(rc, "reaction")
                                if (r != null) {
                                    if (reactionPaidClass != null && reactionPaidClass!!.isInstance(r)) {
                                        results.removeAt(i)
                                    } else if (r.javaClass.name.contains("reactionPaid")) {
                                        results.removeAt(i)
                                    }
                                }
                            }
                            i--
                        }
                    } catch (_: Throwable) {
                    } finally {
                        Trace.endSection()
                    }
                }
            }, unhooksList)
        }

        // 2. Hook ReactionsContainerLayout.setVisibleReactionsList: filter out isStar
        if (reactionsContainerLayoutClass != null) {
            hookAllMethods(reactionsContainerLayoutClass, "setVisibleReactionsList", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideStarReaction) return
                    val args = param.args
                    if (args == null || args.isEmpty()) return
                    val list = (args[0] as? ArrayList<*>) ?: (args[0] as? MutableList<*>) ?: return

                    Trace.beginSection("LiteGram::star_reaction:setVisibleReactionsList")
                    try {
                        var i = list.size - 1
                        while (i >= 0) {
                            val item = list[i]
                            if (item != null) {
                                val isStar = (isStarField?.get(item) ?: ReflectionCache.getFieldValue(item, "isStar")) as? Boolean ?: false
                                if (isStar) {
                                    list.removeAt(i)
                                }
                            }
                            i--
                        }
                    } catch (_: Throwable) {
                    } finally {
                        Trace.endSection()
                    }
                }
            }, unhooksList)

            // 3. Hook ReactionsContainerLayout.dispatchDraw: reset hasStar to false (remove gold glow/gradient)
            hookAllMethods(reactionsContainerLayoutClass, "dispatchDraw", object : XC_MethodHook(120) {
                override fun beforeHookedMethod(param: MethodHookParam) {
                    if (!hideStarReaction) return
                    val instance = param.thisObject ?: return
                    try {
                        hasStarField?.setBoolean(instance, false)
                    } catch (_: Throwable) {}
                }
            }, unhooksList)
        }
    }
}
