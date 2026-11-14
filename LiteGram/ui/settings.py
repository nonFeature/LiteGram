from typing import Any

from ui.settings import Divider, Header, Selector, Text

from LiteGram.data.constants import GITHUB_URL, Keys
from LiteGram.i18n.i18n import t
from LiteGram.main import LiteGramPlugin
from LiteGram.utils.dex_utils import dex_bridge
from LiteGram.utils.extera_utils import resolve_icon
from LiteGram.utils.settings_utils import (
    Switch,
    hide_group_rows,
    open_extera_tab,
    open_url_view,
)

SETTINGS_OPTION_ROWS = Keys.SETTINGS_OPTION_ROWS


def _on_communities_mode_change(val: Any) -> None:
    mode = int(val or 0)
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_communities, mode, reload_settings=False)
    dex_bridge.set_flag(Keys.hide_communities_badges, mode in (1, 2))
    dex_bridge.set_flag(Keys.hide_communities_profile, mode in (1, 3))
    dex_bridge.set_flag(Keys.hide_communities_cards, mode == 1)


def _on_hide_articles_editor_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_articles_editor, val, reload_settings=True)
    dex_bridge.set_flag(Keys.hide_articles_editor, val)


def _on_simplified_articles_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.simplified_articles_editor, val, reload_settings=False)
    dex_bridge.set_flag(Keys.simplified_articles_editor, val)


def _on_hide_ai_button_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_ai_button, val, reload_settings=False)
    dex_bridge.set_flag(Keys.hide_ai_button, val)


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
        Switch(text=t("hide_greeting_button"), key=Keys.hide_greeting_button, subtext=t("greeting_info")),
        Selector(
            text=t("hide_communities"),
            key=Keys.hide_communities,
            default=0,
            items=[
                t("hide_communities_default"),
                t("hide_communities_all"),
                t("hide_communities_badges_only"),
                t("hide_communities_profile_only"),
            ],
            on_change=_on_communities_mode_change,
        ),
        Header(text=t("action_bar")),
        Switch(text=t("hide_action_bar_live_stream"), key=Keys.hide_action_bar_live_stream),
        Switch(text=t("hide_action_bar_archived_stories"), key=Keys.hide_action_bar_archived_stories),
        Switch(text=t("hide_action_bar_send_gift"), key=Keys.hide_action_bar_send_gift),
        Switch(text=t("hide_action_bar_boost_group"), key=Keys.hide_action_bar_boost_group),
        Switch(text=t("hide_action_bar_add_shortcut"), key=Keys.hide_action_bar_add_shortcut),
        Switch(text=t("hide_action_bar_report"), key=Keys.hide_action_bar_report),
        Switch(text=t("hide_action_bar_clear_history"), key=Keys.hide_action_bar_clear_history),
    ]


def _chat_elements_settings() -> list[Any]:
    settings: list[Any] = [
        Header(text=t("gifts")),
        Switch(text=t("hide_bottom_gift_button"), key=Keys.hide_bottom_gift_button),
        Switch(text=t("hide_gift_cards"), key=Keys.hide_gift_cards),
        Switch(text=t("hide_giveaway_cards"), key=Keys.hide_giveaway_cards),
        Switch(text=t("hide_transfer_cards"), key=Keys.hide_transfer_cards),
        Switch(text=t("hide_star_reaction"), key=Keys.hide_star_reaction),
        Switch(text=t("hide_send_money"), key=Keys.hide_chat_send_money),
        Header(text=t("chat_input")),
    ]

    plugin = LiteGramPlugin.get_instance()
    hide_articles = bool(plugin.get_setting(Keys.hide_articles_editor, False))
    settings.append(
        Switch(
            text=t("hide_articles_editor"),
            key=Keys.hide_articles_editor,
            on_change=_on_hide_articles_editor_toggle,
        )
    )
    if not hide_articles:
        settings.append(
            Switch(
                text=t("simplified_articles_editor"),
                key=Keys.simplified_articles_editor,
                on_change=_on_simplified_articles_toggle,
            )
        )
    settings.append(Switch(text=t("hide_todo_button"), key=Keys.hide_todo_button))
    settings.append(Switch(text=t("hide_wallet"), key=Keys.hide_wallet_attach))

    show_ai = False
    try:
        from hook_utils import find_class

        if find_class("com.exteragram.messenger.ai.AiController") is not None:
            show_ai = True
    except Exception:
        pass

    if show_ai:
        settings.extend(
            [
                Header(text=t("ai_features_header")),
                Switch(text=t("hide_ai_button"), key=Keys.hide_ai_button, on_change=_on_hide_ai_button_toggle),
                Switch(text=t("hide_ai_summarize"), key=Keys.hide_ai_summarize),
            ]
        )

    return settings


def _emoji_settings() -> list[Any]:
    return [
        *hide_group_rows("premium_emoji_group", t("premium_emoji_settings_header"), Keys.PREMIUM_EMOJI_ROWS),
        Divider(),
        *hide_group_rows("premium_stickers_group", t("premium_stickers_settings_header"), Keys.PREMIUM_STICKERS_ROWS),
        Divider(),
        Header(text=t("sticker_panel_header")),
        Switch(text=t("hide_group_stickers"), key=Keys.hide_group_stickers),
        Switch(text=t("hide_emoji_search"), key=Keys.hide_emoji_search, subtext=t("emoji_search_info")),
    ]


def _on_premium_badge_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_premium_badge, val, reload_settings=True)


def _profile_settings() -> list[Any]:
    plugin = LiteGramPlugin.get_instance()
    hide_premium = bool(plugin.get_setting(Keys.hide_premium_badge, False))

    elements = [
        Header(text=t("profile_buttons")),
        Switch(text=t("hide_profile_actions_stories_button"), key=Keys.hide_profile_actions_stories_button),
        Switch(text=t("hide_profile_actions_gift_button"), key=Keys.hide_profile_actions_gift_button),
        Switch(text=t("hide_profile_actions_stream_button"), key=Keys.hide_profile_actions_stream_button),
        Header(text=t("profile_tabs")),
        Switch(text=t("hide_stories_tab"), key=Keys.hide_stories_tab),
        Switch(text=t("hide_gifts_tab"), key=Keys.hide_gifts_tab),
        Header(text=t("profile_appearance")),
        Text(
            text=t("manage_reply_elements"),
            link_alias=Keys.reply_elements,
            on_click=open_extera_tab(Keys.reply_elements),
            icon=resolve_icon("extera_outline"),
        ),
        Switch(text=t("hide_profile_background_emoji"), key=Keys.hide_profile_background_emoji),
        Switch(text=t("hide_profile_pinned_gifts"), key=Keys.hide_profile_pinned_gifts, subtext=t("profile_appearance_info")),
        Switch(text=t("hide_profile_colorful_background"), key=Keys.hide_profile_colorful_background),
        Switch(text=t("hide_profile_editor_gifts"), key=Keys.hide_profile_editor_gifts, subtext=t("profile_editor_gifts_info")),
        Switch(text=t("hide_boost_badge"), key=Keys.hide_boost_badge),
        Switch(text=t("hide_premium_badge"), on_change=_on_premium_badge_toggle, key=Keys.hide_premium_badge, subtext=t("premium_badge_info")),
    ]

    if not hide_premium:
        elements.append(Switch(text=t("hide_collectible_status"), key=Keys.hide_collectible_status, subtext=t("collectible_status_info")))

    elements.extend(
        [
            Switch(text=t("hide_stars_rating"), key=Keys.hide_stars_rating),
            Switch(text=t("hide_bot_verification"), key=Keys.hide_bot_verification),
            Switch(text=t("hide_profile_music"), key=Keys.hide_profile_music),
            Switch(text=t("hide_profile_business"), key=Keys.hide_profile_business, subtext=t("profile_business_info")),
            Switch(text=t("hide_profile_balance"), key=Keys.hide_profile_balance),
            Switch(text=t("hide_send_money"), key=Keys.hide_profile_send_money),
        ]
    )

    return elements


def _interface_settings() -> list[Any]:
    items: list[Any] = [
        *hide_group_rows("settings_menu_group", t("settings_options"), SETTINGS_OPTION_ROWS),
        Divider(),
        Header(text=t("drawer_options")),
        Text(
            text=t("manage_drawer_options"),
            link_alias=Keys.drawer_options,
            on_click=open_extera_tab(Keys.drawer_options),
            icon=resolve_icon("extera_outline"),
        ),
        Switch(text=t("hide_wallet"), key=Keys.hide_wallet_drawer),
        Header(text=t("premium_features_header")),
        Switch(text=t("hide_premium_features"), key=Keys.hide_premium_features, subtext=t("premium_features_info")),
    ]

    return items


def _about_settings() -> list[Any]:
    return [
        Header(text=t("about_plugin")),
        Text(text=t("github_repository"), icon="msg_link", on_click=open_url_view(GITHUB_URL)),
        Divider(text=t("github_sub")),
        Switch(
            text=t("enable_debug_logs"),
            key=Keys.enable_debug_logs,
        ),
    ]


def get_main_settings_list() -> list[Any]:
    return [
        Text(text=t("category_chat"), icon="msg_msgbubble3_solar", create_sub_fragment=_chat_settings, link_alias=Keys.chatSettings),
        Text(text=t("category_chat_elements"), icon="msg_discussion", create_sub_fragment=_chat_elements_settings, link_alias=Keys.chatElementsSettings),
        Text(text=t("category_emoji"), icon="msg_reactions_solar", create_sub_fragment=_emoji_settings, link_alias=Keys.emojiSettings),
        Text(text=t("category_profile"), icon="msg_contacts", create_sub_fragment=_profile_settings, link_alias=Keys.profileSettings),
        Text(text=t("category_interface"), icon="msg_settings", create_sub_fragment=_interface_settings, link_alias=Keys.interfaceSettings),
        Text(text=t("category_about"), icon="msg_help", create_sub_fragment=_about_settings, link_alias=Keys.aboutSettings),
    ]
