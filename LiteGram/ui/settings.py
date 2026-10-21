from typing import Any

from ui.settings import Divider, Header, Selector, Text

from LiteGram.data.constants import GITHUB_URL, Keys
from LiteGram.i18n.i18n import t
from LiteGram.main import LiteGramPlugin
from LiteGram.utils.dex_utils import dex_bridge
from LiteGram.utils.extera_utils import resolve_icon
from LiteGram.utils.settings_utils import (
    Switch,
    open_extera_tab,
    open_url_view,
    toggle_premium_emoji_options,
    toggle_premium_stickers_options,
    toggle_settings_options,
)

SETTINGS_OPTION_ROWS = Keys.SETTINGS_OPTION_ROWS


def _on_communities_mode_change(val: Any) -> None:
    mode = int(val or 0)
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_communities, mode, reload_settings=False)
    dex_bridge.set_flag(Keys.hide_communities_badges, mode in (1, 2))
    dex_bridge.set_flag(Keys.hide_communities_profile, mode in (1, 3))


def _on_hide_articles_editor_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_articles_editor, val, reload_settings=True)


def _chat_settings() -> list[Any]:
    chat_list_items: list[Any] = [
        Header(text=t("chat_list")),
        Text(text=t("hide_stories"), link_alias=Keys.hide_stories, on_click=open_extera_tab(Keys.hide_stories), icon=resolve_icon("extera_outline")),
        Text(
            text=t("hide_action_bar_status"),
            link_alias=Keys.hide_action_bar_status,
            on_click=open_extera_tab(Keys.hide_action_bar_status),
            icon=resolve_icon("extera_outline"),
        ),
        Switch(text=t("hide_greeting_button"), key=Keys.hide_greeting_button, subtext=t("hide_greeting_button_sub")),
    ]

    try:
        from LiteGram.utils.utils import get_client_version, parse_version

        if parse_version(get_client_version()) >= (12, 9, 0):
            chat_list_items.append(
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
                )
            )
    except Exception:
        pass

    settings = [
        *chat_list_items,
        Header(text=t("action_bar")),
        Switch(text=t("hide_action_bar_live_stream"), key=Keys.hide_action_bar_live_stream),
        Switch(text=t("hide_action_bar_archived_stories"), key=Keys.hide_action_bar_archived_stories),
        Switch(text=t("hide_action_bar_send_gift"), key=Keys.hide_action_bar_send_gift),
        Switch(text=t("hide_action_bar_boost_group"), key=Keys.hide_action_bar_boost_group),
        Switch(text=t("hide_action_bar_add_shortcut"), key=Keys.hide_action_bar_add_shortcut),
        Switch(text=t("hide_action_bar_report"), key=Keys.hide_action_bar_report),
        Switch(text=t("hide_action_bar_clear_history"), key=Keys.hide_action_bar_clear_history),
        Header(text=t("gifts")),
        Switch(text=t("hide_bottom_gift_button"), key=Keys.hide_bottom_gift_button),
        Switch(text=t("hide_gift_cards"), key=Keys.hide_gift_cards),
        Switch(text=t("hide_giveaway_cards"), key=Keys.hide_giveaway_cards),
        Switch(text=t("hide_star_reaction"), key=Keys.hide_star_reaction),
        Switch(text=t("hide_group_stickers"), key=Keys.hide_group_stickers),
        Switch(text=t("hide_emoji_search"), key=Keys.hide_emoji_search),
    ]

    try:
        from LiteGram.utils.utils import get_client_version, parse_version

        if parse_version(get_client_version()) >= (12, 9, 0):
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
                    )
                )
            settings.append(
                Switch(
                    text=t("hide_todo_button"),
                    subtext=t("hide_todo_button_sub"),
                    key=Keys.hide_todo_button,
                )
            )
    except Exception:
        pass

    settings.extend(
        [
            Header(text=t("premium_emoji_settings_header")),
            Text(text=t("switch_all"), link_alias=Keys.switch_all_premium_emoji, on_click=toggle_premium_emoji_options),
            *[Switch(text=t(text_key), key=key, default=False) for key, text_key in Keys.PREMIUM_EMOJI_ROWS],
            Header(text=t("premium_stickers_settings_header")),
            Text(text=t("switch_all"), link_alias=Keys.switch_all_premium_stickers, on_click=toggle_premium_stickers_options),
            *[Switch(text=t(text_key), key=key, default=False) for key, text_key in Keys.PREMIUM_STICKERS_ROWS],
        ]
    )

    show_ai = False
    try:
        from LiteGram.utils.utils import get_client_version, parse_version

        if parse_version(get_client_version()) >= (12, 6, 0):
            from hook_utils import find_class

            if find_class("com.exteragram.messenger.ai.AiController") is not None:
                show_ai = True
    except Exception:
        pass

    if show_ai:
        settings.extend(
            [
                Header(text=t("ai_features_header")),
                Switch(text=t("hide_ai_button"), key=Keys.hide_ai_button),
                Switch(text=t("hide_ai_summarize"), key=Keys.hide_ai_summarize),
            ]
        )

    return settings


def notify_interfaces_update() -> None:
    try:
        from hook_utils import find_class

        NotificationCenter = find_class("org.telegram.messenger.NotificationCenter")
        MessagesController = find_class("org.telegram.messenger.MessagesController")
        UserConfig = find_class("org.telegram.messenger.UserConfig")
        if NotificationCenter:
            account = getattr(UserConfig, "selectedAccount", 0) if UserConfig else 0
            mask = getattr(MessagesController, "UPDATE_MASK_ALL", 0xFFFF) if MessagesController else 0xFFFF
            try:
                NotificationCenter.getInstance(account).postNotificationName(NotificationCenter.updateInterfaces, mask)
            except Exception:
                pass
            try:
                NotificationCenter.getGlobalInstance().postNotificationName(NotificationCenter.currentUserPremiumStatusChanged)
            except Exception:
                pass
            try:
                NotificationCenter.getGlobalInstance().postNotificationName(NotificationCenter.mainUserInfoChanged)
            except Exception:
                pass
    except Exception:
        pass


def _on_premium_badge_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_premium_badge, val, reload_settings=True)
    notify_interfaces_update()


def _on_collectible_status_toggle(val: bool) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(Keys.hide_collectible_status, val, reload_settings=False)
    notify_interfaces_update()


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
        Switch(text=t("hide_profile_background_emoji"), subtext=t("hide_profile_background_emoji_sub"), key=Keys.hide_profile_background_emoji),
        Switch(text=t("hide_profile_pinned_gifts"), key=Keys.hide_profile_pinned_gifts),
        Switch(text=t("hide_profile_colorful_background"), key=Keys.hide_profile_colorful_background),
        Switch(text=t("hide_profile_editor_gifts"), subtext=t("hide_profile_editor_gifts_sub"), key=Keys.hide_profile_editor_gifts),
        Switch(text=t("hide_boost_badge"), key=Keys.hide_boost_badge),
        Switch(text=t("hide_premium_badge"), subtext=t("hide_premium_badge_sub"), on_change=_on_premium_badge_toggle, key=Keys.hide_premium_badge),
    ]

    if not hide_premium:
        elements.append(
            Switch(
                text=t("hide_collectible_status"),
                subtext=t("hide_collectible_status_sub"),
                key=Keys.hide_collectible_status,
                on_change=_on_collectible_status_toggle,
            )
        )

    elements.extend(
        [
            Switch(text=t("hide_stars_rating"), key=Keys.hide_stars_rating),
            Switch(text=t("hide_bot_verification"), key=Keys.hide_bot_verification),
            Switch(text=t("hide_profile_music"), key=Keys.hide_profile_music),
            Switch(text=t("hide_profile_business"), subtext=t("hide_profile_business_sub"), key=Keys.hide_profile_business),
        ]
    )

    return elements


def _interface_settings() -> list[Any]:
    items: list[Any] = [
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
        Header(text=t("premium_features_header")),
        Switch(text=t("hide_premium_features"), subtext=t("hide_premium_features_sub"), key=Keys.hide_premium_features),
    ]

    return items


def _about_settings() -> list[Any]:
    return [
        Header(text=t("about_plugin")),
        Text(text=t("github_repository"), icon="msg_link", on_click=open_url_view(GITHUB_URL)),
        Divider(text=t("github_sub")),
        Switch(
            text=t("enable_debug_logs"),
            subtext=t("enable_debug_logs_sub"),
            key=Keys.enable_debug_logs,
        ),
    ]


def get_main_settings_list() -> list[Any]:
    return [
        Text(text=t("category_chat"), icon="msg_discussion", create_sub_fragment=_chat_settings, link_alias=Keys.chatSettings),
        Text(text=t("category_profile"), icon="msg_contacts", create_sub_fragment=_profile_settings, link_alias=Keys.profileSettings),
        Text(text=t("category_interface"), icon="msg_settings", create_sub_fragment=_interface_settings, link_alias=Keys.interfaceSettings),
        Text(text=t("category_about"), icon="msg_help", create_sub_fragment=_about_settings, link_alias=Keys.aboutSettings),
    ]
