from typing import Any

from ui.settings import Divider, Header, Text

from LegacyGram.data.constants import GITHUB_URL, Keys
from LegacyGram.i18n.i18n import t
from LegacyGram.utils.settings_utils import (
    Switch,
    is_not_12_1_1_version,
    open_extera_tab,
    open_url_view,
    open_version_info,
    show_restart_bulletin,
    toggle_settings_options,
)
from LegacyGram.utils.utils import get_client_version, parse_version

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


def get_main_settings_list() -> list[Any]:
    is_version_text_red = is_not_12_1_1_version(get_client_version())
    client_version = parse_version(get_client_version())

    if client_version >= (12, 4, 1):
        extera_icon = "extera_outline"
    else:
        extera_icon = "etg_settings"

    settings_options = [
        Header(text=t("settings_options")),
        Text(text=t("switch_all"), link_alias=Keys.switch_all, on_click=toggle_settings_options),
        *[Switch(text=t(text_key), key=key) for key, text_key in SETTINGS_OPTION_ROWS],
    ]

    drawer_options = [
        Header(text=t("drawer_options")),
        Text(text=t("manage_drawer_options"), link_alias=Keys.drawer_options, on_click=open_extera_tab(Keys.drawer_options), icon=extera_icon),
    ]

    chat_list = [
        Header(text=t("chat_list")),
        Text(text=t("hide_stories"), link_alias=Keys.hide_stories, on_click=open_extera_tab(Keys.hide_stories), icon=extera_icon),
        Text(
            text=t("hide_action_bar_status"),
            link_alias=Keys.hide_action_bar_status,
            on_click=open_extera_tab(Keys.hide_action_bar_status),
            icon=extera_icon,
        ),
        Switch(text=t("hide_greeting_button"), subtext=t("hide_greeting_button_sub"), key=Keys.hide_greeting_button),
    ]

    profile_buttons = [
        Header(text=t("profile_buttons")),
        Switch(text=t("hide_profile_actions_stories_button"), key=Keys.hide_profile_actions_stories_button),
        Switch(text=t("hide_profile_actions_gift_button"), key=Keys.hide_profile_actions_gift_button),
        Switch(text=t("hide_profile_actions_stream_button"), key=Keys.hide_profile_actions_stream_button),
    ]

    profile_tabs = [
        Header(text=t("profile_tabs")),
        Switch(text=t("hide_stories_tab"), subtext=t("hide_stories_tab_sub"), key=Keys.hide_stories_tab),
        Switch(text=t("hide_gifts_tab"), key=Keys.hide_gifts_tab),
    ]

    profile_appearance = [
        Header(text=t("profile_appearance")),
        Text(text=t("manage_reply_elements"), link_alias=Keys.reply_elements, on_click=open_extera_tab(Keys.reply_elements), icon=extera_icon),
        Switch(text=t("hide_profile_background_emoji"), subtext=t("hide_profile_background_emoji_sub"), key=Keys.hide_profile_background_emoji),
        Switch(text=t("hide_profile_pinned_gifts"), key=Keys.hide_profile_pinned_gifts),
        Switch(text=t("hide_profile_colorful_background"), key=Keys.hide_profile_colorful_background),
        Switch(text=t("hide_boost_badge"), key=Keys.hide_boost_badge),
        Switch(text=t("hide_gift_hint"), key=Keys.hide_gift_hint),
        Switch(text=t("hide_premium_emoji"), subtext=t("hide_premium_emoji_sub"), key=Keys.hide_premium_emoji),
        Switch(text=t("hide_premium_badge"), subtext=t("hide_premium_badge_sub"), on_change=show_restart_bulletin, key=Keys.hide_premium_badge),
        Switch(text=t("hide_bot_verification"), key=Keys.hide_bot_verification),
    ]

    action_bar = [
        Header(text=t("action_bar")),
        Switch(text=t("hide_action_bar_live_stream"), key=Keys.hide_action_bar_live_stream),
        Switch(text=t("hide_action_bar_archived_stories"), key=Keys.hide_action_bar_archived_stories),
        Switch(text=t("hide_action_bar_send_gift"), key=Keys.hide_action_bar_send_gift),
        Switch(text=t("hide_action_bar_boost_group"), key=Keys.hide_action_bar_boost_group),
        Switch(text=t("hide_action_bar_add_shortcut"), key=Keys.hide_action_bar_add_shortcut),
    ]

    gifts = [
        Header(text=t("gifts")),
        Switch(text=t("hide_bottom_gift_button"), key=Keys.hide_bottom_gift_button),
        Switch(text=t("hide_stars_rating"), key=Keys.hide_stars_rating),
        Switch(text=t("hide_star_reaction"), key=Keys.hide_star_reaction),
    ]

    about_plugin = [
        Header(text=t("about_plugin")),
        Text(text=t("client_version", get_client_version()), on_click=open_version_info(get_client_version()), red=is_version_text_red, icon="msg_help"),
        Text(text=t("github_repository"), icon="msg_link", on_click=open_url_view(GITHUB_URL)),
        Divider(text=t("github_sub")),
    ]

    return [*settings_options, *drawer_options, *chat_list, *profile_buttons, *profile_tabs, *profile_appearance, *action_bar, *gifts, *about_plugin]
