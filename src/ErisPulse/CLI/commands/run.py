"""
Run 命令实现

运行主程序
"""

import os
import time
import sys
import subprocess
from argparse import ArgumentParser
from watchdog.observers import Observer
from rich.panel import Panel
from watchdog.events import FileSystemEventHandler

from ..console import console
from ..base import Command

class ReloadHandler(FileSystemEventHandler):
    """
    文件系统事件处理器
    
    实现热重载功能，监控文件变化并重启进程
    
    {!--< tips >!--}
    1. 支持.py文件修改重载
    2. 支持配置文件修改重载
    {!--< /tips >!--}
    """

    def __init__(self, script_path: str, reload_mode: bool = False):
        """
        初始化处理器
        
        :param script_path: 要监控的脚本路径
        :param reload_mode: 是否启用重载模式
        """
        super().__init__()
        self.script_path = os.path.abspath(script_path)
        self.process = None
        self.last_reload = time.time()
        self.reload_mode = reload_mode
        self.start_process()
        self.watched_files = set()

    def start_process(self):
        """启动监控进程"""
        if self.process:
            self._terminate_process()
            
        console.print(f"[bold]启动进程: [path]{self.script_path}[/][/]") 
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            self.last_reload = time.time()
        except Exception as e:
            console.print(f"[error]启动进程失败: {e}[/]")
            raise

    def _terminate_process(self):
        """
        终止当前进程
        
        :raises subprocess.TimeoutExpired: 进程终止超时时抛出
        """
        try:
            self.process.terminate()
            # 等待最多2秒让进程正常退出
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            console.print("[warning]进程未正常退出，强制终止...[/]")
            self.process.kill()
            self.process.wait()
        except Exception as e:
            console.print(f"[error]终止进程时出错: {e}[/]")

    def on_modified(self, event):
        """
        文件修改事件处理
        
        :param event: 文件系统事件
        """
        now = time.time()
        if now - self.last_reload < 1.0:  # 防抖
            return
            
        if event.src_path.endswith(".py") and self.reload_mode:
            self._handle_reload(event, "文件变动")
        # elif event.src_path.endswith(("config.toml", ".env")):
        #     self._handle_reload(event, "配置变动")

    def _handle_reload(self, event, reason: str):
        """
        处理热重载逻辑
        :param event: 文件系统事件
        :param reason: 重载原因
        """
    
        try:
            import asyncio
            from ... import uninit
            console.print(f"检测到文件变更 ({reason})，正在关闭适配器和模块...")
            asyncio.run(uninit())
        except Exception as e:
            console.print(f"关闭适配器和模块时出错: {e}")
        
        console.print("正在重启...")
        self._terminate_process()
        self.start_process()


class RunCommand(Command):
    name = "run"
    description = "运行主程序"
    
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            'script',
            nargs='?',
            help='要运行的主程序路径 (默认: main.py)'
        )
        parser.add_argument(
            '--reload',
            action='store_true',
            help='启用热重载模式'
        )
        parser.add_argument(
            '--no-reload',
            action='store_true',
            help='禁用热重载模式'
        )
    
    def execute(self, args):
        script = args.script or "main.py"
        
        # 检查脚本是否存在
        if not os.path.exists(script):
            from ... import _prepare_environment
            import asyncio
            asyncio.run(_prepare_environment())
        
        reload_mode = args.reload and not args.no_reload
        
        # 设置文件监控
        self.observer = None
        self.handler = None
        self._setup_watchdog(script, reload_mode)
        
        try:
            # 保持运行
            console.print("\n[cyan]按 Ctrl+C 停止程序[/cyan]")
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            console.print("\n[info]正在安全关闭...[/]")
            self._cleanup()
            console.print("[success]已安全退出[/]")
    
    def _setup_watchdog(self, script_path: str, reload_mode: bool):
        """
        设置文件监控
        
        :param script_path: 要监控的脚本路径
        :param reload_mode: 是否启用重载模式
        """
        watch_dirs = [
            os.path.dirname(os.path.abspath(script_path)),
        ]
        
        # 添加配置目录
        config_dir = os.path.abspath(os.getcwd())
        if config_dir not in watch_dirs:
            watch_dirs.append(config_dir)
        
        self.handler = ReloadHandler(script_path, reload_mode)
        self.observer = Observer()
        
        for d in watch_dirs:
            if os.path.exists(d):
                self.observer.schedule(
                    self.handler,
                    d,
                    recursive=reload_mode
                )
                console.print(f"[dim]监控目录: [path]{d}[/][/]")
        
        self.observer.start()
        
        mode_desc = "[bold]开发重载模式[/]" if reload_mode else "[bold]配置监控模式[/]"
        console.print(Panel(
            f"{mode_desc}\n监控目录: [path]{', '.join(watch_dirs)}[/]",
            title="热重载已启动",
            border_style="info"
        ))
    
    def _cleanup(self):
        """清理资源"""
        if self.observer:
            self.observer.stop()
            if self.handler and self.handler.process:
                self.handler._terminate_process()
            self.observer.join()
