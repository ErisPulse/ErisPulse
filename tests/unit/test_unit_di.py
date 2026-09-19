"""
依赖注入（Depends）单元测试

测试统一依赖注入：Depends 声明提取（注册期 fail-fast）、分发期解析
（同步/异步依赖、异常传播、上下文传递），以及命令 / 事件 / 生命周期
三个注入点的端到端注入与向后兼容（不声明 Depends 的处理器行为不变）。
"""

import asyncio
import importlib
from unittest.mock import AsyncMock, patch

import pytest

from ErisPulse.Core.di import (
    Depends,
    call_with_depends,
    call_with_depends_sync,
    extract_depends,
    resolve_depends,
)
from ErisPulse.Core.Event.base import BaseEventHandler
from ErisPulse.Core.Event.command import command as command_handler
from ErisPulse.Core.lifecycle import lifecycle

config_module = importlib.import_module("ErisPulse.Core.config")


@pytest.fixture(autouse=True)
def clean_state():
    from ErisPulse.Core.adapter import adapter
    from ErisPulse.Core.Event import _clear_all_handlers
    from ErisPulse.Core.Event.message import message as message_handler

    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()
    yield
    _clear_all_handlers()
    command_handler.commands.clear()
    command_handler.aliases.clear()
    command_handler.groups.clear()
    command_handler.permissions.clear()
    command_handler._max_name_tokens = 1
    command_handler.block = True
    message_handler.handler.handlers.clear()
    message_handler.handler._handler_map.clear()
    adapter._onebot_handlers.clear()
    adapter._raw_handlers.clear()
    adapter._onebot_middlewares.clear()
    adapter._bots.clear()


def _msg(text="hello"):
    return {
        "id": f"id_{abs(hash(text))}",
        "time": 1712345678,
        "type": "message",
        "detail_type": "private",
        "platform": "demo",
        "self": {"platform": "demo", "user_id": "bot_x"},
        "user_id": "u1",
        "message": [{"type": "text", "data": {"text": text}}],
        "alt_message": text,
    }


async def _dispatch(text, **kwargs):
    from ErisPulse.Core.adapter import adapter

    with patch.object(config_module.config, "getConfig", return_value="/"):
        await adapter.emit(_msg(text, **kwargs))
        await asyncio.sleep(0.05)


class TestDependsUnit:
    """Depends 提取与解析单元"""

    def test_extract_basic(self):
        async def get_db(event):
            return "db"

        def handler(event, db=Depends(get_db), other=1):
            return db

        result = extract_depends(handler)
        assert list(result) == ["db"]
        assert result["db"].dependency is get_db

    def test_extract_empty(self):
        def handler(event, other=1):
            return other

        assert extract_depends(handler) == {}

    def test_extract_not_callable_raises(self):
        def handler(event, db=Depends("not_callable")):
            return db

        with pytest.raises(ValueError):
            extract_depends(handler)

    def test_extract_no_signature(self):
        assert extract_depends(print) == {}

    @pytest.mark.asyncio
    async def test_resolve_sync_and_async(self):
        calls = []

        def sync_dep(ctx):
            calls.append(("sync", ctx))
            return "s"

        async def async_dep(ctx):
            calls.append(("async", ctx))
            return "a"

        depends = {"d1": Depends(sync_dep), "d2": Depends(async_dep)}
        kwargs = await resolve_depends(depends, "CTX")
        assert kwargs == {"d1": "s", "d2": "a"}
        assert calls == [("sync", "CTX"), ("async", "CTX")]

    @pytest.mark.asyncio
    async def test_resolve_propagates_exception(self):
        async def bad_dep(ctx):
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await resolve_depends({"d": Depends(bad_dep)}, None)

    @pytest.mark.asyncio
    async def test_depends_module_sugar(self):
        """Depends.module 语法糖：等价于依赖函数内 sdk.module.call"""
        from ErisPulse.Core.module import module as module_manager

        dep = Depends.module("DB", "get_session", timeout=3)
        assert isinstance(dep, Depends)

        fake_call = AsyncMock(return_value="CONN")
        with patch.object(module_manager, "call", new=fake_call):
            kwargs = await resolve_depends({"db": dep}, "CTX")
        fake_call.assert_awaited_once_with("DB", "get_session", timeout=3)
        assert kwargs == {"db": "CONN"}

    @pytest.mark.asyncio
    async def test_call_with_depends_load_unload(self):
        """模块生命周期方法（on_load/on_unload）的 Depends 注入"""
        from ErisPulse.Core.Bases.module import BaseModule

        calls = []

        class Mod(BaseModule):
            async def on_load(self, event, session=Depends(lambda ev: "S1")):
                calls.append(("load", event["module_name"], session))
                return True

            async def on_unload(self, event, session=Depends(lambda ev: "S1")):
                calls.append(("unload", event["module_name"], session))
                return True

        m = Mod()
        assert await call_with_depends(m.on_load, {"module_name": "M"}) is True
        assert await call_with_depends(m.on_unload, {"module_name": "M"}) is True
        assert calls == [("load", "M", "S1"), ("unload", "M", "S1")]

    @pytest.mark.asyncio
    async def test_call_with_depends_sync_method(self):
        from ErisPulse.Core.Bases.module import BaseModule

        calls = []

        class Mod(BaseModule):
            def on_load(self, event):  # 同步方法（兼容形态）
                calls.append(event["module_name"])

            def on_unload(self, event):
                pass

        m = Mod()
        await call_with_depends(m.on_load, {"module_name": "M2"})
        assert calls == ["M2"]

    def test_call_with_depends_sync_ctx(self):
        """同步上下文版本：同步依赖正常注入；异步依赖抛 TypeError"""
        from ErisPulse.Core.Bases.module import BaseModule

        calls = []

        def sync_dep(ev):
            return "s"

        async def async_dep(ev):
            return "a"

        class Mod(BaseModule):
            def on_load(self, event, v=Depends(sync_dep)):
                calls.append(("sync", v, event["module_name"]))

            def on_load_bad(self, event, v=Depends(async_dep)):
                calls.append(("bad", v))

            def on_unload(self, event):
                pass

        m = Mod()
        call_with_depends_sync(m.on_load, {"module_name": "M3"})
        assert calls == [("sync", "s", "M3")]

        with pytest.raises(TypeError):
            call_with_depends_sync(m.on_load_bad, {"module_name": "M3"})


class TestCommandInjection:
    """命令处理器依赖注入"""

    @pytest.mark.asyncio
    async def test_depends_injected_into_command(self):
        calls = []

        async def get_session(event):
            calls.append(event)
            return "SESSION"

        @command_handler("admin", args="<target:str>")
        async def admin(event, target: str, db=Depends(get_session)):
            calls.append((target, db))

        await _dispatch("/admin boss")
        assert calls[1] == ("boss", "SESSION")
        assert calls[0].get_command_args() == ["boss"]  # 上下文为 Event 本体

    @pytest.mark.asyncio
    async def test_depends_conflict_raises(self):
        async def get_target(event):
            return "x"

        with pytest.raises(ValueError):

            @command_handler("broken2", args="<target:str>")
            async def broken(event, target: str = Depends(get_target)):
                pass

    @pytest.mark.asyncio
    async def test_dep_exception_replies_error(self):
        async def bad_dep(event):
            raise RuntimeError("dep-boom")

        calls = []

        @command_handler("admin2")
        async def admin(event, db=Depends(bad_dep)):
            calls.append(db)

        errors = []
        with patch.object(
            command_handler, "_send_command_error", new=AsyncMock(side_effect=lambda e, err: errors.append(err))
        ):
            await _dispatch("/admin2")

        assert calls == []
        assert any("dep-boom" in str(e) for e in errors)


class TestEventInjection:
    """事件处理器依赖注入（BaseEventHandler 全事件类型统一入口）"""

    @pytest.mark.asyncio
    async def test_depends_injected_into_event_handler(self):
        from ErisPulse.Core.adapter import adapter

        seen = []

        def get_platform(event):
            return event.get("platform")

        holder = BaseEventHandler("message")

        async def on_msg(event, platform=Depends(get_platform)):
            seen.append(platform)

        holder.register(on_msg)
        try:
            await adapter.emit(_msg("evt"))
            await asyncio.sleep(0.05)
        finally:
            holder.unregister(on_msg)
        assert seen == ["demo"]

    @pytest.mark.asyncio
    async def test_no_depends_backward_compat(self):
        from ErisPulse.Core.adapter import adapter

        seen = []
        holder = BaseEventHandler("message")

        async def plain(event):
            seen.append(event.get("alt_message"))

        holder.register(plain)
        try:
            await adapter.emit(_msg("plain"))
            await asyncio.sleep(0.05)
        finally:
            holder.unregister(plain)
        assert seen == ["plain"]


class TestLifecycleInjection:
    """生命周期钩子依赖注入"""

    @pytest.mark.asyncio
    async def test_depends_injected_into_hook(self):
        seen = []

        def get_tag(data):
            return data.get("tag")

        async def on_event(data, tag=Depends(get_tag)):
            seen.append((data["tag"], tag))

        lifecycle.register("di.test.hook", on_event)
        try:
            await lifecycle.emit("di.test.hook", {"tag": "T1"})
        finally:
            lifecycle.unregister("di.test.hook", on_event)
        assert seen == [("T1", "T1")]

    @pytest.mark.asyncio
    async def test_sync_hook_sync_dep(self):
        seen = []

        def get_tag(data):
            return data.get("tag")

        def sync_hook(data, tag=Depends(get_tag)):
            seen.append(tag)

        lifecycle.register("di.test.sync", sync_hook)
        try:
            await lifecycle.emit("di.test.sync", {"tag": "S1"})
        finally:
            lifecycle.unregister("di.test.sync", sync_hook)
        assert seen == ["S1"]

    @pytest.mark.asyncio
    async def test_sync_ctx_skips_async_dep(self, caplog):
        """同步执行路径遇到异步依赖 → 记错误日志并跳过处理器"""
        import logging

        seen = []

        async def async_dep(data):
            return "x"

        def sync_hook(data, v=Depends(async_dep)):
            seen.append(v)

        lifecycle.register("di.test.skip", sync_hook)
        try:
            with caplog.at_level(logging.ERROR):
                result = lifecycle.emit_sync("di.test.skip", {"tag": 1})
            assert result == {"tag": 1}
        finally:
            lifecycle.unregister("di.test.skip", sync_hook)
        assert seen == []

    def test_unregister_owner_cleans_depends(self):
        """unregister_by_owner 四元组过滤不残留"""
        from ErisPulse.runtime.context import current_owner

        async def hook(data, **kwargs):
            return None

        token = current_owner.set("OwnerX")
        try:
            lifecycle.register("di.test.owner", hook)
        finally:
            current_owner.reset(token)
        assert lifecycle.unregister_by_owner("OwnerX") >= 1
        assert all(o != "OwnerX" for _, _, o, _ in lifecycle._hooks.get("di.test.owner", []))


# ==================== 请求级缓存（use_cache，2.9.0）====================


class TestRequestScopedCache:
    """请求级依赖缓存：同一次事件分发内相同依赖只解析一次"""

    @pytest.fixture
    def di_scope(self):
        from ErisPulse.Core.di import _di_cache

        token = _di_cache.set({})
        yield _di_cache.get()
        _di_cache.reset(token)

    @pytest.mark.asyncio
    async def test_same_dependency_resolved_once(self, di_scope):
        calls = []

        async def get_db(ctx):
            calls.append(ctx)
            return "CONN"

        depends = {"a": Depends(get_db), "b": Depends(get_db)}
        kw = await resolve_depends(depends, "CTX")
        assert kw == {"a": "CONN", "b": "CONN"}
        assert calls == ["CTX"]  # 只解析一次

    @pytest.mark.asyncio
    async def test_cache_scoped_to_request(self, monkeypatch):
        """缓存作用域为单次请求：跨请求不复用（每次请求新的缓存 dict）"""
        from ErisPulse.Core.di import _di_cache

        calls = []

        async def get_db(ctx):
            calls.append(ctx)
            return f"conn-{len(calls)}"

        depends = {"db": Depends(get_db)}

        # 请求 1
        token = _di_cache.set({})
        try:
            kw1 = await resolve_depends(depends, "req1")
        finally:
            _di_cache.reset(token)
        # 请求 2（新的缓存作用域）
        token = _di_cache.set({})
        try:
            kw2 = await resolve_depends(depends, "req2")
        finally:
            _di_cache.reset(token)

        assert kw1["db"] == "conn-1"
        assert kw2["db"] == "conn-2"  # 跨请求重新解析
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_use_cache_false_resolves_each_time(self, di_scope):
        calls = []

        async def fresh(ctx):
            calls.append(1)
            return len(calls)

        depends = {"a": Depends(fresh, use_cache=False), "b": Depends(fresh, use_cache=False)}
        kw = await resolve_depends(depends, None)
        assert kw == {"a": 1, "b": 2}  # use_cache=False 每次都解析

    @pytest.mark.asyncio
    async def test_no_cache_scope_unchanged(self):
        """不在缓存作用域内（lifecycle / 路由独立调用链）→ 每次解析（原行为）"""
        calls = []

        async def get_db(ctx):
            calls.append(1)
            return "x"

        depends = {"a": Depends(get_db), "b": Depends(get_db)}
        kw = await resolve_depends(depends, None)
        assert kw == {"a": "x", "b": "x"}
        assert len(calls) == 2

    @pytest.mark.asyncio
    async def test_module_sugar_shared_cache(self, di_scope):
        """Depends.module 语法糖：同一模块调用的多次声明共享请求级缓存（稳定 cache_key）"""
        from ErisPulse.Core.module import module as module_manager

        fake_call = AsyncMock(return_value="S1")
        depends = {"a": Depends.module("DB", "get_session"), "b": Depends.module("DB", "get_session")}

        with patch.object(module_manager, "call", new=fake_call):
            kw = await resolve_depends(depends, None)
        assert kw == {"a": "S1", "b": "S1"}
        assert fake_call.await_count == 1  # 稳定 cache_key：只调用一次

    @pytest.mark.asyncio
    async def test_module_sugar_distinct_args_not_shared(self, di_scope):
        """不同固定参数的模块声明不共享缓存"""
        from ErisPulse.Core.module import module as module_manager

        fake_call = AsyncMock(side_effect=["A", "B"])
        depends = {
            "a": Depends.module("KV", "get", "name"),
            "b": Depends.module("KV", "get", "other"),
        }

        with patch.object(module_manager, "call", new=fake_call):
            kw = await resolve_depends(depends, None)
        assert kw == {"a": "A", "b": "B"}
        assert fake_call.await_count == 2


    @pytest.mark.asyncio
    async def test_emit_level_cache_scope(self):
        """真链路：同一次 emit 内多个处理器共享缓存；跨 emit 隔离"""
        from ErisPulse.Core.Event.command import command as command_handler

        calls = []

        async def get_db(ctx):
            calls.append(1)
            return "CONN"

        first = []

        @command_handler("dia")
        async def dia(event, db=Depends(get_db)):
            first.append(db)

        await _dispatch("/dia")
        assert first == ["CONN"] and len(calls) == 1  # 单请求单解析

        await _dispatch("/dia")  # 第二次 emit：新请求作用域
        assert len(calls) == 2
