"""
Run 命令实现

直接运行主程序，支持热重载模式
"""

import asyncio
import runpy
import subprocess
import sys
import threading
import time
from argparse import ArgumentParser
from pathlib import Path

from rich.panel import Panel

from ..base import Command
from ..console import console
from ..constants import HARD_RESTART_EXIT_CODE
from ..i18n import i18n
from ..utils.file_watcher import FileSystemEventHandler, PollingObserver


class ReloadHandler(FileSystemEventHandler):
    """
    文件系统事件处理器

    监控 .py 文件变更并触发 sdk.restart() 热重载

    {!--< tips >!--}
    1. 文件监控运行在独立线程
    2. 通过 run_coroutine_threadsafe 安全调度到事件循环
    3. 内置 1 秒防抖，避免短时间内多次重载
    {!--< /tips >!--}
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        """
        初始化热重载处理器

        :param loop: [asyncio.AbstractEventLoop] 用于调度重载协程的事件循环
        """
        super().__init__()
        self._loop = loop
        self._last_reload = 0.0

    def on_modified(self, event):
        """
        文件修改事件回调，对 .py 文件触发热重载

        :param event: [FileSystemEvent] 文件系统事件
        """
        now = time.time()
        if now - self._last_reload < 1.0:
            return
        if event.src_path.endswith(".py"):
            self._last_reload = now
            self._schedule_reload(event)

    def _schedule_reload(self, event):
        """
        在事件循环中调度 SDK 重启以执行热重载

        :param event: [FileSystemEvent] 触发重载的文件系统事件
        """

        async def _do_reload():
            """执行 SDK 重启以完成热重载"""
            try:
                from ... import sdk

                await sdk.restart()
            except Exception as e:
                console.print(
                    f"[error]{i18n.t('cli.run.hot_reload_failed', error=e)}[/]"
                )

            console.print(
                i18n.t("cli.run.file_changed", file=Path(event.src_path).name)
            )

        asyncio.run_coroutine_threadsafe(_do_reload(), self._loop)


class RunCommand(Command):
    """
    Run 命令

    运行主程序，支持热重载模式
    """

    name = "run"
    description = i18n.t("cli.run.description")
    aliases = ["r"]

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "script", nargs="?", default=None, help=i18n.t("cli.run.script_help")
        )
        parser.add_argument(
            "--reload",
            action="store_true",
            default=False,
            help=i18n.t("cli.run.reload_help"),
        )

    def execute(self, args):
        script = args.script
        reload_mode = args.reload

        if script:
            if not Path(script).exists():
                # 列出当前目录的 .py 文件作为上下文参考
                py_files = sorted(Path().glob("*.py"))
                file_list = ", ".join(f.name for f in py_files[:5]) if py_files else None
                hint_text = i18n.t("cli.run.use_init")
                if file_list:
                    hint_text += "  " + i18n.t("cli.run.available_scripts", files=file_list)
                console.print(
                    f"[error]{i18n.t('cli.run.script_not_found', script=script)}[/]"
                )
                console.print(f"[info]{hint_text}[/]")
                return
            if Path(script).is_dir():
                console.print(
                    f"[error]{i18n.t('cli.run.is_directory', script=script)}[/]"
                )
                console.print(
                    "[info]{}[/]".format(i18n.t("cli.run.specify_file", script=script))
                )
                return
            self._run_script(script, reload_mode)
        else:
            self._run_internal(reload_mode)

    _RESTART_EXIT_CODE = HARD_RESTART_EXIT_CODE
    _MAX_CRASH_BACKOFF = 60.0

    def _run_internal(self, reload_mode: bool):
        """
        直接运行 SDK（不指定脚本时）

        以子进程方式运行 SDK，支持硬重启。

        {!--< tips >!--}
        重要设计原则：
        1. 只有硬重启（退出码 42）或 KeyboardInterrupt 才能停止主进程
        2. 模块/适配器的任何错误都**不会**导致主进程退出
        3. 子进程异常退出时自动重试，使用递增退避策略避免刷屏
        {!--< /tips >!--}
        """

        if reload_mode:

            async def _run():
                """
                设置文件监控并运行 SDK

                :return: [None] 无返回值
                """
                from ... import sdk

                loop = asyncio.get_running_loop()
                self._setup_watchdog(".", loop)
                await sdk.run(keep_running=True)

            try:
                asyncio.run(_run())
            except KeyboardInterrupt:
                pass
            finally:
                if hasattr(self, "_observer"):
                    self._observer.stop()
                    self._observer.join()
            return

        cmd = [
            sys.executable,
            "-c",
            "import asyncio; from ErisPulse import sdk; "
            "asyncio.run(sdk.run(keep_running=True))",
        ]

        crash_count = 0
        process = None
        try:
            while True:
                process = subprocess.Popen(cmd)
                process.wait()

                if process.returncode == self._RESTART_EXIT_CODE:
                    console.print(f"[info]{i18n.t('cli.run.restart_request')}[/]")
                    crash_count = 0
                    time.sleep(0.5)
                    continue

                # 非硬重启退出码：模块/适配器内部错误导致子进程异常终止
                # 不退出主进程，等待后自动重试
                crash_count += 1
                backoff = min(self._MAX_CRASH_BACKOFF, 3.0 * crash_count)
                console.print(
                    f"[warning]{i18n.t('cli.run.process_crashed', code=process.returncode)}[/]"
                )
                console.print(
                    f"[info]{i18n.t('cli.run.subprocess_crashed_retry', seconds=backoff)}[/]"
                )
                time.sleep(backoff)
                # 继续循环，重新启动子进程
        except KeyboardInterrupt:
            pass
        finally:
            # 运行器退出（Ctrl+C 等）前必须终止子进程，否则孤儿进程会继续持有
            # 端口等资源，导致下次启动时端口被占用（如监听 8000 的残留进程）。
            if process is not None and process.poll() is None:
                console.print(f"[info]{i18n.t('cli.run.terminating_child')}[/]")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

    def _run_script(self, script_path: str, reload_mode: bool):
        """
        运行指定的脚本文件，可选启用热重载

        :param script_path: [str] 脚本文件路径
        :param reload_mode: [bool] 是否启用热重载模式
        """
        script_path_abs = str(Path(script_path).resolve())

        if reload_mode:
            self._run_script_with_reload(script_path_abs)
        else:
            script_dir = str(Path(script_path_abs).parent)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            try:
                runpy.run_path(script_path_abs, run_name="__main__")
            except SystemExit:
                pass
            except KeyboardInterrupt:
                pass

    def _run_script_with_reload(self, script_path_abs: str):
        """
        以子进程方式运行脚本并监控文件变更以自动重启

        进程的所有终止与重启均在主线程完成；文件监控线程仅负责发出重载信号，
        避免双线程同时操作子进程导致的竞态。脚本进程因错误（如语法错误、异常）
        退出时不会终止重载循环，而是等待下一次文件变更后再尝试重启。

        :param script_path_abs: [str] 脚本的绝对路径
        """
        watch_dir = str(Path(script_path_abs).parent)

        reload_state = {
            "process": None,
            "last_reload": 0.0,
            "changed_file": None,
            "reload_event": threading.Event(),
        }

        def _spawn():
            """启动脚本子进程并记录到 reload_state"""
            reload_state["process"] = subprocess.Popen(
                [sys.executable, script_path_abs]
            )

        class _ScriptReloadHandler(FileSystemEventHandler):
            """
            脚本重载信号处理器，监控 .py 文件变更并发出重载信号

            仅设置重载事件，不直接操作子进程（终止/重启由主线程统一处理）。
            """

            def on_modified(self, event):
                """
                文件修改事件回调，设置重载信号供主线程处理

                :param event: [FileSystemEvent] 文件系统事件
                """
                now = time.time()
                if now - reload_state["last_reload"] < 1.0:
                    return
                if not event.src_path.endswith(".py"):
                    return
                reload_state["last_reload"] = now
                reload_state["changed_file"] = Path(event.src_path).name
                reload_state["reload_event"].set()

        observer = PollingObserver()
        observer.schedule(_ScriptReloadHandler(), watch_dir, recursive=True)
        observer.start()

        console.print(
            Panel(
                i18n.t("cli.run.reload_mode_panel", watch_dir=watch_dir),
                title=i18n.t("cli.run.reload_title"),
                border_style="info",
            )
        )

        try:
            _spawn()
            while True:
                proc = reload_state["process"]
                # 等待进程退出或重载信号（带超时轮询，保证 Ctrl+C 可响应）
                while proc.poll() is None and not reload_state["reload_event"].is_set():
                    reload_state["reload_event"].wait(timeout=0.2)

                if proc.poll() is None:
                    # 进程仍在运行，由文件变更触发重载：先终止再重启
                    console.print(
                        f"[info]{i18n.t('cli.run.file_changed_restart', file=reload_state['changed_file'])}[/]"
                    )
                    reload_state["reload_event"].clear()
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                    _spawn()
                    continue

                # 进程已退出。若无排队的重载请求，提示等待文件变更
                if not reload_state["reload_event"].is_set():
                    if proc.returncode == 0:
                        console.print(f"[info]{i18n.t('cli.run.process_exited')}[/]")
                    else:
                        console.print(
                            f"[warning]{i18n.t('cli.run.process_crashed', code=proc.returncode)}[/]"
                        )
                    while not reload_state["reload_event"].wait(timeout=0.3):
                        pass

                # 收到重载请求，重启进程
                reload_state["reload_event"].clear()
                console.print(
                    f"[info]{i18n.t('cli.run.file_changed_restart', file=reload_state['changed_file'])}[/]"
                )
                _spawn()
        except KeyboardInterrupt:
            pass
        finally:
            proc = reload_state["process"]
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            observer.stop()
            observer.join()

    def _setup_watchdog(self, watch_dir: str, loop: asyncio.AbstractEventLoop):
        """
        配置 watchdog 监控指定目录的文件变更以实现热重载

        :param watch_dir: [str] 要监控的目录路径
        :param loop: [asyncio.AbstractEventLoop] 用于调度重载的事件循环
        """
        if not Path(watch_dir).exists():
            return

        self._observer = PollingObserver()
        self._handler = ReloadHandler(loop=loop)
        self._observer.schedule(self._handler, watch_dir, recursive=True)
        self._observer.start()

        console.print(
            Panel(
                i18n.t("cli.run.reload_mode_panel", watch_dir=watch_dir),
                title=i18n.t("cli.run.reload_title"),
                border_style="info",
            )
        )
