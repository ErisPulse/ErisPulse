"""
国际化模块单元测试

测试I18nManager的语言检测、就近映射、翻译查找和注册功能
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from ErisPulse.Core.i18n import I18nManager

# ==================== I18nManager 基础测试 ====================


class TestI18nManager:
    """国际化管理器测试类"""

    @pytest.fixture
    def i18n_manager(self):
        """创建国际化管理器实例"""
        manager = I18nManager()
        yield manager

    # ==================== 语言检测测试 ====================

    def test_supported_languages(self, i18n_manager):
        """测试支持的语言列表"""
        langs = i18n_manager.get_supported_languages()
        assert "zh-CN" in langs
        assert "zh-TW" in langs
        assert "en" in langs
        assert "ja" in langs
        assert "ru" in langs
        assert len(langs) == 5

    def test_set_and_get_language(self, i18n_manager):
        """测试手动设置语言"""
        i18n_manager.set_language("en")
        assert i18n_manager.get_language() == "en"

        i18n_manager.set_language("zh-TW")
        assert i18n_manager.get_language() == "zh-TW"

    def test_reset_language(self, i18n_manager):
        """测试重置语言"""
        i18n_manager.set_language("en")
        assert i18n_manager.get_language() == "en"

        i18n_manager.reset_language()
        # 重置后应该是检测到的语言
        assert i18n_manager._current_lang is None

    # ==================== 就近映射测试 ====================

    @pytest.mark.parametrize(
        "locale,expected",
        [
            # 简体中文
            ("zh-CN", "zh-CN"),
            ("zh-Hans", "zh-CN"),
            ("zh-SG", "zh-CN"),
            ("zh-MY", "zh-CN"),
            ("zh", "zh-CN"),
            ("chs", "zh-CN"),
            # 繁体中文
            ("zh-TW", "zh-TW"),
            ("zh-Hant", "zh-TW"),
            ("zh-HK", "zh-TW"),
            ("zh-MO", "zh-TW"),
            ("cht", "zh-TW"),
            # 英文
            ("en", "en"),
            ("en-US", "en"),
            ("en-GB", "en"),
            ("en-AU", "en"),
            # 日文
            ("ja", "ja"),
            ("ja-JP", "ja"),
            # 俄文
            ("ru", "ru"),
            ("ru-RU", "ru"),
        ],
    )
    def test_resolve_nearest(self, i18n_manager, locale, expected):
        """测试就近语言映射"""
        assert i18n_manager._resolve_nearest(locale) == expected

    def test_resolve_nearest_with_encoding(self, i18n_manager):
        """测试带编码后缀的locale映射"""
        assert i18n_manager._resolve_nearest("zh_TW.UTF-8") == "zh-TW"
        assert i18n_manager._resolve_nearest("en_US.UTF-8") == "en"
        assert i18n_manager._resolve_nearest("ja_JP.UTF-8") == "ja"

    def test_resolve_nearest_unknown(self, i18n_manager):
        """测试未知语言的映射（回退到默认语言）"""
        assert i18n_manager._resolve_nearest("fr-FR") == "zh-CN"
        assert i18n_manager._resolve_nearest("de-DE") == "zh-CN"
        assert i18n_manager._resolve_nearest("ko-KR") == "zh-CN"

    def test_resolve_nearest_empty(self, i18n_manager):
        """测试空字符串的映射"""
        assert i18n_manager._resolve_nearest("") == "zh-CN"
        assert i18n_manager._resolve_nearest(None) == "zh-CN"

    # ==================== 翻译查找测试 ====================

    def test_translation_exists(self, i18n_manager):
        """测试翻译键存在"""
        i18n_manager.set_language("zh-CN")
        text = i18n_manager.t("core.sdk.init.starting")
        assert text == "SDK 正在初始化..."

    def test_translation_english(self, i18n_manager):
        """测试英文翻译"""
        i18n_manager.set_language("en")
        text = i18n_manager.t("core.sdk.init.starting")
        assert "initializing" in text.lower()

    def test_translation_format_args(self, i18n_manager):
        """测试格式化参数"""
        i18n_manager.set_language("zh-CN")
        text = i18n_manager.t(
            "core.adapter.create_failed", platform="OneBot", error="timeout"
        )
        assert "OneBot" in text
        assert "timeout" in text

    def test_translation_missing_key(self, i18n_manager):
        """测试缺失的翻译键"""
        i18n_manager.set_language("en")
        # 不存在的键应返回键本身
        assert i18n_manager.t("nonexistent.key") == "nonexistent.key"

    def test_translation_default_value(self, i18n_manager):
        """测试默认值"""
        i18n_manager.set_language("en")
        assert i18n_manager.t("nonexistent.key", default="Default") == "Default"

    def test_translation_fallback(self, i18n_manager):
        """测试翻译回退"""
        i18n_manager.set_language("ru")
        # 俄文有翻译
        text = i18n_manager.t("core.sdk.init.starting")
        assert text is not None
        assert text != "core.sdk.init.starting"

    def test_gettext_alias(self, i18n_manager):
        """测试gettext别名"""
        i18n_manager.set_language("zh-CN")
        assert i18n_manager.gettext("core.sdk.init.starting") == i18n_manager.t(
            "core.sdk.init.starting"
        )

    def test_has_translation(self, i18n_manager):
        """测试检查翻译是否存在"""
        i18n_manager.set_language("zh-CN")
        assert i18n_manager.has_translation("core.sdk.init.starting") is True
        assert i18n_manager.has_translation("nonexistent.key") is False

    def test_key_kwarg_not_conflict(self, i18n_manager):
        """测试key=作为格式化参数不与方法参数冲突"""
        i18n_manager.set_language("zh-CN")
        # core.config.set_failed 使用 {key} 占位符
        text = i18n_manager.t("core.config.set_failed", key="mykey", error="err")
        assert "mykey" in text
        assert "err" in text

    # ==================== 注册功能测试 ====================

    def test_register_translations(self, i18n_manager):
        """测试注册自定义翻译"""
        i18n_manager.register(
            "en", {"mybot.welcome": "Welcome to my bot!"}, domain="mybot"
        )
        i18n_manager.set_language("en")
        assert i18n_manager.t("mybot.welcome") == "Welcome to my bot!"

    def test_register_multiple_languages(self, i18n_manager):
        """测试注册多语言翻译"""
        i18n_manager.register("zh-CN", {"test.hello": "你好"}, domain="test")
        i18n_manager.register("en", {"test.hello": "Hello"}, domain="test")
        i18n_manager.register("ja", {"test.hello": "こんにちは"}, domain="test")

        i18n_manager.set_language("zh-CN")
        assert i18n_manager.t("test.hello") == "你好"

        i18n_manager.set_language("en")
        assert i18n_manager.t("test.hello") == "Hello"

        i18n_manager.set_language("ja")
        assert i18n_manager.t("test.hello") == "こんにちは"

    def test_unregister_domain(self, i18n_manager):
        """测试卸载翻译域"""
        i18n_manager.register("en", {"test.key": "Test"}, domain="testdomain")
        i18n_manager.set_language("en")
        assert i18n_manager.t("test.key") == "Test"

        i18n_manager.unregister_domain("testdomain")
        assert i18n_manager.t("test.key") == "test.key"

    def test_register_nearest_mapping(self, i18n_manager):
        """测试注册时使用就近映射"""
        i18n_manager.register("en-US", {"test.nearest": "US English"}, domain="test")
        i18n_manager.set_language("en")
        assert i18n_manager.t("test.nearest") == "US English"

    # ==================== 环境检测测试 ====================

    def test_detect_from_env_lang(self):
        """测试从环境变量检测语言"""
        with (
            patch.dict(os.environ, {"LANG": "ja_JP.UTF-8"}),
            patch.object(I18nManager, "_detect_windows_locale", return_value=None),
        ):
            manager = I18nManager()
            manager.reset_language()
            # 检测到的语言应该基于环境变量
            detected = manager._detect_language()
            assert detected == "ja"

    def test_detect_from_env_lc_all(self):
        """测试从LC_ALL检测语言"""
        with (
            patch.dict(os.environ, {"LC_ALL": "ru_RU.UTF-8", "LANG": ""}),
            patch.object(I18nManager, "_detect_windows_locale", return_value=None),
        ):
            manager = I18nManager()
            detected = manager._detect_language()
            assert detected == "ru"

    def test_detect_env_priority(self):
        """测试环境变量优先级"""
        # LANGUAGE > LC_ALL > LC_MESSAGES > LANG
        with (
            patch.dict(
                os.environ,
                {
                    "LANGUAGE": "ja_JP.UTF-8",
                    "LC_ALL": "ru_RU.UTF-8",
                    "LANG": "en_US.UTF-8",
                },
            ),
            patch.object(I18nManager, "_detect_windows_locale", return_value=None),
        ):
            manager = I18nManager()
            detected = manager._detect_language()
            assert detected == "ja"

    def test_detect_language_list(self):
        """测试LANGUAGE变量中的语言列表"""
        with (
            patch.dict(
                os.environ,
                {
                    "LANGUAGE": "fr_FR:en_US:de_DE",
                    "LANG": "",
                    "LC_ALL": "",
                    "LC_MESSAGES": "",
                },
            ),
            patch.object(I18nManager, "_detect_windows_locale", return_value=None),
        ):
            manager = I18nManager()
            detected = manager._detect_language()
            # fr_FR 不支持，应该回退
            # 但 LANGUAGE 第一个不是 fr -> 应该继续检测
            # 实际上 fr_FR 会回退到 zh-CN (默认)
            assert detected in ["zh-CN", "en"]

    def test_windows_api_priority_over_env(self):
        """测试 Windows API 优先级高于环境变量"""
        # Windows 上 LANG=en_US 但系统语言是中文
        with (
            patch.dict(
                os.environ, {"LANG": "en_US.UTF-8", "LANGUAGE": "", "LC_ALL": ""}
            ),
            patch.object(I18nManager, "_detect_windows_locale", return_value="zh-CN"),
        ):
            manager = I18nManager()
            detected = manager._detect_language()
            assert detected == "zh-CN"

    def test_windows_locale_name_resolution(self):
        """测试 Windows locale 全称映射"""
        assert (
            I18nManager._resolve_windows_locale_name("Chinese (Simplified)_China")
            == "zh-CN"
        )
        assert I18nManager._resolve_windows_locale_name("Chinese (Taiwan)") == "zh-TW"
        assert (
            I18nManager._resolve_windows_locale_name("English (United States)") == "en"
        )
        assert I18nManager._resolve_windows_locale_name("Japanese (Japan)") == "ja"
        assert I18nManager._resolve_windows_locale_name("Russian (Russia)") == "ru"
        assert I18nManager._resolve_windows_locale_name("Unknown") is None


# ==================== 全局实例测试 ====================


class TestGlobalI18n:
    """全局i18n实例测试"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        from ErisPulse.Core.i18n import i18n

        assert i18n is not None
        assert isinstance(i18n, I18nManager)

    def test_global_translation(self):
        """测试全局实例翻译"""
        from ErisPulse.Core.i18n import i18n

        i18n.set_language("zh-CN")
        text = i18n.t("core.sdk.init.starting")
        assert text == "SDK 正在初始化..."

    def test_sdk_i18n_attribute(self):
        """测试sdk.i18n属性"""
        from ErisPulse import sdk
        from ErisPulse.Core.i18n import i18n as global_i18n

        assert sdk.i18n is global_i18n

    def test_all_languages_have_same_keys(self):
        """测试所有语言拥有相同的键集合"""
        from ErisPulse.Core.i18n.locales import get_translations

        langs = ["zh-CN", "zh-TW", "en", "ja", "ru"]
        all_keys = {}
        for lang in langs:
            data = get_translations(lang)
            all_keys[lang] = set(data.keys())

        ref = all_keys["zh-CN"]
        for lang in langs[1:]:
            assert all_keys[lang] == ref, f"{lang} has different keys than zh-CN"
