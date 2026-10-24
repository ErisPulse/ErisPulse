"""
文件变更监控

提供文件系统变更检测能力

{!--< tips >!--}
1. 通过定期比较 .py 文件的 mtime 检测变更
2. 接口与 watchdog.observers.Observer 保持一致 (schedule/start/stop/join)
3. 供运行时插件热重载（runtime/plugin_reload）与 CLI 热重载（CLI/commands/run）共用
4. 默认忽略 .venv/.git 等目录（FILE_WATCHER_IGNORED_DIRS），可经 ignore_dirs 覆盖
{!--< /tips >!--}
"""

import os
import threading
from collections.abc import Iterable
from pathlib import Path

from ..Core.constants import FILE_WATCH_POLL_INTERVAL_SECS, FILE_WATCHER_IGNORED_DIRS
from ..Core.logger import logger


class FileSystemEventHandler:
    """
    文件事件处理器基类

    子类可覆写 on_modified 等回调以响应文件变更事件。

    :example:
    >>> class MyHandler(FileSystemEventHandler):
    ...     def on_modified(self, event):
    ...         print(f"changed: {event.src_path}")
    """

    def on_modified(self, event: "FileChangeEvent") -> None:
        """
        文件修改事件回调

        :param event: [FileChangeEvent] 文件变更事件
        """

    def on_created(self, event: "FileChangeEvent") -> None:
        """
        文件创建事件回调

        :param event: [FileChangeEvent] 文件变更事件
        """

    def on_deleted(self, event: "FileChangeEvent") -> None:
        """
        文件删除事件回调

        :param event: [FileChangeEvent] 文件变更事件
        """

    def on_moved(self, event: "FileChangeEvent") -> None:
        """
        文件移动事件回调

        {!--< tips >!--}
        轮询实现（PollingObserver）基于 mtime 比较，不触发本回调——移动
        表现为旧路径 ``on_deleted`` + 新路径 ``on_created``。
        {!--< /tips >!--}

        :param event: [FileChangeEvent] 文件变更事件
        """


class FileChangeEvent:
    """
    文件变更事件

    :param src_path: [str] 发生变更的文件路径
    :param event_type: [str] 事件类型（"modified" / "created" / "deleted"）
    """

    __slots__ = ("event_type", "is_directory", "src_path")

    def __init__(self, src_path: str, event_type: str = "modified"):
        """
        初始化文件变更事件

        :param src_path: [str] 发生变更的文件路径
        :param event_type: [str] 事件类型（"modified" / "created" / "deleted"）
        """
        self.src_path = src_path
        self.is_directory = False
        self.event_type = event_type


class PollingObserver:
    """
    纯 Python 轮询文件监控器

    通过定期遍历目录并比较 .py 文件的 mtime 检测变更

    {!--< tips >!--}
    1. 接口与 watchdog.observers.Observer 一致 (schedule/start/stop/join)
    2. 轮询运行在后台守护线程，不会阻止进程退出
    3. 仅监控 .py 文件的变更，避免不必要的开销
    4. 忽略目录按目录名在任意层级剪枝；键统一 normcase 规范化，
       Windows 大小写不同的路径写法不会产生虚假删除/创建事件
    5. 单个 handler 回调抛异常只记 warning，不会杀死轮询线程
    {!--< /tips >!--}

    :param interval: [float] 轮询间隔（秒） (默认: FILE_WATCH_POLL_INTERVAL_SECS)
    :param ignore_dirs: [Iterable[str] | None] 忽略的目录名集合；
        None = 使用内置默认清单（FILE_WATCHER_IGNORED_DIRS），
        显式传入列表 = 整体替换（空列表 = 不忽略任何目录）

    :example:
    >>> observer = PollingObserver()
    >>> observer.schedule(MyHandler(), ".", recursive=True)
    >>> observer.start()
    """

    def __init__(
        self,
        interval: float = FILE_WATCH_POLL_INTERVAL_SECS,
        ignore_dirs: Iterable[str] | None = None,
    ):
        """
        初始化轮询监控器

        :param interval: [float] 轮询间隔（秒） (默认: FILE_WATCH_POLL_INTERVAL_SECS)
        :param ignore_dirs: [Iterable[str] | None] 忽略的目录名集合
            (None = 内置默认清单；显式列表 = 整体替换)
        """
        self._interval = interval
        self._watches: list[tuple[FileSystemEventHandler, str, bool]] = []
        # 键统一为 normcase 规范化路径（Windows 下大小写/斜杠差异归一）
        self._mtimes: dict[str, float] = {}
        self._paths: dict[str, str] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        if ignore_dirs is None:
            self._ignore_dirs: frozenset[str] = frozenset(FILE_WATCHER_IGNORED_DIRS)
        else:
            self._ignore_dirs = frozenset(os.path.normcase(d) for d in ignore_dirs)

    @property
    def is_running(self) -> bool:
        """
        轮询线程是否仍在运行

        :return: 是否运行中
        """
        return self._thread is not None and self._thread.is_alive()

    def schedule(
        self,
        event_handler: FileSystemEventHandler,
        path: str,
        recursive: bool = False,
    ) -> None:
        """
        注册事件处理器与监控目录

        :param event_handler: [FileSystemEventHandler] 文件事件处理器
        :param path: [str] 要监控的目录路径
        :param recursive: [bool] 是否递归监控子目录 (默认: False)
        """
        self._watches.append((event_handler, path, recursive))

    def start(self) -> None:
        """记录初始快照后启动后台轮询线程"""
        self._snapshot()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """请求停止轮询线程"""
        self._stop_event.set()

    def join(self) -> None:
        """等待轮询线程结束"""
        if self._thread is not None:
            self._thread.join()

    def _walk_py(self, path: str, recursive: bool):
        """
        遍历目录下的 .py 文件（跳过忽略目录）

        {!--< internal-use >!--}

        :param path: [str] 目录路径
        :param recursive: [bool] 是否递归子目录
        :return: [Generator] .py 文件路径生成器
        """
        for root, dirs, files in os.walk(path, onerror=lambda _e: None):
            if self._ignore_dirs:
                dirs[:] = [d for d in dirs if os.path.normcase(d) not in self._ignore_dirs]
            for name in files:
                if name.endswith(".py"):
                    yield str(Path(root) / name)
            if not recursive:
                break

    @staticmethod
    def _dispatch(
        handler: FileSystemEventHandler,
        method: str,
        event_type: str,
        src_path: str,
    ) -> None:
        """
        派发单个事件到 handler，回调异常只记 warning（轮询线程不因此死亡）

        {!--< internal-use >!--}
        """
        try:
            getattr(handler, method)(FileChangeEvent(src_path, event_type))
        except Exception as e:
            logger.warning(f"file watcher handler {method} failed: {e!r}")

    def _snapshot(self) -> None:
        """
        记录所有 .py 文件的当前 mtime，作为变更比较基准

        {!--< internal-use >!--}
        """
        for _handler, path, recursive in self._watches:
            for file_path in self._walk_py(path, recursive):
                key = os.path.normcase(file_path)
                try:
                    self._mtimes[key] = Path(file_path).stat().st_mtime
                except OSError:
                    pass
                else:
                    self._paths[key] = file_path

    def _run(self) -> None:
        """
        轮询主循环：比较 mtime 并在变更时回调处理器

        除修改外补发创建 / 删除事件：本轮新出现的文件回调 ``on_created``，
        stat 失败（已删除）的文件回调 ``on_deleted``。移动 = 旧路径删除 +
        新路径创建（``on_moved`` 在轮询实现下不触发）。

        {!--< internal-use >!--}
        """
        while not self._stop_event.wait(self._interval):
            # 跨 watch 去重：多个重叠 watch（如 "." 与 "plugins"）本轮已派发
            # 过的文件不再向后续 watch 的 handler 重复派发
            reported: set[str] = set()
            for handler, path, recursive in self._watches:
                seen: set[str] = set()
                for file_path in self._walk_py(path, recursive):
                    key = os.path.normcase(file_path)
                    seen.add(key)
                    if key in reported:
                        continue
                    try:
                        mtime = Path(file_path).stat().st_mtime
                    except OSError:
                        # stat 失败（列目录后被删的竞态）：有基准记录才视为删除
                        if self._mtimes.pop(key, None) is not None:
                            original = self._paths.pop(key, file_path)
                            reported.add(key)
                            self._dispatch(handler, "on_deleted", "deleted", original)
                        continue
                    if key not in self._mtimes:
                        self._mtimes[key] = mtime
                        self._paths[key] = file_path
                        reported.add(key)
                        self._dispatch(handler, "on_created", "created", file_path)
                        continue
                    if self._mtimes[key] != mtime:
                        self._mtimes[key] = mtime
                        self._paths[key] = file_path
                        reported.add(key)
                        self._dispatch(handler, "on_modified", "modified", file_path)
                # 差集检测删除：被删除的文件不会出现在本轮 os.walk 结果里。
                # 前缀比较带路径分隔符后缀，避免 "plugins" 误匹配 "plugins2"
                known_prefix = os.path.normcase(str(Path(path).resolve()))
                gone = [
                    known
                    for known in self._mtimes
                    if known not in seen and known.startswith(known_prefix + os.sep)
                ]
                for key in gone:
                    original = self._paths.pop(key, key)
                    self._mtimes.pop(key, None)
                    if key in reported:
                        continue
                    reported.add(key)
                    self._dispatch(handler, "on_deleted", "deleted", original)


__all__ = ["FileChangeEvent", "FileSystemEventHandler", "PollingObserver"]
