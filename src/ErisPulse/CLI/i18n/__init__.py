"""
ErisPulse CLI 国际化模块

独立于 Core i18n 的 CLI 国际化模块，完全解耦。

{!--< tips >!--}
1. 与 Core i18n 完全独立，无任何依赖关系
2. 支持的语言: zh-CN, zh-TW, en, ja, ru
3. 外部模块通过 CLI.i18n.t() 获取 CLI 相关翻译
{!--< /tips >!--}
"""

import json
import locale as _locale_module
import os
import sys
from pathlib import Path
from typing import Any

# 支持的语言
SUPPORTED_LANGUAGES = ["zh-CN", "zh-TW", "en", "ja", "ru"]
DEFAULT_LANGUAGE = "en"
FALLBACK_LANGUAGE = "en"

# 语言提示最多显示次数（前 N 次启动时提醒用户确认语言）
LANG_HINT_MAX_SHOWS = 5

# 各语言的显示名称（用于多语言提示同时展示）
LANGUAGE_NAMES = {
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
    "en": "English",
    "ja": "日本語",
    "ru": "Русский",
}

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
        self._saved_lang: str | None = self._load_state().get("language")
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
        # ERISPULSE_LANG 环境变量优先级最高（用于测试/运维覆盖）
        env_lang = os.environ.get("ERISPULSE_LANG", "")
        if env_lang:
            return _resolve_nearest(env_lang)
        # 持久化的用户语言选择
        if self._saved_lang:
            return self._saved_lang
        return self._detected_lang

    def set_language(self, lang: str) -> None:
        """手动设置语言并持久化"""
        self._current_lang = _resolve_nearest(lang)
        self._persist_language(self._current_lang)

    def get_language(self) -> str:
        """获取当前语言"""
        return self._get_effective_language()

    def reset_language(self) -> None:
        """重置为自动检测，并重新检测环境"""
        self._current_lang = None
        self._detected_lang = _detect_language()

    @staticmethod
    def _state_path() -> Path:
        """
        获取 CLI 状态文件路径

        :return: [Path] 状态文件路径 (~/.erispulse/cli_state.json)
        """
        return Path.home() / ".erispulse" / "cli_state.json"

    def _load_state(self) -> dict:
        """
        加载 CLI 持久化状态

        {!--< internal-use >!--}

        :return: [dict] 状态字典，读取失败时返回空字典
        """
        try:
            with self._state_path().open(encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _save_state(self, state: dict) -> None:
        """
        保存 CLI 持久化状态

        {!--< internal-use >!--}

        :param state: [dict] 状态字典
        """
        try:
            self._state_path().parent.mkdir(parents=True, exist_ok=True)
            with self._state_path().open("w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _persist_language(self, lang: str) -> None:
        """
        持久化语言选择到状态文件

        {!--< internal-use >!--}

        :param lang: [str] 语言代码
        """
        state = self._load_state()
        state["language"] = lang
        self._saved_lang = lang
        self._save_state(state)

    def get_lang_hint_shown_count(self) -> int:
        """
        获取语言提示已显示次数

        :return: [int] 已显示次数
        """
        return self._load_state().get("lang_hint_count", 0)

    def increment_lang_hint(self) -> int:
        """
        语言提示显示次数 +1 并持久化

        :return: [int] 更新后的已显示次数
        """
        state = self._load_state()
        count = state.get("lang_hint_count", 0) + 1
        state["lang_hint_count"] = count
        self._save_state(state)
        return count

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

    def t_in(
        self, target_lang: str, key: str, default: str | None = None, **kwargs: Any
    ) -> str:
        """
        获取指定语言的翻译文本（用于多语言同时展示）

        :param target_lang: [str] 目标语言代码
        :param key: [str] 翻译键
        :param default: [str] 默认值 (默认: None)
        :param kwargs: 格式化参数
        :return: [str] 翻译文本
        """
        text = self._translations.get(target_lang, {}).get(key)
        if text is None:
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


__all__ = ["LANGUAGE_NAMES", "LANG_HINT_MAX_SHOWS", "CliI18n", "i18n"]
