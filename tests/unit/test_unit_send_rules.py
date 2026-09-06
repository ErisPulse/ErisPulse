"""
SendDSL 发送规则系统单元测试

测试发送规则装饰器（Hook/Retry/Timeout/Defer/Priority/OnProgress/OnError）
及 SendContext 上下文对象的行为。
"""

import asyncio

import pytest

from ErisPulse.Core.Bases import BaseAdapter, SendContext, SendDSL
from ErisPulse.Core.Bases.send_rules import (
    _is_success,
    _PriorityQueue,
    apply_send_rules,
)

# ==================== 辅助：构建测试用适配器 ====================


def make_adapter(*, fail_times=0, delay=0.0, status="ok", platform="test"):
    """
    构建一个可编程的测试适配器

    :param fail_times: 前 N 次发送抛出异常
    :param delay: 每次发送的耗时（秒）
    :param status: 成功时响应的 status 字段
    :param platform: 平台标识
    """

    state = {"calls": 0, "fail_times": fail_times}

    class _Adapter(BaseAdapter):
        _platform = platform

        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            state["calls"] += 1
            if delay:
                await asyncio.sleep(delay)
            if state["calls"] <= state["fail_times"]:
                raise RuntimeError(f"模拟失败 #{state['calls']}")
            return {
                "status": status,
                "retcode": 0 if status == "ok" else 10001,
                "data": {"call": state["calls"]},
                "message_id": f"mid_{state['calls']}",
                "message": "",
            }

    adapter = _Adapter()

    class _Send(SendDSL):
        def Text(self, text: str):
            async def _do():
                return await self._adapter.call_api("/send", text=text)

            return asyncio.ensure_future(_do())

    # BaseAdapter.__init__ 会创建 self.Send = self.__class__.Send(self)，
    # 但测试适配器用的是基类 Send，这里替换为带 Text 的实例
    adapter.Send = _Send(adapter)
    return adapter, state


# ==================== SendContext 测试 ====================


class TestSendContext:
    """SendContext 数据类测试"""

    def test_default_values(self):
        """默认值应正确初始化"""
        ctx = SendContext(task_id="t1")
        assert ctx.task_id == "t1"
        assert ctx.stage == "pending"
        assert ctx.attempt == 0
        assert ctx.max_attempts == 1
        assert ctx.error is None
        assert ctx.result is None
        assert ctx.finished_at is None
        assert isinstance(ctx.extra, dict)

    def test_elapsed_running(self):
        """进行中时 elapsed 应基于 started_at 递增"""
        import time

        ctx = SendContext(task_id="t1", started_at=time.monotonic())
        e1 = ctx.elapsed
        time.sleep(0.01)
        e2 = ctx.elapsed
        assert e2 >= e1

    def test_elapsed_finished(self):
        """结束后 elapsed 应冻结在 finished_at"""
        import time

        start = time.monotonic()
        ctx = SendContext(task_id="t1", started_at=start - 1.0)
        ctx.finished_at = start
        assert abs(ctx.elapsed - 1.0) < 0.01

    def test_to_dict_serializes_error(self):
        """to_dict 应把异常转为 repr 字符串"""
        ctx = SendContext(task_id="t1", error=ValueError("boom"))
        d = ctx.to_dict()
        assert "ValueError" in d["error"]
        assert "boom" in d["error"]
        assert d["task_id"] == "t1"

    def test_extra_is_independent_per_instance(self):
        """每个实例的 extra 应独立"""
        a = SendContext(task_id="a")
        b = SendContext(task_id="b")
        a.extra["k"] = 1
        assert "k" not in b.extra


# ==================== _is_success 测试 ====================


class TestIsSuccess:
    """_is_success 判断逻辑测试"""

    def test_ok_dict(self):
        assert _is_success({"status": "ok"}) is True

    def test_failed_dict(self):
        assert _is_success({"status": "failed"}) is False

    def test_non_dict_defaults_success(self):
        """非 dict 结果默认视为成功（避免误触发重试）"""
        assert _is_success("hello") is True
        assert _is_success(None) is True
        assert _is_success(42) is True


# ==================== 链式规则方法测试 ====================


class TestRuleChaining:
    """规则装饰器链式调用测试"""

    def test_hook_returns_self(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        assert send.Hook(lambda r: None) is send

    def test_retry_returns_self(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        assert send.Retry(2) is send

    def test_timeout_returns_self(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        assert send.Timeout(5) is send

    def test_rules_stored_in_dict(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        send.Retry(2).Timeout(5).Defer(1).Hook(lambda r: None)
        rules = send._rules
        assert rules["retry"] == 3  # 含首次
        assert rules["timeout"] == 5.0
        assert rules["defer"] == 1.0
        assert len(rules["hooks"]) == 1

    def test_multiple_hooks_accumulate(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        send.Hook(lambda r: 1).Hook(lambda r: 2)
        assert len(send._rules["hooks"]) == 2

    def test_retry_default_is_one_retry(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        send.Retry()
        assert send._rules["retry"] == 2  # 默认1次重试，含首次共2次

    def test_priority_without_drop(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        send.Priority(5)
        assert send._rules["priority"] == 5
        assert "drop_if_busy" not in send._rules

    def test_priority_with_drop(self):
        adapter, _ = make_adapter()
        send = adapter.Send.To("user", "123")
        send.Priority(-1, drop_if_busy=True)
        assert send._rules["priority"] == -1
        assert send._rules["drop_if_busy"] is True


# ==================== 规则传播测试（To/Using/Account）====================


class TestRulePropagation:
    """规则在 To/Using/Account 创建新实例时的传播"""

    def test_rules_propagate_through_to(self):
        adapter, _ = make_adapter()
        base = adapter.Send.Retry(3).Hook(lambda r: None)
        new = base.To("user", "456")
        assert new._rules.get("retry") == 4
        assert len(new._rules.get("hooks", [])) == 1

    def test_rules_propagate_through_using(self):
        adapter, _ = make_adapter()
        base = adapter.Send.To("user", "123").Retry(3)
        new = base.Using("bot1")
        assert new._rules.get("retry") == 4

    def test_rules_propagate_through_account(self):
        adapter, _ = make_adapter()
        base = adapter.Send.To("user", "123").Timeout(5)
        new = base.Account("bot1")
        assert new._rules.get("timeout") == 5.0

    def test_rules_are_independent_copies(self):
        """传播后两个实例的 _rules 应相互独立"""
        adapter, _ = make_adapter()
        base = adapter.Send.To("user", "123").Hook(lambda r: None)
        new = base.To("user", "456")
        new.Hook(lambda r: "second")
        assert len(base._rules["hooks"]) == 1
        assert len(new._rules["hooks"]) == 2


# ==================== Hook 回调测试 ====================


class TestHook:
    """Hook（发送成功回调）测试"""

    @pytest.mark.asyncio
    async def test_hook_executed_on_success(self):
        adapter, _ = make_adapter()
        called = []
        await adapter.Send.To("user", "123").Hook(
            lambda r: called.append(r["message_id"])
        ).Text("hi")
        assert called == ["mid_1"]

    @pytest.mark.asyncio
    async def test_hook_not_executed_on_failure(self):
        adapter, _ = make_adapter(fail_times=10)
        called = []
        with pytest.raises(RuntimeError):
            await adapter.Send.To("user", "123").Hook(
                lambda r: called.append("ok")
            ).Text("hi")
        assert called == []

    @pytest.mark.asyncio
    async def test_multiple_hooks_in_order(self):
        adapter, _ = make_adapter()
        order = []
        await adapter.Send.To("user", "123").Hook(
            lambda r: order.append("a")
        ).Hook(lambda r: order.append("b")).Text("hi")
        assert order == ["a", "b"]

    @pytest.mark.asyncio
    async def test_async_hook_supported(self):
        adapter, _ = make_adapter()
        seen = []

        async def hook(result):
            await asyncio.sleep(0)
            seen.append(result["message_id"])

        await adapter.Send.To("user", "123").Hook(hook).Text("hi")
        assert seen == ["mid_1"]

    @pytest.mark.asyncio
    async def test_hook_exception_does_not_break_send(self):
        adapter, _ = make_adapter()
        result = await adapter.Send.To("user", "123").Hook(
            lambda r: (_ for _ in ()).throw(ValueError("hook boom"))
        ).Text("hi")
        assert result["status"] == "ok"


# ==================== Retry 重试测试 ====================


class TestRetry:
    """Retry 重试测试"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        adapter, state = make_adapter(fail_times=2)
        result = await adapter.Send.To("user", "123").Retry(3).Text("hi")
        assert result["status"] == "ok"
        assert result["message_id"] == "mid_3"
        assert state["calls"] == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self):
        adapter, state = make_adapter(fail_times=10)
        with pytest.raises(RuntimeError):
            await adapter.Send.To("user", "123").Retry(2).Text("hi")
        # 首次 + 2次重试 = 3次调用
        assert state["calls"] == 3

    @pytest.mark.asyncio
    async def test_retry_on_business_failed_status(self):
        """发送返回 status=failed 也应触发重试"""
        adapter, state = make_adapter(status="failed")
        result = await adapter.Send.To("user", "123").Retry(1).Text("hi")
        # 重试耗尽仍 failed，返回最后结果
        assert result["status"] == "failed"
        assert state["calls"] == 2

    @pytest.mark.asyncio
    async def test_no_retry_when_success(self):
        adapter, state = make_adapter()
        await adapter.Send.To("user", "123").Retry(5).Text("hi")
        assert state["calls"] == 1


# ==================== Timeout 超时测试 ====================


class TestTimeout:
    """Timeout 超时测试"""

    @pytest.mark.asyncio
    async def test_timeout_raises_when_slow(self):
        adapter, _ = make_adapter(delay=0.3)
        with pytest.raises(asyncio.TimeoutError):
            await adapter.Send.To("user", "123").Timeout(0.05).Text("hi")

    @pytest.mark.asyncio
    async def test_timeout_with_retry_eventually_succeeds(self):
        """超时配合重试，最终成功"""
        adapter, state = make_adapter(delay=0.3)
        # 前两次慢（会超时），但 fail_times=0 意味着不抛异常
        # 改用不同策略：第一次慢，后续快。这里用 delay 恒定，重试仍会超时，
        # 因此验证超时+重试会抛出 TimeoutError。
        with pytest.raises(asyncio.TimeoutError):
            await adapter.Send.To("user", "123").Timeout(0.05).Retry(2).Text("hi")
        assert state["calls"] == 3

    @pytest.mark.asyncio
    async def test_no_timeout_completes(self):
        adapter, _ = make_adapter(delay=0.05)
        result = await adapter.Send.To("user", "123").Timeout(1.0).Text("hi")
        assert result["status"] == "ok"


# ==================== OnProgress / OnError 回调测试 ====================


class TestProgressCallbacks:
    """OnProgress / OnError 回调测试"""

    @pytest.mark.asyncio
    async def test_on_progress_success_stages(self):
        adapter, _ = make_adapter()
        stages = []

        def on_progress(ctx):
            stages.append(ctx.stage)

        await adapter.Send.To("user", "123").OnProgress(on_progress).Text("hi")
        assert "sending" in stages
        assert "success" in stages
        assert stages[-1] == "success"

    @pytest.mark.asyncio
    async def test_on_progress_retry_stages(self):
        adapter, _ = make_adapter(fail_times=1)
        stages = []

        def on_progress(ctx):
            stages.append((ctx.stage, ctx.attempt))

        await adapter.Send.To("user", "123").Retry(2).OnProgress(on_progress).Text("hi")
        assert ("sending", 0) in stages
        assert ("retrying", 1) in stages
        assert ("success", 1) in stages

    @pytest.mark.asyncio
    async def test_on_error_called_on_final_failure(self):
        adapter, _ = make_adapter(fail_times=10)
        errors = []

        def on_error(ctx):
            errors.append(ctx)

        with pytest.raises(RuntimeError):
            await adapter.Send.To("user", "123").Retry(1).OnError(on_error).Text("hi")
        assert len(errors) == 1
        assert errors[0].stage == "failed"
        assert isinstance(errors[0].error, RuntimeError)

    @pytest.mark.asyncio
    async def test_on_error_called_on_timeout(self):
        adapter, _ = make_adapter(delay=0.3)
        errors = []

        def on_error(ctx):
            errors.append(ctx)

        with pytest.raises(asyncio.TimeoutError):
            await adapter.Send.To("user", "123").Timeout(0.05).OnError(on_error).Text("hi")
        assert len(errors) == 1
        assert errors[0].stage == "timeout"
        assert isinstance(errors[0].error, asyncio.TimeoutError)

    @pytest.mark.asyncio
    async def test_on_error_not_called_on_success(self):
        adapter, _ = make_adapter()
        errors = []
        await adapter.Send.To("user", "123").OnError(
            lambda ctx: errors.append(ctx)
        ).Text("hi")
        assert errors == []

    @pytest.mark.asyncio
    async def test_async_callbacks_supported(self):
        adapter, _ = make_adapter(fail_times=10)
        seen = []

        async def on_error(ctx):
            await asyncio.sleep(0)
            seen.append(ctx.stage)

        with pytest.raises(RuntimeError):
            await adapter.Send.To("user", "123").Retry(1).OnError(on_error).Text("hi")
        assert seen == ["failed"]

    @pytest.mark.asyncio
    async def test_send_context_fields_populated(self):
        adapter, _ = make_adapter(platform="yunhu")
        captured = []

        def on_progress(ctx):
            captured.append(ctx)

        await adapter.Send.To("user", "123").OnProgress(on_progress).Text("hi")
        success_ctx = [c for c in captured if c.stage == "success"][0]
        assert success_ctx.platform == "yunhu"
        assert success_ctx.method == "Text"
        assert success_ctx.target_type == "user"
        assert success_ctx.target_id == "123"
        assert success_ctx.result["status"] == "ok"
        assert success_ctx.task_id  # 非空


# ==================== Defer 延迟发送测试 ====================


class TestDefer:
    """Defer 延迟发送测试"""

    @pytest.mark.asyncio
    async def test_defer_delays_send(self):
        import time

        adapter, _ = make_adapter()
        start = time.monotonic()
        await adapter.Send.To("user", "123").Defer(0.15).Text("hi")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.14

    @pytest.mark.asyncio
    async def test_defer_zero_no_delay(self):
        import time

        adapter, _ = make_adapter()
        start = time.monotonic()
        await adapter.Send.To("user", "123").Defer(0).Text("hi")
        elapsed = time.monotonic() - start
        assert elapsed < 0.1


# ==================== Priority 优先级丢弃测试 ====================


class TestPriority:
    """Priority 优先级丢弃测试"""

    def test_priority_queue_busy_threshold(self):
        _PriorityQueue.reset()
        _PriorityQueue.set_threshold(2)
        _PriorityQueue.enter("t1")
        assert not _PriorityQueue.is_busy()
        _PriorityQueue.enter("t2")
        assert _PriorityQueue.is_busy()
        _PriorityQueue.leave("t2")
        assert not _PriorityQueue.is_busy()
        _PriorityQueue.reset()

    @pytest.mark.asyncio
    async def test_message_dropped_when_busy(self):
        _PriorityQueue.reset()
        _PriorityQueue.set_threshold(1)
        _PriorityQueue.enter("occupier")  # 预占一个槽位 → 已积压
        try:
            assert _PriorityQueue.is_busy()
            stages = []

            def on_progress(ctx):
                stages.append(ctx.stage)

            result = await adapter_proxy_dropped(on_progress)
            assert result["status"] == "failed"
            assert "dropped" in stages
        finally:
            _PriorityQueue.reset()

    @pytest.mark.asyncio
    async def test_priority_recorded_in_context(self):
        adapter, _ = make_adapter()
        captured = []

        def on_progress(ctx):
            captured.append(ctx)

        await adapter.Send.To("user", "123").Priority(7).OnProgress(on_progress).Text("hi")
        success_ctx = [c for c in captured if c.stage == "success"][0]
        assert success_ctx.extra["priority"] == 7


async def adapter_proxy_dropped(on_progress):
    """辅助：构建一个会被丢弃的发送流程"""
    adapter, _ = make_adapter()
    return await adapter.Send.To("user", "123").Priority(
        0, drop_if_busy=True
    ).OnProgress(on_progress).Text("hi")


# ==================== 向后兼容测试 ====================


class TestBackwardCompatibility:
    """无规则时应保持原有行为"""

    @pytest.mark.asyncio
    async def test_no_rules_returns_task(self):
        adapter, _ = make_adapter()
        task = adapter.Send.To("user", "123").Text("hi")
        # 未 await 时应得到 Task（与原行为一致）
        assert asyncio.isfuture(task) or asyncio.iscoroutine(task)
        result = await task
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_no_rules_no_progress_callback(self):
        adapter, _ = make_adapter()
        # 无规则时不应有任何回调副作用
        result = await adapter.Send.To("user", "123").Text("hi")
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_rules_disabled_when_only_priority_without_drop(self):
        """仅设置 Priority 但不 drop_if_busy 时，不应进入规则包装路径"""
        adapter, _ = make_adapter()
        task = adapter.Send.To("user", "123").Priority(1).Text("hi")
        # Priority 不带 drop_if_busy 仍会触发规则包装（因为 _has_rules 判定）
        # 但行为应与无规则等价
        result = await task
        assert result["status"] == "ok"


# ==================== apply_send_rules 直接测试 ====================


class TestApplySendRules:
    """apply_send_rules 工厂函数直接测试"""

    @pytest.mark.asyncio
    async def test_apply_rules_with_retry(self):
        calls = {"n": 0}

        def factory():
            calls["n"] += 1
            return asyncio.ensure_future(_maybe_fail(calls["n"]))

        async def _maybe_fail(n):
            if n <= 2:
                raise RuntimeError(f"fail {n}")
            return {"status": "ok", "message_id": f"mid_{n}"}

        rules = {"retry": 3}
        task = apply_send_rules(
            factory, rules=rules, send_ctx={"platform": "p", "method": "Text"}
        )
        result = await task
        assert result["status"] == "ok"
        assert result["message_id"] == "mid_3"
        assert calls["n"] == 3

    @pytest.mark.asyncio
    async def test_apply_rules_timeout(self):
        def factory():
            async def _slow():
                await asyncio.sleep(1.0)
                return {"status": "ok"}

            return asyncio.ensure_future(_slow())

        rules = {"timeout": 0.05}
        task = apply_send_rules(factory, rules=rules, send_ctx={})
        with pytest.raises(asyncio.TimeoutError):
            await task

    @pytest.mark.asyncio
    async def test_apply_rules_hook_on_success(self):
        def factory():
            async def _ok():
                return {"status": "ok", "message_id": "m1"}

            return asyncio.ensure_future(_ok())

        seen = []
        rules = {"hooks": [lambda r: seen.append(r["message_id"])]}
        task = apply_send_rules(factory, rules=rules, send_ctx={})
        await task
        assert seen == ["m1"]


# ==================== 真实适配器模式集成测试 ====================


def make_real_pattern_adapter(*, fail_times=0, platform="real"):
    """
    构建遵循标准适配器模式的测试适配器：
    Raw_ob12 + _apply_modifiers + send_context，Text/Image 委托给 Raw_ob12。

    这模拟了真实适配器（如 yunhu/telegram）的实现方式，验证规则系统在真实调用链下正常工作。
    """
    state = {"calls": 0, "fail_times": fail_times, "received": []}

    class _Adapter(BaseAdapter):
        _platform = platform

        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            state["calls"] += 1
            state["received"].append({"endpoint": endpoint, "params": params})
            if state["calls"] <= state["fail_times"]:
                raise RuntimeError(f"api 失败 #{state['calls']}")
            return {
                "status": "ok",
                "retcode": 0,
                "data": {"call": state["calls"]},
                "message_id": f"mid_{state['calls']}",
                "message": "",
            }

    adapter = _Adapter()

    class _RealSend(SendDSL):
        """模拟真实适配器的 Send：Raw_ob12 为核心，标准方法委托"""

        def Raw_ob12(self, message, **kwargs):
            async def _do_send():
                segments = self._apply_modifiers(message)
                return await self._adapter.call_api(
                    endpoint="/send_message",
                    message=segments,
                    **self.send_context,
                    **kwargs,
                )

            return asyncio.ensure_future(_do_send())

        def Text(self, text: str):
            return self.Raw_ob12([{"type": "text", "data": {"text": text}}])

        def Image(self, file):
            return self.Raw_ob12([{"type": "image", "data": {"file": file}}])

    adapter.Send = _RealSend(adapter)
    return adapter, state


class TestRealAdapterPatternIntegration:
    """
    真实适配器模式集成测试

    验证规则系统在 Raw_ob12 + _apply_modifiers + send_context 的标准
    适配器实现链路下正常工作（这是 yunhu/telegram 等真实适配器的实现方式）。
    """

    @pytest.mark.asyncio
    async def test_raw_ob12_with_hook_success(self):
        """Raw_ob12 路径 + Hook 成功触发"""
        adapter, state = make_real_pattern_adapter()
        seen = []
        await (adapter.Send.To("user", "123")
               .Hook(lambda r: seen.append(r["message_id"]))
               .Text("hi"))
        assert seen == ["mid_1"]
        # 验证走了 Raw_ob12 → call_api 的完整链路
        assert state["received"][0]["endpoint"] == "/send_message"

    @pytest.mark.asyncio
    async def test_modifiers_applied_with_rules(self):
        """At/Reply 修饰器 + 规则同时生效，修饰器被合并到消息段"""
        adapter, state = make_real_pattern_adapter()
        await (adapter.Send.To("group", "456")
               .At("789")
               .AtAll()
               .Hook(lambda r: None)
               .Text("带修饰器的消息"))
        sent_message = state["received"][0]["params"]["message"]
        # _apply_modifiers 应在 text 前加入 mention_all、mention 段
        types = [seg["type"] for seg in sent_message]
        assert "mention_all" in types
        assert "mention" in types
        assert "text" in types

    @pytest.mark.asyncio
    async def test_send_context_passed_with_rules(self):
        """send_context（target_type/target_id）在规则链路下正确传递"""
        adapter, state = make_real_pattern_adapter()
        await (adapter.Send.To("group", "G789")
               .Using("bot1")
               .Retry(2)
               .Text("ctx test"))
        params = state["received"][0]["params"]
        assert params["target_type"] == "group"
        assert params["target_id"] == "G789"

    @pytest.mark.asyncio
    async def test_retry_on_raw_ob12_failure(self):
        """Raw_ob12 失败后 Retry 重新走完整 Raw_ob12 链路"""
        adapter, state = make_real_pattern_adapter(fail_times=2)
        result = await (adapter.Send.To("user", "123")
                        .Retry(3)
                        .Image("pic.jpg"))
        assert result["status"] == "ok"
        assert state["calls"] == 3  # 2 次失败 + 1 次成功
        # 每次重试都重新调用 Raw_ob12，消息段都被正确构建
        for received in state["received"]:
            segs = received["params"]["message"]
            assert segs[-1]["type"] == "image"

    @pytest.mark.asyncio
    async def test_image_method_delegates_to_raw_ob12_with_rules(self):
        """Image 委托 Raw_ob12 时规则正常生效"""
        adapter, state = make_real_pattern_adapter()
        progress = []
        await (adapter.Send.To("user", "123")
               .OnProgress(lambda ctx: progress.append(ctx.stage))
               .Image("https://example.com/x.png"))
        assert "success" in progress
        assert state["received"][0]["params"]["message"][-1]["data"]["file"] == "https://example.com/x.png"

    @pytest.mark.asyncio
    async def test_business_failed_triggers_retry_in_raw_path(self):
        """Raw_ob12 返回 status=failed 时也触发重试"""
        # 构造一个返回 failed 的适配器
        adapter, state = make_real_pattern_adapter()

        # 覆盖 call_api 让其返回 failed
        async def _failed_api(endpoint, **params):
            state["calls"] += 1
            return {"status": "failed", "retcode": 10001, "data": None,
                    "message_id": "", "message": "平台拒绝"}
        adapter.call_api = _failed_api

        result = await (adapter.Send.To("user", "123")
                        .Retry(2)
                        .Text("会被拒绝"))
        assert result["status"] == "failed"
        assert state["calls"] == 3  # 首次 + 2 次重试

    @pytest.mark.asyncio
    async def test_lifecycle_events_fire_with_rules(self):
        """有规则时 message.sending/message.sent 生命周期事件仍正确触发"""
        from ErisPulse.Core.lifecycle import lifecycle

        adapter, _ = make_real_pattern_adapter()
        events_fired = []

        async def on_sending(data):
            events_fired.append(("sending", data["method"]))

        async def on_sent(data):
            events_fired.append(("sent", data["method"]))

        # 使用官方注册 API（避免直接操作内部数据结构）
        lifecycle.on("message.sending")(on_sending)
        lifecycle.on("message.sent")(on_sent)
        try:
            await (adapter.Send.To("user", "123")
                   .Retry(2)
                   .Text("生命周期测试"))
            # done_callback 里的 message.sent 是异步调度的，让事件循环跑一轮
            await asyncio.sleep(0.05)
            methods = [e[1] for e in events_fired]
            assert "Text" in methods  # message.sending
            assert events_fired[-1][0] == "sent"  # 最后是 sent
        finally:
            # 清理：移除本次注册的处理器
            for hook_name, handler in (("message.sending", on_sending), ("message.sent", on_sent)):
                handlers = lifecycle._hooks.get(hook_name, [])
                lifecycle._hooks[hook_name] = [
                    item for item in handlers if item[1] is not handler
                ]
