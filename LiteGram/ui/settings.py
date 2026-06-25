from typing import Any

from ui.settings import Header, Text

from LiteGram.data.constants import GITHUB_URL, Keys
from LiteGram.i18n.i18n import t
from LiteGram.main import LiteGramPlugin
from LiteGram.utils.extera_utils import resolve_icon
from LiteGram.utils.settings_utils import (
    Switch,
    open_extera_tab,
    open_url_view,
    show_restart_bulletin,
    toggle_emoji_search_options,
    toggle_premium_emoji_options,
    toggle_premium_stickers_options,
    toggle_settings_options,
)

SETTINGS_OPTION_ROWS = Keys.SETTINGS_OPTION_ROWS


def _premium_emoji_settings() -> list[Any]:
    return [
        Header(text=t("premium_emoji_settings_header")),
        Text(text=t("switch_all"), link_alias=Keys.switch_all_premium_emoji, on_click=toggle_premium_emoji_options),
        Switch(
            text=t("hide_premium_emoji_packs"),
            key=Keys.hide_premium_emoji_packs,
            default=True,
        ),
        Switch(
            text=t("hide_premium_recent"),
            key=Keys.hide_premium_recent,
            default=True,
        ),
        Switch(
            text=t("hide_premium_search"),
            key=Keys.hide_premium_search,
            default=True,
        ),
        Switch(
            text=t("hide_premium_suggestions"),
            key=Keys.hide_premium_suggestions,
            default=True,
        ),
        Switch(
            text=t("hide_premium_reactions"),
            key=Keys.hide_premium_reactions,
            default=True,
        ),
    ]


def _premium_stickers_settings() -> list[Any]:
    return [
        Header(text=t("premium_stickers_settings_header")),
        Text(text=t("switch_all"), link_alias=Keys.switch_all_premium_stickers, on_click=toggle_premium_stickers_options),
        Switch(
            text=t("hide_premium_stickers_recent"),
            key=Keys.hide_premium_stickers_recent,
            default=True,
        ),
        Switch(
            text=t("hide_premium_stickers_search"),
            key=Keys.hide_premium_stickers_search,
            default=True,
        ),
        Switch(
            text=t("hide_premium_stickers_grid"),
            key=Keys.hide_premium_stickers_grid,
            default=True,
        ),
    ]


def _chat_settings() -> list[Any]:
    return [
        Header(text=t("chat_list")),
        Text(text=t("hide_stories"), link_alias=Keys.hide_stories, on_click=open_extera_tab(Keys.hide_stories), icon=resolve_icon("extera_outline")),
        Text(
            text=t("hide_action_bar_status"),
            link_alias=Keys.hide_action_bar_status,
            on_click=open_extera_tab(Keys.hide_action_bar_status),
            icon=resolve_icon("extera_outline"),
        ),
        Switch(text=t("hide_greeting_button"), subtext=t("hide_greeting_button_sub"), key=Keys.hide_greeting_button),
        Switch(text=t("hide_premium_emoji"), subtext=t("hide_premium_emoji_sub"), key=Keys.hide_premium_emoji),
        *(
            [
                Text(
                    text=t("premium_detailed_settings"),
                    link_alias=Keys.premiumEmojiSettings,
                    create_sub_fragment=_premium_emoji_settings,
                    icon="msg_settings_old",
                ),
            ]
            if bool(LiteGramPlugin.get_instance().get_setting(Keys.hide_premium_emoji, False))
            else []
        ),
        Switch(text=t("hide_premium_stickers"), subtext=t("hide_premium_stickers_sub"), key=Keys.hide_premium_stickers),
        *(
            [
                Text(
                    text=t("premium_detailed_settings"),
                    link_alias=Keys.premiumStickersSettings,
                    create_sub_fragment=_premium_stickers_settings,
                    icon="msg_settings_old",
                ),
            ]
            if bool(LiteGramPlugin.get_instance().get_setting(Keys.hide_premium_stickers, False))
            else []
        ),
        Header(text=t("action_bar")),
        Switch(text=t("hide_action_bar_live_stream"), key=Keys.hide_action_bar_live_stream),
        Switch(text=t("hide_action_bar_archived_stories"), key=Keys.hide_action_bar_archived_stories),
        Switch(text=t("hide_action_bar_send_gift"), key=Keys.hide_action_bar_send_gift),
        Switch(text=t("hide_action_bar_boost_group"), key=Keys.hide_action_bar_boost_group),
        Switch(text=t("hide_action_bar_add_shortcut"), key=Keys.hide_action_bar_add_shortcut),
        Header(text=t("gifts")),
        Switch(text=t("hide_bottom_gift_button"), key=Keys.hide_bottom_gift_button),
        Switch(text=t("hide_gift_cards"), subtext=t("hide_gift_cards_sub"), key=Keys.hide_gift_cards),
        Switch(text=t("hide_giveaway_cards"), subtext=t("hide_giveaway_cards_sub"), key=Keys.hide_giveaway_cards),
        Switch(text=t("hide_stars_rating"), key=Keys.hide_stars_rating),
        Switch(text=t("hide_star_reaction"), key=Keys.hide_star_reaction),
        Header(text=t("emoji_search")),
        Text(text=t("switch_all"), link_alias=Keys.switch_all_emoji_search, on_click=toggle_emoji_search_options),
        *[Switch(text=t(text_key), key=key) for key, text_key in Keys.EMOJI_SEARCH_ROWS],
    ]


def _profile_settings() -> list[Any]:
    return [
        Header(text=t("profile_buttons")),
        Switch(text=t("hide_profile_actions_stories_button"), key=Keys.hide_profile_actions_stories_button),
        Switch(text=t("hide_profile_actions_gift_button"), key=Keys.hide_profile_actions_gift_button),
        Switch(text=t("hide_profile_actions_stream_button"), key=Keys.hide_profile_actions_stream_button),
        Header(text=t("profile_tabs")),
        Switch(text=t("hide_stories_tab"), subtext=t("hide_stories_tab_sub"), key=Keys.hide_stories_tab),
        Switch(text=t("hide_gifts_tab"), key=Keys.hide_gifts_tab),
        Header(text=t("profile_appearance")),
        Text(
            text=t("manage_reply_elements"),
            link_alias=Keys.reply_elements,
            on_click=open_extera_tab(Keys.reply_elements),
            icon=resolve_icon("extera_outline"),
        ),
        Switch(text=t("hide_profile_background_emoji"), subtext=t("hide_profile_background_emoji_sub"), key=Keys.hide_profile_background_emoji),
        Switch(text=t("hide_profile_pinned_gifts"), key=Keys.hide_profile_pinned_gifts),
        Switch(text=t("hide_profile_colorful_background"), key=Keys.hide_profile_colorful_background),
        Switch(text=t("hide_boost_badge"), key=Keys.hide_boost_badge),
        Switch(text=t("hide_premium_badge"), subtext=t("hide_premium_badge_sub"), on_change=show_restart_bulletin, key=Keys.hide_premium_badge),
        Switch(text=t("hide_bot_verification"), key=Keys.hide_bot_verification),
        Header(text=t("gifts")),
        Switch(text=t("hide_collectible_status"), subtext=t("hide_collectible_status_sub"), key=Keys.hide_collectible_status),
        Switch(text=t("hide_gift_hint"), key=Keys.hide_gift_hint),
    ]


def _interface_settings() -> list[Any]:
    return [
        Header(text=t("settings_options")),
        Text(text=t("switch_all"), link_alias=Keys.switch_all, on_click=toggle_settings_options),
        *[Switch(text=t(text_key), key=key) for key, text_key in SETTINGS_OPTION_ROWS],
        Header(text=t("drawer_options")),
        Text(
            text=t("manage_drawer_options"),
            link_alias=Keys.drawer_options,
            on_click=open_extera_tab(Keys.drawer_options),
            icon=resolve_icon("extera_outline"),
        ),
    ]


def _about_settings() -> list[Any]:
    return [
        Header(text=t("about_plugin")),
        Text(text=t("github_repository"), icon="msg_link", on_click=open_url_view(GITHUB_URL)),
        Text(text=t("github_sub")),
    ]


def get_main_settings_list() -> list[Any]:
    return [
        Text(text=t("category_chat"), icon="msg_discussion", create_sub_fragment=_chat_settings, link_alias=Keys.chatSettings),
        Text(text=t("category_profile"), icon="msg_contacts", create_sub_fragment=_profile_settings, link_alias=Keys.profileSettings),
        Text(text=t("category_interface"), icon="msg_settings", create_sub_fragment=_interface_settings, link_alias=Keys.interfaceSettings),
        Text(text=t("category_about"), icon="msg_help", create_sub_fragment=_about_settings, link_alias=Keys.aboutSettings),
    ]
