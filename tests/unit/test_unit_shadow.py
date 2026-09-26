"""
影子模块（方向十一）单元测试

覆盖：归属权影子判定面、事件投递副本隔离（影子 mark_processed 不外溢）、
影子命令目录分流（不顶掉 v1）、出站 Send/Api 记账拦截（不触网、成功形状
假响应）、storage 覆盖层（写隔离/读透传/删墓碑）、生命周期静默、
promote 失败回滚（v1 复活）。
"""

import asyncio
import types

import pytest

from ErisPulse.Core.Event import message
from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.Event.wrapper import Event
from ErisPulse.Core.Bases import BaseAdapter
from ErisPulse.Core.Bases.module import BaseModule
from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.ownership import ownership
from ErisPulse.Core.shadow import shadow_ledger, shadow_manager
from ErisPulse.runtime.context import owner_scope


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter as adapter_manager
    from ErisPulse.Core.Event import _clear_all_handlers

    def _clean():
        _clear_all_handlers()
        command_handler.commands.clear()
        command_handler.aliases.clear()
        command_handler.groups.clear()
        command_handler.permissions.clear()
        command_handler._shadow_catalog.clear()
        command_handler._gate.clear_all()
        adapter_manager._onebot_handlers.clear()
        adapter_manager._raw_handlers.clear()
        adapter_manager._bots.clear()
        shadow_ledger._entries.clear()
        shadow_manager._shadows.clear()
        shadow_manager._overlays.clear()
        ownership._shadow_owners.clear()

    _clean()
    yield
    _clean()


def _msg(text, user_id="u1"):
    return {
        "id": f"id_{abs(hash(text))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "onebot11",
        "self": {"platform": "onebot11", "user_id": "bot_x"},
        "user_id": user_id,
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }


class _FakeAdapter(BaseAdapter):
    def __init__(self, sdk=None):
        super().__init__()
        self.api_calls: "list[str]" = []

    async def start(self):
        pass

    async def shutdown(self):
        pass

    async def call_api(self, endpoint: str, **params):
        self.api_calls.append(endpoint)
        return {"status": "ok", "retcode": 0, "data": None, "message_id": "m1", "message": ""}


# ==================== 判定面 ====================


class TestShadowRegistry:
    def test_register_is_unregister(self):
        assert ownership.is_shadow("sh_x") is False
        ownership.register_shadow("sh_x")
        assert ownership.is_shadow("sh_x") is True
        assert "sh_x" in ownership.shadow_owners()
        ownership.unregister_shadow("sh_x")
        assert ownership.is_shadow("sh_x") is False


def _mk_shadow_handler(seen):
    async def shadow_handler(event):
        seen["shadow_marker"] = event.get("_shadow")
        event.mark_processed()  # 影子的认领只作用于自己的副本

    return shadow_handler


def _mk_normal_handler(seen_list):
    async def normal_handler(event):
        seen_list.append(True)

    return normal_handler


# ==================== 闸 1/2：事件副本与认领隔离 ====================


class TestEventCopyIsolation:
    async def test_shadow_mark_processed_does_not_leak(self):
        ownership.register_shadow("sh_event")
        seen = {"shadow_marker": None}
        normal_ran = []

        with owner_scope("sh_event"):
            message.handler.register(_mk_shadow_handler(seen), priority=10)
        with owner_scope("v1_event"):
            message.handler.register(_mk_normal_handler(normal_ran), priority=0)

        from ErisPulse.Core.adapter import adapter as adapter_manager

        with patch_getConfig():
            await adapter_manager.emit(_msg("hello"))
            await asyncio.sleep(0.05)  # 等待分发协程执行（与治理测试同款）

        assert seen["shadow_marker"] is True
        assert normal_ran == [True]  # 原事件未被影子的认领吞掉

    def test_event_copy_helper(self):
        e = Event({"a": 1})
        copy = Event(dict(e))
        copy["b"] = 2
        assert "b" not in e


# ==================== 闸 3：影子命令目录 ====================


class TestShadowCommandCatalog:
    def test_shadow_command_goes_to_catalog(self):
        ownership.register_shadow("sh_cmd")

        with owner_scope("sh_cmd"):
            @command_handler("sh_cmd", help="影子命令")
            async def sh_cmd(event):
                return 1

        assert "sh_cmd" not in command_handler.commands
        assert "sh_cmd" in command_handler._shadow_catalog
        assert command_handler._shadow_catalog["sh_cmd"]["owner"] == "sh_cmd"

    def test_v1_command_unaffected(self):
        with owner_scope("v1_own"):
            @command_handler("v1_cmd")
            async def v1_cmd(event):
                return 1

        ownership.register_shadow("sh_cmd2")
        with owner_scope("sh_cmd2"):
            @command_handler("v1_cmd")
            async def v1_cmd_shadow(event):
                return 2

        # 影子同名命令不顶掉 v1
        assert command_handler.commands["v1_cmd"]["owner"] == "v1_own"
        assert "v1_cmd" in command_handler._shadow_catalog


# ==================== 闸 4/5：出站记账拦截 ====================


class TestOutboundInterception:
    @pytest.fixture
    def fake_adapter(self):
        adapter_obj = _FakeAdapter()
        return adapter_obj

    async def test_send_intercepted_and_ledgered(self, fake_adapter):
        from ErisPulse.runtime.context import owner_scope as _os

        ownership.register_shadow("sh_send")
        with _os("sh_send"):
            result = fake_adapter.Send.To("user", "u1").Text("影子消息")

        resp = await result if hasattr(result, "__await__") else result
        assert resp["status"] == "ok"  # 成功形状假响应
        assert fake_adapter.api_calls == []  # 未触网
        entries = shadow_ledger.entries("sh_send")
        assert entries and entries[0]["kind"] == "send"
        assert entries[0]["method"] == "Text"
        assert entries[0]["target_id"] == "u1"
        assert "影子消息" in entries[0]["preview"]

    async def test_api_intercepted_and_ledgered(self, fake_adapter):
        ownership.register_shadow("sh_api")
        with owner_scope("sh_api"):
            resp = await fake_adapter.Api.get_self_info()

        assert resp["status"] == "ok"
        assert fake_adapter.api_calls == []
        entries = shadow_ledger.entries("sh_api")
        assert entries and entries[0]["kind"] == "api"
        assert entries[0]["method"] == "get_self_info"

    async def test_non_shadow_send_not_intercepted(self, fake_adapter):
        from ErisPulse.runtime.context import owner_scope as _os

        with _os("real_mod"):
            result = await fake_adapter.Send.To("user", "u1").Text("真实消息")

        resp = await result if hasattr(result, "__await__") else result
        # 关键断言：非影子发送不进影子账本（假适配器未实现 Raw_ob12 返回
        # failed 属预期——链路确实到达了适配器层而非被拦截）
        assert shadow_ledger.entries("real_mod") == []
        assert isinstance(resp, dict)


# ==================== 闸 6：storage 覆盖层 ====================


class TestStorageOverlay:
    async def test_write_isolated_read_passthrough(self):
        from ErisPulse.Core.storage import storage as storage_service

        ownership.register_shadow("sh_st")
        # 先落一个"真库"值（非影子上下文）
        await storage_service.aset("ovl_real", "real")

        with owner_scope("sh_st"):
            await storage_service.aset("ovl_shadow", "from_shadow")
            await storage_service.aset("ovl_real", "shadow_overwrite")
            # 影子读：覆盖层命中（含被影子改写的真库键）
            assert await storage_service.aget("ovl_shadow") == "from_shadow"
            assert await storage_service.aget("ovl_real") == "shadow_overwrite"

        # 影子外读：影子写不泄漏到真库
        assert await storage_service.aget("ovl_shadow") is None
        assert await storage_service.aget("ovl_real") == "real"

    async def test_delete_tombstone(self):
        from ErisPulse.Core.storage import storage as storage_service

        persisted = await storage_service.aset("ovl_tomb", "v")
        ownership.register_shadow("sh_st2")

        with owner_scope("sh_st2"):
            await storage_service.adelete("ovl_tomb")
            assert await storage_service.aget("ovl_tomb") is None  # 墓碑：影子视角已删

        # 真库值不受影响（存储不可用时 aset 返回 False，跳过该断言）
        if persisted:
            assert await storage_service.aget("ovl_tomb") == "v"


# ==================== 闸 7：生命周期静默 ====================


class TestLifecycleSilence:
    async def test_shadow_events_and_hooks_silenced(self):
        from ErisPulse.Core.lifecycle import lifecycle

        ownership.register_shadow("sh_lc")
        seen = []

        with owner_scope("sh_lc"):
            lifecycle.register("module.load", lambda d: seen.append("shadow"))

        with owner_scope("normal_lc"):
            lifecycle.register("module.load", lambda d: seen.append("normal"))

        # 影子自身的 module.load 广播被整体静默（两个钩子都不触发）
        await lifecycle.emit("module.load", {"module_name": "sh_lc", "success": True})
        assert seen == []

        # 普通模块事件正常广播，但影子钩子不参与
        await lifecycle.emit("module.load", {"module_name": "normal_lc", "success": True})
        assert seen == ["normal"]


# ==================== F：promote 回滚 ====================


class _V1(BaseModule):
    async def on_load(self, ctx=None):
        self.loaded = "v1"

    async def on_unload(self, ctx=None):
        pass


class _V2Fail(BaseModule):
    fail_on_load = False  # 转正前置 True：影子装载成功、转正时装载失败

    async def on_load(self, ctx=None):
        if type(self).fail_on_load:
            raise RuntimeError("v2 boom")

    async def on_unload(self, ctx=None):
        pass


class _V2Ok(BaseModule):
    async def on_load(self, ctx=None):
        self.loaded = "v2"

    async def on_unload(self, ctx=None):
        pass


class TestPromote:
    def _fresh_manager(self):
        manager = ModuleManager()
        manager._modules.clear()
        manager._module_classes.clear()
        manager._loaded_modules.clear()
        manager._module_info.clear()
        manager._module_services.clear()
        return manager

    def _setup_shadow(self, manager, v2_class):
        manager.register("Roll", _V1)
        manager.register("Roll_shadow", v2_class, {"meta": {"name": "Roll_shadow", "source": "shadow"}})

        async def _load():
            assert await manager.load("Roll") is True
            assert await manager.load("Roll_shadow") is True

        asyncio.run(_load())
        shadow_manager.bind("Roll", "Roll_shadow")
        ownership.register_shadow("Roll_shadow")

    def test_start_via_path(self, tmp_path):
        from ErisPulse.loaders.module import ModuleLoader

        manager = self._fresh_manager()
        manager.register("Roll", _V1)
        assert asyncio.run(manager.load("Roll")) is True

        src = tmp_path / "roll_v2.py"
        src.write_text(
            "from ErisPulse.Core.Bases.module import BaseModule\n"
            "class RollV2(BaseModule):\n"
            "    async def on_load(self, ctx=None):\n"
            "        self.loaded = 'v2'\n"
            "    async def on_unload(self, ctx=None):\n"
            "        pass\n",
            encoding="utf-8",
        )

        sdk = types.SimpleNamespace()
        loader = ModuleLoader()
        owner = asyncio.run(
            shadow_manager.start("Roll", str(src), manager=manager, sdk=sdk, loader=loader)
        )

        assert owner == "roll_v2"
        assert manager._modules["roll_v2"]._shadow_source == "Roll"
        assert ownership.is_shadow("roll_v2") is True
        assert sdk.roll_v2 is manager._modules["roll_v2"]

    def test_start_requires_loaded_target(self, tmp_path):
        manager = self._fresh_manager()
        src = tmp_path / "x_v9.py"
        src.write_text("x = 1\n", encoding="utf-8")

        with pytest.raises(RuntimeError):
            asyncio.run(shadow_manager.start("ghost_mod", str(src), manager=manager, sdk=None))

    def test_promote_success(self):
        from ErisPulse.loaders.module import ModuleLoader

        manager = self._fresh_manager()
        self._setup_shadow(manager, _V2Ok)

        sdk = types.SimpleNamespace()
        loader = ModuleLoader()
        result = asyncio.run(shadow_manager.promote("Roll", manager, sdk, loader))

        assert result is True
        assert "Roll" in manager._loaded_modules
        assert isinstance(manager._modules["Roll"], _V2Ok)
        assert "Roll_shadow" not in manager._module_classes
        assert ownership.is_shadow("Roll_shadow") is False

    def test_promote_failure_rolls_back_v1(self):
        from ErisPulse.loaders.module import ModuleLoader

        manager = self._fresh_manager()
        self._setup_shadow(manager, _V2Fail)
        _V2Fail.fail_on_load = True  # 转正时装载失败 → 触发回滚

        sdk = types.SimpleNamespace()
        loader = ModuleLoader()
        result = asyncio.run(shadow_manager.promote("Roll", manager, sdk, loader))

        assert result is False
        # v1 复活：旧实例回位继续服务
        assert "Roll" in manager._loaded_modules
        assert isinstance(manager._modules["Roll"], _V1)
        assert sdk is not None


def patch_getConfig():
    """命令分发路径的 prefix 配置 patch（与治理测试同款）"""
    import importlib
    from unittest.mock import patch

    config_module = importlib.import_module("ErisPulse.Core.config")
    return patch.object(config_module.config, "getConfig", return_value="/")
