"""
开发模式细粒度热重载监控

供 ``epsdk run --reload`` 的 worker 与脚本模式子进程共用：

- 按 :func:`runtime.reload_target.classify_reload_path` 判定变更文件的最小
  重载单元（单模块 / 单适配器 / 插件 / 进程重启）
- 合并去抖：首个事件立即触发，窗口内后续变更在窗口静默后统一补发
- 插件目录默认移交 ``PluginReloadWatcher``，本监控排除以免双重触发
"""

import asyncio
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..Core.constants import (
    FILE_RELOAD_DEBOUNCE_SECS,
    FILE_WATCH_POLL_INTERVAL_SECS,
    FILE_WATCHER_IGNORED_DIRS,
)
from ..Core.i18n import i18n
from ..Core.logger import logger
from .file_watcher import (
    FileChangeEvent,
    FileSystemEventHandler,
    PollingObserver,
)
from .frame_config import get_framework_config
from .reload_target import ReloadTarget, classify_reload_path

__all__ = ["DevReloadHandler", "DevWatcher"]


class DevReloadHandler(FileSystemEventHandler):
    """
    细粒度热重载文件事件处理器

    {!--< tips >!--}
    1. 文件监控运行在独立线程，通过 run_coroutine_threadsafe 调度到事件循环
    2. 去抖窗口由 ``FILE_RELOAD_DEBOUNCE_SECS`` 控制
    3. 同一批变更按 ``(kind, name, reason)`` 去重，避免重复重载
    {!--< /tips >!--}
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        sdk: Any,
        *,
        entry_paths: "tuple[str | Path, ...]" = (),
        notify: "Callable[[set[str]], None] | None" = None,
    ):
        """
        初始化处理器

        :param loop: 调度重载协程的事件循环
        :param sdk: SDK 实例（读取注册表并执行重载）
        :param entry_paths: 入口脚本路径（缺省从 ``sys.argv[0]`` 推断）
        :param notify: 文件变更提示回调（接收本批变更路径）
        """
        super().__init__()
        self._loop = loop
        self._sdk = sdk
        self._entry_paths = entry_paths
        self._notify = notify
        self._debounce = FILE_RELOAD_DEBOUNCE_SECS
        self._lock = threading.Lock()
        self._pending: set[str] = set()
        self._timer: threading.Timer | None = None

    def on_modified(self, event: FileChangeEvent) -> None:
        """
        文件修改事件回调

        :param event: 文件系统事件
        """
        self._on_event(event.src_path)

    def on_created(self, event: FileChangeEvent) -> None:
        """
        文件创建事件回调

        :param event: 文件系统事件
        """
        self._on_event(event.src_path)

    def _on_event(self, src_path: str) -> None:
        """{!--< internal-use >!--} 合并去抖入口"""
        if not src_path.endswith(".py"):
            return
        with self._lock:
            if self._timer is not None:
                self._pending.add(src_path)
                return
            paths = {src_path}
            timer = threading.Timer(self._debounce, self._flush_pending)
            timer.daemon = True
            self._timer = timer
        timer.start()
        self._dispatch(paths)

    def _flush_pending(self) -> None:
        """{!--< internal-use >!--} 去抖窗口到期补发合并变更"""
        with self._lock:
            self._timer = None
            if not self._pending:
                return
            paths = set(self._pending)
            self._pending.clear()
        self._dispatch(paths)

    def close(self) -> None:
        """停止补发定时器并清空待发队列"""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._pending.clear()

    def _dispatch(self, paths: set[str]) -> None:
        """{!--< internal-use >!--} 判定目标并调度重载"""
        if self._notify is not None:
            try:
                self._notify(set(paths))
            except Exception as e:
                logger.debug(f"dev watcher notify callback failed: {e!r}")

        targets: dict[tuple[str, str | None, str | None], ReloadTarget] = {}
        for path in sorted(paths):
            target = classify_reload_path(
                path, self._sdk, self._entry_paths
            )
            if target.kind == "plugin":
                continue
            targets[(target.kind, target.name, target.reason)] = target
        if not targets:
            return

        async def _execute() -> None:
            for target in targets.values():
                await self._apply(target)

        try:
            asyncio.run_coroutine_threadsafe(_execute(), self._loop)
        except RuntimeError as e:
            logger.debug(f"dev watcher dispatch dropped: event loop closed ({e!r})")

    async def _apply(self, target: ReloadTarget) -> None:
        """{!--< internal-use >!--} 执行单个重载目标"""
        try:
            if target.kind == "module" and target.name:
                logger.info(
                    i18n.t("runtime.dev_reload.reload_module", name=target.name)
                )
                await self._sdk.reload_module(target.name)
                return
            if target.kind == "adapter" and target.name:
                logger.info(
                    i18n.t(
                        "runtime.dev_reload.reload_adapter", name=target.name
                    )
                )
                await self._sdk.reload_adapter(target.name)
                return

            reason = target.reason or "unmapped"
            logger.info(
                i18n.t("runtime.dev_reload.restart", reason=reason)
            )
            if getattr(self._sdk, "is_supervised", lambda: False)():
                await self._sdk.hard_restart(reason=reason)
            else:
                await self._sdk.restart()
        except Exception as e:
            logger.error(
                i18n.t("runtime.dev_reload.failed", error=e)
            )


class DevWatcher:
    """
    开发模式文件监控器

    监控指定目录（默认当前目录）下的 ``.py`` 变更，按判定结果执行单模块 /
    单适配器重载或进程级重启。

    {!--< tips >!--}
    1. 忽略目录取自 ``ErisPulse.framework.watch_ignore_dirs``；插件目录
       默认追加到忽略清单，由其专用 watcher 处理
    2. 与 ``PluginReloadWatcher`` 可同时运行，二者监控范围互补
    {!--< /tips >!--}
    """

    def __init__(
        self,
        sdk: Any,
        *,
        entry_paths: "tuple[str | Path, ...]" = (),
    ):
        """
        初始化监控器

        :param sdk: SDK 实例
        :param entry_paths: 入口脚本路径
        """
        self._sdk = sdk
        self._entry_paths = entry_paths
        self._observer: PollingObserver | None = None
        self._handler: DevReloadHandler | None = None

    def start(
        self,
        watch_dir: str = ".",
        loop: "asyncio.AbstractEventLoop | None" = None,
        notify: "Callable[[set[str]], None] | None" = None,
    ) -> bool:
        """
        启动监控

        :param watch_dir: 监控目录
        :param loop: 调度重载的事件循环（缺省取当前运行循环）
        :param notify: 文件变更提示回调
        :return: 是否启动成功
        """
        if not Path(watch_dir).exists():
            return False
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return False

        ignore = self._resolve_ignore_dirs()
        merged_ignore = (
            set(FILE_WATCHER_IGNORED_DIRS) if ignore is None else set(ignore)
        )
        self._observer = PollingObserver(ignore_dirs=sorted(merged_ignore))
        self._handler = DevReloadHandler(
            loop,
            self._sdk,
            entry_paths=self._entry_paths,
            notify=notify,
        )
        self._observer.schedule(self._handler, watch_dir, recursive=True)
        self._observer.start()
        return True

    def stop(self) -> None:
        """停止监控（幂等）"""
        if self._handler is not None:
            self._handler.close()
            self._handler = None
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=FILE_WATCH_POLL_INTERVAL_SECS * 2)
            except Exception as e:
                logger.debug(f"dev watcher stop failed: {e!r}")
            self._observer = None

    @staticmethod
    def _resolve_ignore_dirs() -> "list[str] | None":
        """{!--< internal-use >!--} 解析忽略目录（含插件目录）"""
        try:
            framework = get_framework_config()
        except Exception:
            framework = {}

        raw = framework.get("watch_ignore_dirs")
        ignore: list[str] | None = None
        if isinstance(raw, (list, tuple)):
            ignore = [str(d) for d in raw]

        plugin_dirs: list[str] = []
        if framework.get("watch_include_plugin_dirs", True):
            raw_dirs = framework.get("plugins_dir", "plugins")
            if isinstance(raw_dirs, str):
                plugin_dirs = [raw_dirs]
            elif isinstance(raw_dirs, (list, tuple)):
                plugin_dirs = [str(d) for d in raw_dirs]

        if ignore is None:
            if not plugin_dirs:
                return None
            from ..Core.constants import FILE_WATCHER_IGNORED_DIRS

            ignore = list(FILE_WATCHER_IGNORED_DIRS)
        ignore.extend(plugin_dirs)
        return ignore
