"""
ErisPulse SDK 热重载处理器

实现热重载功能，监控文件变化并重启进程
"""

import asyncio
import os
import subprocess
import sys
import threading
import time
from watchdog.events import FileSystemEventHandler

from rich.console import Console

# 全局控制台实例，从CLI模块导入
console = Console()


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
        from ErisPulse.Core import adapter, logger
        # 在重载前确保所有适配器正确停止
        try:
            # 检查适配器是否正在运行
            if hasattr(adapter, '_started_instances') and adapter._started_instances:
                logger.info("正在停止适配器...")
                # 创建新的事件循环来运行异步停止操作
                
                # 如果在主线程中
                if threading.current_thread() is threading.main_thread():
                    try:
                        # 在新线程中运行适配器停止
                        stop_thread = threading.Thread(target=lambda: asyncio.run(adapter.shutdown()))
                        stop_thread.start()
                        stop_thread.join(timeout=10)  # 最多等待10秒
                    except RuntimeError:
                        # 没有运行中的事件循环
                        asyncio.run(adapter.shutdown())
                else:
                    # 在非主线程中，创建新的事件循环
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(adapter.shutdown())
                
                logger.info("适配器已停止")
        except Exception as e:
            logger.warning(f"停止适配器时出错: {e}")
        
        # 原有的重载逻辑
        logger.info(f"检测到文件变更 ({reason})，正在重启...")
        self._terminate_process()
        self.start_process()