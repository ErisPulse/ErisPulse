"""
Run 命令实现

直接运行主程序，支持热重载模式
"""

import asyncio
import os
import runpy
import subprocess
import sys
import threading
import time
from argparse import ArgumentParser

from rich.panel import Panel

from ..base import Command
from ..console import console
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
                i18n.t("cli.run.file_changed", file=os.path.basename(event.src_path))
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
            if not os.path.exists(script):
                console.print(
                    f"[error]{i18n.t('cli.run.script_not_found', script=script)}[/]"
                )
                console.print(f"[info]{i18n.t('cli.run.use_init')}[/]")
                return
            if os.path.isdir(script):
                console.print(
                    f"[error]{i18n.t('cli.run.is_directory', script=script)}[/]"
                )
                console.print(
                    "[info]{0}[/]".format(i18n.t("cli.run.specify_file", script=script))
                )
                return
            self._run_script(script, reload_mode)
        else:
            self._run_internal(reload_mode)

    _RESTART_EXIT_CODE = 42

    def _run_internal(self, reload_mode: bool):
        """
        直接运行 SDK（不指定脚本时）

        以子进程方式运行 SDK，支持硬重启：当 SDK 进程以特定退出码退出时，
        自动重新启动新进程，确保资源完全释放。
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

        import signal

        try:
            while True:
                process = subprocess.Popen(cmd)

                # 转发 SIGTERM/SIGINT 到子进程，使 SDK 能优雅关闭
                def _forward_signal(signum, frame):
                    try:
                        process.send_signal(signum)
                    except Exception:
                        pass

                old_term = signal.signal(signal.SIGTERM, _forward_signal)
                old_int = signal.signal(signal.SIGINT, _forward_signal)

                process.wait()

                # 恢复默认信号处理
                signal.signal(signal.SIGTERM, old_term)
                signal.signal(signal.SIGINT, old_int)

                if process.returncode == self._RESTART_EXIT_CODE:
                    console.print(f"[info]{i18n.t('cli.run.restart_request')}[/]")
                    time.sleep(0.5)
                    continue
                break
        except KeyboardInterrupt:
            pass

    def _run_script(self, script_path: str, reload_mode: bool):
        """
        运行指定的脚本文件，可选启用热重载

        :param script_path: [str] 脚本文件路径
        :param reload_mode: [bool] 是否启用热重载模式
        """
        script_path_abs = os.path.abspath(script_path)

        if reload_mode:
            self._run_script_with_reload(script_path_abs)
        else:
            script_dir = os.path.dirname(script_path_abs)
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
        watch_dir = os.path.dirname(script_path_abs)

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
                reload_state["changed_file"] = os.path.basename(event.src_path)
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
        if not os.path.exists(watch_dir):
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
