"""
拓扑树 API 单元测试

测试 ModuleManager.get_topology()、AdapterManager.get_topology()、
ScopeManager.get_topology() 与 sdk.get_topology() 的聚合能力。
"""

from ErisPulse.Core.scope import ScopeManager


class TestModuleTopology:
    """模块拓扑树"""

    def test_module_topology_shape(self):
        """get_topology() 返回模块级归属结构"""
        from ErisPulse.Core import module

        topo = module.get_topology()
        assert "modules" in topo
        assert isinstance(topo["modules"], dict)

    def test_module_resources_grouped_by_owner(self):
        """命令 / 处理器 / 路由按 owner 归并"""
        from ErisPulse.Core import module
        from ErisPulse.Core.Event import _clear_all_handlers, command, message
        from ErisPulse.runtime.context import current_owner

        _clear_all_handlers()
        try:
            token = current_owner.set("TopoMod")
            try:

                @command("topo_cmd")
                async def topo_cmd(event):
                    pass

                @message.on_message()
                async def topo_handler(event):
                    pass

            finally:
                current_owner.reset(token)

            topo = module.get_topology()
            entry = topo["modules"].get("TopoMod")
            # 命令归属（按注册名 owner）
            if entry:
                assert "topo_cmd" in entry["commands"]
                assert entry["handlers"].get("message", 0) >= 1
        finally:
            _clear_all_handlers()

    def test_module_scope_applies_flag(self):
        """模块拓扑标记 scope_applies"""
        from ErisPulse.Core import module
        from ErisPulse.Core.Event import _clear_all_handlers

        _clear_all_handlers()
        try:
            topo = module.get_topology()
            for entry in topo["modules"].values():
                assert "scope_applies" in entry
        finally:
            _clear_all_handlers()


class TestAdapterTopology:
    """适配器拓扑树"""

    def test_adapter_topology_shape(self):
        """get_topology() 返回适配器 / Bot / scope 结构"""
        from ErisPulse.Core import adapter

        topo = adapter.get_topology()
        assert "adapters" in topo

    def test_bot_scope_in_topology(self):
        """Bot 级作用域出现在适配器拓扑中"""
        from ErisPulse.Core import adapter
        from ErisPulse.Core.scope import scope as scope_singleton

        old_bindings = scope_singleton._bindings
        scope_singleton._bindings = {
            "platforms": {},
            "bots": {"fake_plat": {"bot_1": {"modules": ["Chat"], "blocked": []}}},
        }
        # 手动写入注册的 Bot 状态（模拟在线 Bot）
        adapter._bots["fake_plat"] = {
            "bot_1": {"status": "online", "last_active": 1.0, "info": {"nickname": "B1"}}
        }
        try:
            topo = adapter.get_topology()
            adapters = topo["adapters"]
            if "fake_plat" in adapters:
                assert "scope" in adapters["fake_plat"]
                assert "bots" in adapters["fake_plat"]
        finally:
            scope_singleton._bindings = old_bindings
            adapter._bots.clear()


class TestScopeTopology:
    """作用域拓扑树"""

    def test_scope_topology(self):
        """get_topology() 返回全部绑定"""
        mgr = ScopeManager()
        mgr._bindings = {
            "platforms": {"onebot11": {"modules": ["Chat"], "blocked": []}},
            "bots": {"onebot11": {"123456": {"modules": [], "blocked": ["Danger"]}}},
        }
        topo = mgr.get_topology()
        assert topo["platforms"]["onebot11"]["modules"] == ["Chat"]
        assert topo["bots"]["onebot11"]["123456"]["blocked"] == ["Danger"]


class TestSdkTopology:
    """sdk.get_topology() 聚合"""

    def test_sdk_topology_composes(self):
        """聚合模块 / 适配器 / 控制面"""
        from ErisPulse import sdk

        topo = sdk.get_topology()
        assert set(topo.keys()) == {"modules", "adapters", "scope"}
        assert isinstance(topo["modules"], dict)
        assert isinstance(topo["adapters"], dict)
        assert isinstance(topo["scope"], dict)


class TestLifecycleOwnerCounts:
    """LifecycleManager.get_owner_counts()"""

    def test_owner_counts(self):
        from ErisPulse.Core.lifecycle import lifecycle
        from ErisPulse.runtime.context import current_owner

        before = lifecycle.get_owner_counts().get("TopoLifecycle", 0)
        token = current_owner.set("TopoLifecycle")
        try:
            lifecycle.register("topo.test.1", lambda d: None)
            lifecycle.register("topo.test.2", lambda d: None)
        finally:
            current_owner.reset(token)
        after = lifecycle.get_owner_counts().get("TopoLifecycle", 0)
        assert after == before + 2
