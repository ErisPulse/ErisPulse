"""
热重载监控器基类

收敛各热重载监控器的共用骨架：

- 生命周期状态机：幂等启停（重复 start 返回 False、重复 stop 无操作）、
  启动前准备（无可监控对象返回 False）、停止清理
- 事件循环解析：构造 / 启动时捕获的循环优先，其次主循环注册表延迟回查
- 跨线程调度：重载协程经 ``run_coroutine_threadsafe`` 投递回主事件循环，
  循环未就绪时留痕跳过

子类实现检测机制与重载路由：轮询形态（后台线程 + ``_poll_once``）或
事件形态（外部监控器回调）；对应覆写 :meth:`_begin` / :meth:`_shutdown`。

{!--< internal-use >!--}
"""

from __future__ import annotations

import asyncio
import fnmatch
import threading
from abc import ABC, abstractmethod
from typing import Any

from ..Core.i18n import i18n
from ..Core.logger import logger
from .tasks import _get_main_loop


def _normalize_dist_name(name: str) -> str:
    """名称按 PEP 503 归一（``-`` / ``_`` / ``.`` 等价、小写；glob 场景同样适用）"""
    import re

    return re.sub(r"[-_.]+", "-", name).lower()


class HotReloadWatcherBase(ABC):
    """
    热重载监控器基类

    内置监控范围 ACL（与 strict_mode_exceptions / watch_ignore_dirs 同族）：
    deny 优先于 allow；allow 为空表示"除 deny 外全部"。名单元素支持 glob，
    按组件名（插件名 / entry-point 名）与来源名（发行版名）归一后匹配——
    子类在解析出组件名后经 :meth:`_target_matches` 过滤。

    :param interval: 轮询间隔秒数（语义随子类检测机制）
    :param allow: 白名单（组件名或来源名，glob 支持；空 = 全部）
    :param deny: 黑名单（优先于 allow）
    """

    def __init__(
        self,
        *,
        interval: float,
        allow: list[str] | None = None,
        deny: list[str] | None = None,
    ):
        self._interval = interval
        self._allow = tuple(allow or ())
        self._deny = tuple(deny or ())
        self._running = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    # ==================== 监控范围 ACL ====================

    def _list_hits(self, *names: str, patterns: tuple[str, ...]) -> bool:
        """名单匹配：任一模式（归一后 fnmatch）命中任一给定名字"""
        candidates = tuple(_normalize_dist_name(name) for name in names)
        for pattern in patterns:
            normalized = _normalize_dist_name(pattern)
            if any(fnmatch.fnmatchcase(candidate, normalized) for candidate in candidates):
                return True
        return False

    def _target_matches(self, *names: str) -> bool:
        """监控范围 ACL：deny 命中即排除；allow 空表示全部，非空则须命中"""
        if self._allow or self._deny:
            if self._list_hits(*names, patterns=self._deny):
                return False
            if not self._allow:
                return True
            return self._list_hits(*names, patterns=self._allow)
        return True

    # ==================== 生命周期（模板） ====================

    @property
    def is_running(self) -> bool:
        """
        监控器是否已启动

        :return: 是否运行中
        """
        return self._running

    def start(self) -> bool:
        """
        启动监控（幂等）

        :return: 是否启动成功（已在运行或 :meth:`_prepare` 判定无可监控对象时为 False）
        """
        if self._running:
            return False
        if not self._prepare():
            return False
        self._running = True
        try:
            self._begin()
        except Exception:
            self._running = False
            raise
        return True

    def stop(self) -> None:
        """停止监控（幂等）"""
        if not self._running:
            return
        self._running = False
        self._shutdown()

    @abstractmethod
    def _prepare(self) -> bool:
        """
        {!--< internal-use >!--}
        启动前准备：解析监控对象并建立初始状态

        :return: 是否存在可监控对象（False 时 :meth:`start` 不启动）
        """
        ...

    @abstractmethod
    def _begin(self) -> None:
        """
        {!--< internal-use >!--}
        启动检测机制（后台守护线程或外部监控器）；抛异常时 :meth:`start`
        回滚运行状态
        """
        ...

    @abstractmethod
    def _shutdown(self) -> None:
        """{!--< internal-use >!--} 停止检测机制并释放资源"""
        ...

    # ==================== 轮询形态（可选复用） ====================

    def _run_polling_loop(self) -> None:
        """
        {!--< internal-use >!--}
        轮询形态的线程入口：按间隔调用 :meth:`_poll_once`，异常 debug 留痕
        不中断循环
        """
        while not self._stop_event.wait(self._interval):
            try:
                self._poll_once()
            except Exception as e:
                logger.debug(f"{type(self).__name__} scan failed: {e!r}")

    def _poll_once(self) -> None:  # noqa: B027
        """{!--< internal-use >!--} 单轮扫描（轮询形态子类实现；事件形态子类无需覆写）"""

    def _start_polling_thread(self, name: str) -> None:
        """{!--< internal-use >!--} 启动轮询守护线程（轮询形态子类的 _begin 实现）"""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_polling_loop, daemon=True, name=name)
        self._thread.start()

    def _shutdown_polling_thread(self, join_timeout: float) -> None:
        """{!--< internal-use >!--} 停止轮询守护线程（轮询形态子类的 _shutdown 实现）"""
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=join_timeout)
        self._thread = None

    # ==================== 事件循环解析与调度 ====================

    def _capture_loop(self) -> None:
        """
        {!--< internal-use >!--}
        捕获当前线程的运行中事件循环（构造 / 启动早于 ``sdk.run()`` 时无循环，
        经 :meth:`_resolve_loop` 延迟回查）
        """
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    def _resolve_loop(self) -> asyncio.AbstractEventLoop | None:
        """解析可用事件循环：捕获的循环优先，其次主循环注册表延迟回查"""
        if self._loop is not None and not self._loop.is_closed():
            return self._loop
        main = _get_main_loop()
        if main is not None and not main.is_closed():
            self._loop = main
            return main
        return None

    def _schedule(self, coro: Any, *, skip_log_key: str) -> None:
        """
        把重载协程调度回主事件循环

        :param coro: 重载协程（所有权移交本方法）
        :param skip_log_key: 循环未就绪时的留痕文案 i18n 键
        """
        loop = self._resolve_loop()
        if loop is None:
            logger.warning(i18n.t(skip_log_key))
            return
        asyncio.run_coroutine_threadsafe(coro, loop)


__all__ = ["HotReloadWatcherBase"]
