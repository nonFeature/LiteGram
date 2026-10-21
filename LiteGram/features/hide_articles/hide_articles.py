from typing import Any

from LiteGram.data.constants import Keys
from LiteGram.utils.dex_utils import dex_bridge


def update_simplified_articles_settings(plugin: Any) -> None:
    hide_editor = bool(plugin.get_setting(Keys.hide_articles_editor, False))
    simplified = bool(plugin.get_setting(Keys.simplified_articles_editor, False))
    dex_bridge.set_flag(Keys.hide_articles_editor, hide_editor)
    dex_bridge.set_flag(Keys.simplified_articles_editor, simplified)


update_hide_articles_dex_settings = update_simplified_articles_settings


def register_hide_articles(plugin: Any) -> None:
    try:
        from LiteGram.utils.utils import get_client_version, parse_version

        if parse_version(get_client_version()) < (12, 9, 0):
            return

        update_simplified_articles_settings(plugin)
    except Exception:
        pass
