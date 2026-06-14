"""
ErisPulse 国际化模块

提供多语言支持，支持自动检测用户语言环境并按就近原则映射到支持的语言。

{!--< tips >!--}
1. 框架内部和外部的模块都通过 i18n.t() 获取翻译文本
2. 支持的语言: zh-CN (简体中文), zh-TW (繁体中文), en (英文), ja (日文), ru (俄文)
3. 自动检测语言环境，也可手动设置: i18n.set_language("en")
4. 外部模块可通过 i18n.register() 注册自己的翻译
{!--< /tips >!--}
"""

import locale as _locale_module
import os
import sys
import threading
from typing import Any

from .constants import (
    DEFAULT_LANGUAGE,
    FALLBACK_LANGUAGE,
    SUPPORTED_LANGUAGES,
)


class I18nManager:
    """
    国际化管理器

    负责语言检测、翻译查找和翻译注册。

    语言检测优先级:
    1. 手动通过 set_language() 设置的语言
    2. 配置项 ErisPulse.i18n.language
    3. 环境变量 LANGUAGE / LC_ALL / LC_MESSAGES / LANG
    4. 系统默认 locale (locale.getdefaultlocale)
    5. 默认语言 (zh-CN)

    就近映射规则:
    - zh-TW, zh-HK, zh-MO, zh-Hant -> zh-TW (繁体中文)
    - zh-CN, zh-SG, zh-MY, zh-Hans, zh 及其他 zh* -> zh-CN (简体中文)
    - en, en-US, en-GB 及其他 en* -> en
    - ja, ja-JP 及其他 ja* -> ja
    - ru, ru-RU 及其他 ru* -> ru
    - 其他未识别的语言 -> 默认语言
    """

    # 精确匹配表: 完整 locale code -> 支持的语言
    # 仅处理会被映射的，其他通过主标签推导
    _LOCALE_EXACT_MAP = {
        # 简体中文
        "zh-cn": "zh-CN",
        "zh-hans": "zh-CN",
        "zh-sg": "zh-CN",
        "zh-my": "zh-CN",
        "chs": "zh-CN",
        "zh": "zh-CN",
        # 繁体中文
        "zh-tw": "zh-TW",
        "zh-hant": "zh-TW",
        "zh-hk": "zh-TW",
        "zh-mo": "zh-TW",
        "cht": "zh-TW",
        # 英文
        "en": "en",
        "en-us": "en",
        "en-gb": "en",
        "en-au": "en",
        "en-ca": "en",
        "en-nz": "en",
        "en-ie": "en",
        "en-za": "en",
        "en-in": "en",
        # 日文
        "ja": "ja",
        "ja-jp": "ja",
        # 俄文
        "ru": "ru",
        "ru-ru": "ru",
        "ru-by": "ru",
        "ru-kz": "ru",
    }

    # 繁体中文地区/脚本标识
    _TRADITIONAL_ZH_INDICATORS = {"tw", "hk", "mo", "hant", "cht"}

    # 主标签映射
    _PRIMARY_TAG_MAP = {
        "en": "en",
        "ja": "ja",
        "ru": "ru",
    }

    def __init__(self):
        self._lock = threading.RLock()
        self._current_lang: str | None = None
        self._translations: dict[str, dict[str, str]] = {}
        self._domains: dict[
            str, set[str]
        ] = {}  # domain -> set of keys (for unregister)
        # 加载内置翻译
        self._load_builtin_translations()
        # 初始检测语言
        self._detected_lang = self._detect_language()

    # ==================== 内置翻译加载 ====================

    def _load_builtin_translations(self) -> None:
        """
        加载框架内置翻译数据

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        from . import locales as _locales_pkg

        for lang_code in SUPPORTED_LANGUAGES:
            data = _locales_pkg.get_translations(lang_code)
            if data:
                # 合并到 _translations，标记为内置域
                if lang_code not in self._translations:
                    self._translations[lang_code] = {}
                self._translations[lang_code].update(data)

    # ==================== 语言检测 ====================

    def _resolve_nearest(self, locale_str: str) -> str:
        """
        将任意 locale 字符串映射到最近的支持语言

        :param locale_str: locale 字符串，如 "zh_TW.UTF-8", "en_US", "ja"
        :return: 支持的语言代码

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if not locale_str:
            return DEFAULT_LANGUAGE

        locale_str = str(locale_str)
        # 标准化: 移除编码后缀，统一分隔符
        normalized = locale_str.strip().split(".")[0]
        normalized = normalized.replace("_", "-")
        key = normalized.lower()

        # 精确匹配
        if key in self._LOCALE_EXACT_MAP:
            return self._LOCALE_EXACT_MAP[key]

        parts = normalized.split("-")
        primary = parts[0].lower()

        # 中文特殊处理
        if primary == "zh":
            if len(parts) > 1:
                region = parts[1].lower()
                if region in self._TRADITIONAL_ZH_INDICATORS:
                    return "zh-TW"
            return "zh-CN"

        # 其他语言按主标签映射
        if primary in self._PRIMARY_TAG_MAP:
            return self._PRIMARY_TAG_MAP[primary]

        return DEFAULT_LANGUAGE

    def _detect_language(self) -> str:
        """
        自动检测用户语言环境（跨平台）

        检测顺序:
        Windows:
        1. Windows API: GetUserDefaultLocaleName
        2. 环境变量 LANGUAGE / LC_ALL / LC_MESSAGES / LANG
        3. locale.getlocale() / locale.getdefaultlocale()

        Unix/macOS:
        1. 环境变量 LANGUAGE / LC_ALL / LC_MESSAGES / LANG
        2. locale.getlocale() / locale.getdefaultlocale()

        :return: 检测到的支持语言代码

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        is_windows = sys.platform == "win32"

        # 0. 专用环境变量 ERISPULSE_LANG（最高优先级，用于测试和运维）
        erispulse_lang = os.environ.get("ERISPULSE_LANG", "")
        if erispulse_lang:
            return self._resolve_nearest(erispulse_lang)

        # Windows: 优先使用系统 API（环境变量 LANG 可能被 Git Bash 等工具覆盖）
        if is_windows:
            win_locale = self._detect_windows_locale()
            if win_locale:
                return self._resolve_nearest(win_locale)

        # 环境变量（Unix 主要方式，Windows 备选）
        for env_var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
            env_val = os.environ.get(env_var, "")
            if env_val:
                # LANGUAGE 可能是冒号分隔的列表，取第一个
                first = env_val.split(":")[0].strip()
                if first:
                    return self._resolve_nearest(first)

        # Windows: 尝试更多 locale 获取方式
        if is_windows:
            # locale.getlocale() 可能返回如 ('Chinese (Simplified)_China', '936')
            try:
                loc = _locale_module.getlocale()
                if loc and loc[0] and loc[0] != "C":
                    resolved = self._resolve_windows_locale_name(loc[0])
                    if resolved:
                        return resolved
            except Exception:
                pass

        # locale.getlocale() (当前 locale 设置)
        try:
            loc = _locale_module.getlocale()
            if loc and loc[0] and loc[0] != "C":
                return self._resolve_nearest(loc[0])
        except Exception:
            pass

        # locale.getdefaultlocale() (Python 3.11+ 废弃，但作为兼容层)
        try:
            loc = _locale_module.getdefaultlocale()
            if loc and loc[0] and loc[0] != "C":
                return self._resolve_nearest(loc[0])
        except Exception:
            pass

        return DEFAULT_LANGUAGE

    @staticmethod
    def _resolve_windows_locale_name(locale_name: str) -> str | None:
        """
        将 Windows locale 名称（如 'Chinese (Simplified)_China'）映射到支持语言

        locale.getlocale() 在 Windows 上可能返回语言全称而非代码

        :param locale_name: Windows locale 名称
        :return: 支持的语言代码或 None

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        name_lower = locale_name.lower()

        # 中文
        if "chinese" in name_lower or "中文" in locale_name:
            if "simplified" in name_lower or "简体" in locale_name:
                return "zh-CN"
            if (
                "traditional" in name_lower
                or "繁體" in locale_name
                or "繁体" in locale_name
                or "taiwan" in name_lower
                or "hong kong" in name_lower
                or "macau" in name_lower
                or "台灣" in locale_name
                or "台湾" in locale_name
            ):
                return "zh-TW"
            # 默认简体
            return "zh-CN"

        # 英文
        if "english" in name_lower:
            return "en"

        # 日文
        if "japanese" in name_lower or "日本語" in locale_name:
            return "ja"

        # 俄文
        if "russian" in name_lower or "Русский" in locale_name:
            return "ru"

        return None

    @staticmethod
    def _detect_windows_locale() -> str | None:
        """
        通过 Windows API 检测用户默认 locale

        使用 GetUserDefaultLocaleName / GetSystemDefaultLocaleName 获取
        BCP 47 格式的 locale 名称（如 "zh-CN", "en-US"）

        :return: locale 字符串或 None

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        try:
            import ctypes

            # LOCALE_NAME_USER_DEFAULT = 0x01 on older Windows
            # GetUserDefaultLocaleName 返回 BCP 47 格式
            buf = ctypes.create_unicode_buffer(85)
            # 尝试 GetUserDefaultLocaleName
            res = ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)
            if res > 0 and buf.value:
                return buf.value
        except Exception:
            pass

        # 备选: 通过 GetLocaleInfoW 获取语言 ID 再转换
        try:
            import ctypes

            # LOCALE_USER_DEFAULT = 0x0400 (0x0000 | 0x0400)
            # LOCALE_SISO639LANGNAME = 0x0059, LOCALE_SISO3166CTRYNAME = 0x005A
            # 获取语言代码 (ISO 639)
            lang_buf = ctypes.create_unicode_buffer(9)
            ctry_buf = ctypes.create_unicode_buffer(9)

            # 0x0400 = LOCALE_USER_DEFAULT
            if ctypes.windll.kernel32.GetLocaleInfoW(
                0x0400, 0x0059, lang_buf, 9
            ) and ctypes.windll.kernel32.GetLocaleInfoW(0x0400, 0x005A, ctry_buf, 9):
                lang = lang_buf.value.strip()
                ctry = ctry_buf.value.strip()
                if lang:
                    if ctry:
                        return f"{lang}-{ctry}"
                    return lang
        except Exception:
            pass

        return None

    def _get_effective_language(self) -> str:
        """
        获取当前生效的语言

        优先级: 手动设置 > 配置项 > 检测到的语言

        配置值为 "auto" 时使用自动检测的语言。

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        if self._current_lang is not None:
            return self._current_lang

        # 尝试从配置读取
        try:
            from ..config import config

            cfg_lang = config.getConfig("ErisPulse.i18n.language", None)
            if cfg_lang and isinstance(cfg_lang, str):
                # "auto" 表示使用自动检测的语言
                if cfg_lang.lower() == "auto":
                    return self._detected_lang
                resolved = self._resolve_nearest(cfg_lang)
                return resolved
        except Exception:
            pass

        return self._detected_lang

    # ==================== 公开 API ====================

    def set_language(self, lang: str) -> None:
        """
        手动设置当前语言

        :param lang: 语言代码，如 "zh-CN", "en", "ja", "ru"
        会自动按就近原则映射到支持的语言。

        :example:
        >>> i18n.set_language("en")
        >>> i18n.set_language("zh-TW")  # 繁体中文
        """
        resolved = self._resolve_nearest(lang)
        with self._lock:
            self._current_lang = resolved

    def get_language(self) -> str:
        """
        获取当前生效的语言代码

        :return: str 语言代码，如 "zh-CN", "en"
        """
        return self._get_effective_language()

    def get_supported_languages(self) -> list[str]:
        """
        获取所有支持的语言列表

        :return: list[str] 支持的语言代码列表
        """
        return list(SUPPORTED_LANGUAGES)

    def reset_language(self) -> None:
        """
        重置为自动检测的语言（清除手动设置），并重新检测环境
        """
        with self._lock:
            self._current_lang = None
            self._detected_lang = self._detect_language()

    def t(self, key: str, /, default: str | None = None, **kwargs: Any) -> str:
        """
        获取翻译文本

        :param key: str 翻译键，如 "core.sdk.init.starting"
        :param default: str 默认值，当翻译不存在时返回。默认为 None（返回 key 本身）
        :param kwargs: 格式化参数，如 t("key", name="world") 会填充 {name}
        :return: str 翻译后的文本

        :example:
        >>> i18n.t("core.sdk.init.starting")
        >>> i18n.t("core.adapter.load_failed", platform="OneBot")
        >>> i18n.t("my_module.welcome", default="Welcome!")
        """
        lang = self._get_effective_language()

        text = self._lookup(key, lang)

        if text is None:
            # 回退到回退语言
            if lang != FALLBACK_LANGUAGE:
                text = self._lookup(key, FALLBACK_LANGUAGE)

        if text is None:
            # 回退到默认语言
            if lang != DEFAULT_LANGUAGE and FALLBACK_LANGUAGE != DEFAULT_LANGUAGE:
                text = self._lookup(key, DEFAULT_LANGUAGE)

        if text is None:
            return default if default is not None else key

        # 格式化
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text

        return text

    def gettext(self, key: str, /, default: str | None = None, **kwargs: Any) -> str:
        """
        t() 的别名，兼容 gettext 风格

        :param key: str 翻译键
        :param default: str 默认值
        :param kwargs: 格式化参数
        :return: str 翻译后的文本
        """
        return self.t(key, default, **kwargs)

    def _lookup(self, key: str, lang: str) -> str | None:
        """
        在指定语言中查找翻译键

        {!--< internal-use >!--}
        {!--< /internal-use >!--}
        """
        lang_dict = self._translations.get(lang)
        if lang_dict is None:
            return None
        return lang_dict.get(key)

    # ==================== 翻译注册 API ====================

    def register(
        self, lang: str, translations: dict[str, str], domain: str = "app"
    ) -> None:
        """
        注册翻译文本（供外部模块使用）

        :param lang: str 语言代码，如 "en", "zh-CN"（会按就近原则映射）
        :param translations: dict[str, str] 翻译键值对，如 {"my_module.welcome": "Welcome!"}
        :param domain: str 域名，用于区分不同模块的翻译，默认 "app"

        :example:
        >>> i18n.register("zh-CN", {
        ...     "mybot.welcome": "欢迎使用机器人",
        ...     "mybot.goodbye": "再见",
        ... }, domain="mybot")
        >>> i18n.register("en", {
        ...     "mybot.welcome": "Welcome to the bot",
        ...     "mybot.goodbye": "Goodbye",
        ... }, domain="mybot")
        """
        resolved = self._resolve_nearest(lang)
        with self._lock:
            if resolved not in self._translations:
                self._translations[resolved] = {}
            self._translations[resolved].update(translations)

            # 记录域的键，便于卸载
            if domain not in self._domains:
                self._domains[domain] = set()
            self._domains[domain].update(translations.keys())

    def unregister_domain(self, domain: str) -> None:
        """
        卸载指定域的所有翻译

        :param domain: str 域名

        :example:
        >>> i18n.unregister_domain("mybot")
        """
        with self._lock:
            keys = self._domains.pop(domain, set())
            for key in keys:
                for lang_dict in self._translations.values():
                    lang_dict.pop(key, None)

    def has_translation(self, key: str, lang: str | None = None) -> bool:
        """
        检查翻译键是否存在

        :param key: str 翻译键
        :param lang: str 指定语言，默认为当前语言
        :return: bool 是否存在翻译
        """
        if lang is None:
            lang = self._get_effective_language()
        resolved = self._resolve_nearest(lang)
        return key in self._translations.get(resolved, {})

    def reload(self) -> None:
        """
        重新加载内置翻译并重新检测语言
        """
        with self._lock:
            self._translations.clear()
            self._domains.clear()
            self._load_builtin_translations()
            self._detected_lang = self._detect_language()


# ==================== 模块级单例 ====================

i18n: I18nManager = I18nManager()


__all__ = ["i18n", "I18nManager"]
