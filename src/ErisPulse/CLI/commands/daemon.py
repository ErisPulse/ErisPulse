"""
Daemon 命令实现

管理 ErisPulse 后台进程：启动守护进程、查看状态、停止进程。
"""

import json
import os
import signal
import subprocess
import sys
import time
from argparse import ArgumentParser
from pathlib import Path

from rich.table import Table
from rich.prompt import Prompt

from ..base import Command
from ..console import console
from ..i18n import i18n
from ..utils.display import interactive_select_table

DAEMON_DIR = Path.home() / ".erispulse" / "daemons"


def _ensure_daemon_dir():
    DAEMON_DIR.mkdir(parents=True, exist_ok=True)


def _daemon_file(name: str) -> Path:
    return DAEMON_DIR / f"{name}.json"


def _read_daemon(name: str) -> dict | None:
    f = _daemon_file(name)
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_daemon(name: str, data: dict):
    _ensure_daemon_dir()
    _daemon_file(name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _remove_daemon(name: str):
    f = _daemon_file(name)
    if f.exists():
        f.unlink()


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _list_daemons() -> list[dict]:
    result = []
    _ensure_daemon_dir()
    for f in sorted(DAEMON_DIR.glob("*.json")):
        name = f.stem
        data = _read_daemon(name)
        if data is None:
            f.unlink()  # 损坏的 JSON 直接清理
            continue
        pid = data.get("pid", 0)
        alive = _is_alive(pid)
        if not alive:
            f.unlink()  # 进程已死，清理残留
            continue
        data["name"] = name
        data["alive"] = True
        result.append(data)
    return result


def _start_daemon(name: str, cmd: list[str], cwd: str | None = None):
    """启动后台守护进程，返回 PID"""
    import datetime as _dt

    kwargs = {}
    if cwd:
        kwargs["cwd"] = cwd

    # 确保日志目录存在
    log_dir = Path(cwd or os.getcwd()) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"daemon_{name}_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_fh = open(str(log_file), "a", encoding="utf-8")

    # 强制子进程使用 UTF-8 编码（避免 Windows 上日志乱码）
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    kwargs["env"] = env

    # 分离子进程，输出重定向到日志文件
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh, **kwargs)
    else:
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log_fh, stderr=log_fh, start_new_session=True, **kwargs)

    _write_daemon(name, {
        "pid": proc.pid,
        "name": name,
        "start_time": time.time(),
        "cwd": cwd or os.getcwd(),
        "cmd": cmd,
    })
    return proc.pid


class DaemonCommand(Command):
    """
    Daemon 命令

    查看和管理 ErisPulse 后台守护进程。
    """

    name = "daemon"
    description = i18n.t("cli.daemon.description")
    aliases = ["d"]

    def add_arguments(self, parser: ArgumentParser):
        sub = parser.add_subparsers(dest="action", help=i18n.t("cli.daemon.action_help"))

        # list
        p_list = sub.add_parser("list", aliases=["ls"], help=i18n.t("cli.daemon.list_help"))
        p_list.set_defaults(func=self._list)

        # status
        p_status = sub.add_parser("status", aliases=["st"], help=i18n.t("cli.daemon.status_help"))
        p_status.add_argument("name", nargs="?", default=None, help=i18n.t("cli.daemon.name_help"))
        p_status.set_defaults(func=self._status)

        # stop
        p_stop = sub.add_parser("stop", aliases=["kill"], help=i18n.t("cli.daemon.stop_help"))
        p_stop.add_argument("name", nargs="?", default=None, help=i18n.t("cli.daemon.stop_name_help"))
        p_stop.add_argument("--force", "-f", action="store_true", help=i18n.t("cli.daemon.force_help"))
        p_stop.set_defaults(func=self._stop)

        # logs
        p_logs = sub.add_parser("logs", help=i18n.t("cli.daemon.logs_help"))
        p_logs.add_argument("name", nargs="?", default=None, help=i18n.t("cli.daemon.logs_name_help"))
        p_logs.add_argument("-n", "--lines", type=int, default=20, help=i18n.t("cli.daemon.lines_help"))
        p_logs.add_argument("-f", "--follow", action="store_true", help=i18n.t("cli.daemon.follow_help"))
        p_logs.set_defaults(func=self._logs)

    def execute(self, args):
        action = getattr(args, "action", None)

        # 无子命令：交互模式
        if action is None:
            self._interactive()
            return

        # 子命令但无 name 参数：交互式选择目标（stop/kill/logs/status）
        if action in ("stop", "kill", "logs", "status"):
            name = getattr(args, "name", None)
            if not name:
                daemons = _list_daemons()
                alive = [d for d in daemons if d["alive"]]
                if not alive:
                    console.print(f"[info]{i18n.t('cli.daemon.no_daemons')}[/]")
                    return
                selected = interactive_select_table(
                    i18n.t(f"cli.daemon.select_{action}"),
                    [(d["name"], d["name"], str(d["pid"])) for d in alive],
                    columns=[i18n.t("cli.daemon.col_name"), i18n.t("cli.daemon.col_pid")],
                )
                if not selected:
                    return
                # 单进程模式：只取第一个选中项
                args.name = selected[0] if isinstance(selected, list) else selected

        args.func(args)

    def _interactive(self):
        """交互模式：展示运行进程列表，提供操作选单"""
        daemons = _list_daemons()
        alive = [d for d in daemons if d["alive"]]

        if not alive:
            console.print(f"[info]{i18n.t('cli.daemon.no_daemons')}[/]")
            console.print(f"[dim]{i18n.t('cli.daemon.start_tip')}[/]")
            return

        while True:
            # 打印列表
            self._list(None)

            # 操作选单
            console.print()
            console.print(f"  [info]{i18n.t('cli.daemon.action_prompt')}[/]")
            console.print(f"  [dim]  1. {i18n.t('cli.daemon.opt_status')}    2. {i18n.t('cli.daemon.opt_logs')}    3. {i18n.t('cli.daemon.opt_stop')}    4. {i18n.t('cli.daemon.opt_stop_force')}    q. {i18n.t('cli.daemon.opt_quit')}[/]")

            choice = Prompt.ask(f"\n  {i18n.t('cli.daemon.enter_option')}", choices=["1", "2", "3", "4", "q"], default="q")
            if choice == "q":
                break

            # 选择目标进程
            selected = interactive_select_table(
                i18n.t("cli.daemon.select_target"),
                [(d["name"], d["name"], str(d["pid"])) for d in alive],
                columns=[i18n.t("cli.daemon.col_name"), i18n.t("cli.daemon.col_pid")],
            )
            if not selected:
                continue
            target = selected[0] if isinstance(selected, list) else selected

            if choice == "1":
                self._status_one(target)
            elif choice == "2":
                self._logs_one(target)
            elif choice in ("3", "4"):
                self._stop_one(target, force=(choice == "4"))

            # 刷新进程列表
            daemons = _list_daemons()
            alive = [d for d in daemons if d["alive"]]
            if not alive:
                console.print(f"[info]{i18n.t('cli.daemon.all_stopped')}[/]")
                break

    def _status_one(self, name: str):
        """显示单个进程状态"""
        data = _read_daemon(name)
        if data is None:
            console.print(f"[error]{i18n.t('cli.daemon.not_found', name=name)}[/]")
            return
        alive = _is_alive(data["pid"])
        status_style = "success" if alive else "warning"
        status_text = i18n.t("cli.daemon.running") if alive else i18n.t("cli.daemon.stopped")
        console.print()
        console.print(f"  {i18n.t('cli.daemon.name_label')}: [info]{name}[/]")
        console.print(f"  PID: {data['pid']}")
        console.print(f"  {i18n.t('cli.daemon.status_label')}: [{status_style}]{status_text}[/]")
        if alive:
            uptime = time.time() - data.get("start_time", 0)
            console.print(f"  {i18n.t('cli.daemon.uptime_label')}: {_format_uptime(uptime)}")
        console.print(f"  {i18n.t('cli.daemon.cwd_label')}: {data.get('cwd', '-')}")
        console.print()

    def _logs_one(self, name: str):
        """显示单个进程日志"""
        data = _read_daemon(name)
        if data is None:
            return
        cwd = data.get("cwd", os.getcwd())
        log_dir = Path(cwd) / "logs"
        if log_dir.exists():
            log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if log_files:
                content = log_files[0].read_text(encoding="utf-8", errors="replace")
                lines = content.strip().split("\n")
                console.print()
                for line in lines[-20:]:
                    console.print(f"[dim]{line}[/]")
                console.print()
                return
        console.print(f"[warning]{i18n.t('cli.daemon.no_logs')}[/]")

    def _stop_one(self, name: str, force: bool = False):
        """停止单个进程"""
        from rich.prompt import Confirm
        label = f"{name} (force)" if force else name
        if not Confirm.ask(f"\n  [warning]{i18n.t('cli.daemon.confirm_stop', name=label)}[/]", default=False):
            return
        data = _read_daemon(name)
        if data is None:
            return
        pid = data["pid"]
        if not _is_alive(pid):
            console.print(f"[warning]{i18n.t('cli.daemon.already_stopped', name=name)}[/]")
            _remove_daemon(name)
            return
        sig = signal.SIGKILL if force else signal.SIGTERM
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(pid, sig)
            console.print(f"[success]{i18n.t('cli.daemon.stopped_ok', name=name, pid=pid)}[/]")
        except Exception as e:
            console.print(f"[error]{i18n.t('cli.daemon.stop_failed', name=name, error=e)}[/]")
        _remove_daemon(name)

    def _list(self, args):
        daemons = _list_daemons()

        if not daemons:
            console.print(f"[info]{i18n.t('cli.daemon.no_daemons')}[/]")
            return

        table = Table(title=i18n.t("cli.daemon.running_title"), box=None)
        table.add_column(i18n.t("cli.daemon.col_name"), style="info")
        table.add_column(i18n.t("cli.daemon.col_pid"), justify="right")
        table.add_column(i18n.t("cli.daemon.col_uptime"))
        table.add_column(i18n.t("cli.daemon.col_cwd"))
        for d in daemons:
            uptime = time.time() - d.get("start_time", 0)
            table.add_row(
                d["name"],
                str(d["pid"]),
                _format_uptime(uptime),
                d.get("cwd", "-"),
            )
        console.print(table)

    def _status(self, args):
        if args.name:
            data = _read_daemon(args.name)
            if data is None:
                console.print(f"[error]{i18n.t('cli.daemon.not_found', name=args.name)}[/]")
                return
            alive = _is_alive(data["pid"])
            status_style = "success" if alive else "warning"
            status_text = i18n.t("cli.daemon.running") if alive else i18n.t("cli.daemon.stopped")
            console.print(f"  {i18n.t('cli.daemon.name_label')}: [info]{args.name}[/]")
            console.print(f"  PID: {data['pid']}")
            console.print(f"  {i18n.t('cli.daemon.status_label')}: [{status_style}]{status_text}[/]")
            if alive:
                uptime = time.time() - data.get("start_time", 0)
                console.print(f"  {i18n.t('cli.daemon.uptime_label')}: {_format_uptime(uptime)}")
            console.print(f"  {i18n.t('cli.daemon.cwd_label')}: {data.get('cwd', '-')}")
        else:
            self._list(args)

    def _stop(self, args):
        data = _read_daemon(args.name)
        if data is None:
            console.print(f"[error]{i18n.t('cli.daemon.not_found', name=args.name)}[/]")
            return

        pid = data["pid"]
        if not _is_alive(pid):
            console.print(f"[warning]{i18n.t('cli.daemon.already_stopped', name=args.name)}[/]")
            _remove_daemon(args.name)
            return

        sig = signal.SIGKILL if args.force else signal.SIGTERM
        try:
            if sys.platform == "win32":
                # Windows 上 taskkill 不加 /F 无法有效终止控制台进程
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(pid, sig)
            console.print(f"[success]{i18n.t('cli.daemon.stopped_ok', name=args.name, pid=pid)}[/]")
        except Exception as e:
            console.print(f"[error]{i18n.t('cli.daemon.stop_failed', name=args.name, error=e)}[/]")
        _remove_daemon(args.name)

    def _logs(self, args):
        data = _read_daemon(args.name)
        if data is None:
            console.print(f"[error]{i18n.t('cli.daemon.not_found', name=args.name)}[/]")
            return

        cwd = data.get("cwd", os.getcwd())
        log_dir = Path(cwd) / "logs"
        log_file = None
        if log_dir.exists():
            # 优先 daemon 日志，回退到所有 .log 文件
            log_files = sorted(log_dir.glob("daemon_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not log_files:
                log_files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            if log_files:
                log_file = log_files[0]

        if not log_file:
            console.print(f"[warning]{i18n.t('cli.daemon.no_logs')}[/]")
            return

        if getattr(args, "follow", False):
            # Follow 模式：先显示最后 N 行，然后持续 tail
            self._follow_log(log_file, args.lines)
        else:
            content = log_file.read_text(encoding="utf-8", errors="replace")
            lines = content.strip().split("\n")
            for line in lines[-args.lines:]:
                console.print(f"[dim]{line}[/]")

    def _follow_log(self, log_file: Path, tail_lines: int):
        """实时跟踪日志文件（tail -f）"""
        with open(str(log_file), "r", encoding="utf-8", errors="replace") as f:
            # 先读已有内容
            lines = f.read().strip().split("\n")
            for line in lines[-tail_lines:]:
                console.print(f"[dim]{line}[/]")
            # 定位到文件末尾
            f.seek(0, 2)
            console.print(f"[info]{i18n.t('cli.daemon.following', file=log_file.name)}[/]")
            console.print(f"[dim]{i18n.t('cli.daemon.follow_tip')}[/]")
            try:
                while True:
                    line = f.readline()
                    if line:
                        console.print(f"[dim]{line.rstrip()}[/]")
                    else:
                        time.sleep(0.3)
            except KeyboardInterrupt:
                console.print(f"\n[info]{i18n.t('cli.daemon.follow_stopped')}[/]")


def _format_uptime(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"
