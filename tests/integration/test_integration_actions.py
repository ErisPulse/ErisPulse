"""
出站动作权限（scope.actions）端到端测试

以真实 SendDSL / ApiDSL / RequestDSL + scope 控制面 + owner 上下文协作，
验证模块在事件 handler 执行期（owner 已注入）发起出站调用时被 scope.actions 拦截：

- send：Send DSL（Event.reply 底层同路径）
- api：Api DSL / call 逃生舱
- request：Request DSL accept/reject
- provider：owner 上下文注册的主人身源在模块卸载时自动清理
"""

import pytest

from ErisPulse.Core.Bases import BaseAdapter, BaseModule
from ErisPulse.Core.constants import RETCODE_PERMISSION_DENIED
from ErisPulse.Core.master import master
from ErisPulse.Core.module import ModuleManager
from ErisPulse.Core.scope import scope
from ErisPulse.runtime.context import owner_scope


@pytest.fixture
def isolated_scope():
    """隔离全局 scope 单例配置，测试后恢复"""
    saved = {key: dict(value) if isinstance(value, dict) else value for key, value in scope._bindings.items()}
    yield scope
    scope._bindings.clear()
    scope._bindings.update(saved)
    scope._invalidate_cache()


@pytest.fixture
def reset_master():
    master.reset()
    yield
    master.reset()


def _make_adapter_instance() -> BaseAdapter:
    """构造一个真实 BaseAdapter 子类实例（含 Send/Request/Api DSL）"""

    class FlatAdapter(BaseAdapter):
        async def call_api(self, endpoint: str, **params):
            return {"status": "ok", "retcode": 0, "endpoint": endpoint, **params}

        async def start(self):
            return None

        async def shutdown(self):
            return None

    return FlatAdapter()


@pytest.mark.asyncio
class TestSendActionGate:
    """Send DSL 发送授权"""

    async def test_send_allowed_in_owner_context(self, isolated_scope, reset_master):
        """owner 上下文内默认允许发送（非权限拒绝响应）"""
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Send.To("user", "123").Text("hello")
        assert result.get("retcode") != RETCODE_PERMISSION_DENIED

    async def test_send_denied_when_action_disabled(self, isolated_scope, reset_master):
        """scope 禁用 send 后，owner 上下文内的发送被拒绝"""
        isolated_scope.set_action("MyModule", "send", False, persist=False)
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Send.To("user", "123").Text("hello")
        assert result.get("retcode") == RETCODE_PERMISSION_DENIED

    async def test_send_allowed_without_owner(self, isolated_scope, reset_master):
        """owner 为空（框架层调用）时不受模块级限制"""
        isolated_scope.set_action("MyModule", "send", False, persist=False)
        adapter_inst = _make_adapter_instance()
        result = await adapter_inst.Send.To("user", "123").Text("hello")
        assert result.get("retcode") != RETCODE_PERMISSION_DENIED


@pytest.mark.asyncio
class TestApiActionGate:
    """Api DSL 授权"""

    async def test_api_denied_when_action_disabled(self, isolated_scope, reset_master):
        """scope 禁用 api 后，owner 上下文内的标准 API 调用被拒绝"""
        isolated_scope.set_action("MyModule", "api", False, persist=False)
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Api.get_user_info("123")
        assert result.get("retcode") == RETCODE_PERMISSION_DENIED

    async def test_api_allowed_by_default(self, isolated_scope, reset_master):
        """owner 上下文内默认允许 API 调用"""
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Api.get_self_info()
        assert result.get("retcode") != RETCODE_PERMISSION_DENIED
        assert result.get("endpoint") == "get_self_info"

    async def test_api_call_escape_hatch_denied(self, isolated_scope, reset_master):
        """call() 逃生舱同样受 api 限制"""
        isolated_scope.set_action("MyModule", "api", False, persist=False)
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Api.call("custom.action", foo="bar")
        assert result.get("retcode") == RETCODE_PERMISSION_DENIED


@pytest.mark.asyncio
class TestRequestActionGate:
    """Request DSL 授权"""

    async def test_request_denied_when_action_disabled(self, isolated_scope, reset_master):
        """scope 禁用 request 后，owner 上下文内的 accept 被拒绝"""
        isolated_scope.set_action("MyModule", "request", False, persist=False)
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Request("req_1").accept()
        assert result.get("retcode") == RETCODE_PERMISSION_DENIED

    async def test_request_allowed_by_default(self, isolated_scope, reset_master):
        """owner 上下文内默认允许 request"""
        adapter_inst = _make_adapter_instance()
        with owner_scope("MyModule"):
            result = await adapter_inst.Request("req_1").accept()
        assert result.get("retcode") != RETCODE_PERMISSION_DENIED


class TestProviderOwnerCleanup:
    """provider owner 作用域自动清理（模块卸载场景）"""

    @pytest.mark.asyncio
    async def test_provider_auto_unregistered_on_module_unload(self, isolated_scope, reset_master):
        """模块加载上下文注册的 provider 在卸载时自动注销"""

        class ProviderModule(BaseModule):
            async def on_load(self, event=None):
                def p(platform, user_id):
                    return user_id == "owner_vip"

                master.provider(p)
                return True

            async def on_unload(self, event=None):
                return True

        mgr = ModuleManager()
        mgr._modules.clear()
        mgr._module_classes.clear()
        mgr._loaded_modules.clear()
        mgr._module_info.clear()

        mgr.register("ProviderModule", ProviderModule, {"meta": {"name": "ProviderModule"}})
        assert await mgr.load("ProviderModule") is True
        assert master.is_master("p", "owner_vip") is True

        assert await mgr.unload("ProviderModule") is True
        assert master.is_master("p", "owner_vip") is False
