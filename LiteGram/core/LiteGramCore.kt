package non.feature.litegram.core

import de.robv.android.xposed.XC_MethodHook
import java.util.ArrayList
import non.feature.litegram.hide_communities.HideCommunitiesHook
import non.feature.litegram.premium_badge.PremiumBadgeHook
import non.feature.litegram.premium_emoji.PremiumEmojiHook

class LiteGramCore {
    private val hooks = ArrayList<XC_MethodHook.Unhook>()

    fun load(cl: ClassLoader) {
        try { PremiumEmojiHook.init(cl, hooks) } catch (_: Throwable) {}
        try { HideCommunitiesHook.init(cl, hooks) } catch (_: Throwable) {}
        try { PremiumBadgeHook.init(cl, hooks) } catch (_: Throwable) {}
    }

    fun unload() {
        try { PremiumEmojiHook.unload() } catch (_: Throwable) {}
        try { HideCommunitiesHook.unload() } catch (_: Throwable) {}
        try { PremiumBadgeHook.unload() } catch (_: Throwable) {}

        synchronized(hooks) {
            for (u in hooks) {
                try {
                    u.unhook()
                } catch (_: Throwable) {}
            }
            hooks.clear()
        }

        ReflectionCache.clear()
    }

    fun setFlag(name: String, enabled: Boolean) {
        try { PremiumEmojiHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { HideCommunitiesHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { PremiumBadgeHook.setFlag(name, enabled) } catch (_: Throwable) {}
    }
}
