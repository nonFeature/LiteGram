from typing import Any


def is_debug_logs_enabled(plugin: Any = None) -> bool:
    try:
        if plugin is None:
            from LiteGram.main import LiteGramPlugin

            plugin = LiteGramPlugin._instance
        if plugin:
            from LiteGram.data.constants import Keys

            return bool(plugin.get_setting(Keys.enable_debug_logs, False))
    except Exception:
        pass
    return False


def log_debug(tag_or_msg: str, msg: str | None = None, force: bool = False) -> None:
    if not force and not is_debug_logs_enabled():
        return

    if msg is not None:
        full_msg = f"[{tag_or_msg}] {msg}"
    else:
        full_msg = str(tag_or_msg)

    try:
        from LiteGram.main import LiteGramPlugin

        plugin = LiteGramPlugin._instance
        if plugin:
            plugin.log(f"[LiteGram] {full_msg}")
    except Exception:
        pass


def log_info(tag_or_msg: str, msg: str | None = None) -> None:
    log_debug(tag_or_msg, msg, force=True)


def log_error(tag_or_msg: str, msg: str | None = None, exc: Exception | None = None) -> None:
    if msg is not None:
        full_msg = f"[{tag_or_msg}] {msg}"
    else:
        full_msg = str(tag_or_msg)
    if exc:
        full_msg += f" (Error: {exc})"

    try:
        from LiteGram.main import LiteGramPlugin

        plugin = LiteGramPlugin._instance
        if plugin:
            plugin.log(f"[LiteGram ERROR] {full_msg}")
    except Exception:
        pass
