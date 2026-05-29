from typing import Any, Optional

from base_plugin import BasePlugin
from ui.bulletin import BulletinHelper

from LegacyGram.features.action_bar import register_action_bar
from LegacyGram.features.gift_button import register_gift_button
from LegacyGram.features.greeting_button import register_greeting_button
from LegacyGram.features.media_layout import register_media_layout
from LegacyGram.features.premium_badge import register_premium_badge
from LegacyGram.features.premium_emoji import register_premium_emoji
from LegacyGram.features.profile_actions import register_profile_actions
from LegacyGram.features.profile_appearance import register_profile_appearance
from LegacyGram.features.settings_menu import register_settings_menu
from LegacyGram.features.star_rating import register_star_rating
from LegacyGram.features.star_reaction import register_star_reaction
from LegacyGram.ui.settings import get_main_settings_list


class LegacyGramPlugin(BasePlugin):
    _instance: Optional["LegacyGramPlugin"] = None

    def on_plugin_load(self) -> None:
        LegacyGramPlugin._instance = self
        self.register_hooks()

    def create_settings(self) -> list[Any]:
        return get_main_settings_list()

    def register_hooks(self) -> None:
        register_action_bar(self)
        register_star_rating(self)
        register_media_layout(self)
        register_settings_menu(self)
        register_gift_button(self)
        register_greeting_button(self)
        register_profile_appearance(self)
        register_profile_actions(self)
        register_premium_emoji(self)
        register_premium_badge(self)
        register_star_reaction(self)

    @classmethod
    def get_instance(cls) -> "LegacyGramPlugin":
        if cls._instance is None:
            BulletinHelper.show_error("Error while getting LegacyGramPlugin Instance!")
            raise RuntimeError("Error while getting LegacyGramPlugin Instance!")
        return cls._instance
