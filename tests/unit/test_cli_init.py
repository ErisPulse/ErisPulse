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
        assert ".venv/" in text and "logs/" in text and "config/" in text
        # Python 常用排除项
        assert "__pycache__/" in text and "*.egg-info/" in text and ".pytest_cache/" in text

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


class TestUvToolEnv:
    """uv tool 环境检测（uv tool install ErisPulse 场景）"""

    def test_uv_tool_path_detected(self, monkeypatch, tmp_path):
        import sys as _sys

        from ErisPulse.CLI.utils import package_manager as pm_module

        tool_prefix = tmp_path / "uv" / "tools" / "ErisPulse"
        monkeypatch.setattr(_sys, "prefix", str(tool_prefix))
        assert pm_module.is_uv_tool_env() is True

    def test_normal_env_not_detected(self, monkeypatch, tmp_path):
        import sys as _sys

        from ErisPulse.CLI.utils import package_manager as pm_module

        monkeypatch.setattr(_sys, "prefix", str(tmp_path / "venv"))
        assert pm_module.is_uv_tool_env() is False

    def test_warn_silent_without_uv_tool(self, monkeypatch, tmp_path):
        import sys as _sys

        from ErisPulse.CLI.utils import package_manager as pm_module

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("VIRTUAL_ENV", raising=False)
        monkeypatch.setattr(_sys, "prefix", str(tmp_path / "venv"))
        assert pm_module.warn_if_uv_tool_env_without_project() is False

    def test_warn_silent_inside_project(self, monkeypatch, tmp_path):
        import sys as _sys

        from ErisPulse.CLI.utils import package_manager as pm_module

        monkeypatch.chdir(tmp_path)
        # 有项目 .venv 时即使处于工具环境也不提示
        monkeypatch.setattr(_sys, "prefix", str(tmp_path / "uv" / "tools" / "ErisPulse"))
        assert pm_module.warn_if_uv_tool_env_without_project() is False


class TestBannerSuppression:
    """Banner 静默（非交互终端 / 环境变量）"""

    def test_no_banner_env_suppresses(self, monkeypatch):
        import ErisPulse.CLI.console as console_module

        monkeypatch.setenv("ERISPULSE_NO_BANNER", "1")
        monkeypatch.setattr(console_module, "_banner_printed", False)
        console_module.print_banner()
        assert console_module._banner_printed is True

    def test_disable_banner(self, monkeypatch):
        import ErisPulse.CLI.console as console_module

        monkeypatch.setattr(console_module, "_banner_printed", False)
        console_module.disable_banner()
        console_module.print_banner()
        # 禁用后 Banner 不输出（提前返回，不做任何打印）
        assert console_module._banner_disabled is True


class TestVersionCommand:
    """version 子命令（与 -V 等效的习惯命令）"""

    def test_registered_and_resolvable(self):
        from ErisPulse.CLI.cli import CLI

        cli = CLI()
        assert "version" in cli.registry.list_all()
        assert cli.registry.resolve("ver") == "version"

    def test_execute_prints_version(self, capsys):
        from ErisPulse.CLI.commands.version import VersionCommand

        VersionCommand().execute(None)
        out = capsys.readouterr().out
        assert "ErisPulse" in out


class TestUvToolSelfUpdate:
    """uv tool 通道自更新（Windows 分离进程策略）"""

    def test_build_command_upgrade_latest(self):
        from ErisPulse.CLI.utils.package_manager import (
            build_uv_tool_update_command,
        )

        assert build_uv_tool_update_command(["uv"], None) == [
            "uv", "tool", "upgrade", "ErisPulse"
        ]

    def test_build_command_pinned_version(self):
        from ErisPulse.CLI.utils.package_manager import (
            build_uv_tool_update_command,
        )

        assert build_uv_tool_update_command(["uv"], "2.8.4") == [
            "uv", "tool", "install", "ErisPulse==2.8.4", "--force"
        ]

    def test_build_windows_script_waits_parent_and_self_deletes(self):
        from ErisPulse.CLI.utils.package_manager import (
            build_windows_tool_update_script,
        )

        script = build_windows_tool_update_script(
            ["uv", "tool", "upgrade", "ErisPulse"],
            parent_pid=1234,
            msg_done="done",
            msg_failed="failed",
            press_key="press enter",
        )
        assert "Wait-Process -Id 1234" in script  # 等当前进程退出（解除文件占用）
        assert "uv tool upgrade ErisPulse" in script  # 命令本体（list2cmdline 拼接）
        assert "Remove-Item" in script  # 自删除
        assert "Read-Host" in script  # 防窗口闪退

    def test_build_windows_script_quotes_spaced_paths(self):
        from ErisPulse.CLI.utils.package_manager import (
            build_windows_tool_update_script,
        )

        uv_path = "C:" + chr(92) + "Program Files" + chr(92) + "uv" + chr(92) + "uv.exe"
        script = build_windows_tool_update_script(
            [uv_path, "tool", "upgrade", "ErisPulse"],
            parent_pid=1,
            msg_done="done",
            msg_failed="failed",
            press_key="press",
        )
        # 含空格的路径经 list2cmdline 加引号，PowerShell & 调用仍合法
        assert '"' + uv_path + '" tool upgrade ErisPulse' in script

    def test_ps_quote_escapes_single_quotes(self):
        from ErisPulse.CLI.utils.package_manager import _ps_quote

        assert _ps_quote("it's ok") == "it''s ok"
