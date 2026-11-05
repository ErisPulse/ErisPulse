"""
热重载目标判定单元测试

覆盖插件目录、框架源码、入口脚本、模块/适配器源码归属、歧义与未匹配。
"""

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from ErisPulse.runtime import reload_target


class _FakeClass:
    def __init__(self, module_name: str):
        self.__module__ = module_name


def _install_module(name: str, file: Path) -> None:
    module = types.ModuleType(name)
    module.__file__ = str(file)
    sys.modules[name] = module


def _install_package(name: str, root: Path) -> None:
    package = types.ModuleType(name)
    package.__file__ = str(root / "__init__.py")
    package.__path__ = [str(root)]
    sys.modules[name] = package


def _fake_sdk(modules=None, adapters=None):
    module_manager = SimpleNamespace(_module_classes=modules or {})
    adapter_manager = SimpleNamespace(_adapters=adapters or {})
    return SimpleNamespace(module=module_manager, adapter=adapter_manager)


@pytest.fixture
def package_tree(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core.py").write_text("", encoding="utf-8")
    (pkg / "util.py").write_text("", encoding="utf-8")
    _install_package("pkg", pkg)
    _install_module("pkg.core", pkg / "core.py")
    _install_module("pkg.util", pkg / "util.py")
    yield pkg
    for name in ("pkg", "pkg.core", "pkg.util"):
        sys.modules.pop(name, None)


@pytest.fixture
def adapter_tree(tmp_path):
    pkg = tmp_path / "adapter_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core.py").write_text("", encoding="utf-8")
    _install_package("adapter_pkg", pkg)
    _install_module("adapter_pkg.core", pkg / "core.py")
    yield pkg
    for name in ("adapter_pkg", "adapter_pkg.core"):
        sys.modules.pop(name, None)


class TestClassifyReloadPath:
    def test_module_source_file(self, package_tree):
        sdk = _fake_sdk(
            modules={"MyMod": _FakeClass("pkg.core")},
        )
        target = reload_target.classify_reload_path(
            package_tree / "core.py", sdk
        )
        assert target.kind == "module"
        assert target.name == "MyMod"

    def test_module_sibling_file(self, package_tree):
        sdk = _fake_sdk(
            modules={"MyMod": _FakeClass("pkg.core")},
        )
        target = reload_target.classify_reload_path(
            package_tree / "util.py", sdk
        )
        assert target.kind == "module"
        assert target.name == "MyMod"

    def test_adapter_source_file(self, adapter_tree):
        class FakeAdapter:
            pass

        FakeAdapter.__module__ = "adapter_pkg.core"
        sdk = _fake_sdk(adapters={"MyAdapter": FakeAdapter()})
        target = reload_target.classify_reload_path(
            adapter_tree / "core.py", sdk
        )
        assert target.kind == "adapter"
        assert target.name == "MyAdapter"

    def test_plugin_directory(self, tmp_path, monkeypatch):
        plugins = tmp_path / "plugins"
        plugins.mkdir()
        changed = plugins / "dice.py"
        changed.write_text("", encoding="utf-8")
        monkeypatch.setattr(
            reload_target, "_plugin_dirs", lambda: [plugins.resolve()]
        )
        target = reload_target.classify_reload_path(changed, _fake_sdk())
        assert target.kind == "plugin"
        assert target.name == "dice"

    def test_entry_script(self, tmp_path):
        entry = tmp_path / "main.py"
        entry.write_text("", encoding="utf-8")
        target = reload_target.classify_reload_path(
            entry, _fake_sdk(), entry_paths=(entry,)
        )
        assert target.kind == "restart"
        assert target.reason == "entry"

    def test_framework_source(self):
        framework_file = Path(reload_target.__file__).resolve()
        target = reload_target.classify_reload_path(
            framework_file, _fake_sdk()
        )
        assert target.kind == "restart"
        assert target.reason == "framework"

    def test_ambiguous_module_matches(self, package_tree):
        sdk = _fake_sdk(
            modules={
                "ModA": _FakeClass("pkg.core"),
                "ModB": _FakeClass("pkg.util"),
            }
        )
        target = reload_target.classify_reload_path(
            package_tree / "core.py", sdk
        )
        assert target.kind == "restart"
        assert target.reason == "ambiguous"

    def test_unmapped_file(self, tmp_path):
        changed = tmp_path / "other.py"
        target = reload_target.classify_reload_path(changed, _fake_sdk())
        assert target.kind == "restart"
        assert target.reason == "unmapped"

    def test_non_python_file(self, tmp_path):
        target = reload_target.classify_reload_path(
            tmp_path / "note.txt", _fake_sdk()
        )
        assert target.kind == "restart"
        assert target.reason == "non-python"
