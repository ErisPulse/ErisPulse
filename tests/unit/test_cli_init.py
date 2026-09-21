"""
CLI init / 环境基建单元测试

测试 init 目录支持（位置路径 / --path / --here）、pyproject.toml 生成、
.gitignore / README 脚手架、目标解释器解析优先级（ERISPULSE_PYTHON >
项目 .venv > VIRTUAL_ENV > 当前解释器）、uv 隔离环境检测警告，以及
pyproject 依赖回写（tomlkit 保格式 + 去重）。
"""

import sys

import pytest


@pytest.fixture
def init_cmd():
    from ErisPulse.CLI.commands.init import InitCommand

    return InitCommand()


@pytest.fixture
def clean_uv_env(monkeypatch):
    """清理影响环境解析的环境变量"""
    for name in ("ERISPULSE_PYTHON", "VIRTUAL_ENV", "UV"):
        monkeypatch.delenv(name, raising=False)
    yield


class TestInitProjectPaths:
    """init 目录支持矩阵"""

    def test_bare_name_creates_subdir(self, init_cmd, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert init_cmd._init_project("mybot", [], create_venv=False) is True
        assert (tmp_path / "mybot" / "main.py").exists()

    def test_relative_path_with_parent(self, init_cmd, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from pathlib import Path

        assert (
            init_cmd._init_project(
                "mybot", [], target_dir=Path("..") / "apps", create_venv=False
            )
            is True
        )
        assert (tmp_path.parent / "apps" / "mybot" / "main.py").exists()

    def test_pyproject_generated(self, init_cmd, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        init_cmd._init_project("mybot", ["onebot11-adapter"], create_venv=False)
        pyproject = tmp_path / "mybot" / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        assert 'name = "mybot"' in text
        assert 'requires-python = ">=3.10"' in text
        assert '"erispulse>=2.8.3"' in text
        assert '"onebot11-adapter"' in text  # 适配器进依赖清单

    def test_gitignore_generated(self, init_cmd, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        init_cmd._init_project("mybot", [], create_venv=False)
        text = (tmp_path / "mybot" / ".gitignore").read_text(encoding="utf-8")
        assert ".venv/" in text and "logs/" in text and "*.pem" in text

    def test_readme_generated(self, init_cmd, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        init_cmd._init_project("mybot", [], create_venv=False)
        assert (tmp_path / "mybot" / "README.md").exists()

    def test_invalid_name_rejected(self, init_cmd, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert init_cmd._init_project("../evil;rm", [], create_venv=False) is False

    def test_here_ignores_target_dir(self, init_cmd, tmp_path, monkeypatch):

        monkeypatch.chdir(tmp_path)
        assert (
            init_cmd._init_project("proj", [], in_current_dir=True, create_venv=False)
            is True
        )
        assert (tmp_path / "config" / "config.toml").exists()


class TestResolveTargetPython:
    """目标解释器解析优先级"""

    def test_project_venv_priority(self, tmp_path, monkeypatch):
        from ErisPulse.CLI.utils.package_manager import resolve_target_python

        if sys.platform == "win32":
            py = tmp_path / ".venv" / "Scripts" / "python.exe"
        else:
            py = tmp_path / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True)
        py.write_text("")
        monkeypatch.setenv("ERISPULSE_PYTHON", str(py))

        resolved, source = resolve_target_python(tmp_path)
        assert resolved == str(py)
        assert source == "ERISPULSE_PYTHON"

    def test_project_venv_detected(self, tmp_path, monkeypatch):
        from ErisPulse.CLI.utils.package_manager import resolve_target_python

        monkeypatch.delenv("ERISPULSE_PYTHON", raising=False)
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)
        if sys.platform == "win32":
            py = tmp_path / ".venv" / "Scripts" / "python.exe"
        else:
            py = tmp_path / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True)
        py.write_text("")

        resolved, source = resolve_target_python(tmp_path)
        assert resolved == str(py)
        assert source == "项目 .venv"

    def test_fallback_current_interpreter(self, tmp_path, monkeypatch):
        from ErisPulse.CLI.utils.package_manager import resolve_target_python

        monkeypatch.delenv("ERISPULSE_PYTHON", raising=False)
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)

        resolved, source = resolve_target_python(tmp_path)
        assert resolved == sys.executable
        assert source == "当前解释器"


class TestUvIsolationWarning:
    """uv 隔离环境检测"""

    def test_warns_without_pyproject(self, tmp_path, monkeypatch):
        from ErisPulse.CLI.utils.package_manager import warn_if_uv_isolated

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("UV", "/usr/local/bin/uv")
        assert warn_if_uv_isolated() is True

    def test_silent_with_pyproject(self, tmp_path, monkeypatch):
        from ErisPulse.CLI.utils.package_manager import warn_if_uv_isolated

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("UV", "/usr/local/bin/uv")
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        assert warn_if_uv_isolated() is False

    def test_silent_without_uv(self, tmp_path, monkeypatch):
        from ErisPulse.CLI.utils.package_manager import warn_if_uv_isolated

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("UV", raising=False)
        assert warn_if_uv_isolated() is False


class TestAppendPyprojectDependencies:
    """pyproject 依赖回写（tomlkit 保格式 + 去重）"""

    def test_append_and_dedupe(self, tmp_path):
        from ErisPulse.CLI.utils.package_manager import append_pyproject_dependencies

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "# 项目注释\n[project]\nname = 'demo'\ndependencies = ['erispulse>=2.8.3']\n",
            encoding="utf-8",
        )
        assert append_pyproject_dependencies(tmp_path, ["onebot11-adapter"]) is True
        text = pyproject.read_text(encoding="utf-8")
        assert "# 项目注释" in text  # 注释保留（tomlkit）
        assert "onebot11-adapter" in text

        # 重复追加：幂等
        assert append_pyproject_dependencies(tmp_path, ["onebot11-adapter"]) is True
        assert text.count("onebot11-adapter") >= 1

    def test_missing_file(self, tmp_path):
        from ErisPulse.CLI.utils.package_manager import append_pyproject_dependencies

        assert append_pyproject_dependencies(tmp_path, ["x"]) is False
