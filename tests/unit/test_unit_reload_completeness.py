"""
模块重载完备性（方向 10）单元测试

覆盖：平台事件方法注入的 owner 回收（含 "*" 通配）、路由注销的
(namespace, path) 精确性（跨命名空间 / HTTP 与 SSE 同 path 互不误删）、
on_load 失败半卸载（失败后无残留资源、可立即重新加载）、reload 快照
回滚（失败后注册表 / sdk 属性 / sys.modules 恢复、旧实例继续服务），
以及归属权统一门面（ownership）的基础行为。
"""

import sys
import types

import pytest

from ErisPulse.Core.Event.wrapper import (
    _platform_event_methods,
    get_platform_event_methods,
    register_event_method,
    unregister_event_methods_by_owner,
    unregister_platform_event_methods,
)
from ErisPulse.runtime.context import owner_scope


# ==================== A1：事件方法 owner 回收 ====================


class TestEventMethodOwnerReclaim:
    def test_reclaim_removes_owned_methods(self):
        with owner_scope("m_audit"):
            @register_event_method("auditplat")
            def get_thing(self):
                return 1

        assert "get_thing" in get_platform_event_methods("auditplat")
        assert unregister_event_methods_by_owner("m_audit") == 1
        assert "get_thing" not in get_platform_event_methods("auditplat")
        # 幂等：重复注销返回 0
        assert unregister_event_methods_by_owner("m_audit") == 0

    def test_reclaim_covers_wildcard_platform(self):
        with owner_scope("m_audit_star"):
            @register_event_method("*")
            def get_star_thing(self):
                return 2

        assert "get_star_thing" in get_platform_event_methods("*")
        assert unregister_event_methods_by_owner("m_audit_star") == 1
        assert "get_star_thing" not in get_platform_event_methods("*")

    def test_unowned_registration_not_tracked(self):
        @register_event_method("auditplat_free")
        def get_free_thing(self):
            return 3

        try:
            # 无 owner 上下文的注册（适配器级）不由 owner 清理负责
            assert unregister_event_methods_by_owner("m_nobody") == 0
            assert "get_free_thing" in get_platform_event_methods("auditplat_free")
        finally:
            unregister_platform_event_methods("auditplat_free")


# ==================== A3：路由注销精确性 ====================


class TestRouteUnregisterPrecision:
    @pytest.fixture
    def router_manager(self):
        from ErisPulse.Core.router import RouterManager

        rm = RouterManager()
        _ = rm.app  # 触发 web 栈加载
        return rm

    def test_cross_namespace_same_path_not_deleted(self, router_manager):
        rm = router_manager

        async def h_a(event):
            return 1

        async def h_b(event):
            return 2

        # 构造跨命名空间同 full_path：/onebot11/ws 可由两种 (prefix, path) 组合产出
        rm.register_http_route("onebot11", "ws", h_a)
        rm.register_http_route("onebot11/ws", "", h_b)

        rm.unregister_all_by_namespace("onebot11")

        # nsB 的同 full_path 路由必须健在（注册表 + Starlette 路由表双确认）
        assert "/onebot11/ws" in rm._http_routes.get("onebot11/ws", {})
        remaining = [
            r for r in rm.app.routes if getattr(r, "path", None) == "/onebot11/ws"
        ]
        assert len(remaining) == 1

        # 收尾：清掉 nsB
        rm.unregister_all_by_namespace("onebot11/ws")

    def test_http_sse_same_path_type_isolated(self, router_manager):
        rm = router_manager

        async def h_http(event):
            return 1

        async def h_sse(emitter):
            return 1

        rm.register_http_route("onebot11", "stream", h_http)
        rm.register_sse("onebot11/stream", "", h_sse)

        # 卸载 HTTP 命名空间：SSE 路由不受牵连（旧实现按 path 过滤会误删）
        rm.unregister_all_by_namespace("onebot11")
        assert "/onebot11/stream" in rm._sse_routes.get("onebot11/stream", {})
        sse_routes = [
            r
            for r in rm.app.routes
            if getattr(r, "path", None) == "/onebot11/stream"
            and "GET" in (getattr(r, "methods", None) or set())
        ]
        assert len(sse_routes) == 1

        # 卸载 SSE 命名空间：HTTP 路由同样不受牵连（先重建一个）
        rm.register_http_route("onebot11", "stream", h_http)
        rm.unregister_all_by_namespace("onebot11/stream")
        assert "/onebot11/stream" in rm._http_routes.get("onebot11", {})

        rm.unregister_all_by_namespace("onebot11")


# ==================== A2：on_load 失败半卸载 ====================


class TestOnLoadFailureHalfUnload:
    def _make_manager(self):
        from ErisPulse.Core.module import ModuleManager

        manager = ModuleManager()
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        manager._module_services.clear()
        return manager

    def test_failed_load_leaves_no_owned_resources(self):
        import asyncio

        from ErisPulse.Core.Event import message
        from ErisPulse.Core.module import ModuleManager

        manager = self._make_manager()
        registered = []

        class Boom:
            async def on_load(self, ctx=None):
                # on_load 半途注册资源后崩溃——半卸载必须回收它
                async def _h(event):
                    return None

                message.handler.register(_h)
                registered.append(_h)
                raise RuntimeError("boom")

        manager.register("boom_mod", Boom)
        assert asyncio.run(manager.load("boom_mod")) is False

        # 实例未入注册表，且 on_load 半途注册的处理器已被回收
        assert "boom_mod" not in manager._modules
        assert not any(h.get("func") in registered for h in message.handler.handlers)

    def test_module_reloadable_after_failed_load(self):
        import asyncio

        from ErisPulse.Core.module import ModuleManager

        manager = self._make_manager()
        attempts = {"n": 0}

        class Retry:
            async def on_load(self, ctx=None):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise RuntimeError("first boom")

        manager.register("retry_mod", Retry)
        assert asyncio.run(manager.load("retry_mod")) is False
        assert asyncio.run(manager.load("retry_mod")) is True
        assert "retry_mod" in manager._loaded_modules


# ==================== B：reload 快照回滚 ====================


class RichFakeManager:
    """带完整注册表的 Fake 管理器（回滚断言用）"""

    def __init__(self):
        self.calls: "list[tuple]" = []
        self._module_classes = {"Weather": object}
        self._module_info = {"Weather": {"meta": {"name": "Weather"}}}
        self._modules = {"Weather": "old_instance"}
        self._loaded_modules = {"Weather"}
        self._module_services = {"Weather": None}
        self._lazy_modules = {}
        self.load_should_fail = False

    def _collect_dependents(self, name):
        return []

    async def unload(self, name):
        self.calls.append(("unload", name))
        self._loaded_modules.discard(name)
        self._modules.pop(name, None)
        return True

    def unregister(self, name):
        self.calls.append(("unregister", name))
        self._module_classes.pop(name, None)
        self._module_info.pop(name, None)
        return True

    def register(self, name, cls, info):
        self.calls.append(("register", name))
        self._module_classes[name] = cls
        self._module_info[name] = info
        return True

    def register_lazy(self, name, proxy):
        pass

    async def load(self, name):
        self.calls.append(("load", name))
        if self.load_should_fail:
            return False
        self._modules[name] = "new_instance"
        self._loaded_modules.add(name)
        return True

    def get(self, name):
        return self._modules.get(name)


def _make_module_in_sys(name):
    mod = types.ModuleType(name)

    class Weather:
        pass

    Weather.__module__ = name
    mod.Weather = Weather
    # reload_module 读取旧模块对象的 moduleInfo（meta.source / top_level）
    mod.moduleInfo = {"meta": {"name": "Weather"}}
    sys.modules[name] = mod
    return mod


class TestReloadSnapshotRollback:
    def _build_loader(self, old_mod):
        from ErisPulse.loaders.module import ModuleLoader

        loader = ModuleLoader()
        loader._last_module_objs = {"Weather": old_mod}

        class FakeFinder:
            def __init__(self):
                self.load_count = 0

            def find_by_name(self, name):
                return self

            def load(self):
                self.load_count += 1
                raise FileNotFoundError("package uninstalled")

            def clear_cache(self):
                pass

            def get_top_level_modules(self, package):
                return []

        loader._finder = FakeFinder()
        return loader

    def test_failed_reload_restores_state(self):
        pkg = "erp_test_rollback_weather"
        old_mod = _make_module_in_sys(pkg)
        try:
            manager = RichFakeManager()
            manager.load_should_fail = True

            import types as _types

            sdk = _types.SimpleNamespace(Weather="old_instance")
            loader = self._build_loader(old_mod)

            result = __import__("asyncio").run(
                loader.reload_module("Weather", manager, sdk)
            )

            assert result is False
            # 旧注册状态全部恢复
            assert manager._module_classes["Weather"] is manager._module_classes["Weather"]
            assert manager._modules["Weather"] == "old_instance"
            assert "Weather" in manager._loaded_modules
            assert sdk.Weather == "old_instance"
            # sys.modules 条目被恢复（purge 后又回填）
            assert sys.modules.get(pkg) is old_mod
            # 重载快照对象保持为旧模块对象
            assert loader._last_module_objs["Weather"] is old_mod
            # 恢复动作经过 register（注册存根重建）
            assert ("register", "Weather") in manager.calls
        finally:
            sys.modules.pop(pkg, None)

    def test_removed_package_is_unload_not_rollback(self):
        pkg = "erp_test_removed_weather"
        old_mod = _make_module_in_sys(pkg)
        try:
            from ErisPulse.loaders.module import ModuleLoader

            manager = RichFakeManager()
            loader = ModuleLoader()
            loader._last_module_objs = {"Weather": old_mod}

            # find_by_name 返回 None：安装包已被卸载 → 视作卸载成功，不回滚
            class FakeFinder:
                def find_by_name(self, name):
                    return None

                def clear_cache(self):
                    pass

            loader._finder = FakeFinder()

            import asyncio

            assert asyncio.run(loader.reload_module("Weather", manager, __import__("types").SimpleNamespace())) is True
            assert "Weather" not in loader._last_module_objs
        finally:
            sys.modules.pop(pkg, None)


# ==================== 归属权统一门面 ====================


class TestOwnershipFacade:
    def test_counts_orphans_no_crash(self):
        from ErisPulse.Core.ownership import ownership

        assert isinstance(ownership.counts(), dict)
        assert isinstance(ownership.orphans(), list)

    def test_reclaim_sync_unknown_owner(self):
        from ErisPulse.Core.ownership import ownership

        result = ownership.reclaim_sync("definitely_not_registered_xyz")
        assert isinstance(result, dict)

    def test_module_manager_audit_passthrough(self):
        from ErisPulse.Core.module import ModuleManager

        manager = ModuleManager()
        report = manager.audit("definitely_not_registered_xyz")
        assert report["owner"] == "definitely_not_registered_xyz"
        assert "counts" in report and "orphans" in report
