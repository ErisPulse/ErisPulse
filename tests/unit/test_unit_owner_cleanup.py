"""
归属权（owner）兜底清理单元测试

覆盖：路由首页入口 / 中间件、适配器事件处理器与中间件、自定义会话类型、
运行时事件覆写（persist=False）的 owner 归属记录与卸载清理。
"""

import asyncio

import pytest

from ErisPulse.Core.adapter import AdapterManager
from ErisPulse.Core.Event import overrides, session_type
from ErisPulse.Core.Event.wrapper import register_event_mixin, unregister_platform_event_methods
from ErisPulse.Core.router import RouterManager
from ErisPulse.runtime.context import owner_scope


@pytest.mark.unit
class TestRouterHomeEntryOwner:
    """首页入口按钮的 owner 归属与清理"""

    def test_register_records_owner(self):
        manager = RouterManager()
        with owner_scope("MyModule"):
            manager.register_home_entry(name="入口", url="/my")
        assert manager._home_entries[0]["owner"] == "MyModule"
        # 无 owner 上下文时记录为 None（框架级资源，不被模块清理误删）
        manager.register_home_entry(name="框架", url="/core")
        assert manager._home_entries[-1]["owner"] is None

    def test_unregister_by_owner(self):
        manager = RouterManager()
        with owner_scope("A"):
            manager.register_home_entry(name="A入口", url="/a")
        with owner_scope("B"):
            manager.register_home_entry(name="B入口", url="/b")
        manager.register_home_entry(name="框架入口", url="/core")

        removed = manager.unregister_home_entries_by_owner("A")
        assert removed == 1
        urls = [e["url"] for e in manager._home_entries]
        assert "/a" not in urls
        assert "/b" in urls and "/core" in urls


@pytest.mark.unit
class TestRouterMiddlewareOwner:
    """路由中间件的 owner 归属与兜底清理"""

    def test_middleware_cleanup_by_owner(self):
        manager = RouterManager()

        with owner_scope("MyModule"):
            @manager.middleware("/MyModule/*")
            async def mw_module(request):
                return request

            @manager.middleware()
            async def mw_global(request):
                return request

        with owner_scope("Other"):
            @manager.middleware()
            async def mw_other(request):
                return request

        # 注册后：路径中间件 1 个、全局中间件 2 个（MyModule + Other）
        assert len(manager._route_middlewares.get("/MyModule/*", [])) == 1
        assert len(manager._global_middlewares) == 2

        result = manager.unregister_all_by_owner("MyModule")
        assert result["middleware_count"] == 2
        # 该 owner 的中间件已移除：路径中间件清空（空键回收）、全局仅剩 Other
        assert len(manager._route_middlewares.get("/MyModule/*", [])) == 0
        assert len(manager._global_middlewares) == 1
        # 归属记录同步清除
        assert all(r["owner"] != "MyModule" for r in manager._middleware_records)
        assert any(r["owner"] == "Other" for r in manager._middleware_records)


@pytest.mark.unit
class TestAdapterHandlerOwner:
    """适配器事件处理器 / 中间件的 owner 归属与清理"""

    def test_on_handlers_removed_by_owner(self):
        manager = AdapterManager()

        with owner_scope("MyModule"):
            @manager.on("message")
            async def handler_module(data):
                return data

        with owner_scope("Other"):
            @manager.on("message")
            async def handler_other(data):
                return data

        removed = manager.unregister_handlers_by_owner("MyModule")
        assert removed == 1
        owners = [h.get("owner") for h in manager._onebot_handlers.get("message", [])]
        assert "MyModule" not in owners
        assert "Other" in owners

    def test_middleware_removed_by_owner(self):
        manager = AdapterManager()

        with owner_scope("MyModule"):
            @manager.middleware
            async def middleware_module(data):
                return data

        assert id(middleware_module) in manager._onebot_middleware_owners
        removed = manager.unregister_handlers_by_owner("MyModule")
        assert removed == 1
        assert middleware_module not in manager._onebot_middlewares
        assert id(middleware_module) not in manager._onebot_middleware_owners

    def test_platform_handlers_cleaned_via_adapter_cleanup(self):
        """适配器资源清理时移除以平台名为 owner 自有的处理器"""
        manager = AdapterManager()

        async def run():
            with owner_scope("MyPlatform"):
                @manager.on("notice")
                async def handler_platform(data):
                    return data

            await manager._cleanup_adapter_resources("MyPlatform")

        asyncio.run(run())
        assert manager._onebot_handlers.get("notice") is None


@pytest.mark.unit
class TestSessionTypeOwner:
    """自定义会话类型的 owner 归属与清理"""

    def setup_method(self):
        session_type._custom_type_to_id_field.clear()
        session_type._custom_id_field_to_type.clear()
        session_type._custom_receive_to_send.clear()
        session_type._custom_send_to_receive.clear()
        session_type._custom_type_owners.clear()

    def teardown_method(self):
        self.setup_method()

    def test_register_records_owner_and_cleanup(self):
        with owner_scope("MyAdapter"):
            assert session_type.register_custom_type("poke", "user", "poke_id") is True
        # 无 owner 上下文注册的类型不记录归属
        assert session_type.register_custom_type("shared", "user", "shared_id") is True

        removed = session_type.unregister_custom_types_by_owner("MyAdapter")
        assert removed == 1
        assert "poke" not in session_type._custom_type_to_id_field
        assert "shared" in session_type._custom_type_to_id_field
        assert "poke" not in session_type._custom_type_owners

    def test_unregister_custom_type_clears_owner_record(self):
        with owner_scope("MyAdapter"):
            session_type.register_custom_type("poke", "user", "poke_id")
        assert session_type.unregister_custom_type("poke") is True
        assert "poke" not in session_type._custom_type_owners
        # 重复按 owner 清理不再计数
        assert session_type.unregister_custom_types_by_owner("MyAdapter") == 0

    def test_clear_custom_types_clears_owner_records(self):
        with owner_scope("MyAdapter"):
            session_type.register_custom_type("poke", "user", "poke_id")
        session_type.clear_custom_types()
        assert session_type._custom_type_owners == {}


@pytest.mark.unit
class TestPlatformEventMethodCleanup:
    """平台事件方法扩展（EventMixin）的清理"""

    def test_unregister_platform_event_methods(self):
        class FakeMixin:
            def get_subject(self):
                return ""

            def get_from(self):
                return ""

        register_event_mixin("MyPlatform", FakeMixin)
        methods = unregister_platform_event_methods("MyPlatform")
        assert methods == 2
        from ErisPulse.Core.Event.wrapper import get_platform_event_methods

        assert get_platform_event_methods("MyPlatform") == []


@pytest.mark.unit
class TestRuntimeOverridesOwner:
    """运行时事件覆写（persist=False）的 owner 归属与清理"""

    def setup_method(self):
        overrides.clear()

    def teardown_method(self):
        overrides.clear()

    def test_runtime_write_cleaned_by_owner(self):
        with owner_scope("MyModule"):
            overrides.message.set("Target", persist=False, pattern="签到*")
            overrides.command.set("Target", "roll", persist=False, master=True)
            overrides.acl.set("roll*", persist=False, deny=["onebot11:u_bad"])

        removed = overrides.unregister_by_owner("MyModule")
        assert removed == 3
        assert overrides.message.get("Target") is None
        assert overrides.command.get("Target", "roll") == {}
        assert overrides.acl.get("roll*") == {"allow": [], "deny": []}

    def test_persistent_write_not_cleaned(self):
        """persist=True 属用户配置语义，不被 owner 清理"""
        with owner_scope("MyModule"):
            overrides.message.set("Target", persist=True, pattern="签到*")

        assert overrides.unregister_by_owner("MyModule") == 0
        assert overrides.message.get("Target") == {"pattern": "签到*"}
        overrides.message.delete("Target")

    def test_persist_upgrade_removes_runtime_record(self):
        """persist=True 覆盖运行时写入后，卸载不再清理该路径"""
        with owner_scope("MyModule"):
            overrides.message.set("Target", persist=False, pattern="a*")
            overrides.message.set("Target", persist=True, pattern="b*")

        assert overrides.unregister_by_owner("MyModule") == 0
        assert overrides.message.get("Target") == {"pattern": "b*"}
        overrides.message.delete("Target")
