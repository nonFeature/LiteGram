package non.feature.litegram.core

import de.robv.android.xposed.XC_MethodHook
import java.util.ArrayList
import non.feature.litegram.action_bar.ActionBarHook
import non.feature.litegram.gift_cards.GiftCardsHook
import non.feature.litegram.hide_articles.HideArticlesHook
import non.feature.litegram.hide_communities.HideCommunitiesHook
import non.feature.litegram.hide_emoji_search.HideEmojiSearchHook
import non.feature.litegram.hide_premium_features.HidePremiumFeaturesHook
import non.feature.litegram.media_layout.MediaLayoutHook
import non.feature.litegram.premium_badge.PremiumBadgeHook
import non.feature.litegram.premium_emoji.PremiumEmojiHook
import non.feature.litegram.profile_actions.ProfileActionsHook
import non.feature.litegram.profile_appearance.ProfileAppearanceHook
import non.feature.litegram.star_reaction.StarReactionHook

class LiteGramCore {
    private val hooks = ArrayList<XC_MethodHook.Unhook>()

    fun load(cl: ClassLoader) {
        try { PremiumEmojiHook.init(cl, hooks) } catch (_: Throwable) {}
        try { HideCommunitiesHook.init(cl, hooks) } catch (_: Throwable) {}
        try { PremiumBadgeHook.init(cl, hooks) } catch (_: Throwable) {}
        try { HideArticlesHook.init(cl, hooks) } catch (_: Throwable) {}
        try { GiftCardsHook.init(cl, hooks) } catch (_: Throwable) {}
        try { StarReactionHook.init(cl, hooks) } catch (_: Throwable) {}
        try { HideEmojiSearchHook.init(cl, hooks) } catch (_: Throwable) {}
        try { ProfileAppearanceHook.init(cl, hooks) } catch (_: Throwable) {}
        try { MediaLayoutHook.init(cl, hooks) } catch (_: Throwable) {}
        try { ProfileActionsHook.init(cl, hooks) } catch (_: Throwable) {}
        try { ActionBarHook.init(cl, hooks) } catch (_: Throwable) {}
        try { HidePremiumFeaturesHook.init(cl, hooks) } catch (_: Throwable) {}
    }

    fun unload() {
        try { PremiumEmojiHook.unload() } catch (_: Throwable) {}
        try { HideCommunitiesHook.unload() } catch (_: Throwable) {}
        try { PremiumBadgeHook.unload() } catch (_: Throwable) {}
        try { HideArticlesHook.unload() } catch (_: Throwable) {}
        try { GiftCardsHook.unload() } catch (_: Throwable) {}
        try { StarReactionHook.unload() } catch (_: Throwable) {}
        try { HideEmojiSearchHook.unload() } catch (_: Throwable) {}
        try { ProfileAppearanceHook.unload() } catch (_: Throwable) {}
        try { MediaLayoutHook.unload() } catch (_: Throwable) {}
        try { ProfileActionsHook.unload() } catch (_: Throwable) {}
        try { ActionBarHook.unload() } catch (_: Throwable) {}
        try { HidePremiumFeaturesHook.unload() } catch (_: Throwable) {}

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
        try { HideArticlesHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { GiftCardsHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { StarReactionHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { HideEmojiSearchHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { ProfileAppearanceHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { MediaLayoutHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { ProfileActionsHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { ActionBarHook.setFlag(name, enabled) } catch (_: Throwable) {}
        try { HidePremiumFeaturesHook.setFlag(name, enabled) } catch (_: Throwable) {}
    }
}
