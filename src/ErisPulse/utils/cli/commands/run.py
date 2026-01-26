"""
Run 命令实现

运行主程序
"""

import os
import sys
import time
from argparse import ArgumentParser
from watchdog.observers import Observer
from rich.panel import Panel

from ...console import console
from ...reload_handler import ReloadHandler
from ..base import Command


class RunCommand(Command):
    """运行命令"""
    
    name = "run"
    description = "运行主程序"
    
    def add_arguments(self, parser: ArgumentParser):
        """添加命令参数"""
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
        """执行命令"""
        script = args.script or "main.py"
        
        # 检查脚本是否存在
        if not os.path.exists(script):
            from .. import _prepare_environment
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
