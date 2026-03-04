"""
Run 命令实现

运行主程序
"""

import os
import time
import sys
import subprocess
import tempfile
from argparse import ArgumentParser
from watchdog.observers import Observer
from rich.panel import Panel
from watchdog.events import FileSystemEventHandler

from ..console import console
from ..base import Command


class ReloadHandler(FileSystemEventHandler):
    """
    文件系统事件处理器
    
    实现热重载功能，监控 .py 文件变更并自动重启
    
    {!--< tips >!--}
    1. 仅在 --reload 模式下启用监控
    2. 监控 .py 文件，修改后创建清理信号文件并重启
    3. 子进程检测到清理信号文件后自动调用 sdk.uninit()
    4. 进程终止时使用清理信号文件确保资源正确释放
    {!--< /tips >!--}
    """

    def __init__(self, script_path: str, reload_mode: bool = False):
        """
        初始化处理器
        
        :param script_path: [str] 要监控的脚本路径
        :param reload_mode: [bool] 是否启用重载模式 (默认: False)
        """
        super().__init__()
        self.script_path = os.path.abspath(script_path)
        self.process = None
        self.last_reload = time.time()
        self.reload_mode = reload_mode
        # 清理信号文件
        self.cleanup_file = os.path.join(
            tempfile.gettempdir(),
            f"erispulse_cleanup_{os.getpid()}.signal"
        )
        self.start_process()

    def start_process(self):
        """
        启动监控进程
        
        注入环境变量，让子进程知道自己是由 CLI 启动的
        """
        if self.process:
            self._terminate_process()
        
        console.print(f"[bold]启动进程: [path]{self.script_path}[/][/]") 
        env = os.environ.copy()
        env['ERISPULSE_SUBPROCESS'] = 'true'
        env['ERISPULSE_CLEANUP_FILE'] = self.cleanup_file
        
        self.process = subprocess.Popen(
            [sys.executable, self.script_path],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=env
        )
        self.last_reload = time.time()

    def _terminate_process(self):
        """
        终止当前进程
        
        创建清理信号文件，通知子进程执行清理操作
        等待最多 10 秒让进程正常退出
        """
        try:
            # console.print(f"[dim]正在终止进程 (PID: {self.process.pid})[/]")
            console.print(f"[dim]正在终止进程[/]")

            # 创建清理信号文件
            try:
                with open(self.cleanup_file, 'w') as f:
                    f.write('cleanup')
                # console.print(f"[dim]已创建清理信号文件: {self.cleanup_file}[/]")
            except Exception as e:
                console.print(f"[warning]创建清理信号文件失败: {e}[/]")
            
            # 等待子进程开始清理
            time.sleep(0.5)
            
            # 终止进程
            self.process.terminate()
            
            # 等待进程退出
            returncode = self.process.wait(timeout=10)
            console.print(f"[dim]进程已退出[/]")
            
            # 清理信号文件
            try:
                if os.path.exists(self.cleanup_file):
                    os.remove(self.cleanup_file)
            except Exception:
                pass
        except subprocess.TimeoutExpired:
            console.print("[warning]进程未在10秒内正常退出，强制终止[/]")
            self.process.kill()
            self.process.wait()
        except Exception as e:
            console.print(f"[error]终止进程时出错: {e}[/]")

    def on_modified(self, event):
        """
        文件修改事件处理
        
        仅在 --reload 模式下监控 .py 文件变更
        
        :param event: [FileSystemEvent] 文件系统事件
        """
        now = time.time()
        if now - self.last_reload < 1.0:  # 防抖
            return
            
        if event.src_path.endswith(".py") and self.reload_mode:
            self._handle_reload(event, "文件变动")

    def _handle_reload(self, event, reason: str):
        """
        处理热重载逻辑
        
        创建清理信号文件，通知子进程执行清理，然后重启进程
        
        :param event: [FileSystemEvent] 文件系统事件
        :param reason: [str] 重载原因
        """
        console.print(f"检测到文件变更 ({reason})，正在重启...")
        self._terminate_process()
        self.start_process()


class RunCommand(Command):
    """
    Run 命令
    
    运行主程序，支持热重载模式
    """

    name = "run"
    description = "运行主程序"
    
    def add_arguments(self, parser: ArgumentParser):
        """
        添加命令行参数
        
        :param parser: [ArgumentParser] 参数解析器
        """
        parser.add_argument(
            'script',
            nargs='?',
            default='main.py',
            help='要运行的主程序路径 (默认: main.py)'
        )
        parser.add_argument(
            '--reload',
            action='store_true',
            default=False,
            help='启用热重载模式'
        )
    
    def execute(self, args):
        """
        执行命令
        
        :param args: [Namespace] 命令行参数
        """
        script = args.script
        reload_mode = args.reload
        
        # 检查脚本是否存在
        if not os.path.exists(script):
            console.print(f"[info]脚本 [path]{script}[/] 不存在，正在创建...[/]")
            from ... import _prepare_environment
            import asyncio
            asyncio.run(_prepare_environment(script))
        
        # 设置文件监控
        self.observer = Observer()
        self.handler = ReloadHandler(script, reload_mode)
        self._setup_watchdog(script, reload_mode)
        
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._cleanup()
    
    def _setup_watchdog(self, script_path: str, reload_mode: bool) -> list:
        """
        设置文件监控
        
        :param script_path: [str] 要监控的脚本路径
        :param reload_mode: [bool] 是否启用重载模式
        :return: [list] 监控的目录列表
        """
        watch_dirs = [
            os.path.dirname(os.path.abspath(script_path)),
        ]
        
        for d in watch_dirs:
            if os.path.exists(d):
                self.observer.schedule(
                    self.handler,
                    d,
                    recursive=reload_mode
                )
                console.print(f"[dim]监控目录: [path]{d}[/][/]")

        if reload_mode:
            console.print(Panel(
                f"[bold]开发重载模式[/]\n监控目录: [path]{', '.join(watch_dirs)}[/]",
                title="热重载已启动",
                border_style="info"
            ))
        else:
            console.print(Panel(
                f"主程序: [path]{script_path}[/]",
                title="程序已启动",
                border_style="info"
            ))
        
        # 启动 observer
        self.observer.start()
        return watch_dirs
    
    def _cleanup(self):
        """
        清理资源
        
        停止文件监控，终止子进程
        """
        if self.observer:
            self.observer.stop()
            self.observer.join()
            if self.handler and self.handler.process:
                self.handler._terminate_process()
