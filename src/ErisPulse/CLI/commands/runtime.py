"""
Stop / Restart 命令实现

控制由 ``epsdk run`` 启动的运行实例：``.erispulse/runtime.json`` 状态文件
记录监督进程 PID、当前子进程 PID 与原始启动命令，``stop`` 优雅终止实例，
``restart`` 停止后按原参数重新启动。

POSIX 停止走 SIGINT（监督进程按 Ctrl+C 同款路径收尾，finally 链终止子进程），
超时逐级升级 SIGTERM / SIGKILL；Windows 无优雅信号语义，先断子进程再终止
监督进程（避免监督者把强杀误判为崩溃重新拉起）。
"""

import subprocess
import sys
from argparse import ArgumentParser, Namespace

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils import runtime_state


def _stop_instance(state: dict, force: bool = False) -> bool:
    """
    停止一个运行实例（子进程先断，监督进程优雅收尾后逐级升级）

    :param state: 状态字典（pid / child_pid）
    :param force: 跳过优雅信号直接强制终止
    :return: 是否成功停止
    """
    pid = state.get("pid")
    child_pid = state.get("child_pid")
    if not isinstance(pid, int) or not runtime_state.pid_alive(pid):
        return False

    # 1. 先断框架子进程：Windows 强停监督进程前必须先断子，
    #    否则监督者会把强杀误判为崩溃而按退避策略重新拉起
    if isinstance(child_pid, int) and runtime_state.pid_alive(child_pid):
        runtime_state.terminate(child_pid, force=force or os_needs_force())
        if not runtime_state.wait_gone(child_pid, runtime_state.FORCE_TIMEOUT_SECS):
            runtime_state.kill_tree_hard(child_pid)

    # 2. 停监督进程：优雅信号 → 等待 → 强制
    if not force:
        runtime_state.terminate(pid, force=False)
        if runtime_state.wait_gone(pid, runtime_state.GRACEFUL_TIMEOUT_SECS):
            return True
        console.print(f"[warning]{i18n.t('cli.stop.graceful_timeout')}[/]")
    runtime_state.terminate(pid, force=True)
    if runtime_state.wait_gone(pid, runtime_state.FORCE_TIMEOUT_SECS):
        return True
    runtime_state.kill_tree_hard(pid)
    return not runtime_state.pid_alive(pid)


def os_needs_force() -> bool:
    """Windows 无优雅信号语义：子进程直接强停"""
    return sys.platform.startswith("win")


class StopCommand(Command):
    """
    stop 命令

    停止正在运行的 ErisPulse 实例（由 ``epsdk run`` 启动）
    """

    name = "stop"
    description = i18n.t("cli.stop.description")
    aliases: list = []
    category = "project"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=i18n.t("cli.stop.force_help"),
        )
        parser.add_argument(
            "--pid",
            type=int,
            default=None,
            help=i18n.t("cli.stop.pid_help"),
        )

    def execute(self, args: Namespace) -> None:
        state = runtime_state.read()
        if args.pid is not None:
            state = {"pid": args.pid, "child_pid": None}
        if state is None or not runtime_state.pid_alive(state.get("pid", -1)):
            console.print(f"[warning]{i18n.t('cli.stop.not_running')}[/]")
            runtime_state.clear()
            return

        pid = state.get("pid")
        console.print(f"[info]{i18n.t('cli.stop.stopping', pid=pid)}[/]")
        if _stop_instance(state, force=bool(args.force)):
            runtime_state.clear()
            console.print(f"[success]{i18n.t('cli.stop.stopped')}[/]")
        else:
            console.print(f"[error]{i18n.t('cli.stop.failed', pid=pid)}[/]")
            raise SystemExit(1)


class RestartCommand(Command):
    """
    restart 命令

    重启正在运行的 ErisPulse 实例（停止后按原参数重新启动，前台接管控制台）
    """

    name = "restart"
    description = i18n.t("cli.restart.description")
    aliases: list = []
    category = "project"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help=i18n.t("cli.stop.force_help"),
        )
        parser.add_argument(
            "--pid",
            type=int,
            default=None,
            help=i18n.t("cli.stop.pid_help"),
        )

    def execute(self, args: Namespace) -> None:
        state = runtime_state.read()
        if args.pid is not None:
            state = {"pid": args.pid, "child_pid": None}

        if state is None or not runtime_state.pid_alive(state.get("pid", -1)):
            console.print(f"[warning]{i18n.t('cli.restart.not_running_hint')}[/]")
            runtime_state.clear()
            return

        argv = state.get("argv") or [sys.argv[0], "run"]
        console.print(f"[info]{i18n.t('cli.stop.stopping', pid=state.get('pid'))}[/]")
        if not _stop_instance(state, force=bool(args.force)):
            console.print(f"[error]{i18n.t('cli.stop.failed', pid=state.get('pid'))}[/]")
            raise SystemExit(1)
        runtime_state.clear()
        console.print(f"[info]{i18n.t('cli.restart.starting_new', cmd=' '.join(argv))}[/]")
        # 前台接管：新实例写自己的状态文件，退出码透传
        raise SystemExit(subprocess.call(argv))


__all__ = ["StopCommand", "RestartCommand"]
