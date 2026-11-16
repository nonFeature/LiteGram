from collections.abc import Callable, Sequence
from typing import Any

from android.view import View
from org.telegram.messenger import R as R_tg  # ty: ignore
from ui.bulletin import BulletinHelper
from ui.settings import Selector as BaseSelector, Switch as BaseSwitch

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
    Uses key for link_alias, default is False.
    Ensures an on_change handler is always attached so exteraGram notifies Python
    and immediately syncs settings cache and native DEX flags on every toggle.
    """
    link_alias = key if link_alias is None else link_alias

    def _switch_on_change(val: bool) -> None:
        try:
            plugin = LiteGramPlugin.get_instance()
            plugin.set_setting(key, val, reload_settings=False)
        except Exception:
            pass
        if on_change is not None:
            on_change(val)

    return BaseSwitch(
        key=key,
        text=text,
        default=default,
        subtext=subtext,
        icon=icon,
        on_change=_switch_on_change,
        on_long_click=on_long_click,
        link_alias=link_alias,
    )


def Selector(
    key: str,
    text: str,
    items: Sequence[str] | None = None,
    default: int = 0,
    icon: str | None = None,
    on_change: Callable[[Any], None] | None = None,
    on_long_click: Callable[[View], None] | None = None,
    link_alias: str | None = None,
    **kwargs: Any,
) -> Any:
    """
    Uses key for link_alias by default if not explicitly provided,
    enabling deeplink copying on long click.
    """
    link_alias = key if link_alias is None else link_alias
    return BaseSelector(
        key=key,
        text=text,
        items=items,
        default=default,
        icon=icon,
        on_change=on_change,
        on_long_click=on_long_click,
        link_alias=link_alias,
        **kwargs,
    )


_EXPANDED_GROUPS: set[str] = set()


def _stable_row_id(key: str) -> int:
    return hash(key) & 0x7FFFFFFF


def _hidden_count(rows: Sequence[tuple[str, str]]) -> int:
    plugin = LiteGramPlugin.get_instance()
    return sum(1 for key, _ in rows if bool(plugin.get_setting(key, False)))


def _reload_settings_page(anchor_key: str) -> None:
    # Rebuild the settings page by re-writing one key with its current value;
    # the value is unchanged, only the reload side effect matters.
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(anchor_key, bool(plugin.get_setting(anchor_key, False)), reload_settings=True)


def _toggle_group_expanded(group_key: str, anchor_key: str) -> None:
    if group_key in _EXPANDED_GROUPS:
        _EXPANDED_GROUPS.discard(group_key)
    else:
        _EXPANDED_GROUPS.add(group_key)
    _reload_settings_page(anchor_key)


def _toggle_whole_group(rows: Sequence[tuple[str, str]]) -> None:
    plugin = LiteGramPlugin.get_instance()
    new_state = any(not bool(plugin.get_setting(key, False)) for key, _ in rows)
    for key, _ in rows:
        plugin.set_setting(key, new_state, reload_settings=False)
    _reload_settings_page(rows[0][0])


def _toggle_group_child(key: str) -> None:
    plugin = LiteGramPlugin.get_instance()
    plugin.set_setting(key, not bool(plugin.get_setting(key, False)), reload_settings=True)


def hide_group_rows(group_key: str, title: str, rows: Sequence[tuple[str, str]]) -> list[Any]:
    """Expandable switch group in the style of extera's own SwitchGroup
    (exteraSettings?s=md3Styles): a switch row with an "n/N" counter that
    expands into round checkboxes, one per (key, text_key).

    Row/switch/children are raw UItems wrapped in the SDK's Custom row type;
    tapping the row expands/collapses it, the switch toggles the whole group.
    Everything is stored as plain booleans via set_setting (which also syncs
    the DEX flags); expansion state is in-memory only.
    """
    from android_utils import OnClickListener
    from org.telegram.ui.Components import UItem  # ty: ignore
    from ui.settings import Custom  # ty: ignore[unresolved-import]

    hidden = _hidden_count(rows)
    total = len(rows)

    group_item = UItem.asExteraExpandableSwitch(
        _stable_row_id(group_key),
        title,
        f"{hidden}/{total}",
        OnClickListener(lambda view: _toggle_whole_group(rows)),
    )
    group_item.setChecked(hidden > 0)
    group_item.setCollapsed(group_key not in _EXPANDED_GROUPS)

    items: list[Any] = [
        Custom(
            item=group_item,
            on_click=lambda view: _toggle_group_expanded(group_key, rows[0][0]),
            link_alias=group_key,
        )
    ]

    if group_key in _EXPANDED_GROUPS:
        plugin = LiteGramPlugin.get_instance()
        for key, text_key in rows:
            child_item = UItem.asRoundCheckbox(_stable_row_id(key), t(text_key))
            child_item.setChecked(bool(plugin.get_setting(key, False)))
            child_item.pad()

            def make_on_child_click(setting_key: str) -> Callable[[View], None]:
                def on_child_click(view: View) -> None:
                    _toggle_group_child(setting_key)

                return on_child_click

            items.append(
                Custom(
                    item=child_item,
                    on_click=make_on_child_click(key),
                    link_alias=key,
                )
            )

    return items


def on_toggle_with_restart(key: str) -> Callable[[bool], None]:
    def callback(val: bool):
        plugin = LiteGramPlugin.get_instance()
        plugin.set_setting(key, val)
        show_restart_bulletin(val)

    return callback


on_media_toggle = on_toggle_with_restart


def open_extera_tab(tab_name: str) -> Callable[[View], None]:
    def callback(view: View):
        open_extera_setting(tab_name)

    return callback


def open_url_view(url: str) -> Callable[[View], None]:
    def callback(view: View):
        open_url(url)

    return callback


def show_restart_bulletin(_enabled: bool = False) -> None:
    BulletinHelper.show_with_button(text=t("restart_required"), button_text=t("restart"), icon_res_id=R_tg.raw.info, on_click=lambda: restart_app())


def show_restart_bulletin_if_disabled(enabled: bool) -> None:
    if not enabled:
        show_restart_bulletin(False)


def reload_ui_on_change(key: str) -> Callable[[bool], None]:
    def callback(enabled: bool):
        LiteGramPlugin.get_instance().set_setting(key, enabled, reload_settings=True)

    return callback


def reload_ui_and_show_restart_bulletin_if_disabled(key: str) -> Callable[[bool], None]:
    def callback(enabled: bool):
        LiteGramPlugin.get_instance().set_setting(key, enabled, reload_settings=True)
        if not enabled:
            show_restart_bulletin(False)

    return callback
