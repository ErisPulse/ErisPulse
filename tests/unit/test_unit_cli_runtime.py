"""
CLI 运行时控制（stop / restart）单元测试

覆盖：状态文件读写、进程存活判定、stop/restart 在无实例时的行为、
stop --pid 指定 PID 的优雅终止路径。
"""

import os

import pytest

from ErisPulse.CLI.commands.runtime import RestartCommand, StopCommand
from ErisPulse.CLI.utils import runtime_state


@pytest.fixture
def in_tmp_project(tmp_path, monkeypatch):
    """隔离到临时项目目录（状态文件以 cwd 为维度）"""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.mark.unit
class TestRuntimeState:
    """状态文件读写与进程存活判定"""

    def test_roundtrip(self, in_tmp_project):
        assert runtime_state.read() is None
        runtime_state.write(pid=123, argv=["epsdk", "run"], child_pid=456)
        state = runtime_state.read()
        assert state["pid"] == 123
        assert state["child_pid"] == 456
        assert state["argv"] == ["epsdk", "run"]

        runtime_state.update_child(789)
        assert runtime_state.read()["child_pid"] == 789

        runtime_state.clear()
        assert runtime_state.read() is None

    def test_corrupted_state_returns_none(self, in_tmp_project):
        runtime_state.state_path().parent.mkdir(parents=True, exist_ok=True)
        runtime_state.state_path().write_text("{not json", encoding="utf-8")
        assert runtime_state.read() is None

    def test_pid_alive(self):
        assert runtime_state.pid_alive(os.getpid()) is True
        assert runtime_state.pid_alive(-1) is False


@pytest.mark.unit
class TestStopCommand:
    async def test_stop_without_state_is_noop(self, in_tmp_project, capsys):
        cmd = StopCommand()
        cmd.execute(_args(force=False, pid=None))
        out = capsys.readouterr().out
        assert out  # 未运行提示已输出
        assert runtime_state.read() is None

    async def test_stop_dead_pid_reports(self, in_tmp_project, capsys):
        runtime_state.write(pid=999999999, argv=["epsdk", "run"])
        cmd = StopCommand()
        cmd.execute(_args(force=False, pid=None))
        out = capsys.readouterr().out
        assert runtime_state.read() is None  # 状态文件被清理

    async def test_stop_pid_override(self, in_tmp_project, capsys):
        # --pid 指向不存活进程：报告未运行，不写状态文件
        cmd = StopCommand()
        cmd.execute(_args(force=False, pid=999999999))
        out = capsys.readouterr().out
        assert out


@pytest.mark.unit
class TestRestartCommand:
    async def test_restart_without_state_hints_run(self, in_tmp_project, capsys):
        cmd = RestartCommand()
        cmd.execute(_args(force=False, pid=None))
        out = capsys.readouterr().out
        assert "epsdk run" in out
        assert runtime_state.read() is None


@pytest.mark.unit
class TestRestartContainerHot:
    """容器内实例（PID 1）restart 改走进程内热重启信号"""

    async def test_pid1_signals_framework_child(self, in_tmp_project, monkeypatch, capsys):
        import signal as signal_mod

        killed: list[tuple[int, object]] = []

        def fake_kill(pid, sig):
            # 放行 pid_alive 的 0 号信号存活探测，只记录真实热重启信号
            if sig != 0:
                killed.append((pid, sig))

        monkeypatch.setattr(signal_mod, "SIGUSR1", object(), raising=False)
        monkeypatch.setattr(os, "kill", fake_kill)
        monkeypatch.setattr(
            "ErisPulse.CLI.commands.runtime.subprocess.call",
            lambda *a, **k: pytest.fail("容器内实例不应走停止后重拉路径"),
        )

        runtime_state.write(pid=1, argv=["epsdk", "run"], child_pid=os.getpid())
        cmd = RestartCommand()
        cmd.execute(_args(force=False, pid=None))  # 不应抛 SystemExit

        assert len(killed) == 1
        assert killed[0][0] == os.getpid()
        # 状态文件保留：实例仍在运行，未被清理
        assert runtime_state.read() is not None
        out = capsys.readouterr().out
        assert str(os.getpid()) in out

    async def test_pid1_without_sigusr1_reports_unsupported(self, in_tmp_project, monkeypatch, capsys):
        import signal as signal_mod

        monkeypatch.delattr(signal_mod, "SIGUSR1", raising=False)
        runtime_state.write(pid=1, argv=["epsdk", "run"], child_pid=os.getpid())

        cmd = RestartCommand()
        with pytest.raises(SystemExit) as exc_info:
            cmd.execute(_args(force=False, pid=None))

        assert exc_info.value.code == 1
        out = capsys.readouterr().out
        assert out
        # 状态文件保留，未误杀实例
        assert runtime_state.read() is not None

    async def test_pid1_non_posix_env_reported(self, in_tmp_project, monkeypatch, capsys):
        """SIGUSR1 存在但 os.kill 失败（权限等）：报告不支持并保留实例"""
        import signal as signal_mod

        monkeypatch.setattr(signal_mod, "SIGUSR1", object(), raising=False)

        def _fail_kill(pid, sig):
            if sig != 0:
                raise PermissionError(1, "operation not permitted")

        monkeypatch.setattr(os, "kill", _fail_kill)
        runtime_state.write(pid=1, argv=["epsdk", "run"], child_pid=os.getpid())

        cmd = RestartCommand()
        with pytest.raises(SystemExit) as exc_info:
            cmd.execute(_args(force=False, pid=None))

        assert exc_info.value.code == 1
        assert runtime_state.read() is not None


def _args(force: bool, pid):
    """构造 argparse Namespace 桩"""
    from argparse import Namespace

    return Namespace(force=force, pid=pid)
