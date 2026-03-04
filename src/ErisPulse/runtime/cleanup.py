"""
清理管理模块

提供跨平台的进程清理机制，确保子进程能正确调用 sdk.uninit()

{!--< tips >!--}
1. 文件监听机制在所有平台上都能可靠工作
2. 信号处理机制在 Linux/macOS 上优先工作
3. 进程退出时会自动执行清理
{!--< /tips >!--}
"""

import os
import sys
import asyncio
import signal
import threading
from typing import Optional

from ..Core import logger


class CleanupManager:
    """
    清理管理器
    
    提供跨平台的清理机制，确保子进程在终止时能正确清理资源
    
    {!--< tips >!--}
    1. 文件监听机制在所有平台上都能可靠工作
    2. 信号处理机制在 Linux/macOS 上优先工作
    3. 防止重复清理，确保只执行一次
    {!--< /tips >!--}
    """
    
    def __init__(self, signal_file: str = ""):
        """
        初始化清理管理器
        
        :param signal_file: [str] 清理信号文件路径，用于跨进程通信
        """
        self.signal_file = signal_file
        self.listener_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self._cleanup_in_progress = False
        self._lock = asyncio.Lock()
        
    def start(self):
        """
        启动清理监听
        
        启动文件监听线程和信号处理器，确保进程被终止时能执行清理
        """
        if self.signal_file:
            # 启动文件监听线程
            self.listener_thread = threading.Thread(
                target=self._listener,
                daemon=True,
                name="ErisPulseCleanup"
            )
            self.listener_thread.start()
            logger.debug(f"清理监听已启动，文件: {self.signal_file}")
        
        # 注册信号处理器
        self._register_signals()
        
    def _listener(self):
        """
        清理监听线程
        
        持续监听清理信号文件，当文件出现时执行清理
        
        {!--< internal-use >!--}
        """
        while not self.stop_event.is_set():
            if os.path.exists(self.signal_file):
                # 执行清理
                self._trigger_cleanup_async()
                break
            self.stop_event.wait(0.5)
    
    def _trigger_cleanup_async(self):
        """
        在事件循环中触发清理
        
        获取当前事件循环，在其中运行清理任务
        
        {!--< internal-use >!--}
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(self._cleanup(), loop)
        else:
            loop.run_until_complete(self._cleanup())
    
    def _register_signals(self):
        """
        注册信号处理器
        
        注册 SIGTERM 和 SIGINT 信号处理器，确保进程被终止时能执行清理
        
        {!--< internal-use >!--}
        """
        def handler(signum, frame):
            logger.info(f"收到信号 {signum}")
            asyncio.run(self._cleanup())
        
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
        
        if sys.platform == 'win32' and hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, handler)
    
    async def _cleanup(self):
        """
        执行清理
        
        调用 sdk.uninit() 清理所有适配器和模块资源，然后退出进程
        
        {!--< internal-use >!--}
        """
        async with self._lock:
            if self._cleanup_in_progress:
                return
            self._cleanup_in_progress = True
        
        try:
            logger.info("正在清理 SDK 资源...")
            from .. import sdk
            await sdk.uninit()
            logger.info("SDK 资源清理完成")
        except Exception as e:
            logger.error(f"清理失败: {e}")
        finally:
            # 即使有未完成的异步任务也退出
            os._exit(0)
    
    def stop(self):
        """
        停止清理监听
        
        停止文件监听线程，等待最多 1 秒
        
        {!--< internal-use >!--}
        """
        if self.listener_thread:
            self.stop_event.set()
            self.listener_thread.join(timeout=1)


# 全局清理管理器实例
_cleanup_manager: Optional[CleanupManager] = None


def setup_cleanup_subprocess(signal_file: str = ""):
    """
    设置子进程清理机制
    
    根据环境变量 ERISPULSE_SUBPROCESS 判断是否需要启动清理机制
    如果是子进程，则启动清理监听线程和信号处理器
    
    :param signal_file: [str] 清理信号文件路径，用于跨进程通信 (默认: 从环境变量读取)
    """
    global _cleanup_manager
    
    if os.environ.get('ERISPULSE_SUBPROCESS', '').lower() != 'true':
        return
    
    if not signal_file:
        signal_file = os.environ.get('ERISPULSE_CLEANUP_FILE', '')
    
    if signal_file:
        # 创建并启动清理管理器
        _cleanup_manager = CleanupManager(signal_file)
        _cleanup_manager.start()
        logger.info("检测到子进程模式，已启用清理机制")
    else:
        logger.info("检测到子进程模式，已注册信号处理器")


def send_cleanup_signal(signal_file: str) -> bool:
    """
    发送清理信号
    
    创建清理信号文件，通知子进程执行清理操作
    
    :param signal_file: [str] 清理信号文件路径
    :return: [bool] 操作是否成功
    """
    try:
        with open(signal_file, 'w') as f:
            f.write('cleanup')
        logger.debug(f"已创建清理信号文件: {signal_file}")
        return True
    except Exception as e:
        logger.error(f"创建清理信号文件失败: {e}")
        return False
