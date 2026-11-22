"""
解耦插槽接线测试（P0 环治理批次）

覆盖经插槽反向注入的公共 API：
- di.set_module_caller：``Depends.module`` 的模块调用器注入 / 卸载 / 未注册报错
- i18n.set_language_source：语言来源回调插槽
- i18n.set_event_emitter：语言变更事件发射插槽
- i18n.on_language_config_changed：模块级配置失效广播（含非单例实例）
"""

import asyncio

import pytest

from ErisPulse.Core import di
from ErisPulse.Core.constants import EVENT_I18N_LANGUAGE_CHANGED
from ErisPulse.Core.di import Depends, set_module_caller
from ErisPulse.Core.i18n import (
    I18nManager,
    i18n,
    on_language_config_changed,
    set_event_emitter,
    set_language_source,
)


class TestModuleCallerSlot:
    @pytest.fixture(autouse=True)
    def _restore_caller(self):
        original = di._module_caller
        yield
        set_module_caller(original)

    def test_depends_module_resolves_through_slot(self):
        calls = []

        def fake_caller(module_name, method, args, kwargs):
            calls.append((module_name, method, args, kwargs))
            return "svc-result"

        set_module_caller(fake_caller)
        dep = Depends.module("DB", "get_session", 1, key="x")
        assert asyncio.run(dep.dependency(object())) == "svc-result"
        assert calls == [("DB", "get_session", (1,), {"key": "x"})]

    def test_depends_module_awaits_caller_result(self):
        async def async_caller(module_name, method, args, kwargs):
            return f"awaited-{method}"

        set_module_caller(async_caller)
        dep = Depends.module("m", "run")
        assert asyncio.run(dep.dependency(None)) == "awaited-run"

    def test_depends_module_without_caller_raises(self):
        set_module_caller(None)
        dep = Depends.module("m", "run")
        with pytest.raises(RuntimeError, match="module caller"):
            asyncio.run(dep.dependency(None))


class TestLanguageSourceSlot:
    @pytest.fixture(autouse=True)
    def _restore_source(self):
        original = i18n._language_source
        yield
        set_language_source(original)

    def test_set_and_unset_language_source(self):
        seen = []

        def provider():
            seen.append(1)
            return "en"

        set_language_source(provider)
        assert i18n._language_source is not None
        assert i18n._language_source() == "en"
        set_language_source(None)
        assert i18n._language_source is None
        assert seen == [1]


class TestEventEmitterSlot:
    @pytest.fixture(autouse=True)
    def _restore_emitter(self):
        original = i18n._event_emitter
        yield
        i18n.set_event_emitter(original)

    def test_module_level_set_event_emitter_forwards(self):
        captured = []

        def emitter(event, payload):
            captured.append((event, payload))

        set_event_emitter(emitter)
        assert i18n._event_emitter is emitter
        i18n._emit_language_changed("en", "zh-CN")
        assert captured == [(EVENT_I18N_LANGUAGE_CHANGED, {"language": "en", "previous": "zh-CN"})]

    def test_emit_with_no_emitter_is_noop(self):
        set_event_emitter(None)
        i18n._emit_language_changed("en", None)  # 不应抛错


class TestLanguageConfigBroadcast:
    def test_broadcast_clears_effective_language_cache(self):
        manager = I18nManager()
        manager._eff_lang_cache = "en"
        on_language_config_changed({"key": "ErisPulse.i18n.language"})
        assert manager._eff_lang_cache is None

    def test_broadcast_ignores_unrelated_keys(self):
        manager = I18nManager()
        manager._eff_lang_cache = "en"
        on_language_config_changed({"key": "other.section.key"})
        assert manager._eff_lang_cache == "en"

    def test_broadcast_covers_all_active_managers(self):
        """广播遍历活跃实例表：非单例实例也被失效"""
        m1, m2 = I18nManager(), I18nManager()
        m1._eff_lang_cache = "en"
        m2._eff_lang_cache = "ja"
        on_language_config_changed({"key": "ErisPulse.i18n.language"})
        assert m1._eff_lang_cache is None
        assert m2._eff_lang_cache is None
