"""
管理器 SDK 引用懒解析回归测试

防护 2.5~2.10.2 期间的休眠缺陷：set_sdk_ref 调用方被移除后 _sdk 恒为 None，
导致模块热重载、影子模块、依赖通知、SDK 属性清理静默失效。
"""

import asyncio

import pytest

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.module import ModuleManager


class TestSdkRefLazyResolution:
    """未注入时懒解析根单例，显式注入优先"""

    def test_bare_managers_resolve_root_sdk(self):
        from ErisPulse import sdk as root_sdk

        assert ModuleManager().sdk_ref() is root_sdk
        assert AdapterManager().sdk_ref() is root_sdk

    def test_explicit_injection_takes_priority(self):
        from ErisPulse.Core.module import ModuleManager

        class FakeSDK:
            pass

        mgr = ModuleManager()
        fake = FakeSDK()
        assert mgr.set_sdk_ref(fake) is True
        assert mgr.sdk_ref() is fake

    def test_reload_without_init_returns_false_gracefully(self):
        """SDK 未初始化（无 loader）时 reload 优雅返回 False，而非静默 None 异常"""
        assert asyncio.run(ModuleManager().reload("Weather")) is False

    def test_reload_all_without_init_returns_empty(self):
        assert asyncio.run(ModuleManager().reload_all()) == {}
