"""
Run 命令实现

直接运行主程序，支持热重载模式
"""

import os
import time
import asyncio
from argparse import ArgumentParser
from watchdog.observers import Observer
from rich.panel import Panel
from watchdog.events import FileSystemEventHandler

from ..console import console
from ..base import Command


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
        super().__init__()
        self._loop = loop
        self._last_reload = 0.0

    def on_modified(self, event):
        now = time.time()
        if now - self._last_reload < 1.0:
            return
        if event.src_path.endswith(".py"):
            self._last_reload = now
            self._schedule_reload(event)

    def _schedule_reload(self, event):
        async def _do_reload():
            try:
                from ... import sdk
                await sdk.restart()
            except Exception as e:
                console.print(f"[error]热重载失败: {e}[/]")

        console.print(f"检测到文件变更 ({os.path.basename(event.src_path)})，正在热重载...")
        asyncio.run_coroutine_threadsafe(_do_reload(), self._loop)


class RunCommand(Command):
    """
    Run 命令
    
    运行主程序，支持热重载模式
    """

    name = "run"
    description = "运行主程序"
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'script',
            nargs='?',
            default=None,
            help='要运行的主程序路径 (不指定则直接运行 SDK)'
        )
        parser.add_argument(
            '--reload',
            action='store_true',
            default=False,
            help='启用热重载模式'
        )
    
    def execute(self, args):
        script = args.script
        reload_mode = args.reload
        
        if script:
            if not os.path.exists(script):
                console.print(f"[error]脚本 [path]{script}[/] 不存在[/]")
                console.print("[info]使用 [cyan]epsdk init[/cyan] 创建新项目[/]")
                return
            self._run_script(script, reload_mode)
        else:
            self._run_internal(reload_mode)

    def _run_internal(self, reload_mode: bool):
        """
        直接运行 SDK（不指定脚本时）
        """
        async def _run():
            from ... import sdk

            if reload_mode:
                loop = asyncio.get_running_loop()
                self._setup_watchdog(".", loop)

            await sdk.run(keep_running=True)

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            pass
        finally:
            if reload_mode and hasattr(self, '_observer'):
                self._observer.stop()
                self._observer.join()

    def _run_script(self, script_path: str, reload_mode: bool):
        """
        运行指定脚本文件
        """
        async def _run():
            from ... import sdk

            if reload_mode:
                loop = asyncio.get_running_loop()
                watch_dir = os.path.dirname(os.path.abspath(script_path))
                self._setup_watchdog(watch_dir, loop)

            await sdk.run(keep_running=True)

        try:
            asyncio.run(_run())
        except KeyboardInterrupt:
            pass
        finally:
            if reload_mode and hasattr(self, '_observer'):
                self._observer.stop()
                self._observer.join()

    def _setup_watchdog(self, watch_dir: str, loop: asyncio.AbstractEventLoop):
        if not os.path.exists(watch_dir):
            return

        self._observer = Observer()
        self._handler = ReloadHandler(loop=loop)
        self._observer.schedule(self._handler, watch_dir, recursive=True)
        self._observer.start()

        console.print(Panel(
            f"[bold]开发重载模式[/]\n监控目录: [path]{watch_dir}[/]",
            title="热重载已启动",
            border_style="info"
        ))
