"""
BaseFinder 远程目标环境支持单元测试

验证 BaseFinder 在配置了不同的 python_executable 时，通过子进程查询目标环境的
entry-points 的行为。这是修复"安装在 venv 但查询读取 pipx env"这类跨环境错位的关键。
"""

import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from ErisPulse.finders.bases.finder import (
    BaseFinder,
    _RemoteEntryPoint,
    _RemoteDist,
)


class _ConcreteFinder(BaseFinder):
    """用于测试的具体 finder"""

    def _get_entry_point_group(self) -> str:
        return "test.group"


class TestRemoteEntryPoint:
    """_RemoteEntryPoint 轻量代理测试"""

    def test_attributes(self):
        """应正确保存传入的字段"""
        ep = _RemoteEntryPoint({
            "name": "foo",
            "value": "mod:Cls",
            "group": "g",
            "dist_name": "FooPkg",
            "dist_version": "1.0.0",
            "summary": "A foo package",
        })
        assert ep.name == "foo"
        assert ep.value == "mod:Cls"
        assert ep.group == "g"
        assert ep.dist.name == "FooPkg"
        assert ep.dist.version == "1.0.0"

    def test_dist_none(self):
        """dist_name 为 None 时 dist 应为 None"""
        ep = _RemoteEntryPoint({
            "name": "foo",
            "value": "mod:Cls",
            "group": "g",
            "dist_name": None,
            "dist_version": None,
        })
        assert ep.dist is None

    def test_metadata_summary(self):
        """应通过 dist.metadata.get('Summary') 取得摘要"""
        ep = _RemoteEntryPoint({
            "name": "foo",
            "value": "mod:Cls",
            "group": "g",
            "dist_name": "Foo",
            "dist_version": "1.0",
            "summary": "hello",
        })
        assert ep.dist.metadata.get("Summary") == "hello"

    def test_load_raises(self):
        """跨环境 entry-point 的 load() 应抛 RuntimeError"""
        ep = _RemoteEntryPoint({
            "name": "foo",
            "value": "mod:Cls",
            "group": "g",
        })
        with pytest.raises(RuntimeError):
            ep.load()


class TestBaseFinderTargetPython:
    """BaseFinder 的 python_executable 参数测试"""

    def test_default_python(self):
        """默认应使用 sys.executable"""
        f = _ConcreteFinder()
        assert f._python_executable == sys.executable

    def test_custom_python(self):
        """应使用传入的 python_executable"""
        f = _ConcreteFinder(python_executable="/some/path/python")
        assert f._python_executable == "/some/path/python"

    def test_is_remote_target_same(self):
        """与当前解释器相同时返回 False"""
        f = _ConcreteFinder(python_executable=sys.executable)
        assert f._is_remote_target() is False

    def test_is_remote_target_different(self):
        """与当前解释器不同时返回 True"""
        f = _ConcreteFinder(python_executable="/some/other/python")
        assert f._is_remote_target() is True

    def test_remote_target_uses_subprocess(self):
        """远程目标应通过子进程查询，而非本地 importlib.metadata"""
        f = _ConcreteFinder(python_executable="/some/other/python")

        # mock 子进程返回空结果
        with patch.object(f, "_fetch_remote_entry_points", return_value=[]) as mock_fetch:
            result = f.find_all()
            mock_fetch.assert_called_once_with("test.group")
            assert result == []

    def test_local_target_uses_importlib(self):
        """本地目标应使用 importlib.metadata"""
        f = _ConcreteFinder(python_executable=sys.executable)

        # 不应调用 _fetch_remote_entry_points
        with patch.object(f, "_fetch_remote_entry_points") as mock_fetch:
            mock_fetch.return_value = []  # 不会被调用
            f.find_all()
            mock_fetch.assert_not_called()

    def test_fetch_remote_handles_subprocess_failure(self):
        """子进程失败时应返回空列表，不抛异常"""
        f = _ConcreteFinder(python_executable="/nonexistent/python")
        result = f._fetch_remote_entry_points("any.group")
        # 应返回空列表（具体取决于 subprocess.run 行为）
        # 由于路径不存在，subprocess 可能抛 FileNotFoundError，被捕获返回 []
        assert result == []

    def test_cache_persists_across_calls(self):
        """缓存应在有效期内避免重复查询"""
        f = _ConcreteFinder(python_executable="/some/other/python")

        call_count = {"n": 0}

        def mock_fetch(group):
            call_count["n"] += 1
            return []

        with patch.object(f, "_fetch_remote_entry_points", side_effect=mock_fetch):
            f.find_all()
            f.find_all()
            f.find_all()

        # 第二次和第三次应命中缓存，只调用一次
        assert call_count["n"] == 1

    def test_clear_cache_forces_refresh(self):
        """clear_cache 后应重新查询"""
        f = _ConcreteFinder(python_executable="/some/other/python")

        call_count = {"n": 0}

        def mock_fetch(group):
            call_count["n"] += 1
            return []

        with patch.object(f, "_fetch_remote_entry_points", side_effect=mock_fetch):
            f.find_all()
            f.clear_cache()
            f.find_all()

        assert call_count["n"] == 2


class TestEndToEndWithCurrentPython:
    """端到端测试：用当前 Python 作为目标，验证子进程查询能正常工作"""

    def test_fetch_with_current_python_returns_entries(self):
        """用当前 Python 作为目标时，子进程查询应能返回 entry-points 数据结构"""
        f = _ConcreteFinder(python_executable=sys.executable)

        # 强制走远程路径（即使目标是当前 python）
        with patch.object(f, "_is_remote_target", return_value=True):
            # 使用一个不存在的组，确保返回空但流程完整
            result = f._fetch_remote_entry_points("nonexistent.group.xyz")
            assert isinstance(result, list)
            # 不存在的组应该返回空
            assert result == []
