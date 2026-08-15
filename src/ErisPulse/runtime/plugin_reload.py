"""
ErisPulse 本地插件热重载监控

监控插件文件夹（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir``
配置）下 ``.py`` 文件的变更，变化时自动重新加载对应插件。

设计要点：
- 复用 CLI 的 :class:`PollingObserver`（纯 Python mtime 轮询，后台守护线程）
- 文件变更回调在线程中触发，通过 :func:`asyncio.run_coroutine_threadsafe`
  把重载协程调度回主事件循环执行，避免线程内直接 await
- 变更去抖：短时间（默认 1 秒）内的连续变更只触发一次重载
"""

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

from ..CLI.utils.file_watcher import FileSystemEventHandler, PollingObserver
from ..Core.logger import logger


class _PluginChangeHandler(FileSystemEventHandler):
    """
    {!--< internal-use >!--}
    插件文件变更处理器：.py 变更时调度重载协程
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, on_change: Callable[[str], Coroutine[Any, Any, None]]):
        self._loop = loop
        self._on_change = on_change
        self._last_trigger = 0.0
        self._debounce = 1.0

    def on_modified(self, event):
        """文件修改回调：去抖后调度重载"""
        now = time.monotonic()
        if now - self._last_trigger < self._debounce:
            return
        self._last_trigger = now
        if event.src_path.endswith(".py"):
            logger.info(f"plugin file changed: {event.src_path}")
            try:
                asyncio.run_coroutine_threadsafe(
                    self._on_change(event.src_path), self._loop
                )
            except RuntimeError:
                logger.warning("plugin reload skipped: event loop not running")


class PluginReloadWatcher:
    """
    本地插件热重载监控器

    封装轮询文件监控器，监控插件文件夹变更并触发对应插件的重载回调。

    :param on_reload: 重载回调（接收插件名，返回协程），在主事件循环中执行
    :param interval: 轮询间隔（秒，默认 1.0）

    :example:
    >>> async def handle(name):
    ...     await sdk.reload_plugin(name)
    >>> watcher = PluginReloadWatcher(handle)
    >>> watcher.start()
    >>> # ... 运行中 ...
    >>> watcher.stop()
    """

    def __init__(
        self,
        on_reload: Callable[[str], Coroutine[Any, Any, None]],
        interval: float = 1.0,
    ):
        self._on_reload = on_reload
        self._interval = interval
        self._observer: PollingObserver | None = None
        self._dirs: list[str] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def is_running(self) -> bool:
        """
        监控器是否已启动

        :return: 是否运行中
        """
        return self._observer is not None and self._observer._thread is not None

    def _plugin_dirs(self) -> list[str]:
        """
        解析插件目录列表（与 PluginFolderLoader 同源）

        :return: 插件目录字符串列表
        """
        from .frame_config import get_framework_config

        try:
            framework_config = get_framework_config()
        except Exception:
            framework_config = {}

        raw = framework_config.get("plugins_dir", "plugins")
        if isinstance(raw, str):
            return [raw]
        if isinstance(raw, (list, tuple)):
            return [str(d) for d in raw]
        return ["plugins"]

    def start(self) -> bool:
        """
        启动插件文件监控

        :return: 是否启动成功（无插件目录或已在运行返回 False）
        """
        if self.is_running:
            return False

        self._dirs = [d for d in self._plugin_dirs() if d]
        if not self._dirs:
            return False

        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

        handler = _PluginChangeHandler(self._loop, self._handle_change)
        observer = PollingObserver(interval=self._interval)
        for d in self._dirs:
            observer.schedule(handler, d, recursive=True)
        observer.start()
        self._observer = observer
        logger.info(f"plugin hot reload watching: {self._dirs}")
        return True

    def stop(self) -> None:
        """
        停止插件文件监控
        """
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join()
            except Exception:
                pass
            self._observer = None

    async def _handle_change(self, src_path: str) -> None:
        """
        {!--< internal-use >!--}
        将文件路径解析为插件名并触发重载回调
        """
        from pathlib import Path

        path = Path(src_path).resolve()
        if path.suffix != ".py":
            return
        # 匹配插件目录前缀，把相对路径的首段作为插件名
        for d in self._dirs:
            base = Path(d).resolve()
            try:
                rel = path.relative_to(base)
            except ValueError:
                continue
            parts = list(rel.parts)
            if not parts:
                continue
            # 单文件：plugins/dice.py → dice（首段含 .py 后缀）
            # 包形式：plugins/weather/Core.py → weather；__init__.py 同样取包名
            name = parts[0]
            name = name.removesuffix(".py")
            await self._on_reload(name)
            return

    async def close(self) -> None:
        """
        停止监控并等待后台线程结束
        """
        self.stop()


__all__ = ["PluginReloadWatcher"]
