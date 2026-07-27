"""
i18n 键声明 Schema 单元测试

测试 I18nKey / BaseI18n 的基本功能、register() 行为，
以及 BaseModule / BaseAdapter 的 _ensure_i18n_registered() 集成。
"""

import pytest

from ErisPulse.Core.Bases import BaseI18n, I18nKey, key
from ErisPulse.Core.i18n import i18n

# ==================== I18nKey 单元测试 ===========================


class TestI18nKey:
    """I18nKey 构造与字段测试"""

    def test_default_required(self):
        """default 是必填项，缺失或为空应抛 ValueError"""
        with pytest.raises(ValueError):
            I18nKey("")
        with pytest.raises(TypeError):
            I18nKey()  # type: ignore[call-arg]

    def test_default_not_registered_to_any_language(self):
        """default 是语言无关的兜底文本，不应被注册到任何语言"""
        k = I18nKey(default="你好")
        assert k.default == "你好"
        assert k.translations == {}  # 没有任何语言翻译

    def test_explicit_language_translations(self):
        """显式传入的语言参数才被注册到 translations"""
        k = I18nKey(default="fallback", zh_CN="正式中文", en="English")
        assert k.default == "fallback"  # default 与翻译独立
        assert k.translations == {"zh-CN": "正式中文", "en": "English"}

    def test_optional_languages(self):
        """可选语言（en/ja/ru/zh_TW/zh_CN）按需加入 translations"""
        k = I18nKey(
            default="hi",
            en="Hello",
            ja="こんにちは",
            ru="Привет",
            zh_TW="妳好",
            zh_CN="你好",
        )
        assert k.translations == {
            "zh-CN": "你好",
            "en": "Hello",
            "ja": "こんにちは",
            "ru": "Привет",
            "zh-TW": "妳好",
        }
        assert k.default == "hi"  # default 不在 translations 中

    def test_explicit_key(self):
        """explicit_key 应正确返回显式指定的 key 路径"""
        k = I18nKey(default="x", key="my.deep.path")
        assert k.explicit_key == "my.deep.path"

    def test_no_explicit_key(self):
        """未指定 key 时 explicit_key 返回 None"""
        k = I18nKey(default="x")
        assert k.explicit_key is None

    def test_repr_contains_essentials(self):
        """__repr__ 应包含 default 和语言列表"""
        k = I18nKey(default="hi", en="Hello")
        r = repr(k)
        assert "hi" in r
        assert "en" in r

    def test_key_alias(self):
        """模块级别名 key 等价于 I18nKey"""
        assert key is I18nKey
        k = key(default="x")
        assert isinstance(k, I18nKey)


class TestImportPaths:
    """验证两种导入路径都能访问同一组类"""

    def test_bases_and_runtime_export_same_classes(self):
        """``Core.Bases`` 与 ``runtime`` 应导出同一个类对象"""
        from ErisPulse.Core.Bases import (
            BaseConfig as BasesBaseConfig,
            BotAccountConfig as BasesBotAccountConfig,
            BaseI18n as BasesBaseI18n,
            I18nKey as BasesI18nKey,
        )
        from ErisPulse.runtime import (
            BaseConfig as RtBaseConfig,
            BotAccountConfig as RtBotAccountConfig,
        )
        from ErisPulse.runtime.config_schema import BaseConfig as RtCsBaseConfig

        # config_schema 的符号通过 runtime 懒加载重新导出（同一对象）
        assert BasesBaseConfig is RtBaseConfig is RtCsBaseConfig
        assert BasesBotAccountConfig is RtBotAccountConfig

        # i18n_schema 的符号仅从 Core.Bases 导出（runtime 不再提供）
        assert BasesBaseI18n.__name__ == "BaseI18n"
        assert BasesI18nKey.__name__ == "I18nKey"

    def test_runtime_does_not_export_i18n_schema(self):
        """runtime 不应再导出 BaseI18n / I18nKey（已迁移到 Core.Bases）"""
        import ErisPulse.runtime as rt

        assert not hasattr(rt, "BaseI18n"), "BaseI18n 不应从 runtime 导出"
        assert not hasattr(rt, "I18nKey"), "I18nKey 不应从 runtime 导出"
        assert "BaseI18n" not in rt.__all__
        assert "I18nKey" not in rt.__all__

    def test_bases_all_includes_schema_types(self):
        """``Core.Bases.__all__`` 应包含新导出的 Schema 类型"""
        from ErisPulse.Core import Bases

        for name in (
            "BaseConfig",
            "BotAccountConfig",
            "BaseI18n",
            "I18nKey",
            "AdapterConfig",
        ):
            assert name in Bases.__all__, f"{name} 未在 Bases.__all__ 中声明"
            assert hasattr(Bases, name), f"{name} 未在 Bases 模块中导出"


# ==================== BaseI18n 集合测试 ====================


class TestBaseI18nCollection:
    """BaseI18n 类的 _collect_keys 与 register 行为"""

    def test_collect_keys_basic(self):
        """_collect_keys 应收集所有 I18nKey 类属性"""

        class MyKeys(BaseI18n):
            hello: I18nKey = I18nKey(default="你好", en="Hello")
            bye: I18nKey = I18nKey(default="再见", en="Bye")

        keys = MyKeys._collect_keys()
        assert set(keys.keys()) == {"hello", "bye"}
        assert keys["hello"].default == "你好"
        assert keys["bye"].default == "再见"

    def test_collect_keys_ignores_underscore(self):
        """下划线开头的属性应被忽略"""

        class MyKeys(BaseI18n):
            public: I18nKey = I18nKey(default="公开")
            _private: I18nKey = I18nKey(default="私密")

        keys = MyKeys._collect_keys()
        assert "public" in keys
        assert "_private" not in keys

    def test_collect_keys_ignores_non_i18nkey(self):
        """非 I18nKey 类型的属性应被忽略"""

        class MyKeys(BaseI18n):
            valid: I18nKey = I18nKey(default="ok")
            not_key: str = "just a string"
            number: int = 42

        keys = MyKeys._collect_keys()
        assert set(keys.keys()) == {"valid"}

    def test_collect_keys_inheritance(self):
        """子类应继承父类的键，且同名覆盖"""

        class Parent(BaseI18n):
            a: I18nKey = I18nKey(default="A")
            b: I18nKey = I18nKey(default="B-parent")

        class Child(Parent):
            b: I18nKey = I18nKey(default="B-child")
            c: I18nKey = I18nKey(default="C")

        keys = Child._collect_keys()
        assert set(keys.keys()) == {"a", "b", "c"}
        assert keys["a"].default == "A"
        assert keys["b"].default == "B-child"  # 子类覆盖
        assert keys["c"].default == "C"

    def test_register_with_prefix(self):
        """register() 应使用 prefix + 属性名作为键路径"""
        # 使用唯一 domain 防止与其他测试互相干扰
        domain = f"test_register_prefix_{id(self)}"

        class MyKeys(BaseI18n):
            hello: I18nKey = I18nKey(default="你好", zh_CN="你好", en="Hello")

        try:
            count = MyKeys.register(prefix="mymod.", domain=domain)
            # zh-CN + en = 2 条（default 不注册）
            assert count == 2

            # 直接检查 translations 字典（避免修改全局语言状态）
            assert i18n._translations.get("zh-CN", {}).get("mymod.hello") == "你好"
            assert i18n._translations.get("en", {}).get("mymod.hello") == "Hello"
        finally:
            i18n.unregister_domain(domain)

    def test_register_with_explicit_key(self):
        """显式 key 参数应覆盖 prefix+属性名"""
        domain = f"test_register_explicit_{id(self)}"

        class MyKeys(BaseI18n):
            attr_name: I18nKey = I18nKey(
                default="hi",
                en="hello",
                key="custom.full.path",
            )

        try:
            MyKeys.register(prefix="ignored.", domain=domain)
            # 显式键被注册
            assert i18n._translations.get("en", {}).get("custom.full.path") == "hello"
            # prefix+属性名 不应被注册
            assert "ignored.attr_name" not in i18n._translations.get("en", {})
        finally:
            i18n.unregister_domain(domain)

    def test_register_mixed_keys(self):
        """混合使用显式 key 和自动 key"""
        domain = f"test_register_mixed_{id(self)}"

        class MyKeys(BaseI18n):
            auto: I18nKey = I18nKey(default="auto-zh", en="auto-en")
            manual: I18nKey = I18nKey(
                default="manual-zh",
                en="manual-en",
                key="manual.explicit",
            )

        try:
            MyKeys.register(prefix="mymod.", domain=domain)
            assert i18n._translations.get("en", {}).get("mymod.auto") == "auto-en"
            assert i18n._translations.get("en", {}).get("manual.explicit") == "manual-en"
        finally:
            i18n.unregister_domain(domain)

    def test_register_idempotent(self):
        """重复调用 register() 不应报错，覆盖旧值"""
        domain = f"test_register_idem_{id(self)}"

        class MyKeys(BaseI18n):
            k: I18nKey = I18nKey(default="v1", zh_CN="v1")

        try:
            MyKeys.register(prefix="mymod.", domain=domain)
            # 第二次注册相同内容
            MyKeys.register(prefix="mymod.", domain=domain)
            assert i18n._translations.get("zh-CN", {}).get("mymod.k") == "v1"
        finally:
            i18n.unregister_domain(domain)

    def test_register_returns_count(self):
        """register() 返回注册的条目总数（语言 × 键）"""
        domain = f"test_register_count_{id(self)}"

        class MyKeys(BaseI18n):
            a: I18nKey = I18nKey(default="a", en="A", ja="あ")
            b: I18nKey = I18nKey(default="b", zh_CN="b")  # 仅 zh-CN

        try:
            # a: 2 条 (en, ja), b: 1 条 (zh-CN) —— default 不注册
            count = MyKeys.register(prefix="mymod.", domain=domain)
            assert count == 3
        finally:
            i18n.unregister_domain(domain)


# ==================== BaseModule 集成测试 ====================


class TestBaseModuleI18nIntegration:
    """BaseModule._ensure_i18n_registered() 集成"""

    def test_module_registers_i18nclass_keys(self):
        """声明 I18nClass 的模块应自动注册翻译键"""
        from ErisPulse.Core.Bases import BaseModule

        domain = "TestModForI18n"

        class TestModForI18n(BaseModule):
            class I18nClass(BaseI18n):
                welcome: I18nKey = I18nKey(
                    default="Welcome",
                    zh_CN="欢迎",
                    en="Welcome",
                )

            async def on_load(self, event):
                return True

            async def on_unload(self, event):
                return True

        instance = TestModForI18n()
        instance._module_name = domain  # 模拟 ModuleManager 注入

        try:
            instance._ensure_i18n_registered()
            assert i18n._translations.get("en", {}).get(f"{domain}.welcome") == "Welcome"
            assert i18n._translations.get("zh-CN", {}).get(f"{domain}.welcome") == "欢迎"
        finally:
            i18n.unregister_domain(domain)

    def test_module_without_i18nclass_noop(self):
        """未声明 I18nClass 的模块调用 _ensure_i18n_registered 不应报错"""
        from ErisPulse.Core.Bases import BaseModule

        class NoI18nModule(BaseModule):
            async def on_load(self, event):
                return True

            async def on_unload(self, event):
                return True

        instance = NoI18nModule()
        instance._module_name = "NoI18n"
        # 不应抛出异常
        instance._ensure_i18n_registered()

    def test_module_with_invalid_i18nclass_silent(self):
        """I18nClass 非 BaseI18n 子类时应静默跳过"""
        from ErisPulse.Core.Bases import BaseModule

        class InvalidModule(BaseModule):
            I18nClass = "not a class"  # 故意错误

            async def on_load(self, event):
                return True

            async def on_unload(self, event):
                return True

        instance = InvalidModule()
        instance._module_name = "Invalid"
        # 不应抛出异常
        instance._ensure_i18n_registered()

    def test_module_i18n_registered_before_config(self):
        """_ensure_config_exists 应先调用 i18n 注册"""
        # 这个测试验证：配置生成时引用的 i18n 键已经注册
        from dataclasses import dataclass
        from dataclasses import field as dc_field

        from ErisPulse.Core.Bases import BaseModule

        domain = "CfgI18nMod"

        @dataclass
        class CfgI18nConfig:
            endpoint: str = dc_field(
                default="",
                metadata={
                    "description": {"i18n": f"{domain}.endpoint", "default": "API"},
                },
            )

        class CfgI18nMod(BaseModule):
            ConfigClass = CfgI18nConfig

            class I18nClass(BaseI18n):
                endpoint: I18nKey = I18nKey(
                    default="API",
                    en="API Endpoint",
                )

            async def on_load(self, event):
                return True

            async def on_unload(self, event):
                return True

        instance = CfgI18nMod()
        instance._module_name = domain

        try:
            # 直接调用 _ensure_config_exists，应先注册 i18n 键
            instance._ensure_config_exists()
            assert i18n._translations.get("en", {}).get(f"{domain}.endpoint") == "API Endpoint"
        finally:
            i18n.unregister_domain(domain)


# ==================== BaseAdapter 集成测试 ====================


class TestBaseAdapterI18nIntegration:
    """BaseAdapter._ensure_i18n_registered() 集成"""

    def test_adapter_registers_i18nclass_keys(self):
        """声明 I18nClass 的适配器应自动注册翻译键"""
        from ErisPulse.Core.Bases import BaseAdapter

        class TestAdpForI18n(BaseAdapter):
            class I18nClass(BaseI18n):
                endpoint: I18nKey = I18nKey(
                    default="API",
                    en="API Endpoint",
                )

            async def call_api(self, endpoint, **params):
                return {}

            async def start(self):
                pass

            async def shutdown(self):
                pass

        # 适配器在 __init__ 时会自动调用 _ensure_i18n_registered
        TestAdpForI18n()
        domain = "TestAdpForI18n"  # 默认用类名作为 domain

        try:
            assert i18n._translations.get("en", {}).get(f"{domain}.endpoint") == "API Endpoint"
        finally:
            i18n.unregister_domain(domain)

    def test_adapter_without_i18nclass_init_ok(self):
        """未声明 I18nClass 的适配器 __init__ 应正常"""
        from ErisPulse.Core.Bases import BaseAdapter

        class NoI18nAdapter(BaseAdapter):
            async def call_api(self, endpoint, **params):
                return {}

            async def start(self):
                pass

            async def shutdown(self):
                pass

        # 不应抛出异常
        adapter = NoI18nAdapter()
        assert adapter is not None
