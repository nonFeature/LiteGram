from collections.abc import Callable

from android.view import View
from org.telegram.messenger import R as R_tg  # ty: ignore
from ui.bulletin import BulletinHelper
from ui.settings import Switch as BaseSwitch

from LiteGram.data.constants import Keys
from LiteGram.i18n.i18n import t
from LiteGram.main import LiteGramPlugin
from LiteGram.utils.extera_utils import open_extera_setting
from LiteGram.utils.utils import open_url, restart_app


def Switch(
    key: str,
    text: str,
    default: bool | None = False,
    subtext: str | None = None,
    icon: str | None = None,
    on_change: Callable[[bool], None] | None = None,
    on_long_click: Callable[[View], None] | None = None,
    link_alias: str | None = None,
) -> BaseSwitch:
    """
    Uses key for link_alias, default is False
    """
    link_alias = key if link_alias is None else link_alias
    return BaseSwitch(key=key, text=text, default=default, subtext=subtext, icon=icon, on_change=on_change, on_long_click=on_long_click, link_alias=link_alias)


def toggle_settings_options(_: View | None = None) -> None:
    plugin_instance = LiteGramPlugin.get_instance()
    row_keys = [key for key, _ in Keys.SETTINGS_OPTION_ROWS]

    new_state = any(not bool(plugin_instance.get_setting(key, False)) for key in row_keys)
    for i, key in enumerate(row_keys):
        plugin_instance.set_setting(key, new_state, reload_settings=(i == len(row_keys) - 1))


def toggle_emoji_search_options(_: View | None = None) -> None:
    plugin_instance = LiteGramPlugin.get_instance()
    row_keys = [key for key, _ in Keys.EMOJI_SEARCH_ROWS]

    new_state = any(not bool(plugin_instance.get_setting(key, False)) for key in row_keys)
    for i, key in enumerate(row_keys):
        plugin_instance.set_setting(key, new_state, reload_settings=(i == len(row_keys) - 1))


def toggle_premium_emoji_options(_: View | None = None) -> None:
    plugin_instance = LiteGramPlugin.get_instance()
    row_keys = [
        Keys.hide_premium_emoji_packs,
        Keys.hide_premium_search,
        Keys.hide_premium_suggestions,
    ]

    new_state = any(not bool(plugin_instance.get_setting(key, True)) for key in row_keys)
    for i, key in enumerate(row_keys):
        plugin_instance.set_setting(key, new_state, reload_settings=(i == len(row_keys) - 1))


def toggle_premium_stickers_options(_: View | None = None) -> None:
    plugin_instance = LiteGramPlugin.get_instance()
    row_keys = [
        Keys.hide_premium_stickers_recent,
        Keys.hide_premium_stickers_search,
        Keys.hide_premium_stickers_grid,
    ]

    new_state = any(not bool(plugin_instance.get_setting(key, True)) for key in row_keys)
    for i, key in enumerate(row_keys):
        plugin_instance.set_setting(key, new_state, reload_settings=(i == len(row_keys) - 1))


def open_extera_tab(tab_name: str) -> Callable[[View], None]:
    def callback(view: View):
        open_extera_setting(tab_name, plugin_id="litegram")

    return callback


def open_url_view(url: str) -> Callable[[View], None]:
    def callback(view: View):
        open_url(url)

    return callback


def show_restart_bulletin(_enabled: bool) -> None:
    BulletinHelper.show_with_button(text=t("restart_required"), button_text=t("restart"), icon_res_id=R_tg.raw.info, on_click=lambda: restart_app())


def show_restart_bulletin_if_disabled(enabled: bool) -> None:
    if not enabled:
        show_restart_bulletin(False)
