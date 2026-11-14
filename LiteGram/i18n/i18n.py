from hook_utils import find_class

from LiteGram.i18n.locales import STRINGS

_DEFAULT_LANG = "en"

_LocaleController = None
_Locale = None
_cached_lang = None


def _normalize_lang(code: str) -> str:
    # "pt-BR" -> "pt", "ru-raw" -> "ru"
    return (code or "").lower().replace("_", "-").replace("-raw", "").split("-", 1)[0]


def _detect_language() -> str:
    global _LocaleController, _Locale

    # Telegram's own language setting first, the OS locale second
    try:
        if _LocaleController is None:
            _LocaleController = find_class("org.telegram.messenger.LocaleController")
        if _LocaleController:
            info = _LocaleController.getInstance().getCurrentLocaleInfo()
            if info:
                code = _normalize_lang(str(info.getLangCode()))
                if code in STRINGS:
                    return code
    except Exception:
        pass

    try:
        if _Locale is None:
            _Locale = find_class("java.util.Locale")
        if _Locale:
            code = _normalize_lang(str(_Locale.getDefault().getLanguage()))
            if code in STRINGS:
                return code
    except Exception:
        pass

    return _DEFAULT_LANG


def get_system_language() -> str:
    global _cached_lang
    if _cached_lang is None:
        _cached_lang = _detect_language()
    return _cached_lang


def t(key: str, *args) -> str:
    """Translates and replaces {0}, {1} placeholders with provided arguments"""
    lang = get_system_language()
    result = STRINGS.get(lang, {}).get(key)
    if result is None and lang != _DEFAULT_LANG:
        result = STRINGS.get(_DEFAULT_LANG, {}).get(key)
    if result is None:
        return f"MISSING: {key}"

    return result.format(*args)
