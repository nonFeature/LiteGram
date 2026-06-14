from hook_utils import find_class

from LiteGram.i18n.locales import STRINGS

_Locale = None
_cached_lang = None


def get_system_language() -> str:
    global _Locale, _cached_lang
    if _cached_lang is not None:
        return _cached_lang
    try:
        if _Locale is None:
            _Locale = find_class("java.util.Locale")

        if not _Locale:
            _cached_lang = "en"
            return _cached_lang

        lang = _Locale.getDefault().getLanguage()
        _cached_lang = lang if lang in STRINGS else "en"
        return _cached_lang
    except Exception:
        pass

    _cached_lang = "en"
    return _cached_lang


def t(key: str, *args) -> str:
    """Translates and replaces {0}, {1} placeholders with provided arguments"""
    lang = get_system_language()
    target_locale = STRINGS.get(lang, STRINGS.get("en", {}))
    result = target_locale.get(key)
    if result is None:
        return f"MISSING: {key}"

    return result.format(*args)
