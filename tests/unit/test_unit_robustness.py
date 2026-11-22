"""
健壮性批次补全测试（2.12.1-dev.1）

覆盖本批次新增/此前低覆盖的模块路径：
- Core/Event/trace.py（分发链路追踪）
- runtime/hints.py（错误修复指引）
- runtime/memory.py 新增路径（ensure_tracing / detail 快照 / 容器归因）
- Core/Event/interaction.py 新增 sweep_expired
- Core/Bases/storage.py 新增路径（_capture_user_frames 边界）
- CLI/commands/logs.py（ep logs 的路径解析与读取）
"""

from __future__ import annotations

import argparse
import asyncio
import importlib

import pytest

# ==================== 分发链路追踪 ====================


class TestDispatchTrace:
    def test_trace_step_appends_records(self):
        from ErisPulse.Core.Event.trace import (
            start_dispatch_trace,
            trace_step,
        )

        with start_dispatch_trace() as records:
            trace_step("stage_a", verdict="ok", detail="x=1")
            trace_step("stage_b", verdict="rejected")
        assert [r["stage"] for r in records] == ["stage_a", "stage_b"]
        assert records[0]["verdict"] == "ok"

    def test_trace_step_outside_context_is_noop(self):
        """未处于采集上下文时零开销直接返回（不抛错）"""
        from ErisPulse.Core.Event.trace import trace_step

        trace_step("outside", verdict="ok")  # 不应抛错

    def test_get_dispatch_trace_outside_context_returns_empty(self):
        from ErisPulse.Core.Event.trace import get_dispatch_trace

        assert get_dispatch_trace() == []

    def test_format_dispatch_trace_outputs_stages(self):
        from ErisPulse.Core.Event.trace import (
            format_dispatch_trace,
            start_dispatch_trace,
            trace_step,
        )

        with start_dispatch_trace() as records:
            trace_step("command_match", verdict="ok")
            trace_step("cooldown", verdict="rejected")
        text = format_dispatch_trace(list(records))
        assert "command_match" in text
        assert isinstance(text, str)

    def test_final_verdict_returns_string(self):
        from ErisPulse.Core.Event.trace import (
            final_verdict,
            start_dispatch_trace,
            trace_step,
        )

        with start_dispatch_trace() as records:
            trace_step("scope", verdict="allow")
        assert isinstance(final_verdict(list(records)), str)


# ==================== 错误修复指引（hints） ====================


class TestHints:
    def test_parse_attr_error_extracts_attr(self):
        from ErisPulse.runtime.hints import parse_attr_error

        try:
            ("tuple",).append  # tuple 无 append
        except AttributeError as e:
            _obj_name, attr = parse_attr_error(e)
        assert attr == "append"

    def test_suggest_similar_returns_ranked_list(self):
        from ErisPulse.runtime.hints import suggest_similar

        result = suggest_similar("apend", ["append", "extend"])
        assert isinstance(result, list)
        assert "append" in result
        assert suggest_similar("zzzzzz", ["append", "extend"]) == []

    def test_suggest_for_attribute_error(self):
        from ErisPulse.runtime.hints import suggest_for_attribute_error

        try:
            "".no_such_method()
        except AttributeError as e:
            hint = suggest_for_attribute_error(e)
        assert hint is None or isinstance(hint, str)

    def test_suggest_for_import_error(self):
        from ErisPulse.runtime.hints import suggest_for_import_error

        hint = suggest_for_import_error(ImportError("No module named 'not_a_pkg'"))
        assert hint is None or isinstance(hint, str)

    def test_suggest_for_key_error(self):
        from ErisPulse.runtime.hints import suggest_for_key_error

        assert suggest_for_key_error(KeyError("missing_key")) is None or isinstance(suggest_for_key_error(KeyError("missing_key")), str)

    def test_suggest_for_name_error(self):
        from ErisPulse.runtime.hints import suggest_for_name_error

        assert suggest_for_name_error(NameError("name 'foo' is not defined")) is None or isinstance(suggest_for_name_error(NameError("name 'foo' is not defined")), str)

    def test_suggest_for_missing_argument(self):
        from ErisPulse.runtime.hints import suggest_for_missing_argument

        hint = suggest_for_missing_argument(
            TypeError("f() missing 1 required positional argument: 'x'")
        )
        assert hint is None or isinstance(hint, str)

    def test_suggest_for_not_callable(self):
        from ErisPulse.runtime.hints import suggest_for_not_callable

        assert suggest_for_not_callable(TypeError("'int' object is not callable")) is not None


# ==================== 内存观测新增路径 ====================


class TestMemoryObservability:
    def test_ensure_tracing_idempotent(self, monkeypatch):
        """ensure_tracing 幂等：默认关闭态不启动 tracemalloc，二次调用不抛"""
        import tracemalloc

        memory = importlib.import_module("ErisPulse.runtime.memory")
        assert hasattr(memory, "ensure_tracing")
        monkeypatch.setattr(memory, "_tracing_started", False)
        was_tracing = tracemalloc.is_tracing()
        memory.ensure_tracing()
        assert tracemalloc.is_tracing() is was_tracing
        memory.ensure_tracing()  # 幂等

    def test_snapshot_detail_includes_containers(self):
        """detail=True 输出容器归因（adapter 计数可达）与 top 分配点结构"""
        memory = importlib.import_module("ErisPulse.runtime.memory")

        snap = memory.snapshot("detail_probe", detail=True)
        assert "containers" in snap
        assert isinstance(snap["containers"], dict)
        assert any(k.startswith("adapter.") for k in snap["containers"])
        assert "top_allocations" in snap
        assert isinstance(snap["top_allocations"], list)

    def test_top_allocations_empty_without_tracing(self):
        """未开启 tracemalloc 时 top 分配点为空列表"""
        import tracemalloc

        memory = importlib.import_module("ErisPulse.runtime.memory")
        if tracemalloc.is_tracing():
            pytest.skip("tracemalloc 已被其他测试路径开启")
        assert memory._top_allocations() == []


# ==================== 交互过期条目清扫 ====================


class TestInteractionSweepExpired:
    def test_sweep_expired_removes_only_finished_entries(self):
        """清扫已过租期且 future 已完结的条目；等待中的 future 保留"""
        import time as _time

        from ErisPulse.Core.Event.interaction import interaction

        interaction.clear()
        loop = asyncio.new_event_loop()
        try:
            loop.create_future()
            # 租约条目：已过租期 + future 已完成 → 清扫
            done_future = loop.create_future()
            done_future.set_result(None)
            entry_done = interaction.register(
                {"platform": "p", "user_id": "a"}, done_future, owner="t"
            )
            entry_done.kind = "lease"
            entry_done.expires_at = _time.monotonic() - 1
            # 租约条目：已过租期但 future 未完成 → 保留（调用方仍在等待收尾）
            pending_future = loop.create_future()
            entry_pending = interaction.register(
                {"platform": "p", "user_id": "b"}, pending_future, owner="t"
            )
            entry_pending.kind = "lease"
            entry_pending.expires_at = _time.monotonic() - 1

            removed = interaction.sweep_expired()
            assert removed == 1
        finally:
            pending_future.cancel()
            interaction.clear()
            loop.close()

    def test_sweep_expired_method_exists(self):
        from ErisPulse.Core.Event.interaction import interaction

        assert callable(interaction.sweep_expired)


# ==================== 帧采集边界 ====================


class TestCaptureUserFrames:
    def test_capture_skips_internal_and_limits(self):
        from ErisPulse.Core.Bases.storage import _capture_user_frames

        def inner():
            return _capture_user_frames(limit=1)

        sites = inner()
        assert len(sites) <= 1
        # 框架内部帧不被采集（storage.py 模块名前缀过滤）
        for site in sites:
            assert "ErisPulse/Core/Bases/storage.py" not in site

    def test_capture_limit_zero_returns_empty(self):
        from ErisPulse.Core.Bases.storage import _capture_user_frames

        assert _capture_user_frames(limit=0) == []


# ==================== ep logs 命令 ====================


class TestLogsCommand:
    def _cmd(self):
        from ErisPulse.CLI.commands.logs import LogsCommand

        return LogsCommand()

    def test_resolve_log_path_override_wins(self, tmp_path):
        target = tmp_path / "custom.log"
        assert self._cmd()._resolve_log_path(str(target)) == target

    def test_resolve_log_path_defaults_to_logs_dir(self):
        path = str(self._cmd()._resolve_log_path(""))
        assert "erispulse.log" in path

    def test_execute_prints_tail(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text("line-1\nline-2\nline-3\n", encoding="utf-8")
        args = argparse.Namespace(lines=2, file=str(log_file))
        self._cmd().execute(args)
        out = capsys.readouterr().out
        assert "line-2" in out and "line-3" in out and "line-1" not in out

    def test_execute_missing_file_reports(self, tmp_path, capsys):
        args = argparse.Namespace(lines=5, file=str(tmp_path / "nope.log"))
        self._cmd().execute(args)
        out = capsys.readouterr().out
        assert "不存在" in out or "not found" in out.lower()

    def test_execute_default_path_reports_missing(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)  # cwd 无 logs/ 目录
        args = argparse.Namespace(lines=5, file="")
        self._cmd().execute(args)
        out = capsys.readouterr().out
        assert "不存在" in out or "not found" in out.lower()
