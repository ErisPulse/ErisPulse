"""
已安装发行版热重载 SDK 方法级集成测试

覆盖 ``sdk.enable_package_hot_reload`` / ``sdk.stop_package_hot_reload``
的启用往返、重复启用拒绝与显式参数覆盖配置。
"""

from pathlib import Path

import pytest

from ErisPulse.runtime.package_reload import _normalize_dist_name
from ErisPulse.sdk import SDK

pytestmark = pytest.mark.integration


class _FakeDist:
    """模拟 importlib.metadata.Distribution：文件清单定位到临时目录"""

    def __init__(self, name: str, root: Path, files: list[str]):
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

    def __init__(self, name: str, dist, group: str):
        self.name = name
        self.dist = dist
        self._group = group


def _seed_dist(tmp_path: Path, module_name: str = "dice"):
    """在临时目录造一个 dist 的 .py 文件并返回 fake entry-points 列表"""
    root = tmp_path / "site"
    for rel in ("dice/__init__.py", "dice/core.py"):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {rel}\n", encoding="utf-8")
    dist = _FakeDist("ErisPulse-Dice", root, ["dice/__init__.py", "dice/core.py"])
    ep = _FakeEP(module_name, dist, "erispulse.module")
    return [ep]


def _patch_eps(monkeypatch, eps):
    """钉住 watcher 模块的 entry-points 读取"""
    package_reload = __import__(
        "ErisPulse.runtime.package_reload", fromlist=["_iter_entry_points"]
    )
    by_group: dict[str, list] = {}
    for ep in eps:
        by_group.setdefault(ep._group, []).append(ep)
    monkeypatch.setattr(package_reload, "_iter_entry_points", lambda group: by_group.get(group, []))


@pytest.fixture
def sdk(tmp_path):
    """带隔离工作目录的 SDK 实例（测试结束停配置监视线程）"""
    from ErisPulse.Core.config import ConfigManager

    workdir = tmp_path / "proj"
    workdir.mkdir()
    original_cwd = Path.cwd()
    import os

    os.chdir(workdir)
    instance = SDK()
    yield instance
    instance.disable_hot_reload()
    ConfigManager.stop_all_watchers()
    os.chdir(original_cwd)


class TestEnableStopRoundtrip:
    def test_enable_and_stop(self, sdk, tmp_path, monkeypatch):
        """启用后监控器就位并运行；停止后清空且线程退出"""
        eps = _seed_dist(tmp_path)
        _patch_eps(monkeypatch, eps)

        assert sdk.enable_hot_reload(interval=0.05) is True
        watcher = sdk._package_reload_watcher
        assert watcher is not None and watcher.is_running

        sdk.stop_package_hot_reload()
        assert sdk._package_reload_watcher is None
        assert watcher.is_running is False
        assert watcher._thread is None

    def test_double_enable_returns_false(self, sdk, tmp_path, monkeypatch):
        """已在运行时再次启用返回 False（不重复建监控）"""
        eps = _seed_dist(tmp_path)
        _patch_eps(monkeypatch, eps)

        assert sdk.enable_hot_reload(interval=0.05) is True
        first = sdk._package_reload_watcher
        assert sdk.enable_hot_reload(interval=0.05) is False
        assert sdk._package_reload_watcher is first

    def test_stop_is_idempotent(self, sdk):
        """未启用时停止不抛错（幂等）"""
        sdk.stop_package_hot_reload()
        assert getattr(sdk, "_package_reload_watcher", None) is None

    def test_explicit_args_override_config(self, sdk, tmp_path, monkeypatch):
        """显式参数生效且未读取配置（配置读取器被替换为必抛桩）"""
        import importlib

        eps = _seed_dist(tmp_path)
        _patch_eps(monkeypatch, eps)

        frame_config = importlib.import_module("ErisPulse.runtime.frame_config")

        def _no_config(key, default=None):
            raise AssertionError(f"显式参数齐全时不应读配置: {key}")

        monkeypatch.setattr(frame_config, "get_framework_value", _no_config)
        assert sdk.enable_hot_reload(interval=0.05, allow=["dice"], deny=[]) is True
        watcher = sdk._package_reload_watcher
        assert watcher is not None
        assert watcher._allow == (_normalize_dist_name("dice"),)
        assert watcher._deny == ()

    def test_allowlist_filter_excludes_unlisted_dist(self, sdk, tmp_path, monkeypatch):
        """allow 白名单生效：未命中的发行版不进入包监控集（插件面仍启用 → 统一返回 True）"""
        eps = _seed_dist(tmp_path, module_name="dice")
        _patch_eps(monkeypatch, eps)

        assert sdk.enable_hot_reload(interval=0.05, allow=["ErisPulse-Other"]) is True
        assert sdk._package_reload_watcher is None
        assert sdk._plugin_watcher is not None and sdk._plugin_watcher.is_running

    def test_unified_flag_blocks_reenable(self, sdk, tmp_path, monkeypatch):
        """统一开关置位后再次启用被拒（先 disable 再启用可换参数）"""
        eps = _seed_dist(tmp_path)
        _patch_eps(monkeypatch, eps)
        assert sdk.enable_hot_reload(interval=0.05) is True
        assert sdk.enable_hot_reload(interval=0.05) is False
        sdk.disable_hot_reload()
        assert sdk.enable_hot_reload(interval=0.05) is True


class TestConfigDrivenStart:
    def test_start_watcher_reads_config(self, sdk, tmp_path, monkeypatch):
        """_start_hot_reload_watcher 按配置驱动：enabled=false 不启用，true 启用"""
        import importlib

        eps = _seed_dist(tmp_path)
        _patch_eps(monkeypatch, eps)

        frame_config = importlib.import_module("ErisPulse.runtime.frame_config")
        values = {"auto_reload.enabled": True, "auto_reload.interval": 0.05}

        def fake_get(key, default=None):
            return values.get(key, default)

        monkeypatch.setattr(frame_config, "get_framework_value", fake_get)

        sdk._start_hot_reload_watcher()
        assert sdk._package_reload_watcher is not None
        sdk._stop_hot_reload_watcher()
        assert sdk._package_reload_watcher is None

        values["auto_reload.enabled"] = False
        sdk._start_hot_reload_watcher()
        assert sdk._package_reload_watcher is None
