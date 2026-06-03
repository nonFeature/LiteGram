from typing import Any

from ui.settings import Divider, Header, Text

from LegacyGram.data.constants import GITHUB_URL, Keys
from LegacyGram.i18n.i18n import t
from LegacyGram.utils.extera_utils import resolve_icon
from LegacyGram.utils.settings_utils import (
    Switch,
    open_extera_tab,
    open_url_view,
    show_restart_bulletin,
    toggle_settings_options,
)

SETTINGS_OPTION_ROWS = [
    (Keys.hide_premium_row, "hide_premium_row"),
    (Keys.hide_stars_row, "hide_stars_row"),
    (Keys.hide_ton_row, "hide_ton_row"),
    (Keys.hide_wallet_row, "hide_wallet_row"),
    (Keys.hide_business_row, "hide_business_row"),
    (Keys.hide_send_a_gift_row, "hide_send_a_gift_row"),
    (Keys.hide_help_section, "hide_help_section"),
]


def get_settings_options_list() -> list[Any]:
    return [
        Header(text=t("settings_options")),
        Text(text=t("switch_all"), link_alias=Keys.switch_all, on_click=toggle_settings_options),
        *[Switch(text=t(text_key), key=key) for key, text_key in SETTINGS_OPTION_ROWS],
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
        Header(text=t("action_bar")),
        Switch(text=t("hide_action_bar_live_stream"), key=Keys.hide_action_bar_live_stream),
        Switch(text=t("hide_action_bar_archived_stories"), key=Keys.hide_action_bar_archived_stories),
        Switch(text=t("hide_action_bar_send_gift"), key=Keys.hide_action_bar_send_gift),
        Switch(text=t("hide_action_bar_boost_group"), key=Keys.hide_action_bar_boost_group),
        Switch(text=t("hide_action_bar_add_shortcut"), key=Keys.hide_action_bar_add_shortcut),
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
        Text(text=t("manage_reply_elements"), link_alias=Keys.reply_elements, on_click=open_extera_tab(Keys.reply_elements), icon="extera_outline"),
        Switch(text=t("hide_profile_background_emoji"), subtext=t("hide_profile_background_emoji_sub"), key=Keys.hide_profile_background_emoji),
        Switch(text=t("hide_profile_pinned_gifts"), key=Keys.hide_profile_pinned_gifts),
        Switch(text=t("hide_profile_colorful_background"), key=Keys.hide_profile_colorful_background),
        Switch(text=t("hide_boost_badge"), key=Keys.hide_boost_badge),
        Switch(text=t("hide_gift_hint"), key=Keys.hide_gift_hint),
        Switch(text=t("hide_premium_emoji"), subtext=t("hide_premium_emoji_sub"), key=Keys.hide_premium_emoji),
        Switch(text=t("hide_premium_badge"), subtext=t("hide_premium_badge_sub"), on_change=show_restart_bulletin, key=Keys.hide_premium_badge),
        Switch(text=t("hide_bot_verification"), key=Keys.hide_bot_verification),
        Header(text=t("gifts")),
        Switch(text=t("hide_collectible_status"), subtext=t("hide_collectible_status_sub"), key=Keys.hide_collectible_status),
        Switch(text=t("force_disable_particles"), subtext=t("force_disable_particles_sub"), key=Keys.force_disable_particles),
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


def _gifts_settings() -> list[Any]:
    return [
        Header(text=t("gifts")),
        Switch(text=t("hide_bottom_gift_button"), key=Keys.hide_bottom_gift_button),
        Switch(text=t("hide_gift_cards"), subtext=t("hide_gift_cards_sub"), key=Keys.hide_gift_cards),
        Switch(text=t("hide_gift_dialogs_send"), subtext=t("hide_gift_dialogs_send_sub"), key=Keys.hide_gift_dialogs_send),
        Switch(text=t("hide_gift_dialogs_view"), subtext=t("hide_gift_dialogs_view_sub"), key=Keys.hide_gift_dialogs_view),
        Switch(text=t("hide_giveaway_cards"), subtext=t("hide_giveaway_cards_sub"), key=Keys.hide_giveaway_cards),
        Switch(text=t("hide_stars_rating"), key=Keys.hide_stars_rating),
        Switch(text=t("hide_star_reaction"), key=Keys.hide_star_reaction),
    ]


def _about_settings() -> list[Any]:
    return [
        Header(text=t("about_plugin")),
        Text(text=t("github_repository"), icon="msg_link", on_click=open_url_view(GITHUB_URL)),
        Divider(text=t("github_sub")),
    ]


def get_main_settings_list() -> list[Any]:
    return [
        Text(text=t("category_chat"), icon="msg_discussion", create_sub_fragment=_chat_settings),
        Text(text=t("category_profile"), icon="msg_contacts", create_sub_fragment=_profile_settings),
        Text(text=t("category_interface"), icon="msg_settings", create_sub_fragment=_interface_settings),
        Text(text=t("category_gifts"), icon="msg_gift_premium", create_sub_fragment=_gifts_settings),
        Text(text=t("category_about"), icon="msg_help", create_sub_fragment=_about_settings),
    ]
