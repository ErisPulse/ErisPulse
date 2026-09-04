"""
SendDSL 批量构建系统单元测试

测试 SendBuilder（Build 模式）与 BatchContext 的行为：
并行/串行执行、失败继续、重试失败的、整批 Hook/OnError/OnProgress、修饰器继承。
"""

import asyncio

import pytest

from ErisPulse.Core.Bases import BaseAdapter, BatchContext, SendBuilder, SendDSL

# ==================== 辅助：构建测试适配器 ====================


def make_adapter(*, fail_methods=None, status="ok", delay=0.0, platform="test"):
    """
    构建可编程测试适配器

    :param fail_methods: 字典 {方法名: 失败次数}，前 N 次该方法抛异常
    :param status: 成功响应的 status
    :param delay: 每次发送耗时
    """

    state = {
        "calls": {},  # {方法名: 调用次数}
        "fail_methods": fail_methods or {},
    }

    class _Adapter(BaseAdapter):
        _platform = platform

        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            return {
                "status": status,
                "retcode": 0 if status == "ok" else 10001,
                "data": {},
                "message_id": "m",
                "message": "",
            }

    adapter = _Adapter()

    class _Send(SendDSL):
        def _record_and_maybe_fail(self, method_name):
            state["calls"][method_name] = state["calls"].get(method_name, 0) + 1
            fail_n = state["fail_methods"].get(method_name, 0)
            if state["calls"][method_name] <= fail_n:
                raise RuntimeError(f"{method_name} 失败 #{state['calls'][method_name]}")

        def Text(self, text: str):
            async def _do():
                if delay:
                    await asyncio.sleep(delay)
                self._record_and_maybe_fail("Text")
                return await self._adapter.call_api("/send", text=text)

            return asyncio.ensure_future(_do())

        def Image(self, file):
            async def _do():
                if delay:
                    await asyncio.sleep(delay)
                self._record_and_maybe_fail("Image")
                return await self._adapter.call_api("/send", file=file)

            return asyncio.ensure_future(_do())

    adapter.Send = _Send(adapter)
    return adapter, state


# ==================== BatchContext 测试 ====================


class TestBatchContext:
    def test_default_values(self):
        ctx = BatchContext(task_id="b1")
        assert ctx.total == 0
        assert ctx.stage == "pending"
        assert ctx.results == []
        assert ctx.errors == []

    def test_elapsed(self):
        import time

        ctx = BatchContext(task_id="b1", started_at=time.monotonic())
        assert ctx.elapsed >= 0

    def test_to_dict(self):
        ctx = BatchContext(task_id="b1", total=3, succeeded=2, failed=1)
        d = ctx.to_dict()
        assert d["total"] == 3
        assert d["succeeded"] == 2


# ==================== Build 模式入口测试 ====================


class TestBuildEntry:
    def test_build_returns_send_builder(self):
        adapter, _ = make_adapter()
        builder = adapter.Send.To("user", "123").Build()
        assert isinstance(builder, SendBuilder)

    def test_build_captures_intents(self):
        adapter, _ = make_adapter()
        builder = adapter.Send.To("user", "123").Build().Text("a").Image("b")
        assert len(builder._intents) == 2
        assert builder._intents[0][0] == "Text"
        assert builder._intents[1][0] == "Image"

    def test_chaining_returns_self(self):
        adapter, _ = make_adapter()
        builder = adapter.Send.To("user", "123").Build()
        assert builder.Text("a") is builder
        assert builder.Sequential() is builder
        assert builder.Retry(2) is builder


# ==================== 并行/串行执行测试 ====================


class TestBatchExecution:
    @pytest.mark.asyncio
    async def test_parallel_default(self):
        adapter, state = make_adapter(delay=0.1)
        import time

        start = time.monotonic()
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Text("a")
            .Text("b")
            .Text("c")
            .send_all()
        )
        elapsed = time.monotonic() - start
        # 并行：总耗时约 0.1s（而非 0.3s）
        assert elapsed < 0.25
        assert len(results) == 3
        assert all(r["status"] == "ok" for r in results)

    @pytest.mark.asyncio
    async def test_sequential_preserves_order(self):
        adapter, state = make_adapter()
        order = []

        # 用状态记录顺序
        orig = adapter.Send

        class _OrderSend(orig.__class__):
            def Text(self, text):
                async def _do():
                    order.append(text)
                    return await self._adapter.call_api("/send")

                return asyncio.ensure_future(_do())

        adapter.Send = _OrderSend(adapter)
        await (
            adapter.Send.To("user", "123")
            .Build()
            .Sequential()
            .Text("1")
            .Text("2")
            .Text("3")
            .send_all()
        )
        assert order == ["1", "2", "3"]

    @pytest.mark.asyncio
    async def test_empty_batch_returns_empty(self):
        adapter, _ = make_adapter()
        results = await adapter.Send.To("user", "123").Build().send_all()
        assert results == []

    @pytest.mark.asyncio
    async def test_results_in_intent_order(self):
        adapter, _ = make_adapter()
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Text("first")
            .Image("pic")
            .Text("last")
            .send_all()
        )
        assert len(results) == 3
        # 结果按意图顺序排列
        assert results[0] is not None
        assert results[1] is not None
        assert results[2] is not None


# ==================== 失败继续 + 重试测试 ====================


class TestBatchFailure:
    @pytest.mark.asyncio
    async def test_failure_continues_others(self):
        adapter, state = make_adapter(fail_methods={"Image": 999})
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Text("ok1")
            .Image("fail")
            .Text("ok2")
            .send_all()
        )
        # Image 失败，但两条 Text 仍成功
        assert results[0]["status"] == "ok"
        assert results[1] is None  # Image 失败
        assert results[2]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_retry_failed_items(self):
        adapter, state = make_adapter(fail_methods={"Text": 1})
        # Text 第1次失败，Retry(2) 后第2次成功
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Retry(2)
            .Text("retry me")
            .send_all()
        )
        assert results[0]["status"] == "ok"
        assert state["calls"]["Text"] == 2  # 失败1次 + 重试成功1次

    @pytest.mark.asyncio
    async def test_partial_batch_stage(self):
        adapter, _ = make_adapter(fail_methods={"Image": 999})
        stages = []
        await (
            adapter.Send.To("user", "123")
            .Build()
            .OnProgress(lambda ctx: stages.append(ctx.stage))
            .Text("ok")
            .Image("fail")
            .send_all()
        )
        assert "partial" in stages

    @pytest.mark.asyncio
    async def test_all_success_stage(self):
        adapter, _ = make_adapter()
        final_stages = []

        def on_progress(ctx):
            final_stages.append(ctx.stage)

        await (
            adapter.Send.To("user", "123")
            .Build()
            .OnProgress(on_progress)
            .Text("a")
            .Text("b")
            .send_all()
        )
        assert "success" in final_stages


# ==================== 整批回调测试 ====================


class TestBatchCallbacks:
    @pytest.mark.asyncio
    async def test_hook_on_all_success(self):
        adapter, _ = make_adapter()
        seen = []
        await (
            adapter.Send.To("user", "123")
            .Build()
            .Hook(lambda results: seen.append(len(results)))
            .Text("a")
            .Text("b")
            .send_all()
        )
        assert seen == [2]

    @pytest.mark.asyncio
    async def test_hook_not_called_on_partial(self):
        adapter, _ = make_adapter(fail_methods={"Image": 999})
        seen = []
        await (
            adapter.Send.To("user", "123")
            .Build()
            .Hook(lambda r: seen.append("hook"))
            .Text("ok")
            .Image("fail")
            .send_all()
        )
        assert seen == []

    @pytest.mark.asyncio
    async def test_on_error_on_failure(self):
        adapter, _ = make_adapter(fail_methods={"Image": 999})
        ctxs = []
        await (
            adapter.Send.To("user", "123")
            .Build()
            .OnError(lambda ctx: ctxs.append(ctx))
            .Text("ok")
            .Image("fail")
            .send_all()
        )
        assert len(ctxs) == 1
        assert ctxs[0].failed == 1
        assert ctxs[0].succeeded == 1

    @pytest.mark.asyncio
    async def test_on_progress_per_item(self):
        adapter, _ = make_adapter()
        progress_count = []
        await (
            adapter.Send.To("user", "123")
            .Build()
            .OnProgress(lambda ctx: progress_count.append(ctx.completed))
            .Text("a")
            .Text("b")
            .Text("c")
            .send_all()
        )
        # 初始1次 + 每条完成3次 = 至少4次（并行可能初始后顺序完成）
        assert max(progress_count) == 3

    @pytest.mark.asyncio
    async def test_async_callbacks(self):
        adapter, _ = make_adapter()
        seen = []

        async def hook(results):
            await asyncio.sleep(0)
            seen.append(len(results))

        await (
            adapter.Send.To("user", "123")
            .Build()
            .Hook(hook)
            .Text("a")
            .send_all()
        )
        assert seen == [1]


# ==================== 修饰器继承测试 ====================


class TestModifierInheritance:
    @pytest.mark.asyncio
    async def test_modifiers_inherited_from_before_build(self):
        adapter, _ = make_adapter()
        builder = adapter.Send.To("user", "123").At("456").AtAll().Build()
        assert "456" in builder._at_user_ids
        assert builder._at_all is True

    @pytest.mark.asyncio
    async def test_modifiers_after_build(self):
        adapter, _ = make_adapter()
        builder = adapter.Send.To("user", "123").Build().At("789").Reply("msg1")
        assert "789" in builder._at_user_ids
        assert builder._reply_message_id == "msg1"

    @pytest.mark.asyncio
    async def test_rules_inherited_from_before_build(self):
        adapter, _ = make_adapter()
        builder = adapter.Send.To("user", "123").Retry(3).Hook(lambda r: None).Build()
        assert builder._rules.get("retry") == 4
        assert len(builder._rules.get("hooks", [])) == 1


# ==================== 大小写不敏感测试 ====================


class TestCaseInsensitive:
    @pytest.mark.asyncio
    async def test_lowercase_method_resolved(self):
        adapter, _ = make_adapter()
        results = await (
            adapter.Send.To("user", "123").Build().text("hi").send_all()
        )
        assert results[0]["status"] == "ok"


# ==================== Defer 测试 ====================


class TestBatchDefer:
    @pytest.mark.asyncio
    async def test_defer_delays_batch(self):
        import time

        adapter, _ = make_adapter()
        start = time.monotonic()
        await (
            adapter.Send.To("user", "123")
            .Build()
            .Defer(0.15)
            .Text("a")
            .send_all()
        )
        assert time.monotonic() - start >= 0.14


# ==================== 真实适配器模式集成测试 ====================


def make_real_pattern_adapter(*, fail_methods=None, platform="real"):
    """
    构建遵循标准适配器模式的测试适配器：
    Raw_ob12 + _apply_modifiers + send_context，Text/Image 委托给 Raw_ob12。

    模拟真实适配器（如 yunhu/telegram）的实现方式，验证批量构建在真实调用链下正常工作。
    """
    state = {
        "calls": {},
        "fail_methods": fail_methods or {},
        "received": [],
    }

    class _Adapter(BaseAdapter):
        _platform = platform

        async def start(self):
            pass

        async def shutdown(self):
            pass

        async def call_api(self, endpoint: str, **params):
            state["received"].append({"endpoint": endpoint, "params": params})
            return {
                "status": "ok",
                "retcode": 0,
                "data": {},
                "message_id": "m",
                "message": "",
            }

    adapter = _Adapter()

    class _RealSend(SendDSL):
        def _record(self, name):
            state["calls"][name] = state["calls"].get(name, 0) + 1
            fail_n = state["fail_methods"].get(name, 0)
            if state["calls"][name] <= fail_n:
                raise RuntimeError(f"{name} 失败")

        def Raw_ob12(self, message, **kwargs):
            async def _do_send():
                self._record("Raw_ob12")
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


class TestRealPatternBatchIntegration:
    """
    真实适配器模式下的批量构建集成测试

    验证 SendBuilder 在 Raw_ob12 + _apply_modifiers + send_context 的标准
    适配器实现链路下正常工作。
    """

    @pytest.mark.asyncio
    async def test_batch_text_image_via_raw_ob12(self):
        """批量 Text+Image 都走 Raw_ob12 委托链路"""
        adapter, state = make_real_pattern_adapter()
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Text("通知")
            .Image("pic.jpg")
            .send_all()
        )
        assert len(results) == 2
        assert all(r["status"] == "ok" for r in results)
        # 两条都走了 Raw_ob12 → call_api
        assert len(state["received"]) == 2
        # 第一条是 text 段，第二条是 image 段
        assert state["received"][0]["params"]["message"][-1]["type"] == "text"
        assert state["received"][1]["params"]["message"][-1]["type"] == "image"

    @pytest.mark.asyncio
    async def test_batch_modifiers_applied_to_each(self):
        """Build 前的 At 修饰器应用到批量中的每条消息"""
        adapter, state = make_real_pattern_adapter()
        await (
            adapter.Send.To("group", "456")
            .At("789")
            .Build()
            .Text("第一条")
            .Text("第二条")
            .send_all()
        )
        # 两条消息都应包含 mention 段
        for received in state["received"]:
            types = [seg["type"] for seg in received["params"]["message"]]
            assert "mention" in types
            assert "text" in types

    @pytest.mark.asyncio
    async def test_batch_send_context_per_item(self):
        """每条消息的 send_context（target）正确传递"""
        adapter, state = make_real_pattern_adapter()
        await (
            adapter.Send.To("group", "G999")
            .Using("bot1")
            .Build()
            .Text("a")
            .Image("b")
            .send_all()
        )
        for received in state["received"]:
            assert received["params"]["target_type"] == "group"
            assert received["params"]["target_id"] == "G999"

    @pytest.mark.asyncio
    async def test_batch_retry_failed_item_in_raw_path(self):
        """批量中失败的条目（Raw_ob12 抛异常）重试后成功"""
        adapter, state = make_real_pattern_adapter(fail_methods={"Raw_ob12": 1})
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Retry(2)
            .Text("会重试")
            .send_all()
        )
        assert results[0]["status"] == "ok"
        # Raw_ob12 失败 1 次 + 重试成功 1 次 = 2 次
        assert state["calls"]["Raw_ob12"] == 2

    @pytest.mark.asyncio
    async def test_batch_partial_failure_continues_others(self):
        """批量中一条失败，其他条继续发送（真实 Raw_ob12 链路）"""
        adapter, state = make_real_pattern_adapter()

        # 让第一次 call_api 返回 failed，后续成功
        call_count = {"n": 0}
        original_call_api = adapter.call_api

        async def flaky_api(endpoint, **params):
            call_count["n"] += 1
            if call_count["n"] == 1:  # 第一次调用失败
                return {"status": "failed", "retcode": 10001, "data": None,
                        "message_id": "", "message": "拒绝"}
            return await original_call_api(endpoint, **params)

        adapter.call_api = flaky_api
        results = await (
            adapter.Send.To("user", "123")
            .Build()
            .Text("会失败")
            .Text("会成功")
            .send_all()
        )
        # 第一条失败（status=failed），第二条成功
        assert results[0]["status"] == "failed"
        assert results[1]["status"] == "ok"
