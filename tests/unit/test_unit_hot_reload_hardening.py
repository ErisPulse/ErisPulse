"""
热重载汇总预检与文件监控新能力单元测试

覆盖：precheck_source_trees 汇总报错（不首个即停）、GBK 编码拒绝、
PollingObserver 忽略目录剪枝 / 前缀重叠 / handler 异常守卫、
插件路径解析、process_state 跨进程契约。
"""

import time

import pytest

from ErisPulse.loaders._reload_utils import (
    clear_source_caches_for_files,
    precheck_source_trees,
)
from ErisPulse.runtime.file_watcher import FileSystemEventHandler, PollingObserver
from ErisPulse.runtime.plugin_reload import resolve_plugin_name


class _Recorder(FileSystemEventHandler):
    def __init__(self):
        self.created, self.deleted, self.modified = [], [], []

    def on_created(self, event):
        self.created.append(event.src_path)

    def on_deleted(self, event):
        self.deleted.append(event.src_path)

    def on_modified(self, event):
        self.modified.append(event.src_path)


@pytest.mark.unit
class TestPrecheckSourceTrees:
    """汇总式语法预检"""

    def test_reports_all_failures_not_first_only(self, tmp_path):
        """两个文件各有语法错误：全部报出"""
        bad1 = tmp_path / "bad1.py"
        bad1.write_text("def f(:\n", encoding="utf-8")
        bad2 = tmp_path / "bad2.py"
        bad2.write_text("x = = 1\n", encoding="utf-8")
        good = tmp_path / "good.py"
        good.write_text("x = 1\n", encoding="utf-8")

        failures = precheck_source_trees(
            "reload_all",
            [
                ("mod-a", [bad1, good]),
                ("mod-b", [bad2]),
            ],
            i18n_key="loader.module.reload_all_precheck_failed",
        )
        assert len(failures) == 2
        assert any("bad1" in f for f in failures)
        assert any("bad2" in f for f in failures)

    def test_all_pass_returns_empty(self, tmp_path):
        good = tmp_path / "ok.py"
        good.write_text("x = 1\n", encoding="utf-8")
        assert (
            precheck_source_trees("t", [("m", [good])], i18n_key="k") == []
        )

    def test_gbk_encoded_source_rejected(self, tmp_path):
        """GBK 中文源文件（无 coding 声明）在预检即拒绝

        样本用字符串字面量（其 GBK 字节构成非法 UTF-8 序列——与真实
        import 的拒绝行为一致；纯注释碰巧合法 UTF-8 时 import 本身
        也宽容接受，预检与 import 语义对齐）。
        """
        bad = tmp_path / "gbk.py"
        bad.write_bytes('msg = "配置文件错误"\n'.encode("gbk"))
        failures = precheck_source_trees("t", [("m", [bad])], i18n_key="k")
        assert failures, "GBK 源文件应被预检拒绝"
        assert any("gbk.py" in f for f in failures)

    def test_pep263_coding_declaration_still_passes(self, tmp_path):
        """带 coding 声明的合法文件不受严格解码影响"""
        ok = tmp_path / "declared.py"
        ok.write_bytes(b"# -*- coding: gbk -*-\nx = 1\n")
        assert precheck_source_trees("t", [("m", [ok])], i18n_key="k") == []

    def test_clear_source_caches_for_files(self, tmp_path):
        """按路径清 pyc：缓存文件被删除"""
        src = tmp_path / "m.py"
        src.write_text("x = 1\n", encoding="utf-8")
        import py_compile

        py_compile.compile(str(src), doraise=True)
        pyc = src.parent / "__pycache__" / "m.cpython-313.pyc"
        if not pyc.exists():
            # 版本号不同：按目录通配
            candidates = list((src.parent / "__pycache__").glob("m.*.pyc"))
            assert candidates, "pyc should exist after compile"
            pyc = candidates[0]
        assert pyc.exists()
        clear_source_caches_for_files([src])
        assert not pyc.exists()


@pytest.mark.unit
class TestPollingObserverIgnoreDirs:
    """文件监控忽略目录与边界"""

    def test_walker_prunes_ignored_dirs(self, tmp_path):
        rec = _Recorder()
        observer = PollingObserver(interval=0.05, ignore_dirs=[".venv"])
        observer.schedule(rec, str(tmp_path), recursive=True)
        observer.start()
        try:
            (tmp_path / ".venv").mkdir()
            (tmp_path / ".venv" / "x.py").write_text("x = 1", encoding="utf-8")
            (tmp_path / "app.py").write_text("x = 1", encoding="utf-8")
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline and not rec.created:
                time.sleep(0.02)
            assert any(p.endswith("app.py") for p in rec.created)
            assert not any(".venv" in p for p in rec.created)
        finally:
            observer.stop()
            observer.join()

    def test_prefix_overlapping_dirs_no_spurious_delete(self, tmp_path):
        """plugins 与 plugins2 同时监控：改 plugins2 文件不产生虚假删除"""
        (tmp_path / "plugins").mkdir()
        (tmp_path / "plugins2").mkdir()
        f2 = tmp_path / "plugins2" / "a.py"
        f2.write_text("x = 1", encoding="utf-8")
        rec = _Recorder()
        observer = PollingObserver(interval=0.05)
        observer.schedule(rec, str(tmp_path / "plugins"), recursive=True)
        observer.schedule(rec, str(tmp_path / "plugins2"), recursive=True)
        observer.start()
        try:
            time.sleep(0.15)
            f2.write_text("x = 2", encoding="utf-8")
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline and not rec.modified:
                time.sleep(0.02)
            assert any(p.endswith("a.py") for p in rec.modified)
            assert rec.deleted == [], "前缀重叠不得产生虚假删除事件"
        finally:
            observer.stop()
            observer.join()

    def test_handler_exception_does_not_kill_thread(self, tmp_path):
        """handler 回调抛异常：轮询线程存活，后续事件仍送达"""

        class _Boom(FileSystemEventHandler):
            def on_modified(self, event):
                raise RuntimeError("boom")

            def on_created(self, event):
                pass

        target = tmp_path / "x.py"
        target.write_text("x = 1", encoding="utf-8")
        observer = PollingObserver(interval=0.05)
        observer.schedule(_Boom(), str(tmp_path), recursive=False)
        observer.start()
        try:
            time.sleep(0.15)
            target.write_text("x = 2", encoding="utf-8")
            time.sleep(0.2)  # 若线程死亡，这里不会崩但后续也不会派发
            assert observer.is_running, "handler 异常后轮询线程应存活"
        finally:
            observer.stop()
            observer.join()

    def test_is_running_property(self, tmp_path):
        observer = PollingObserver(interval=0.05)
        assert observer.is_running is False
        observer.start()
        try:
            assert observer.is_running is True
        finally:
            observer.stop()
            observer.join()
        assert observer.is_running is False


@pytest.mark.unit
class TestPluginNameResolution:
    """插件名解析（热发现路由的基础）"""

    def test_single_file_and_package(self, tmp_path, monkeypatch):
        (tmp_path / "plugins" / "weather" / "Core.py").parent.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        assert (
            resolve_plugin_name(str(tmp_path / "plugins" / "dice.py"), ["plugins"])
            == "dice"
        )
        assert (
            resolve_plugin_name(
                str(tmp_path / "plugins" / "weather" / "Core.py"), ["plugins"]
            )
            == "weather"
        )

    def test_outside_plugin_dirs_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_plugin_name(str(tmp_path / "elsewhere.py"), ["plugins"]) is None

    def test_non_py_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert resolve_plugin_name(str(tmp_path / "x.txt"), ["plugins"]) is None


@pytest.mark.unit
class TestProcessStateContract:
    """runtime/process_state.py 与 CLI runtime_state 的跨进程 JSON 契约"""

    def test_mark_read_clear_roundtrip(self, tmp_path, monkeypatch):
        from ErisPulse.runtime import process_state

        monkeypatch.chdir(tmp_path)
        (tmp_path / process_state.STATE_DIR).mkdir()
        state_file = tmp_path / process_state.STATE_DIR / "runtime.json"
        state_file.write_text('{"pid": 123}', encoding="utf-8")

        process_state.mark_hard_restart(reason="self-update", pid=999)
        data = process_state.read()
        assert data["pid"] == 123  # 既有字段保留
        assert data["hard_restart_reason"] == "self-update"
        assert data["hard_restart_pid"] == 999
        assert isinstance(data["hard_restart_at"], float)

        process_state.clear_mark()
        data = process_state.read()
        assert "hard_restart_reason" not in data
        assert data["pid"] == 123  # 非标记字段不受影响

    def test_dir_and_file_names_match_cli(self):
        """目录/文件名常量与 CLI 侧一致（跨进程契约）"""
        from ErisPulse.runtime import process_state

        assert process_state.STATE_DIR == ".erispulse"
        assert process_state.STATE_FILE == "runtime.json"

    def test_read_missing_returns_none(self, tmp_path, monkeypatch):
        from ErisPulse.runtime import process_state

        monkeypatch.chdir(tmp_path)
        assert process_state.read() is None
