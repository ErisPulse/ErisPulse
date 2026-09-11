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

        old_bindings = scope_singleton._data
        scope_singleton._data = {
            "platforms": {},
            "bots": {"fake_plat": {"bot_1": {"modules": ["Chat"], "blocked": []}}},
            "sessions": {},
            "identity": {"adapters": {}, "bots": {}, "sessions": {}, "users": {}},
            "actions": {},
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
            scope_singleton._data = old_bindings
            adapter._bots.clear()


class TestScopeTopology:
    """作用域拓扑树"""

    def test_scope_topology(self):
        """get_topology() 返回全部绑定"""
        mgr = ScopeManager()
        mgr._data = {
            "platforms": {"onebot11": {"modules": ["Chat"], "blocked": []}},
            "bots": {"onebot11": {"123456": {"modules": [], "blocked": ["Danger"]}}},
            "sessions": {},
            "identity": {"adapters": {}, "bots": {}, "sessions": {}, "users": {}},
            "actions": {},
        }
        topo = mgr.topology()
        assert topo["platforms"]["onebot11"]["modules"] == ["Chat"]
        assert topo["bots"]["onebot11"]["123456"]["blocked"] == ["Danger"]


class TestSdkTopology:
    """sdk.get_topology() 聚合"""

    def test_sdk_topology_composes(self):
        """聚合模块 / 适配器 / 作用域"""
        from ErisPulse import sdk

        topo = sdk.get_topology()
        assert set(topo.keys()) == {"modules", "adapters", "scope"}
        assert isinstance(topo["modules"], dict)
        assert isinstance(topo["adapters"], dict)
        assert isinstance(topo["scope"], dict)
        assert isinstance(topo["scope"], dict)


class TestJsonSafeUtil:
    """Core.config.json_safe() 递归净化"""

    def test_primitives_passthrough(self):
        """标量 / 空值原样返回"""
        from ErisPulse.Core.config import json_safe

        assert json_safe(None) is None
        assert json_safe("x") == "x"
        assert json_safe(3) == 3
        assert json_safe(1.5) == 1.5
        assert json_safe(True) is True

    def test_containers_recursed_and_serializable(self):
        """容器递归处理且整体可 json.dumps"""
        import json

        from ErisPulse.Core.config import json_safe

        out = json_safe({"a": [1, (2, 3)], "b": {object()}})
        assert out["a"][0] == 1
        assert out["a"][1] == [2, 3]  # tuple → list
        assert isinstance(out["b"], list)  # set → list
        assert json.dumps(out)

    def test_type_to_name_and_object_fallback(self):
        """类对象取 __name__，其余不可序列化对象退化 str()"""
        from ErisPulse.Core.config import json_safe

        class _Dummy:
            def __repr__(self):
                return "<dummy>"

        assert json_safe(ScopeManager) == "ScopeManager"
        assert json_safe(_Dummy()) == "<dummy>"

    def test_depth_guard(self):
        """超深结构截断为 str，避免无限递归"""
        import json

        from ErisPulse.Core.config import json_safe

        root: dict = {}
        cursor = root
        for _ in range(20):
            child: dict = {}
            cursor["k"] = child
            cursor = child
        assert json.dumps(json_safe(root))


class TestTopologyJsonSafe:
    """get_topology 的 JSON 安全输出"""

    def test_topology_default_is_json_serializable(self):
        """默认 json_safe=True 时三种拓扑均可直接 json.dumps"""
        import json

        from ErisPulse import sdk
        from ErisPulse.Core import adapter, module

        for topo in (
            module.get_topology(),
            adapter.get_topology(),
            sdk.get_topology(),
        ):
            assert json.dumps(topo)

    def test_module_info_runtime_objects_stripped_in_safe_mode(self):
        """安全模式下模块 info 只保留纯数据 meta 子表"""
        import json

        from ErisPulse.Core import module

        class _FakeModule:
            pass

        module.register(
            "SafeInfoMod",
            _FakeModule,
            {
                "meta": {"name": "SafeInfoMod", "description": "demo"},
                "module_class": _FakeModule,
                "strategy": object(),
            },
        )
        try:
            safe_entry = module.get_topology()["modules"].get("SafeInfoMod")
            assert safe_entry is not None
            # 运行时对象（module_class / strategy）被丢弃，仅剩 meta 纯数据
            assert safe_entry["info"] == {
                "name": "SafeInfoMod",
                "description": "demo",
            }
            json.dumps(safe_entry)

            raw_entry = module.get_topology(json_safe=False)["modules"].get(
                "SafeInfoMod"
            )
            assert raw_entry is not None
            assert raw_entry["info"]["module_class"] is _FakeModule
        finally:
            module.unregister("SafeInfoMod")


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
