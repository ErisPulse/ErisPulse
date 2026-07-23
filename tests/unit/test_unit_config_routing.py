"""
配置热更新路由单元测试

验证框架核心将 config.set / config.updated 事件路由到模块/适配器的 on_config_update：
- config.set 触发后调用 on_config_update
- config.updated 配置变化时触发 on_config_update
- 配置无变化时不触发
- 未实现 on_config_update 的组件不报错
"""

from dataclasses import dataclass, field

from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.lifecycle import lifecycle
from ErisPulse.runtime.config_schema import BaseConfig


@dataclass
class _TestCfg(BaseConfig):
    msg: str = field(default="hello", metadata={"description": "msg"})
    flag: bool = field(default=True, metadata={"description": "flag"})


def _make_module_class(name, received):
    class _Mod(BaseModule):
        ConfigClass = _TestCfg

        async def on_load(self, event):
            pass

        async def on_unload(self, event):
            pass

        def on_config_update(self, old_config, new_config):
            received.append((old_config, new_config))

    _Mod.__name__ = name
    return _Mod


class TestConfigSetRouting:
    """config.set 事件路由"""

    def test_config_set_triggers_on_config_update(self):
        """setConfig 触发 config.set → 调用模块 on_config_update"""
        from ErisPulse.Core.module import ModuleManager

        received = []
        mgr = ModuleManager()
        ModCls = _make_module_class("RoutingTestMod1", received)

        # 注册并手动放入已加载状态（绕过完整 load 流程）
        mgr._module_classes["RoutingTestMod1"] = ModCls
        instance = object.__new__(ModCls)
        instance._module_name = "RoutingTestMod1"
        instance.ConfigClass = _TestCfg
        mgr._modules["RoutingTestMod1"] = instance
        mgr._loaded_modules.add("RoutingTestMod1")

        try:
            # 模拟 config.set 事件（key 匹配模块配置键）
            lifecycle.emit_sync(
                "config.set",
                {
                    "key": "RoutingTestMod1.msg",
                    "old_value": "hello",
                    "new_value": "world",
                },
            )
            # 核心路由应调用一次 on_config_update（具体配置值取决于 getConfig，测试环境无配置文件）
            assert len(received) == 1
        finally:
            mgr._loaded_modules.discard("RoutingTestMod1")
            mgr._modules.pop("RoutingTestMod1", None)

    def test_config_set_non_matching_key_ignored(self):
        """config.set 的 key 不匹配任何模块时不触发"""
        from ErisPulse.Core.module import ModuleManager

        received = []
        mgr = ModuleManager()
        ModCls = _make_module_class("RoutingTestMod2", received)

        instance = object.__new__(ModCls)
        instance._module_name = "RoutingTestMod2"
        instance.ConfigClass = _TestCfg
        mgr._modules["RoutingTestMod2"] = instance
        mgr._loaded_modules.add("RoutingTestMod2")

        try:
            lifecycle.emit_sync(
                "config.set",
                {
                    "key": "SomeOtherModule.field",
                    "old_value": None,
                    "new_value": "x",
                },
            )
            assert len(received) == 0
        finally:
            mgr._loaded_modules.discard("RoutingTestMod2")
            mgr._modules.pop("RoutingTestMod2", None)


class TestConfigUpdatedRouting:
    """config.updated 事件路由"""

    def test_config_updated_triggers_on_change(self):
        """config.updated 配置块变化时触发"""
        from ErisPulse.Core.module import ModuleManager

        received = []
        mgr = ModuleManager()
        ModCls = _make_module_class("RoutingTestMod3", received)

        instance = object.__new__(ModCls)
        instance._module_name = "RoutingTestMod3"
        instance.ConfigClass = _TestCfg
        mgr._modules["RoutingTestMod3"] = instance
        mgr._loaded_modules.add("RoutingTestMod3")

        try:
            lifecycle.emit_sync(
                "config.updated",
                {
                    "old_config": {"RoutingTestMod3": {"msg": "old", "flag": True}},
                    "new_config": {"RoutingTestMod3": {"msg": "new", "flag": True}},
                    "config_file": "config/config.toml",
                },
            )
            assert len(received) == 1
        finally:
            mgr._loaded_modules.discard("RoutingTestMod3")
            mgr._modules.pop("RoutingTestMod3", None)

    def test_config_updated_no_change_skipped(self):
        """config.updated 配置块无变化时不触发"""
        from ErisPulse.Core.module import ModuleManager

        received = []
        mgr = ModuleManager()
        ModCls = _make_module_class("RoutingTestMod4", received)

        instance = object.__new__(ModCls)
        instance._module_name = "RoutingTestMod4"
        instance.ConfigClass = _TestCfg
        mgr._modules["RoutingTestMod4"] = instance
        mgr._loaded_modules.add("RoutingTestMod4")

        try:
            lifecycle.emit_sync(
                "config.updated",
                {
                    "old_config": {"RoutingTestMod4": {"msg": "same", "flag": True}},
                    "new_config": {"RoutingTestMod4": {"msg": "same", "flag": True}},
                    "config_file": "config/config.toml",
                },
            )
            assert len(received) == 0
        finally:
            mgr._loaded_modules.discard("RoutingTestMod4")
            mgr._modules.pop("RoutingTestMod4", None)


class TestNoOnConfigUpdate:
    """未实现 on_config_update 的组件"""

    def test_module_without_on_config_update_no_error(self):
        """未实现 on_config_update 的模块不报错（hasattr 检查）"""
        from ErisPulse.Core.module import ModuleManager

        class _PlainMod(BaseModule):
            async def on_load(self, event):
                pass

            async def on_unload(self, event):
                pass

        mgr = ModuleManager()
        instance = object.__new__(_PlainMod)
        instance._module_name = "PlainRoutingMod"
        mgr._modules["PlainRoutingMod"] = instance
        mgr._loaded_modules.add("PlainRoutingMod")

        try:
            # 不应抛异常
            lifecycle.emit_sync(
                "config.updated",
                {
                    "old_config": {"PlainRoutingMod": {"a": 1}},
                    "new_config": {"PlainRoutingMod": {"a": 2}},
                    "config_file": "config/config.toml",
                },
            )
        finally:
            mgr._loaded_modules.discard("PlainRoutingMod")
            mgr._modules.pop("PlainRoutingMod", None)
