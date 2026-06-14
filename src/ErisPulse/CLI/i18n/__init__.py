"""
ErisPulse CLI 国际化模块

独立于 Core i18n 的 CLI 国际化模块，完全解耦。

{!--< tips >!--}
1. 与 Core i18n 完全独立，无任何依赖关系
2. 支持的语言: zh-CN, zh-TW, en, ja, ru
3. 外部模块通过 CLI.i18n.t() 获取 CLI 相关翻译
{!--< /tips >!--}
"""

import locale as _locale_module
import os
import sys
from typing import Any

# 支持的语言
SUPPORTED_LANGUAGES = ["zh-CN", "zh-TW", "en", "ja", "ru"]
DEFAULT_LANGUAGE = "en"
FALLBACK_LANGUAGE = "en"

# 精确 locale -> 语言 映射（与 Core i18n 保持一致）
_LOCALE_EXACT_MAP = {
    "zh-cn": "zh-CN",
    "zh-hans": "zh-CN",
    "zh-sg": "zh-CN",
    "zh-my": "zh-CN",
    "chs": "zh-CN",
    "zh": "zh-CN",
    "zh-tw": "zh-TW",
    "zh-hant": "zh-TW",
    "zh-hk": "zh-TW",
    "zh-mo": "zh-TW",
    "cht": "zh-TW",
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
    "en-au": "en",
    "en-ca": "en",
    "en-nz": "en",
    "en-ie": "en",
    "en-za": "en",
    "en-in": "en",
    "ja": "ja",
    "ja-jp": "ja",
    "ru": "ru",
    "ru-ru": "ru",
    "ru-by": "ru",
    "ru-kz": "ru",
}
_TRADITIONAL_ZH_INDICATORS = {"tw", "hk", "mo", "hant", "cht"}
_PRIMARY_TAG_MAP = {"en": "en", "ja": "ja", "ru": "ru"}


def _resolve_nearest(locale_str: str) -> str:
    """将任意 locale 映射到最近的支持语言"""
    if not locale_str:
        return DEFAULT_LANGUAGE
    locale_str = str(locale_str)
    normalized = locale_str.strip().split(".")[0]
    normalized = normalized.replace("_", "-")
    key = normalized.lower()
    if key in _LOCALE_EXACT_MAP:
        return _LOCALE_EXACT_MAP[key]
    parts = normalized.split("-")
    primary = parts[0].lower()
    if primary == "zh":
        if len(parts) > 1 and parts[1].lower() in _TRADITIONAL_ZH_INDICATORS:
            return "zh-TW"
        return "zh-CN"
    if primary in _PRIMARY_TAG_MAP:
        return _PRIMARY_TAG_MAP[primary]
    return DEFAULT_LANGUAGE


def _detect_windows_locale() -> str | None:
    """通过 Windows API 检测用户 locale"""
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(85)
        if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85) > 0 and buf.value:
            return buf.value
    except Exception:
        pass
    return None


def _detect_language() -> str:
    """自动检测用户语言环境"""
    is_windows = sys.platform == "win32"

    # 专用环境变量 ERISPULSE_LANG（最高优先级，用于测试和运维）
    erispulse_lang = os.environ.get("ERISPULSE_LANG", "")
    if erispulse_lang:
        return _resolve_nearest(erispulse_lang)

    # Windows: 优先系统 API
    if is_windows:
        win_locale = _detect_windows_locale()
        if win_locale:
            return _resolve_nearest(win_locale)
    # 环境变量
    for env_var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        env_val = os.environ.get(env_var, "")
        if env_val:
            first = env_val.split(":")[0].strip()
            if first:
                return _resolve_nearest(first)
    # locale 模块
    try:
        loc = _locale_module.getlocale()
        if loc and loc[0] and loc[0] != "C":
            return _resolve_nearest(loc[0])
    except Exception:
        pass
    try:
        loc = _locale_module.getdefaultlocale()
        if loc and loc[0] and loc[0] != "C":
            return _resolve_nearest(loc[0])
    except Exception:
        pass
    return DEFAULT_LANGUAGE


class CliI18n:
    """
    CLI 国际化管理器

    与 Core i18n 完全独立，专门处理 CLI 命令的翻译文本。
    """

    def __init__(self):
        self._current_lang: str | None = None
        self._translations: dict[str, dict[str, str]] = {}
        self._detected_lang = _detect_language()
        self._load_builtin()

    def _load_builtin(self):
        """加载内置 CLI 翻译"""
        from . import locales as _locales_pkg

        for lang_code in SUPPORTED_LANGUAGES:
            data = _locales_pkg.get_translations(lang_code)
            if data:
                if lang_code not in self._translations:
                    self._translations[lang_code] = {}
                self._translations[lang_code].update(data)

    def _get_effective_language(self) -> str:
        if self._current_lang is not None:
            return self._current_lang
        return self._detected_lang

    def set_language(self, lang: str) -> None:
        """手动设置语言"""
        self._current_lang = _resolve_nearest(lang)

    def get_language(self) -> str:
        """获取当前语言"""
        return self._get_effective_language()

    def reset_language(self) -> None:
        """重置为自动检测，并重新检测环境"""
        self._current_lang = None
        self._detected_lang = _detect_language()

    def t(self, key: str, default: str | None = None, **kwargs: Any) -> str:
        """
        获取 CLI 翻译文本

        :param key: 翻译键
        :param default: 默认值
        :param kwargs: 格式化参数
        :return: 翻译文本
        """
        lang = self._get_effective_language()
        text = self._translations.get(lang, {}).get(key)
        if text is None and lang != FALLBACK_LANGUAGE:
            text = self._translations.get(FALLBACK_LANGUAGE, {}).get(key)
        if text is None and lang != DEFAULT_LANGUAGE:
            text = self._translations.get(DEFAULT_LANGUAGE, {}).get(key)
        if text is None:
            return default if default is not None else key
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text


# 模块级单例
i18n: CliI18n = CliI18n()


__all__ = ["i18n", "CliI18n"]
