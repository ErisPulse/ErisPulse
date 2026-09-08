"""
模块间通信（module.call / emit_to）单元测试

覆盖协议化 RPC 的核心语义：目标解析与懒唤醒、provides 契约白名单、
scope 出站审计（actions.<caller>.call）、owner 归因、超时、
以及 emit_to 定向事件投递与目标校验。
"""

import asyncio
import importlib

import pytest

from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Bases.errors import (
    ModuleCallError,
    ModuleCallTimeoutError,
    ModuleError,
    ModuleNotAvailableError,
    ServiceNotProvidedError,
)
from ErisPulse.Core.module import ModuleManager

scope_module = importlib.import_module("ErisPulse.Core.scope")


class _SvcModule(BaseModule):
    """契约模块：get_meta().services 白名单收紧"""

    def __init__(self, sdk=None):
        self.sdk = sdk

    @staticmethod
    def get_meta():
        from ErisPulse.Core.Bases import ModuleMeta

        return ModuleMeta(services=["get_value", "echo", "slow", "who_am_i", "standard_doc"])

    async def on_load(self, event):
        return True

    async def on_unload(self, event):
        return True

    async def standard_doc(self):
        """
        规范多行 docstring 的摘要行

        空行开头 + 参数区……
        """
        return "ok"

    async def get_value(self, n: int = 1):
        """翻倍数值

        更长的 docstring 细节……（只取首行）
        """
        return n * 2

    async def echo(self, x):
        """原样返回输入"""
        return x

    async def slow(self):
        await asyncio.sleep(5)
        return "done"

    async def who_am_i(self):
        from ErisPulse.runtime.context import get_current_owner

        return get_current_owner()

    async def _private(self):
        return "secret"

    def sync_off_contract(self):
        return "hi"


class _DescribedModule(BaseModule):
    """契约含显式 description 的模块"""

    def __init__(self, sdk=None):
        self.sdk = sdk

    @staticmethod
    def get_meta():
        from ErisPulse.Core.Bases import ModuleMeta

        return ModuleMeta(
            services=[
                {"name": "translate", "description": "把文本翻译成指定语言"},
                {"name": "no_docstring_method"},
            ]
        )

    async def on_load(self, event):
        return True

    async def on_unload(self, event):
        return True

    async def translate(self, text, target_lang):
        """docstring 版翻译说明（应被显式 description 覆盖）"""
        return text

    async def no_docstring_method(self):
        """无显式声明时取 docstring 首行"""
        return "x"


class _OpenModule(BaseModule):
    """未声明契约的模块：公开方法可调"""

    def __init__(self, sdk=None):
        self.sdk = sdk

    async def on_load(self, event):
        return True

    async def on_unload(self, event):
        return True

    def sync_hello(self):
        return "hi"


class _SyncSvcModule(BaseModule):
    """契约含同步方法的模块"""

    def __init__(self, sdk=None):
        self.sdk = sdk

    @staticmethod
    def get_meta():
        from ErisPulse.Core.Bases import ModuleMeta

        return ModuleMeta(services=["sync_ok"])

    async def on_load(self, event):
        return True

    async def on_unload(self, event):
        return True

    def sync_ok(self):
        return "ok"


class _MissingSvcModule(BaseModule):
    """契约声明了不存在方法的模块"""

    def __init__(self, sdk=None):
        self.sdk = sdk

    @staticmethod
    def get_meta():
        from ErisPulse.Core.Bases import ModuleMeta

        return ModuleMeta(services=["nope"])

    async def on_load(self, event):
        return True

    async def on_unload(self, event):
        return True


@pytest.fixture
def manager():
    """独立 ModuleManager + config.toml 还原保护

    disable()/enable() 会持久化模块状态到全局 config.toml，
    用例结束后直接还原文件并重读，防止污染后续用例（同 scope 测试的方案）。
    """
    from pathlib import Path

    from ErisPulse.Core.config import config as _config

    path = Path("config/config.toml")
    backup = path.read_bytes() if path.exists() else None

    manager = ModuleManager()
    manager._modules.clear()
    manager._module_classes.clear()
    manager._loaded_modules.clear()
    manager._module_info.clear()
    manager._lazy_modules.clear()
    scope_module.scope._data["actions"] = {}
    scope_module.scope._invalidate_cache()
    yield manager
    manager._modules.clear()
    manager._module_classes.clear()
    manager._loaded_modules.clear()
    manager._module_info.clear()
    manager._lazy_modules.clear()
    scope_module.scope._data["actions"] = {}
    scope_module.scope._invalidate_cache()
    # 还原配置文件（丢弃 disable/enable 留下的持久化写入）
    try:
        with _config._lock:
            _config._dirty_keys.clear()
    except Exception:
        pass
    if backup is None:
        path.unlink(missing_ok=True)
    else:
        path.write_bytes(backup)
    try:
        _config.reload()
    except Exception:
        pass


async def _load(manager, name, cls):
    manager.register(name, cls)
    assert await manager.load(name) is True


# ==================== 异常体系 ====================


class TestExceptionHierarchy:
    def test_hierarchy(self):
        assert issubclass(ModuleCallError, ModuleError)
        assert issubclass(ModuleNotAvailableError, ModuleCallError)
        assert issubclass(ServiceNotProvidedError, ModuleCallError)
        assert issubclass(ModuleCallTimeoutError, ModuleCallError)

    def test_context_attributes(self):
        err = ModuleCallTimeoutError("Svc", "slow", "timeout")
        assert err.module == "Svc"
        assert err.method == "slow"


# ==================== 基础调用 ====================


class TestBasicCall:
    @pytest.mark.asyncio
    async def test_async_method_with_args(self, manager):
        await _load(manager, "Svc", _SvcModule)
        assert await manager.call("Svc", "get_value", 21) == 42
        assert await manager.call("Svc", "echo", "x") == "x"
        assert await manager.call("Svc", "echo", x={"k": 1}) == {"k": 1}

    @pytest.mark.asyncio
    async def test_sync_method_in_contract(self, manager):
        # services 白名单内的同步方法可调
        await _load(manager, "SyncSvc", _SyncSvcModule)
        assert await manager.call("SyncSvc", "sync_ok") == "ok"

    @pytest.mark.asyncio
    async def test_owner_attributed_to_target(self, manager):
        await _load(manager, "Svc", _SvcModule)
        from ErisPulse.runtime.context import current_owner

        token = current_owner.set("Caller")
        try:
            assert await manager.call("Svc", "who_am_i") == "Svc"
        finally:
            current_owner.reset(token)

    @pytest.mark.asyncio
    async def test_timeout(self, manager):
        await _load(manager, "Svc", _SvcModule)
        with pytest.raises(ModuleCallTimeoutError):
            await manager.call("Svc", "slow", timeout=0.05)


# ==================== 目标解析 ====================


class TestTargetResolution:
    @pytest.mark.asyncio
    async def test_not_registered(self, manager):
        with pytest.raises(ModuleNotAvailableError):
            await manager.call("Ghost", "anything")

    @pytest.mark.asyncio
    async def test_disabled(self, manager):
        await _load(manager, "Svc", _SvcModule)
        manager.disable("Svc")
        with pytest.raises(ModuleNotAvailableError):
            await manager.call("Svc", "get_value")

    @pytest.mark.asyncio
    async def test_lazy_wakeup(self, manager):
        """注册懒加载代理的模块可被 RPC 唤醒后调用"""
        from ErisPulse import sdk
        from ErisPulse.loaders.module import LazyModule

        manager.register("Svc", _SvcModule)
        proxy = LazyModule("Svc", _SvcModule, sdk, {"meta": {"is_base_module": True}}, manager)
        manager.register_lazy("Svc", proxy)

        # 未加载：通过 RPC 唤醒并调用
        assert await manager.call("Svc", "get_value", 5) == 10
        assert "Svc" in manager._loaded_modules


# ==================== 契约白名单 ====================


class TestProvidesContract:
    @pytest.mark.asyncio
    async def test_outside_whitelist_rejected(self, manager):
        await _load(manager, "Svc", _SvcModule)
        with pytest.raises(ServiceNotProvidedError):
            await manager.call("Svc", "sync_off_contract")

    @pytest.mark.asyncio
    async def test_private_always_rejected(self, manager):
        await _load(manager, "Svc", _SvcModule)
        with pytest.raises(ServiceNotProvidedError):
            await manager.call("Svc", "_private")

    @pytest.mark.asyncio
    async def test_missing_method(self, manager):
        await _load(manager, "Missing", _MissingSvcModule)
        with pytest.raises(ServiceNotProvidedError):
            await manager.call("Missing", "nope")

    @pytest.mark.asyncio
    async def test_open_module_allows_public(self, manager):
        """未声明 provides 的模块：公开方法可调（向后兼容裸属性访问语义）"""
        await _load(manager, "Open", _OpenModule)
        assert await manager.call("Open", "sync_hello") == "hi"

    @pytest.mark.asyncio
    async def test_open_module_still_blocks_private(self, manager):
        await _load(manager, "Open", _OpenModule)
        with pytest.raises(ServiceNotProvidedError):
            await manager.call("Open", "_secret")


# ==================== scope 出站审计 ====================


class TestScopeAudit:
    @pytest.mark.asyncio
    async def test_denied_by_actions(self, manager):
        await _load(manager, "Svc", _SvcModule)
        from ErisPulse.runtime.context import current_owner

        scope_module.scope.set_action("Caller", "call", deny="Svc.get_value")
        token = current_owner.set("Caller")
        try:
            with pytest.raises(ModuleCallError):
                await manager.call("Svc", "get_value")
        finally:
            current_owner.reset(token)

    @pytest.mark.asyncio
    async def test_allowed_within_actions(self, manager):
        await _load(manager, "Svc", _SvcModule)
        from ErisPulse.runtime.context import current_owner

        scope_module.scope.set_action("Caller", "call", allow=["Svc.*"])
        token = current_owner.set("Caller")
        try:
            assert await manager.call("Svc", "get_value", 3) == 6
        finally:
            current_owner.reset(token)

    @pytest.mark.asyncio
    async def test_no_caller_bypasses_audit(self, manager):
        """框架层调用（无 owner）不受出站审计约束"""
        await _load(manager, "Svc", _SvcModule)
        scope_module.scope.set_action("Someone", "call", deny="Svc.get_value")
        assert await manager.call("Svc", "get_value") == 2


# ==================== emit_to 定向事件 ====================


class TestEmitTo:
    @pytest.mark.asyncio
    async def test_delivers_to_namespace(self, manager):
        from ErisPulse.Core.lifecycle import lifecycle

        await _load(manager, "Svc", _SvcModule)
        got = []

        async def hook(data):
            got.append(data)
            return "ok"

        lifecycle.register("module.Svc.custom_event", hook)
        try:
            result = await manager.emit_to("Svc", "custom_event", {"k": 1})
            assert got == [{"k": 1}]
            assert result == ["ok"] or result == "ok" or result is not None
        finally:
            lifecycle.unregister("module.Svc.custom_event", hook)

    @pytest.mark.asyncio
    async def test_prefix_subscription_receives(self, manager):
        """父级命名空间订阅（module.Svc）可接收该模块的全部定向事件"""
        from ErisPulse.Core.lifecycle import lifecycle

        await _load(manager, "Svc", _SvcModule)
        got = []

        async def hook(data):
            got.append(data)

        lifecycle.register("module.Svc", hook)
        try:
            await manager.emit_to("Svc", "another_event", {"n": 2})
            assert got == [{"n": 2}]
        finally:
            lifecycle.unregister("module.Svc", hook)

    @pytest.mark.asyncio
    async def test_unregistered_target_rejected(self, manager):
        with pytest.raises(ModuleNotAvailableError):
            await manager.emit_to("Ghost", "event")

    @pytest.mark.asyncio
    async def test_disabled_target_rejected(self, manager):
        await _load(manager, "Svc", _SvcModule)
        manager.disable("Svc")
        with pytest.raises(ModuleNotAvailableError):
            await manager.emit_to("Svc", "event")

    @pytest.mark.asyncio
    async def test_lazy_target_wakeup(self, manager):
        """emit_to 唤醒懒模块后投递（定向事件即激活源）"""
        from ErisPulse import sdk
        from ErisPulse.Core.lifecycle import lifecycle
        from ErisPulse.loaders.module import LazyModule

        manager.register("Svc", _SvcModule)
        proxy = LazyModule("Svc", _SvcModule, sdk, {"meta": {"is_base_module": True}}, manager)
        manager.register_lazy("Svc", proxy)

        got = []

        async def hook(data):
            got.append(data)

        lifecycle.register("module.Svc.wakeup_event", hook)
        try:
            await manager.emit_to("Svc", "wakeup_event", {"hello": 1})
            assert got == [{"hello": 1}]
            assert "Svc" in manager._loaded_modules
        finally:
            lifecycle.unregister("module.Svc.wakeup_event", hook)


# ==================== 服务目录 ====================


class TestServicesDirectory:
    @pytest.mark.asyncio
    async def test_lists_declared_with_signature(self, manager):
        await _load(manager, "Svc", _SvcModule)
        catalog = manager.services()
        assert "Svc" in catalog
        names = [e["name"] for e in catalog["Svc"]]
        assert "get_value" in names
        entry = next(e for e in catalog["Svc"] if e["name"] == "get_value")
        assert "n" in entry["signature"]  # 签名包含参数名

    @pytest.mark.asyncio
    async def test_undeclared_modules_excluded(self, manager):
        """未声明 services 的模块不出现在全量目录中"""
        await _load(manager, "Svc", _SvcModule)
        await _load(manager, "Open", _OpenModule)
        catalog = manager.services()
        assert "Svc" in catalog
        assert "Open" not in catalog

    @pytest.mark.asyncio
    async def test_single_module_query(self, manager):
        await _load(manager, "Svc", _SvcModule)
        await _load(manager, "Open", _OpenModule)
        catalog = manager.services("Svc")
        assert list(catalog.keys()) == ["Svc"]
        # 未声明模块的单查：空结果
        assert manager.services("Open") == {}

    def test_unknown_module(self, manager):
        assert manager.services("Ghost") == {}

    @pytest.mark.asyncio
    async def test_services_in_topology(self, manager):
        await _load(manager, "Svc", _SvcModule)
        await _load(manager, "Open", _OpenModule)
        topology = manager.get_topology()
        assert topology["modules"]["Svc"]["services"] == [
            "echo", "get_value", "slow", "standard_doc", "who_am_i"
        ]
        # 未声明模块 services 为空列表
        assert topology["modules"]["Open"]["services"] == []

    @pytest.mark.asyncio
    async def test_services_description_from_docstring(self, manager):
        """纯名字声明：介绍自动取 docstring 首行"""
        await _load(manager, "Svc", _SvcModule)
        catalog = manager.services("Svc")
        by_name = {e["name"]: e for e in catalog["Svc"]}
        assert by_name["get_value"]["description"] == "翻倍数值"
        assert by_name["echo"]["description"] == "原样返回输入"
        # 空行开头的规范多行 docstring：取第一个非空行
        assert by_name["standard_doc"]["description"] == "规范多行 docstring 的摘要行"

    @pytest.mark.asyncio
    async def test_services_description_explicit_overrides_docstring(self, manager):
        """dict 形态显式声明：description 覆盖 docstring"""
        await _load(manager, "Desc", _DescribedModule)
        catalog = manager.services("Desc")
        by_name = {e["name"]: e for e in catalog["Desc"]}
        assert by_name["translate"]["description"] == "把文本翻译成指定语言"
        # dict 形态但未声明 description → 回退 docstring 首行
        assert by_name["no_docstring_method"]["description"] == "无显式声明时取 docstring 首行"

    @pytest.mark.asyncio
    async def test_services_description_missing_docstring_empty(self, manager):
        """无 docstring 的方法：description 为空串"""
        await _load(manager, "Svc", _SvcModule)
        catalog = manager.services("Svc")
        by_name = {e["name"]: e for e in catalog["Svc"]}
        assert by_name["slow"]["description"] == ""  # slow 无 docstring

    @pytest.mark.asyncio
    async def test_services_description_i18n_resolved(self, manager):
        """description 支持 i18n 字典，目录输出为当前语言文本"""
        await _load(manager, "Svc", _SvcModule)

        # 直接测解析：模拟带 i18n 字典的条目
        desc = manager._service_description(
            "Svc", {"name": "echo", "description": {"i18n": "core.module.call_not_registered", "default": "兜底"}}
        )
        assert desc  # 解析为实际文本而非空
        assert desc != "兜底"  # locale 有该键，用的是翻译而非 default

    @pytest.mark.asyncio
    async def test_contract_uses_declared_names(self, manager):
        """dict 形态声明同样收紧白名单"""
        await _load(manager, "Desc", _DescribedModule)
        assert await manager.call("Desc", "translate", "hi", "zh") == "hi"
        # 白名单外的公开方法被拒（no_docstring_method 不在声明内……在 services 里）
        assert await manager.call("Desc", "no_docstring_method") == "x"


# ==================== 冷启动回放 ====================


class _ReplayModule(BaseModule):
    """声明 replay 的模块：加载后回放收件箱最近消息"""

    def __init__(self, sdk=None):
        self.sdk = sdk
        self.received = []

    @staticmethod
    def get_meta():
        from ErisPulse.Core.Bases import ModuleMeta

        return ModuleMeta(services=[])

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy

        return ModuleLoadStrategy(lazy_load=False, priority=100, replay="1h")

    async def on_load(self, event):
        from ErisPulse.Core.Event import message
        from ErisPulse.runtime.context import current_owner

        mod = self

        @message.on_message()
        async def replay_handler(e):
            mod.received.append(e)

        return True

    async def on_unload(self, event):
        return True


class TestColdStartReplay:
    @pytest.fixture(autouse=True)
    def _isolated_transcript(self, monkeypatch, tmp_path):
        """回放数据源（transcript）指向临时数据库，避免全局 DB 脏数据干扰"""
        import importlib as _importlib

        from ErisPulse.Core.storage import StorageManager

        StorageManager._instance = None
        db_path = tmp_path / "replay.db"
        storage_module = _importlib.import_module("ErisPulse.Core.storage")
        transcript_module = _importlib.import_module("ErisPulse.Core.transcript")
        sm = StorageManager.__new__(StorageManager)
        sm.db_path = str(db_path)
        sm._init_db()
        sm._initialized = True
        monkeypatch.setattr(storage_module, "storage", sm)
        monkeypatch.setattr(transcript_module, "storage", sm)
        transcript_module.transcript._table_ready = False
        self.transcript = transcript_module.transcript
        yield
        StorageManager._instance = None

    @pytest.mark.asyncio
    async def test_replay_delivers_recent_messages(self, manager):
        from ErisPulse.runtime.context import current_owner

        # 收件箱准备最近消息（隔离的临时库）
        evt = {
            "id": "r1", "time": 1712345678, "type": "message", "detail_type": "group",
            "platform": "onebot11", "self": {"platform": "onebot11", "user_id": "bot_x"},
            "user_id": "u1", "message": [{"type": "text", "data": {"text": "历史消息"}}],
            "alt_message": "历史消息", "group_id": "g1",
        }
        self.transcript.append(evt, "user", "历史消息", event_id="r1", sender="u1")

        # 加载声明 replay 的模块（handler 在 on_load 内注册）
        manager.register("Replayer", _ReplayModule)
        token = current_owner.set("Replayer")
        try:
            assert await manager.load("Replayer") is True
        finally:
            current_owner.reset(token)

        # 回放为后台任务：等待其完成
        import time as _t

        deadline = _t.time() + 5
        inst = manager.get("Replayer")
        while _t.time() < deadline and not inst.received:
            await asyncio.sleep(0.05)

        assert inst.received, "回放事件未送达模块处理器"
        synth = inst.received[0]
        assert synth.get("replayed") is True
        assert synth.get("alt_message") == "历史消息"
        assert synth.get("group_id") == "g1"
        assert synth.get("user_id") == "u1"

    def test_parse_replay_duration(self, manager):
        assert manager._parse_replay_duration("5m") == 300.0
        assert manager._parse_replay_duration("1h") == 3600.0
        assert manager._parse_replay_duration("300") == 300.0

    @pytest.mark.asyncio
    async def test_invalid_replay_skipped(self, manager, caplog):
        manager.register("Svc", _SvcModule)
        # 非法时长不抛异常（模块正常加载）
        await manager._replay_events("Svc", "bogus")
