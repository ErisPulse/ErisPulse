"""
ErisPulse 本地插件热重载监控

监控插件文件夹（默认 ``plugins/``，可通过 ``ErisPulse.framework.plugins_dir``
配置）下 ``.py`` 文件的变更，变化时自动重新加载对应插件。

设计要点：
- 复用 :class:`~ErisPulse.runtime.file_watcher.PollingObserver`（纯 Python mtime 轮询，后台守护线程）
- 消费 created / modified / deleted 三类事件：新增插件热装载、删除插件热卸载
  （复用加载器「发现不到即移除」语义）、修改触发热重载
- 文件变更回调在线程中触发，通过 :func:`asyncio.run_coroutine_threadsafe`
  把重载协程调度回主事件循环执行，避免线程内直接 await；事件循环支持延迟
  解析（启动早于 ``sdk.run()`` 时先记住 None，触发时经主循环注册表回查）
- 变更合并去抖：首个事件立即触发，窗口（FILE_RELOAD_DEBOUNCE_SECS）内的
  后续变更合并且窗口静默后统一补发一次（不丢弃）
- 重载失败且文件 mtime 又变化（编辑器原子保存的半写窗口）时单次重试
"""

import asyncio
import threading
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

from ..Core.constants import (
    FILE_RELOAD_DEBOUNCE_SECS,
    FILE_WATCH_POLL_INTERVAL_SECS,
    PLUGIN_RELOAD_RETRY_DELAY_SECS,
)
from ..Core.i18n import i18n
from ..Core.logger import logger
from .file_watcher import FileSystemEventHandler, PollingObserver


class _PluginChangeHandler(FileSystemEventHandler):
    """
    {!--< internal-use >!--}
    插件文件变更处理器：created/modified/deleted 合并去抖后调度重载协程
    """

    @staticmethod
    def _stat_mtime(path: str) -> float | None:
        """{!--< internal-use >!--} 读取文件 mtime，失败（已删除等）返回 None"""
        try:
            return Path(path).stat().st_mtime
        except OSError:
            return None

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop | None,
        on_change: Callable[[str], Coroutine[Any, Any, Any]],
    ):
        self._loop = loop
        self._on_change = on_change
        self._debounce = FILE_RELOAD_DEBOUNCE_SECS
        self._lock = threading.Lock()
        self._pending: set[str] = set()
        self._timer: threading.Timer | None = None

    # ------------------------------------------------------------------
    # 事件回调（watchdog 线程 / 轮询线程中触发）
    # ------------------------------------------------------------------

    def on_modified(self, event) -> None:
        """文件修改回调：合并去抖后调度重载"""
        self._on_event(event.src_path, "runtime.plugin.file_changed")

    def on_created(self, event) -> None:
        """文件创建回调：新插件文件纳入热装载"""
        self._on_event(event.src_path, "runtime.plugin.file_created")

    def on_deleted(self, event) -> None:
        """文件删除回调：复用加载器「发现不到即移除」语义热卸载"""
        self._on_event(event.src_path, "runtime.plugin.file_deleted")

    def on_moved(self, event) -> None:
        """文件移动回调（轮询实现不触发，watchdog 实现接入时等价删除+创建）"""
        dest = getattr(event, "dest_path", None)
        self._on_event(event.src_path, "runtime.plugin.file_deleted")
        if dest:
            self._on_event(dest, "runtime.plugin.file_created")

    def _on_event(self, src_path: str, message_key: str) -> None:
        if not src_path.endswith(".py"):
            return
        logger.info(i18n.t(message_key, path=src_path))
        with self._lock:
            if self._timer is not None:
                # 去抖窗口内：合并入队，窗口静默后由定时器统一补发
                self._pending.add(src_path)
                return
            # 窗口外：立即触发（保持「保存即重载」的即时性），并武装补发定时器。
            # 定时器先存字段再在锁外 start：并发 close() 可能把字段置 None，
            # 锁外必须用局部引用，否则 watcher 线程内 AttributeError
            paths = {src_path}
            timer = threading.Timer(self._debounce, self._flush_pending)
            timer.daemon = True
            self._timer = timer
        timer.start()
        self._dispatch(paths)

    def _flush_pending(self) -> None:
        """去抖窗口到期：补发窗口内合并的变更（可为空）"""
        with self._lock:
            self._timer = None
            if not self._pending:
                return
            paths = set(self._pending)
            self._pending.clear()
        self._dispatch(paths)

    def close(self) -> None:
        """停止补发定时器（监控停止时调用）"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._pending.clear()

    # ------------------------------------------------------------------
    # 调度到主事件循环
    # ------------------------------------------------------------------

    def _resolve_loop(self) -> asyncio.AbstractEventLoop | None:
        """解析可用事件循环：构造时捕获的循环优先，其次主循环注册表延迟解析"""
        if self._loop is not None and not self._loop.is_closed():
            return self._loop
        try:
            from .tasks import _get_main_loop

            main = _get_main_loop()
        except Exception:
            main = None
        if main is not None and not main.is_closed():
            self._loop = main
            return main
        return None

    def _dispatch(self, paths: set[str]) -> None:
        loop = self._resolve_loop()
        if loop is None:
            logger.warning(i18n.t("runtime.plugin.reload_skipped_no_loop"))
            return
        try:
            asyncio.run_coroutine_threadsafe(self._drain(paths), loop)
        except RuntimeError:
            logger.warning(i18n.t("runtime.plugin.reload_skipped_no_loop"))

    async def _drain(self, paths: set[str]) -> None:
        """逐个触发重载回调；失败且文件仍在变化（半写窗口）时单次重试"""
        for path in sorted(paths):
            name = resolve_plugin_name(path)
            if name is None:
                continue
            before = self._stat_mtime(path)
            try:
                ok = await self._on_change(name)
            except Exception as e:
                logger.error(i18n.t("runtime.plugin.reload_failed", name=name, error=repr(e)))
                continue
            if ok is False and before is not None:
                await asyncio.sleep(PLUGIN_RELOAD_RETRY_DELAY_SECS)
                after = self._stat_mtime(path)
                if after is not None and after != before:
                    logger.info(i18n.t("runtime.plugin.reload_retried", path=path))
                    try:
                        await self._on_change(name)
                    except Exception as e:
                        logger.error(
                            i18n.t("runtime.plugin.reload_failed", name=name, error=repr(e))
                        )


def resolve_plugin_name(src_path: str, plugin_dirs: list[str] | None = None) -> str | None:
    """
    {!--< internal-use >!--}
    将插件文件路径解析为插件名（单文件取文件名，包形式取首段目录名）

    供插件热重载的调度线程与 PluginReloadWatcher 回调共用。
    """
    path = Path(src_path).resolve()
    if path.suffix != ".py":
        return None
    dirs = plugin_dirs
    if dirs is None:
        from .frame_config import get_framework_config

        try:
            framework_config = get_framework_config()
        except Exception:
            framework_config = {}
        raw = framework_config.get("plugins_dir", "plugins")
        if isinstance(raw, str):
            dirs = [raw]
        elif isinstance(raw, (list, tuple)):
            dirs = [str(d) for d in raw]
        else:
            dirs = ["plugins"]
    for d in dirs:
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
        return parts[0].removesuffix(".py")
    return None


class PluginReloadWatcher:
    """
    本地插件热重载监控器

    封装轮询文件监控器，监控插件文件夹变更并触发对应插件的重载回调。

    :param on_reload: 重载回调（接收插件名，返回协程），在主事件循环中执行
    :param interval: 轮询间隔（秒，默认 FILE_WATCH_POLL_INTERVAL_SECS）

    :example:
    >>> async def handle(name):
    ...     await sdk.reload_module(name)
    >>> watcher = PluginReloadWatcher(handle)
    >>> watcher.start()
    >>> # ... 运行中 ...
    >>> watcher.stop()
    """

    def __init__(
        self,
        on_reload: Callable[[str], Coroutine[Any, Any, Any]],
        interval: float = FILE_WATCH_POLL_INTERVAL_SECS,
    ):
        self._on_reload = on_reload
        self._interval = interval
        self._observer: PollingObserver | None = None
        self._handler: _PluginChangeHandler | None = None
        self._dirs: list[str] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def is_running(self) -> bool:
        """
        监控器是否已启动

        :return: 是否运行中
        """
        return self._observer is not None and self._observer.is_running

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

    def _resolve_ignore_dirs(self) -> list[str] | None:
        """
        {!--< internal-use >!--}
        解析文件监控忽略目录：ErisPulse.framework.watch_ignore_dirs
        （None = 内置默认清单；列表 = 整体替换；[] = 不忽略）
        """
        from .frame_config import get_framework_config

        try:
            framework_config = get_framework_config()
        except Exception:
            return None
        raw = framework_config.get("watch_ignore_dirs")
        if raw is None:
            return None
        if isinstance(raw, (list, tuple)):
            return [str(d) for d in raw]
        return None

    def start(self) -> bool:
        """
        启动插件文件监控

        {!--< tips >!--}
        无运行事件循环时仍返回 True：事件循环经主循环注册表延迟解析
        （``sdk.run()`` 启动后自动可用），此前触发的变更会记 warning 跳过。
        {!--< /tips >!--}

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
            logger.warning(i18n.t("runtime.plugin.watcher_no_loop"))

        self._handler = _PluginChangeHandler(self._loop, self._handle_change)
        observer = PollingObserver(
            interval=self._interval,
            ignore_dirs=self._resolve_ignore_dirs(),
        )
        for d in self._dirs:
            observer.schedule(self._handler, d, recursive=True)
        observer.start()
        self._observer = observer
        logger.info(i18n.t("runtime.plugin.watching", dirs=self._dirs))
        return True

    def stop(self) -> None:
        """
        停止插件文件监控
        """
        if self._handler is not None:
            self._handler.close()
            self._handler = None
        if self._observer is not None:
            try:
                self._observer.stop()
                # 有限等待：事件循环线程内调用 close()/stop() 时不被一个
                # 轮询周期卡住；线程为守护线程，超时后自行退出
                self._observer.join(timeout=self._interval * 2)
            except Exception as e:
                logger.debug(i18n.t("runtime.watcher.stop_failed", error=e))
            self._observer = None

    async def _handle_change(self, src_path: str) -> Any:
        """
        {!--< internal-use >!--}
        将文件路径解析为插件名并触发重载回调（透传回调返回值）
        """
        name = resolve_plugin_name(src_path, self._dirs)
        if name is None:
            return None
        return await self._on_reload(name)

    async def close(self) -> None:
        """
        停止监控并等待后台线程结束
        """
        self.stop()


__all__ = ["PluginReloadWatcher", "resolve_plugin_name"]
