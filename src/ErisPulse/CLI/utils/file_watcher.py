"""
文件变更监控

提供文件系统变更检测能力

{!--< tips >!--}
1. 通过定期比较 .py 文件的 mtime 检测变更
2. 接口与 watchdog.observers.Observer 保持一致 (schedule/start/stop/join)
3. 用于实现 CLI 的热重载功能
{!--< /tips >!--}
"""

import os
import threading
from pathlib import Path


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

        :param event: [FileChangeEvent] 文件变更事件
        """


class FileChangeEvent:
    """
    文件变更事件

    :param src_path: [str] 发生变更的文件路径
    """

    __slots__ = ("event_type", "is_directory", "src_path")

    def __init__(self, src_path: str):
        """
        初始化文件变更事件

        :param src_path: [str] 发生变更的文件路径
        """
        self.src_path = src_path
        self.is_directory = False
        self.event_type = "modified"


class PollingObserver:
    """
    纯 Python 轮询文件监控器

    通过定期遍历目录并比较 .py 文件的 mtime 检测变更

    {!--< tips >!--}
    1. 接口与 watchdog.observers.Observer 一致 (schedule/start/stop/join)
    2. 轮询运行在后台守护线程，不会阻止进程退出
    3. 仅监控 .py 文件的变更，避免不必要的开销
    {!--< /tips >!--}

    :param interval: [float] 轮询间隔（秒） (默认: 1.0)

    :example:
    >>> observer = PollingObserver()
    >>> observer.schedule(MyHandler(), ".", recursive=True)
    >>> observer.start()
    """

    def __init__(self, interval: float = 1.0):
        """
        初始化轮询监控器

        :param interval: [float] 轮询间隔（秒） (默认: 1.0)
        """
        self._interval = interval
        self._watches: list[tuple[FileSystemEventHandler, str, bool]] = []
        self._mtimes: dict[str, float] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

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

    @staticmethod
    def _walk_py(path: str, recursive: bool):
        """
        遍历目录下的 .py 文件

        {!--< internal-use >!--}

        :param path: [str] 目录路径
        :param recursive: [bool] 是否递归子目录
        :return: [Generator] .py 文件路径生成器
        """
        for root, _dirs, files in os.walk(path):
            for name in files:
                if name.endswith(".py"):
                    yield str(Path(root) / name)
            if not recursive:
                break

    def _snapshot(self) -> None:
        """
        记录所有 .py 文件的当前 mtime，作为变更比较基准

        {!--< internal-use >!--}
        """
        for _handler, path, recursive in self._watches:
            for file_path in self._walk_py(path, recursive):
                try:
                    self._mtimes[file_path] = Path(file_path).stat().st_mtime
                except OSError:
                    pass

    def _run(self) -> None:
        """
        轮询主循环：比较 mtime 并在变更时回调处理器

        {!--< internal-use >!--}
        """
        while not self._stop_event.wait(self._interval):
            for handler, path, recursive in self._watches:
                for file_path in self._walk_py(path, recursive):
                    try:
                        mtime = Path(file_path).stat().st_mtime
                    except OSError:
                        self._mtimes.pop(file_path, None)
                        continue
                    if self._mtimes.get(file_path) != mtime:
                        self._mtimes[file_path] = mtime
                        handler.on_modified(FileChangeEvent(file_path))


__all__ = ["FileChangeEvent", "FileSystemEventHandler", "PollingObserver"]
