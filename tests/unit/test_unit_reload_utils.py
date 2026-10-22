"""
热重载共用工具单元测试（loaders/_reload_utils.py）

模块与适配器重载管线共用的字节码缓存清理与语法预检的唯一实现。
"""

import importlib.util
import sys
import types
from pathlib import Path

from ErisPulse.loaders._reload_utils import (
    clear_source_caches,
    expand_source_files,
    module_objects_by_names,
    precheck_source_files,
)


def _fake_mod(file_path):
    mod = types.ModuleType("fake")
    mod.__file__ = str(file_path)
    return mod


class TestExpandSourceFiles:
    def test_package_init_expands_recursively(self, tmp_path):
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "__init__.py").write_text("")
        (tmp_path / "pkg" / "a.py").write_text("")
        (tmp_path / "pkg" / "sub").mkdir()
        (tmp_path / "pkg" / "sub" / "b.py").write_text("")
        files = expand_source_files([tmp_path / "pkg" / "__init__.py"])
        names = {f.name for f in files}
        assert names == {"__init__.py", "a.py", "b.py"}

    def test_single_file_and_filters(self, tmp_path):
        py = tmp_path / "x.py"
        py.write_text("")
        so = tmp_path / "y.so"
        so.write_text("")
        files = expand_source_files([None, "", py, so])
        assert files == [py]

    def test_dedupes(self, tmp_path):
        py = tmp_path / "x.py"
        py.write_text("")
        assert expand_source_files([py, py]) == [py]


class TestClearSourceCaches:
    def test_clears_pyc_for_single_file(self, tmp_path):
        py = tmp_path / "m.py"
        py.write_text("x = 1\n")
        cache = importlib.util.cache_from_source(str(py))
        assert cache
        Path(cache).parent.mkdir(parents=True, exist_ok=True)
        Path(cache).write_bytes(b"fake")
        clear_source_caches([_fake_mod(py)])
        assert not Path(cache).exists()

    def test_tolerates_none_and_missing_files(self, tmp_path):
        clear_source_caches([None, _fake_mod(tmp_path / "ghost.py")])

    def test_names_lookup(self, tmp_path, monkeypatch):
        py = tmp_path / "n.py"
        py.write_text("")
        mod = _fake_mod(py)
        monkeypatch.setitem(sys.modules, "some_top", mod)
        assert module_objects_by_names(["some_top", "missing"]) == [mod]


class TestPrecheckSourceFiles:
    def test_valid_file_passes(self, tmp_path):
        py = tmp_path / "ok.py"
        py.write_text("x = 1\n")
        assert precheck_source_files(
            "c", [py], i18n_key="loader.module.reload_precheck_failed"
        )

    def test_syntax_error_rejects(self, tmp_path):
        py = tmp_path / "bad.py"
        py.write_text("def f(:\n")
        assert not precheck_source_files(
            "c", [py], i18n_key="loader.module.reload_precheck_failed"
        )

    def test_empty_list_passes(self):
        assert precheck_source_files("c", [], i18n_key="x")

    def test_over_limit_skips(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "ErisPulse.loaders._reload_utils.MODULE_RELOAD_PRECHECK_MAX_FILES", 2
        )
        files = []
        for i in range(3):
            f = tmp_path / f"f{i}.py"
            # 第 3 个文件超限被跳过：其中含语法错误也不阻断（交快照回滚兜底）
            f.write_text("def broken(:\n" if i == 2 else "x = 1\n")
            files.append(f)
        assert precheck_source_files("c", files, i18n_key="x") is True
