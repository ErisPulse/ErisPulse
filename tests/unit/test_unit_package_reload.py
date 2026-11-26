"""
已安装发行版热重载监控单元测试

覆盖 PackageReloadWatcher 的组件解析、allow/deny 监控范围 ACL、两级签名扫描
（mtime/size 快扫 + sha256 确认）与重载编排留痕，以及
start / stop 入口的配置驱动行为。
"""

import hashlib
import importlib
from types import SimpleNamespace

import pytest

from ErisPulse.runtime.package_reload import PackageReloadWatcher

base_storage_module = importlib.import_module("ErisPulse.Core.Bases.storage")
logger_module = importlib.import_module("ErisPulse.Core.logger")

# ==================== 测试脚手架 ====================


class _FakeDist:
    """模拟 importlib.metadata.Distribution：文件清单定位到临时目录"""

    def __init__(self, name: str, root, files: list[str]):
        self._name = name
        self._root = root
        self.files = files

    @property
    def metadata(self):
        return {"Name": self._name}

    def locate_file(self, package_path):
        return self._root / package_path


class _FakeEP:
    """模拟 importlib.metadata.EntryPoint"""

    def __init__(self, name: str, dist):
        self.name = name
        self.dist = dist


def _make_sdk(module_names=("dice",), adapter_names=()):
    """带 module / adapter 管理器桩的 SDK 替身（reload 调用记录在 calls）"""
    calls: list[tuple[str, str]] = []

    async def module_reload(name, **kwargs):
        calls.append(("module", name))
        return True

    async def adapter_reload(name, **kwargs):
        calls.append(("adapter", name))
        return True

    sdk = SimpleNamespace(
        module=SimpleNamespace(
            list_items=lambda: dict.fromkeys(module_names, True),
            reload=module_reload,
        ),
        adapter=SimpleNamespace(
            list_items=lambda: dict.fromkeys(adapter_names, True),
            reload=adapter_reload,
        ),
    )
    return sdk, calls


def _fake_eps(monkeypatch, eps):
    """钉住 watcher 模块的 entry-points 读取"""
    module_pkg = importlib.import_module("ErisPulse.runtime.package_reload")
    by_group = {
        "erispulse.module": [ep for ep in eps if ep._group == "erispulse.module"],
        "erispulse.adapter": [ep for ep in eps if ep._group == "erispulse.adapter"],
    }
    monkeypatch.setattr(module_pkg, "_iter_entry_points", lambda group: by_group.get(group, []))


def _seed_dist(tmp_path, dist_name="ErisPulse-Dice", module_name="dice", *, files=("dice/__init__.py", "dice/core.py")):
    """在临时目录造一个 dist 的 .py 文件并返回 (fake ep 列表, 根目录)"""
    root = tmp_path / "site"
    for rel in files:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {rel}\n", encoding="utf-8")
    dist = _FakeDist(dist_name, root, list(files))
    ep = _FakeEP(module_name, dist)
    ep._group = "erispulse.module"
    return [ep], root


# ==================== 监控范围 ACL（allow / deny） ====================


class TestTargetMatching:
    def test_empty_lists_match_all(self):
        watcher = PackageReloadWatcher(SimpleNamespace(), allow=[], deny=[])
        assert watcher._target_matches("dice", "ErisPulse-Dice")
        assert watcher._target_matches("anything", "Any-Dist")

    def test_allowlist_matches_component_and_dist_normalized(self):
        watcher = PackageReloadWatcher(SimpleNamespace(), allow=["Dice", "erispulse_dice"], deny=[])
        assert watcher._target_matches("dice", "ErisPulse-Dice")
        assert watcher._target_matches("other", "erispulse.dice")  # dist 名命中
        assert not watcher._target_matches("other", "ErisPulse-Other")

    def test_deny_takes_precedence_over_allow(self):
        watcher = PackageReloadWatcher(SimpleNamespace(), allow=["dice"], deny=["ErisPulse-Dice"])
        assert not watcher._target_matches("dice", "ErisPulse-Dice")  # 双名单命中：deny 优先
        assert not watcher._target_matches("onebot", "ErisPulse-Onebot")  # allow 非空且未命中
        assert watcher._target_matches("dice", "ErisPulse-Other")  # allow 命中（组件名）+ deny 未命中

    def test_deny_alone_excludes_matched_only(self):
        watcher = PackageReloadWatcher(SimpleNamespace(), allow=[], deny=["ErisPulse-Dice"])
        assert not watcher._target_matches("dice", "ErisPulse-Dice")
        assert watcher._target_matches("onebot", "ErisPulse-Onebot")  # 空 allow = 除 deny 外全部

    def test_glob_patterns_supported(self):
        watcher = PackageReloadWatcher(SimpleNamespace(), allow=["ErisPulse-Storage-*"], deny=["*-postgres"])
        assert watcher._target_matches("sqlite", "ErisPulse-Storage-SQLite")  # glob + 归一
        assert not watcher._target_matches("postgres", "ErisPulse-Storage-Postgres")  # deny glob 优先
        assert not watcher._target_matches("aiomysql", "ErisPulse-MySQL")  # allow 未命中


# ==================== 组件解析 ====================


class TestResolveWatches:
    def test_loaded_components_grouped_by_dist(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        adapter_dist = _FakeDist("ErisPulse-Onebot", tmp_path / "site2", ["onebot/__init__.py"])
        (tmp_path / "site2" / "onebot").mkdir(parents=True)
        (tmp_path / "site2" / "onebot" / "__init__.py").write_text("x\n", encoding="utf-8")
        adapter_ep = _FakeEP("onebot11", adapter_dist)
        adapter_ep._group = "erispulse.adapter"
        _fake_eps(monkeypatch, eps + [adapter_ep])

        sdk, _calls = _make_sdk(module_names=("dice",), adapter_names=("onebot11",))
        watcher = PackageReloadWatcher(sdk)
        watches = watcher._resolve_watches()

        assert set(watches) == {"erispulse-dice", "erispulse-onebot"}
        assert ("module", "dice") in watches["erispulse-dice"].components
        assert ("adapter", "onebot11") in watches["erispulse-onebot"].components

    def test_skips_unloaded_and_distless(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        runtime_ep = _FakeEP("MyRuntime", None)  # 运行时注册：无发行版信息
        runtime_ep._group = "erispulse.module"
        _fake_eps(monkeypatch, eps + [runtime_ep])

        sdk, _calls = _make_sdk(module_names=("dice",))  # MyRuntime 未加载
        watcher = PackageReloadWatcher(sdk)
        watches = watcher._resolve_watches()

        assert set(watches) == {"erispulse-dice"}

    def test_allowlist_filter_excludes_unlisted_dist(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        _fake_eps(monkeypatch, eps)
        sdk, _calls = _make_sdk(module_names=("dice",))
        watcher = PackageReloadWatcher(sdk, allow=["ErisPulse-Other"])
        assert watcher._resolve_watches() == {}


# ==================== 两级签名扫描 ====================


class TestScan:
    def _watcher_with_snapshot(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        _fake_eps(monkeypatch, eps)
        sdk, calls = _make_sdk(module_names=("dice",))
        watcher = PackageReloadWatcher(sdk)
        watcher._watches = watcher._resolve_watches()
        watch = watcher._watches["erispulse-dice"]
        watcher._collect_files(watch)
        return watcher, watch, calls

    def test_content_change_detected(self, tmp_path, monkeypatch):

        watcher, watch, _calls = self._watcher_with_snapshot(tmp_path, monkeypatch)
        target = next(p for p in watch.files if p.name == "core.py")
        # 内容变化 + mtime/size 变化（保证快扫命中）
        target.write_text("# rewritten\n", encoding="utf-8")
        st = target.stat()
        watch.files[target] = (st.st_mtime_ns + 1_000_000, st.st_size)

        changed = watcher._scan_once()
        assert [w.dist_name for w, _c in changed] == ["ErisPulse-Dice"]

    def test_mtime_only_touch_not_triggered(self, tmp_path, monkeypatch):
        watcher, watch, _calls = self._watcher_with_snapshot(tmp_path, monkeypatch)
        target = next(iter(watch.files))
        # 仅 mtime 变化、内容不变（touch 语义）：sha256 确认层应过滤
        old_mt, size = watch.files[target]
        watch.files[target] = (old_mt + 1_000_000, size)

        assert watcher._scan_once() == []

    def test_deleted_file_detected(self, tmp_path, monkeypatch):
        watcher, watch, _calls = self._watcher_with_snapshot(tmp_path, monkeypatch)
        target = next(p for p in watch.files if p.name == "core.py")
        target.unlink()

        changed = watcher._scan_once()
        assert [w.dist_name for w, _c in changed] == ["ErisPulse-Dice"]

    def test_no_change_no_trigger(self, tmp_path, monkeypatch):
        watcher, watch, _calls = self._watcher_with_snapshot(tmp_path, monkeypatch)
        assert watcher._scan_once() == []


# ==================== 重载编排 ====================


class TestReloadOrchestration:
    @pytest.mark.asyncio
    async def test_reload_calls_module_and_adapter_managers(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        adapter_ep = _FakeEP("onebot11", eps[0].dist)  # 同一 dist 提供适配器
        adapter_ep._group = "erispulse.adapter"
        _fake_eps(monkeypatch, eps + [adapter_ep])
        sdk, calls = _make_sdk(module_names=("dice",), adapter_names=("onebot11",))
        watcher = PackageReloadWatcher(sdk)
        watcher._watches = watcher._resolve_watches()
        watch = watcher._watches["erispulse-dice"]

        await watcher._reload(watch, list(watch.components))

        assert ("module", "dice") in calls
        assert ("adapter", "onebot11") in calls

    @pytest.mark.asyncio
    async def test_reload_failure_does_not_abort_rest(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        _fake_eps(monkeypatch, eps)
        sdk, calls = _make_sdk(module_names=("dice",))

        async def failing_reload(name, **kwargs):
            raise RuntimeError("boom")

        sdk.module.reload = failing_reload
        warnings: list[str] = []
        monkeypatch.setattr(logger_module.logger, "warning", lambda m, *a, **k: warnings.append(str(m)))
        watcher = PackageReloadWatcher(sdk)
        watch = SimpleNamespace(dist_name="ErisPulse-Dice", components=[("module", "dice")])

        await watcher._reload(watch, list(watch.components))  # 不向调用方传播

        assert len(warnings) == 1 and "dice" in warnings[0]

    @pytest.mark.asyncio
    async def test_reload_false_result_warns(self, tmp_path, monkeypatch):
        eps, _root = _seed_dist(tmp_path)
        _fake_eps(monkeypatch, eps)
        sdk, _calls = _make_sdk(module_names=("dice",))

        async def false_reload(name, **kwargs):
            return False

        sdk.module.reload = false_reload
        warnings: list[str] = []
        monkeypatch.setattr(logger_module.logger, "warning", lambda m, *a, **k: warnings.append(str(m)))
        watcher = PackageReloadWatcher(sdk)
        watch = SimpleNamespace(dist_name="ErisPulse-Dice", components=[("module", "dice")])

        await watcher._reload(watch, list(watch.components))

        assert len(warnings) == 1


# ==================== 配置驱动启停 ====================


class TestStartStop:
    def test_disabled_by_config_does_not_start(self, monkeypatch):
        sdk_module = importlib.import_module("ErisPulse.sdk")
        monkeypatch.setattr(
            sdk_module.SDK,
            "enable_hot_reload",
            lambda self_obj: False,
        )
        sdk = sdk_module.SDK()
        sdk._start_hot_reload_watcher()
        assert getattr(sdk, "_package_reload_watcher", None) is None

    def test_watcher_direct_roundtrip(self, tmp_path, monkeypatch):
        """监控器直构往返：start 后线程就位、stop 后退出（不经 SDK 配置入口）"""
        eps, _root = _seed_dist(tmp_path)
        _fake_eps(monkeypatch, eps)
        sdk, _calls = _make_sdk(module_names=("dice",))
        watcher = PackageReloadWatcher(sdk, interval=0.05)
        assert watcher.start() is True
        try:
            assert watcher.is_running and watcher._thread is not None
        finally:
            watcher.stop()
        assert watcher._thread is None
        assert watcher.is_running is False

    def test_stop_is_idempotent(self):
        sdk = SimpleNamespace()
        sdk_module = importlib.import_module("ErisPulse.sdk")
        sdk_module.SDK.stop_package_hot_reload(sdk)  # 未启动时调用不抛错
        assert getattr(sdk, "_package_reload_watcher", None) is None


# ==================== 文件哈希基准 ====================


class TestFileHash:
    def test_hash_matches_reference(self, tmp_path):
        target = tmp_path / "a.py"
        target.write_bytes(b"payload")
        assert PackageReloadWatcher._file_hash(target) == hashlib.sha256(b"payload").hexdigest()

    def test_unreadable_file_returns_none(self, tmp_path):
        missing = tmp_path / "missing.py"
        assert PackageReloadWatcher._file_hash(missing) is None
