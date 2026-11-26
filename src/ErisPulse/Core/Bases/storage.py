"""
ErisPulse 存储基类

提供存储后端和查询构建器的抽象接口，支持不同存储介质的统一访问。

{!--< tips >!--}
1. 异步接口（aget/aset/.../aExecute/...）是原生主接口，所有内置后端基于异步驱动实现
2. 同步接口（get/set/.../Execute/...）为兼容层，内部通过 AsyncBridge 桥接到后台事件循环执行
3. 具体存储后端（SQLite/MySQL/PostgreSQL/Redis 等）需继承 BaseStorage 并实现异步抽象方法
4. 事务：异步代码使用 ``async with storage.atransaction():``，同步代码使用 ``with storage.transaction():``
{!--< /tips >!--}
"""

import asyncio
import atexit
import concurrent.futures
import logging
import sys
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import AsyncIterator, Callable
from concurrent.futures import TimeoutError as _FutureTimeout
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from contextvars import ContextVar
from typing import Any, ClassVar, Generic, TypeVar

from ..constants import (
    STORAGE_BRIDGE_JOIN_TIMEOUT_SECS,
    STORAGE_SYNC_IN_ASYNC_WARN_COOLDOWN_SECS,
    STORAGE_SYNC_WARN_SITES_CAPACITY,
    STORAGE_THREAD_BRIDGE_POOL_SIZE,
    STORAGE_TXN_COMMIT_TIMEOUT_SECS,
    STORAGE_TXN_SLOW_WARN_SECS,
    STRICT_SYNC_IN_ASYNC_DEFAULT,
    SYNC_IN_ASYNC_BRIDGE_WAIT_SECS,
)
from ..i18n import i18n
from ..logger import logger
from .errors import StorageOperationError, StrictModeError

# 哨兵值，用于区分"键不存在"和"值为 None"
_SENTINEL = object()

# 当前任务上下文中绑定的活动异步事务（async with atransaction() 内可见）
_current_txn: ContextVar["_AsyncTransaction | None"] = ContextVar(
    "erispulse_storage_current_txn", default=None
)

# sync-in-async 警告的调用点登记表（调用点描述 → 最近一次警告的单调时间戳）
_sync_in_async_warn_sites: "OrderedDict[str, float]" = OrderedDict()
# 登记表读写锁：_warn_sync_in_async 从任意线程调用，get → move_to_end 与
# popitem 淘汰的交错会使 move_to_end 抛 KeyError 并沿 AsyncBridge.run 传播
_sync_in_async_warn_lock = threading.Lock()
_sync_in_async_warn_counts: "OrderedDict[str, int]" = OrderedDict()
_warn_summary_at = 0.0

# 用户帧判定：模块名以此表为前缀的帧视为框架/标准库内部帧，跳过采集
# （模块名而非文件路径——用户项目路径可能包含任何子串）
_INTERNAL_FRAME_MODULE_PREFIXES = ("ErisPulse", "asyncio", "contextlib")


def _capture_user_frames(limit: int) -> list[str]:
    """
    {!--< internal-use >!--}
    跳过框架与标准库内部帧，采集最近的用户层调用帧描述（``文件:行号 (函数名)``）

    供 sync-in-async 警告与慢事务观测定位调用来源；最多回溯 16 帧或采满
    limit 个即止，采集不足 limit 个时以实际数量返回。内部帧按模块名判定
    （``ErisPulse*`` / ``asyncio*`` / ``contextlib``），同步调用链上的用户帧
    必然可达；协程/异步生成器边界可能截断帧链（f_back 为 None），此时以
    实际采集结果为准（可能为空）。

    :param limit: 最多采集的帧数
    :return: 用户层调用帧描述列表（按调用链由近及远排序）
    """
    sites: list[str] = []
    try:
        frame = sys._getframe(1)
    except ValueError:  # 无帧支持的环境（嵌入解释器等）
        return sites
    for _ in range(16):
        if frame is None or len(sites) >= limit:
            break
        module_name = str(frame.f_globals.get("__name__") or "")
        if not module_name.startswith(_INTERNAL_FRAME_MODULE_PREFIXES):
            sites.append(
                f"{frame.f_code.co_filename}:{frame.f_lineno} ({frame.f_code.co_name})"
            )
        frame = frame.f_back
    return sites


def _warn_sync_in_async() -> None:
    """
    {!--< internal-use >!--}
    同步存储 API 在异步上下文调用的聚合告警（防刷屏）

    不逐调用点即时告警——按「文件:行号 (函数名)」累计计数，每个冷却窗口
    （``framework.sync_warn_cooldown``，默认 60s）输出一条汇总：次数、调用
    点数与 Top 调用点。严格模式（``framework.strict.sync_in_async``）开启时
    不聚合，直接抛错。
    """
    global _warn_summary_at

    sites = _capture_user_frames(limit=1)
    callsite = sites[0] if sites else "<未知调用点>"
    now = time.monotonic()
    from ...runtime.frame_config import (
        get_framework_value,  # 惰性：Core 装配窗口内快照读取回环（见 frame_config._framework_defaults）
    )

    if get_framework_value("strict.sync_in_async", STRICT_SYNC_IN_ASYNC_DEFAULT):
        # 严格模式：阻塞式调用直接抛错（消息带调用点与 a 前缀指引），
        # 开发期当场暴露，不进入运行期
        raise StrictModeError(i18n.t("core.storage.sync_in_async_strict", callsite=callsite))

    window = get_framework_value("sync_warn_cooldown", STORAGE_SYNC_IN_ASYNC_WARN_COOLDOWN_SECS)
    should_warn = False
    summary_total = 0
    summary_sites_n = 0
    summary_sites = ""
    with _sync_in_async_warn_lock:
        _sync_in_async_warn_sites[callsite] = now
        _sync_in_async_warn_counts[callsite] = (
            _sync_in_async_warn_counts.get(callsite, 0) + 1
        )
        while len(_sync_in_async_warn_sites) > STORAGE_SYNC_WARN_SITES_CAPACITY:
            _sync_in_async_warn_sites.popitem(last=False)
        if now - _warn_summary_at >= window:
            _warn_summary_at = now
            total = sum(_sync_in_async_warn_counts.values())
            should_warn = total > 0
            top = sorted(
                _sync_in_async_warn_counts.items(), key=lambda kv: -kv[1]
            )[:5]
            _sync_in_async_warn_counts.clear()
            summary_sites = "; ".join(site for site, _count in top)
            summary_total = total
            summary_sites_n = len(top)
    if should_warn:
        try:
            from ..logger import logger

            logger.warning(
                i18n.t(
                    "core.storage.sync_in_loop_summary",
                    total=summary_total,
                    sites_n=summary_sites_n,
                    callsites=summary_sites,
                    window=int(window),
                )
            )
        except Exception:
            pass


def _has_running_loop() -> bool:
    """
    {!--< internal-use >!--}
    判断当前线程是否有正在运行的事件循环

    :return: 是否存在运行中的事件循环
    """
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False

_THREAD_BRIDGE_LOCAL = threading.local()
_THREAD_BRIDGE_POOL: "concurrent.futures.ThreadPoolExecutor | None" = None
_THREAD_BRIDGE_POOL_LOCK = threading.Lock()


def _get_thread_bridge_pool() -> "concurrent.futures.ThreadPoolExecutor":
    """{!--< internal-use >!--} 线程桥接池（进程级懒初始化，退出时随解释器回收）"""
    global _THREAD_BRIDGE_POOL
    if _THREAD_BRIDGE_POOL is None:
        with _THREAD_BRIDGE_POOL_LOCK:
            if _THREAD_BRIDGE_POOL is None:
                _THREAD_BRIDGE_POOL = concurrent.futures.ThreadPoolExecutor(
                    max_workers=STORAGE_THREAD_BRIDGE_POOL_SIZE,
                    thread_name_prefix="EP-StorageThreadBridge",
                )
                atexit.register(_THREAD_BRIDGE_POOL.shutdown, wait=False, cancel_futures=True)
    return _THREAD_BRIDGE_POOL


def _thread_bridge_worker(coro: Any) -> Any:
    """
    {!--< internal-use >!--}
    线程桥接 worker：每线程一个独立事件循环（惰性创建、随线程存活）

    连接资源按循环对象缓存在 ``_loop_resources``（WeakKeyDictionary）——
    循环随线程持久存在，连接同样复用，不产生逐调用建连。
    """
    loop = getattr(_THREAD_BRIDGE_LOCAL, "loop", None)
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _THREAD_BRIDGE_LOCAL.loop = loop
    return loop.run_until_complete(coro)


class _PreJoinExitHooks:
    """
    {!--< internal-use >!--}
    解释器退出时先于线程 join 执行的钩子序列

    CPython 退出先执行 ``threading._shutdown()``——依次调用经
    ``threading._register_atexit`` 登记的回调，再 join 全部非 daemon 线程——
    ``atexit`` 回调排在其后。aiosqlite 0.22 起连接线程为非 daemon 线程，
    依赖 ``atexit`` 关闭连接的进程会永久停在 join 上。本序列在 join 之前
    按序执行：依赖存储的退出刷盘 → 停止全部存活后端的同步资源 → 停止桥接循环。
    """

    _flushers: ClassVar[list[Callable[[], None]]] = []
    _registered: ClassVar[bool] = False

    @classmethod
    def register_flusher(cls, flusher: Callable[[], None]) -> None:
        """
        登记退出刷盘回调（须在后端连接停止之前完成的落盘）

        :param flusher: 无参回调，在退出阶段的主线程内同步执行
        """
        cls._flushers.append(flusher)
        cls.ensure_registered()

    @classmethod
    def ensure_registered(cls) -> None:
        """{!--< internal-use >!--} 向 ``threading._register_atexit`` 登记本序列（幂等）"""
        if cls._registered:
            return
        from threading import _register_atexit  # pyright: ignore[reportAttributeAccessIssue]

        _register_atexit(cls._run)
        cls._registered = True

    @classmethod
    def _run(cls) -> None:
        """
        {!--< internal-use >!--}
        刷盘 → 停后端同步资源 → 停桥

        单步失败不阻断后续步骤与进程退出；留痕走标准库 logging（标准 logging
        的 shutdown 晚于本序列）。
        """
        exit_log = logging.getLogger(f"{__name__}.exit")
        for flusher in tuple(cls._flushers):
            try:
                flusher()
            except Exception:
                exit_log.warning("storage exit flusher failed", exc_info=True)
        for backend in list(BaseStorage._LIVE_BACKENDS):
            try:
                backend._stop_sync_resources()
            except Exception:
                exit_log.warning("storage backend stop failed at exit", exc_info=True)
        try:
            AsyncBridge().close()
        except Exception:
            exit_log.warning("storage bridge close failed at exit", exc_info=True)


class AsyncBridge:
    """
    同步兼容层的后台事件循环桥接器

    以守护线程运行一个常驻事件循环，同步兼容方法通过
    :meth:`run` 将协程提交到该循环并阻塞等待结果。
    进程级单例，解释器退出时自动停止。

    {!--< tips >!--}
    1. 所有后端的同步 API 共享同一个桥接循环
    2. 在桥接线程内禁止再调用同步兼容接口（会自我阻塞）
    3. 在异步上下文（已有运行中事件循环的线程）调用同步 API 仍可工作，
       但会短暂阻塞该事件循环，建议改用 a 前缀异步方法
    {!--< /tips >!--}
    """

    _instance: "AsyncBridge | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "AsyncBridge":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_started", False):
            return
        with self._instance_lock:
            if getattr(self, "_started", False):
                return
            self._loop: asyncio.AbstractEventLoop | None = None
            self._ready = threading.Event()
            self._thread = threading.Thread(
                target=self._run_loop, name="ErisPulse-StorageBridge", daemon=True
            )
            self._thread.start()
            self._ready.wait()
            self._started = True
            _PreJoinExitHooks.ensure_registered()

    def _run_loop(self) -> None:
        """{!--< internal-use >!--} 桥接线程入口：启动常驻事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        # 桥接循环同样安装 owner 感知任务工厂：同步 API 经
        # run_coroutine_threadsafe 携带的 owner 上下文在本循环内派生的
        # 任务自动归属、卸载兜底取消——消除主循环外任务绕过归属表的
        # 盲区（热重载跨 loop 残留的根因之一）。懒导入规避 Core.Bases
        # 早期加载链与 runtime 包的循环引用；失败不阻塞桥接启动。
        try:
            from ...runtime.tasks import install_owner_task_factory

            install_owner_task_factory(self._loop)
        except Exception as e:
            try:
                from ..logger import logger

                logger.warning(i18n.t("core.storage.bridge_factory_failed", error=e))
            except Exception:
                pass
        self._ready.set()
        try:
            self._loop.run_forever()
        finally:
            try:
                self._loop.close()
            except Exception:
                pass

    @staticmethod
    def _watch_abandoned(future: "concurrent.futures.Future[Any]") -> None:
        """
        {!--< internal-use >!--}
        跟进调用方已超时返回的桥接操作

        未取消的操作留在执行队列中继续完成，完成后在此留痕：失败 WARNING
        （调用方已拿到超时返回值，无从得知这次失败），成功 DEBUG。回调在完成
        该 future 的线程内执行——桥接循环线程内经 ``call_soon`` 投递，不占循环。

        :param future: 调用方已放弃等待的 future
        """

        def _done(fut: "concurrent.futures.Future[Any]") -> None:
            try:
                fut.result()
            except concurrent.futures.CancelledError:
                return
            except BaseException as e:
                failure = e  # except 的 as 变量在块结束时被删除，闭包须经独立名字持有

                def _report() -> None:
                    logger.warning(i18n.t("core.storage.sync_bridge_late_failure", error=failure))

            else:

                def _report() -> None:
                    logger.debug("sync storage op finished after caller timeout")

            try:
                asyncio.get_running_loop().call_soon(_report)
            except RuntimeError:
                _report()

        future.add_done_callback(_done)

    def run(self, coro: Any, timeout: float | None = None, *, cancel_on_timeout: bool = False) -> Any:
        """
        在桥接事件循环上执行协程并阻塞等待结果

        :param coro: 要执行的协程对象（所有权移交本方法）
        :param timeout: 可选超时秒数（默认无限等待）
        :param cancel_on_timeout: 等待超时后是否取消尚未完成的操作；False 时操作
            留在桥接循环上继续完成（写不丢），结果经 :meth:`_watch_abandoned` 留痕
        :return: 协程的返回值
        :raises RuntimeError: 桥接已关闭或在桥接线程内重入调用时
        :raises concurrent.futures.TimeoutError: 等待超时
        """
        loop = self._loop
        if loop is None or loop.is_closed():
            coro.close()
            raise RuntimeError(i18n.t("core.storage.bridge_closed"))
        if self._thread is threading.current_thread():
            coro.close()
            raise RuntimeError(i18n.t("core.storage.bridge_reentrant"))

        if _has_running_loop():
            _warn_sync_in_async()

        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout)
        except _FutureTimeout:
            if cancel_on_timeout:
                future.cancel()
            else:
                self._watch_abandoned(future)
            raise

    def close(self) -> None:
        """
        停止桥接事件循环（解释器退出时自动调用）

        幂等：循环未启动或已停止时为无操作。
        """
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            loop.call_soon_threadsafe(loop.stop)
        except RuntimeError:
            return
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=STORAGE_BRIDGE_JOIN_TIMEOUT_SECS)


class _AsyncTransaction:
    """
    {!--< internal-use >!--}
    异步事务句柄

    由 :meth:`BaseStorage.atransaction` 与同步兼容事务共同驱动，
    连接的获取/提交/回滚/释放委托给后端的对应 hook。
    """

    __slots__ = ("_open_site", "_started_at", "conn", "handle", "storage")

    def __init__(self, storage: "BaseStorage"):
        self.storage = storage
        self.conn: Any = None
        self.handle: Any = None
        self._started_at: float | None = None
        self._open_site: str = ""

    async def start(self) -> None:
        """
        获取专用连接并开启事务

        兜底超时（STORAGE_TXN_BEGIN_TIMEOUT_SECS）：无论后端层行为如何，
        事务开启挂起超过阈值即抛 StorageOperationError——事务无限死等
        （如另一长事务持锁且调用方永不提交）属框架缺陷，必须可观测。

        开启失败（连接获取超时 / BEGIN 超时 / BEGIN 直接抛错如 database
        is locked）时就地释放已获取的连接——否则连接永久泄漏（SQLite 泄漏
        连接线程与 fd，池后端泄漏池容量，锁竞争越重泄漏越多）。
        """
        from ...runtime.frame_config import get_framework_value  # 惰性：Core 装配窗口内快照读取回环
        from ..constants import STORAGE_TXN_BEGIN_TIMEOUT_SECS

        begin_timeout = get_framework_value(
            "txn_begin_timeout", STORAGE_TXN_BEGIN_TIMEOUT_SECS
        )
        try:
            self.conn = await asyncio.wait_for(
                self.storage._acquire_txn_conn(), begin_timeout
            )
            self.handle = await asyncio.wait_for(
                self.storage._begin_txn(self.conn), begin_timeout
            )
        except asyncio.TimeoutError as e:
            await self._release_failed_conn()
            raise StorageOperationError(
                f"事务开启超时（>{begin_timeout}s）:"
                "存在长时间持锁的事务或连接池不可用",
                operation="transaction_begin",
            ) from e
        except BaseException:
            # BEGIN 直接抛错（如 OperationalError: database is locked）：
            # 先释放连接再向调用方传播原始异常
            await self._release_failed_conn()
            raise
        # 持锁时长观测锚点：BEGIN 成功即计时（覆盖事务块内全部用户代码耗时）
        self._started_at = time.monotonic()

    async def _release_failed_conn(self) -> None:
        """{!--< internal-use >!--} 开启失败路径释放已获取的连接（无连接时为无操作）"""
        conn, self.conn = self.conn, None
        if conn is None:
            return
        try:
            await self.storage._release_txn_conn(conn)
        except Exception as e:
            # 归还失败即连接泄漏：必须可见（WARNING 起步），不得静默
            logger.warning(i18n.t("core.storage.txn_conn_release_failed", error=e))

    async def finish(self, exc: BaseException | None) -> None:
        """
        结束事务：无异常时提交，有异常时回滚，最后释放连接

        :param exc: 触发回滚的异常（None 表示正常提交）
        """
        conn, self.conn = self.conn, None
        handle, self.handle = self.handle, None
        started_at, self._started_at = self._started_at, None
        if conn is None:
            return
        from ...runtime.frame_config import get_framework_value  # 惰性：Core 装配窗口内快照读取回环
        commit_timeout = get_framework_value(
            "txn_commit_timeout", STORAGE_TXN_COMMIT_TIMEOUT_SECS
        )
        try:
            if exc is None:
                await asyncio.wait_for(
                    self.storage._commit_txn(conn, handle),
                    commit_timeout,
                )
            else:
                await asyncio.wait_for(
                    self.storage._rollback_txn(conn, handle),
                    commit_timeout,
                )
        except asyncio.TimeoutError as e:
            raise StorageOperationError(
                f"事务{'提交' if exc is None else '回滚'}超时"
                f"（>{STORAGE_TXN_COMMIT_TIMEOUT_SECS:g}s）：连接半死或锁长时间"
                "不可得，连接已释放交还池侧",
                operation="transaction_finish",
            ) from e
        finally:
            await self.storage._release_txn_conn(conn)
            # 回滚路径同样持锁，一并纳入观测
            self._warn_slow_txn(started_at)

    def _warn_slow_txn(self, started_at: float | None) -> None:
        """{!--< internal-use >!--} 持锁时长超过 STORAGE_TXN_SLOW_WARN_SECS 时告警并附开启位置"""
        if started_at is None:
            return
        duration = time.monotonic() - started_at
        from ...runtime.frame_config import get_framework_value  # 惰性：Core 装配窗口内快照读取回环
        slow_warn = get_framework_value("txn_slow_warn", STORAGE_TXN_SLOW_WARN_SECS)
        if duration <= slow_warn:
            return
        try:
            logger.warning(
                i18n.t(
                    "core.storage.txn_slow",
                    duration=f"{duration:.2f}",
                    threshold=f"{STORAGE_TXN_SLOW_WARN_SECS:g}",
                    frames=self._open_site,
                )
            )
        except Exception as e:
            logger.debug(f"slow-txn warning emit failed: {e!r}")


class _EmptyTransaction:
    """{!--< internal-use >!--}空事务上下文（存储未就绪时使用）"""

    def __enter__(self) -> "_EmptyTransaction":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _NestedTransaction:
    """{!--< internal-use >!--}同步嵌套事务占位（复用外层事务）"""

    def __enter__(self) -> "_NestedTransaction":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _SyncTransaction:
    """
    {!--< internal-use >!--}
    同步事务兼容上下文

    在桥接事件循环上开启事务，并把事务句柄按调用线程登记，
    使事务块内的同步操作路由到事务连接。
    """

    def __init__(self, storage: "BaseStorage"):
        self._storage = storage
        self._txn: _AsyncTransaction | None = None

    def __enter__(self) -> _AsyncTransaction:
        storage = self._storage
        # 开启可取消：超时后尚未开始的开绝不延迟执行（否则取得连接与写锁后
        # 无人收尾）；已开始的开启被取消时由 start() 就地释放连接
        txn = storage._bridge_run(
            storage._new_async_transaction_and_start(), cancel_on_timeout=True
        )
        if txn is None:
            raise StorageOperationError(
                "事务开启等待超时：桥接循环拥堵，未取得事务",
                operation="transaction_begin",
            )
        # 开启位置采集：__enter__ 运行在用户线程，用户帧可达（桥接循环内
        # 采集拿不到）；bridge_run 返回即 start 完成，finish 前赋值必然可见
        txn._open_site = " <- ".join(_capture_user_frames(limit=2)) or "<未知调用点>"
        storage._register_sync_txn(threading.get_ident(), txn)
        self._txn = txn
        return txn

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        storage = self._storage
        txn, self._txn = self._txn, None
        if txn is None:
            return
        storage._unregister_sync_txn(threading.get_ident())
        # 收尾不可取消：提交/回滚与连接归还即使调用方超时返回也必须在桥接循环上完成
        storage._bridge_run(txn.finish(exc_val))
        # 不吞异常：与旧版 _Transaction 一致，异常照常向外传播


# 构建器绑定的存储后端类型（KV / SQL 各自参数化，_storage 免二次收窄）
_StorageT = TypeVar("_StorageT", bound="BaseStorage")


class BaseQueryBuilder(ABC, Generic[_StorageT]):
    """
    查询构建器抽象基类

    定义链式调用风格的查询构建接口，所有链式方法返回 self，
    终止方法返回实际结果。

    终止方法以异步原生（aExecute/aExecuteOne/aCount/aExists）为抽象接口，
    同步方法（Execute/...）由基类桥接提供兼容实现。

    {!--< tips >!--}
    使用方式：
    1. await storage.Table("users").Insert({"name": "Alice"}).aExecute()
    2. storage.Table("users").Insert({"name": "Alice"}).Execute()  # 同步兼容
    {!--< /tips >!--}
    """

    def __init__(self, storage: _StorageT, table: str):
        self._storage = storage
        self._table = table
        self._operation: str | None = None
        self._columns: list[str] = []
        self._data: dict[str, Any] | list[dict[str, Any]] | None = None
        self._where_clauses: list[str] = []
        self._where_params: list[Any] = []
        self._order_by: list[tuple[str, bool]] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._as_dict: bool = False

    def ToDict(self) -> "BaseQueryBuilder[_StorageT]":
        """
        将 SELECT 结果以字典形式返回（链式修饰，返回 self）

        设置后 ``Execute()`` / ``aExecute()`` 等终止方法的 SELECT 结果
        从 tuple 转为 dict（列名 → 值）。未调用本方法的链保持原有
        tuple 行为，完全向后兼容。

        :return: self

        :example:
        >>> rows = await storage.Table("users").Select("name", "age").ToDict().aExecute()
        >>> # [{'name': 'Alice', 'age': 30}, ...]
        """
        self._as_dict = True
        return self

    def Select(self, *columns: str) -> "BaseQueryBuilder[_StorageT]":
        """
        指定查询列

        :param columns: 列名列表，为空时表示 SELECT *
        :return: self

        :example:
        >>> storage.Table("users").Select("name", "age").Execute()
        """
        self._operation = "select"
        self._columns = list(columns)
        return self

    def Insert(self, data: dict[str, Any]) -> "BaseQueryBuilder[_StorageT]":
        """
        插入一行数据

        :param data: 列名到值的映射
        :return: self

        :example:
        >>> storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        """
        self._operation = "insert"
        self._data = data
        return self

    def InsertMulti(self, data: list[dict[str, Any]]) -> "BaseQueryBuilder[_StorageT]":
        """
        批量插入多行数据

        :param data: 列名到值的映射列表
        :return: self

        :example:
        >>> storage.Table("users").InsertMulti([
        ...     {"name": "Alice", "age": 30},
        ...     {"name": "Bob", "age": 25}
        ... ]).Execute()
        """
        self._operation = "insert_multi"
        self._data = data
        return self

    def Update(self, data: dict[str, Any]) -> "BaseQueryBuilder[_StorageT]":
        """
        更新数据

        :param data: 列名到新值的映射
        :return: self

        :example:
        >>> storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()
        """
        self._operation = "update"
        self._data = data
        return self

    def Delete(self) -> "BaseQueryBuilder[_StorageT]":
        """
        删除行

        :return: self

        :example:
        >>> storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
        """
        self._operation = "delete"
        return self

    def Where(self, condition: str, *params: Any) -> "BaseQueryBuilder[_StorageT]":
        """
        添加 WHERE 条件

        多次调用时条件之间以 AND 连接

        :param condition: 条件表达式（使用占位符，如 "age > ?"）
        :param params: 占位符对应的参数值
        :return: self

        :example:
        >>> storage.Table("users").Where("age > ?", 18).Where("name LIKE ?", "A%").Execute()
        """
        self._where_clauses.append(condition)
        self._where_params.extend(params)
        return self

    def OrderBy(self, column: str, desc: bool = False) -> "BaseQueryBuilder[_StorageT]":
        """
        添加排序规则

        多次调用时按添加顺序组合 ORDER BY

        :param column: 排序列名
        :param desc: 是否降序（默认升序）
        :return: self

        :example:
        >>> storage.Table("users").OrderBy("age", desc=True).OrderBy("name").Execute()
        """
        self._order_by.append((column, desc))
        return self

    def Limit(self, count: int) -> "BaseQueryBuilder[_StorageT]":
        """
        限制返回条数

        :param count: 最大返回条数
        :return: self

        :example:
        >>> storage.Table("users").Limit(10).Execute()
        """
        self._limit = count
        return self

    def Offset(self, count: int) -> "BaseQueryBuilder[_StorageT]":
        """
        设置偏移量

        :param count: 跳过的条数
        :return: self

        :example:
        >>> storage.Table("users").Limit(10).Offset(20).Execute()
        """
        self._offset = count
        return self

    def copy(self) -> "BaseQueryBuilder[_StorageT]":
        """
        深拷贝当前构建器状态

        :return: 新的构建器实例
        """
        new = self.__class__(self._storage, self._table)
        new._operation = self._operation
        new._columns = list(self._columns)
        new._data = (
            dict(self._data)
            if isinstance(self._data, dict)
            else [dict(d) for d in self._data]
            if isinstance(self._data, list)
            else None
        )
        new._where_clauses = list(self._where_clauses)
        new._where_params = list(self._where_params)
        new._order_by = list(self._order_by)
        new._limit = self._limit
        new._offset = self._offset
        new._as_dict = self._as_dict
        return new

    def clear(self) -> "BaseQueryBuilder[_StorageT]":
        """
        重置构建器状态

        :return: self
        """
        self._operation = None
        self._columns = []
        self._data = None
        self._where_clauses = []
        self._where_params = []
        self._order_by = []
        self._limit = None
        self._offset = None
        return self

    # 异步原生终止方法（抽象）

    @abstractmethod
    async def aExecute(self) -> "list[tuple] | list[dict[str, Any]] | int":
        """
        执行构建的查询

        - SELECT 返回 list[tuple]（调用 ToDict() 后为 list[dict]）
        - INSERT/UPDATE/DELETE 返回受影响行数 int

        :return: 查询结果或受影响行数
        """
        ...

    @abstractmethod
    async def aExecuteOne(self) -> "tuple | dict[str, Any] | None":
        """
        执行查询并返回单条结果

        :return: 单行元组（调用 ToDict() 后为字典）或 None
        """
        ...

    @abstractmethod
    async def aCount(self) -> int:
        """
        执行 COUNT 查询

        :return: 匹配的行数
        """
        ...

    @abstractmethod
    async def aExists(self) -> bool:
        """
        检查是否存在匹配的记录

        :return: 是否存在
        """
        ...

    # 同步兼容终止方法

    def _routed_execute(self, coro_factory: Any) -> Any:
        """
        {!--< internal-use >!--}
        同步终止方法执行入口：在调用方线程捕获事务路由连接后桥接执行

        :param coro_factory: 接受可选 conn 关键字参数、返回协程的工厂
        :return: 查询结果
        """
        conn = self._storage._routing_conn()
        if conn is not None:
            return self._storage._bridge_run(coro_factory(conn=conn))
        return self._storage._bridge_run(coro_factory())

    def Execute(self) -> "list[tuple] | list[dict[str, Any]] | int":
        """
        执行构建的查询（同步兼容，桥接到 :meth:`aExecute`）

        - SELECT 返回 list[tuple]（调用 ToDict() 后为 list[dict]）
        - INSERT/UPDATE/DELETE 返回受影响行数 int

        :return: 查询结果或受影响行数

        :example:
        >>> rows = storage.Table("users").Select("name", "age").Execute()
        """
        return self._routed_execute(self.aExecute)

    def ExecuteOne(self) -> "tuple | dict[str, Any] | None":
        """
        执行查询并返回单条结果（同步兼容，桥接到 :meth:`aExecuteOne`）

        :return: 单行元组（调用 ToDict() 后为字典）或 None
        """
        return self._routed_execute(self.aExecuteOne)

    def Count(self) -> int:
        """
        执行 COUNT 查询（同步兼容，桥接到 :meth:`aCount`）

        :return: 匹配的行数
        """
        return self._routed_execute(self.aCount)

    def Exists(self) -> bool:
        """
        检查是否存在匹配的记录（同步兼容，桥接到 :meth:`aExists`）

        :return: 是否存在
        """
        return self._routed_execute(self.aExists)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(table={self._table!r}, op={self._operation!r})"
        )


class BaseStorage(ABC):
    """
    存储后端抽象基类（异步原生）

    定义键值存储和表管理的统一接口，所有存储后端必须继承并实现此基类。

    {!--< tips >!--}
    1. 异步方法（aget/aset/aExecute/...）为原生主接口，内置后端基于异步驱动实现
    2. 同步方法（get/set/Execute/...）为兼容层，通过 AsyncBridge 桥接到后台事件循环
    3. 异步事务使用 ``async with storage.atransaction():``，
       同步事务使用 ``with storage.transaction():``（嵌套事务自动复用外层）
    4. 自定义后端若不接受 ``conn`` 关键字参数（连接路由），请将类属性
       ``_SUPPORTS_CONN_ROUTING`` 设为 False（默认即为 False）
    {!--< /tips >!--}
    """

    # 是否支持将事务连接路由进异步实现（conn 关键字参数）
    # 内置 SQL 后端为 True；未实现 conn 参数的第三方后端保持 False
    _SUPPORTS_CONN_ROUTING: bool = False
    # 线程桥接能力：True = 服务端支持真并发连接（MVCC），异步上下文的同步调用
    # 改走有界线程池（每 worker 独立事件循环，互不排队）；False = 单写锁模型
    # （SQLite 及未知后端），维持单桥接循环串行——写锁语义要求串行，不可并发
    _SUPPORTS_THREAD_BRIDGE: bool = False

    # 存活后端登记表（弱引用）：退出阶段据此停止各后端的同步资源
    _LIVE_BACKENDS: ClassVar["weakref.WeakSet[BaseStorage]"] = weakref.WeakSet()

    def __init__(self) -> None:
        # 同步事务登记表：调用线程 ID → 事务句柄
        self._sync_txns: dict[int, _AsyncTransaction] = {}
        self._sync_txns_lock = threading.Lock()

    def _register_live(self) -> None:
        """{!--< internal-use >!--} 登记为存活后端，并确保退出钩子序列已登记"""
        BaseStorage._LIVE_BACKENDS.add(self)
        _PreJoinExitHooks.ensure_registered()

    def _stop_sync_resources(self) -> None:  # noqa: B027
        """{!--< internal-use >!--} 退出阶段不经事件循环同步停止后端资源；默认无需处理"""

    def _ensure_txn_state(self) -> None:
        """
        {!--< internal-use >!--}
        确保同步事务登记表存在（``__new__`` 绕过 ``__init__`` 的实例兜底）
        """
        if not hasattr(self, "_sync_txns") or not hasattr(self, "_sync_txns_lock"):
            object.__setattr__(self, "_sync_txns", {})
            object.__setattr__(self, "_sync_txns_lock", threading.Lock())

    # 基础 hook

    def _is_ready(self) -> bool:
        """
        {!--< internal-use >!--}
        检查存储后端是否已初始化完成

        :return: 是否已初始化完成
        """
        return True

    def _bridge_run(
        self, coro: Any, timeout: float | None = None, *, cancel_on_timeout: bool = False
    ) -> Any:
        """
        {!--< internal-use >!--}
        将协程提交到桥接事件循环并阻塞等待结果（同步兼容层的执行入口）

        调用方处于异步上下文时施加有界等待（``framework.sync_in_async_bridge_wait``，
        默认 10s）：超时后调用方拿到 None 返回（fail-soft）——把"无限冻结调用方
        事件循环"收敛为有界等待。默认不取消尚未完成的操作：写操作仍在桥接
        循环上完成（写最终落库），完成后的失败另行告警；只读调用方传入
        ``cancel_on_timeout=True``，超时即取消排队中的操作。纯同步线程调用不受限
        （等待事务、迁移等长操作属合法场景）。

        :param coro: 要执行的协程对象
        :param timeout: 可选超时秒数（显式传入时优先于配置上限）
        :param cancel_on_timeout: 等待超时后是否取消尚未完成的操作
        :return: 协程的返回值；异步上下文下桥接等待超时返回 None
        """
        if timeout is None and _has_running_loop():
            from ...runtime.frame_config import (  # 惰性：Core 装配窗口内快照读取回环
                get_framework_value,
            )

            timeout = get_framework_value(
                "sync_in_async_bridge_wait", SYNC_IN_ASYNC_BRIDGE_WAIT_SECS
            )
            if timeout == 0:
                timeout = None
        try:
            if getattr(self, "_SUPPORTS_THREAD_BRIDGE", False) and _has_running_loop():
                # 真并发后端：有界线程池执行（每 worker 独立事件循环），
                # 不经过单桥接循环的串行队列——主循环阻塞时长即操作本身耗时
                return self._thread_bridge_run(coro, timeout, cancel_on_timeout)
            return AsyncBridge().run(coro, timeout, cancel_on_timeout=cancel_on_timeout)
        except _FutureTimeout:
            try:
                frame = sys._getframe(1)
                site = f"{frame.f_code.co_filename}:{frame.f_lineno} ({frame.f_code.co_name})"
            except ValueError:
                site = "?"
            logger.warning(
                i18n.t(
                    "core.storage.sync_in_async_bridge_timeout",
                    wait=timeout,
                    callsite=site,
                )
            )
            return None

    def _thread_bridge_run(
        self, coro: Any, timeout: float | None, cancel_on_timeout: bool = False
    ) -> Any:
        """
        {!--< internal-use >!--}
        有界线程池桥接：真并发后端（``_SUPPORTS_THREAD_BRIDGE``）的同步调用
        执行路径——worker 线程各持独立事件循环（连接按循环缓存，随线程存活），
        调用间互不排队。超时语义与桥接循环一致：调用方拿到 None 返回（由
        :meth:`_bridge_run` 统一转换）；操作默认不取消，留在队列中继续完成。

        :param coro: 要执行的协程对象
        :param timeout: 等待上限秒数
        :param cancel_on_timeout: 等待超时后是否取消尚未完成的操作
        :return: 协程的返回值
        """
        if _has_running_loop():
            _warn_sync_in_async()
        future = _get_thread_bridge_pool().submit(_thread_bridge_worker, coro)
        try:
            return future.result(timeout)
        except _FutureTimeout:
            if cancel_on_timeout:
                future.cancel()
            else:
                AsyncBridge._watch_abandoned(future)
            raise

    def _routing_conn(self) -> Any:
        """
        {!--< internal-use >!--}
        获取当前调用线程绑定的同步事务连接（无活动事务时为 None）

        仅在 ``_SUPPORTS_CONN_ROUTING`` 为 True 的后端上生效。
        """
        if not self._SUPPORTS_CONN_ROUTING:
            return None
        self._ensure_txn_state()
        registry = self._sync_txns
        if not registry:
            return None
        txn = registry.get(threading.get_ident())
        if txn is not None and txn.conn is not None:
            return txn.conn
        return None

    def _register_sync_txn(self, thread_id: int, txn: _AsyncTransaction) -> None:
        """{!--< internal-use >!--} 按调用线程登记同步事务句柄"""
        self._ensure_txn_state()
        with self._sync_txns_lock:
            self._sync_txns[thread_id] = txn

    def _unregister_sync_txn(self, thread_id: int) -> None:
        """{!--< internal-use >!--} 移除调用线程的同步事务登记"""
        self._ensure_txn_state()
        with self._sync_txns_lock:
            self._sync_txns.pop(thread_id, None)

    async def _new_async_transaction_and_start(self) -> _AsyncTransaction:
        """
        {!--< internal-use >!--}
        创建并开启事务句柄（同步事务入口，须在桥接循环上执行，
        保证事务连接与后续同步路由操作处于同一事件循环）
        """
        txn = _AsyncTransaction(self)
        await txn.start()
        return txn

    # 事务连接 hook（后端必须实现）

    @abstractmethod
    async def _acquire_txn_conn(self) -> Any:
        """
        {!--< internal-use >!--}
        获取事务专用连接

        :return: 后端连接对象
        """
        ...

    @abstractmethod
    async def _begin_txn(self, conn: Any) -> Any:
        """{!--< internal-use >!--} 开启事务

        :return: 方言事务句柄（无需句柄的后端返回 None）
        """
        ...

    @abstractmethod
    async def _commit_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} 提交事务"""
        ...

    @abstractmethod
    async def _rollback_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} 回滚事务"""
        ...

    @abstractmethod
    async def _release_txn_conn(self, conn: Any) -> None:
        """{!--< internal-use >!--} 释放事务专用连接"""
        ...

    # 异步原生接口（抽象）

    @abstractmethod
    async def aget(self, key: str, default: Any = None, *, conn: Any = None) -> Any:
        """
        异步获取存储项的值

        支持嵌套键访问，如 "user.settings.theme" 会从存储的嵌套对象中获取值

        :param key: 存储项键名，支持嵌套路径（如 "user.settings.theme"）
        :param default: 默认值（当键不存在时返回）
        :param conn: 内部参数：事务连接路由（``_SUPPORTS_CONN_ROUTING`` 为 True
            的后端须接收；默认 None 表示自行获取连接）
        :return: 存储项的值

        :example:
        >>> timeout = await storage.aget("network.timeout", 30)
        """
        ...

    @abstractmethod
    async def aset(self, key: str, value: Any, *, conn: Any = None) -> bool:
        """
        异步设置存储项的值

        支持嵌套键设置，如 "user.settings.theme" 会更新存储的嵌套对象中的对应字段

        :param key: 存储项键名，支持嵌套路径（如 "user.settings.theme"）
        :param value: 存储项的值
        :param conn: 内部参数：事务连接路由
        :return: 操作是否成功

        :example:
        >>> await storage.aset("app.name", "MyApp")
        """
        ...

    @abstractmethod
    async def adelete(self, key: str, *, conn: Any = None) -> bool:
        """
        异步删除存储项

        支持嵌套键删除，如 "user.settings.theme" 会删除嵌套对象中的对应字段

        :param key: 存储项键名，支持嵌套路径
        :param conn: 内部参数：事务连接路由
        :return: 操作是否成功

        :example:
        >>> await storage.adelete("temp.session")
        """
        ...

    @abstractmethod
    async def aget_all_keys(self, *, conn: Any = None) -> list[str]:
        """
        异步获取所有存储项的键名

        :param conn: 内部参数：事务连接路由
        :return: 键名列表

        :example:
        >>> all_keys = await storage.aget_all_keys()
        """
        ...

    @abstractmethod
    async def aclear(self, *, conn: Any = None) -> bool:
        """
        异步清空所有存储项

        :param conn: 内部参数：事务连接路由
        :return: 操作是否成功

        :example:
        >>> await storage.aclear()
        """
        ...

    @abstractmethod
    def Table(self, table_name: str) -> BaseQueryBuilder[Any]:
        """
        获取指定表的查询构建器

        :param table_name: 表名
        :return: 查询构建器实例

        :example:
        >>> rows = await storage.Table("users").Select("name").aExecute()
        """
        ...

    @abstractmethod
    async def aCreateTable(self, table_name: str, columns: dict[str, str]) -> bool:
        """
        异步创建表

        :param table_name: 表名
        :param columns: 列名到类型的映射（如 {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}）
        :return: 操作是否成功
        """
        ...

    @abstractmethod
    async def aDropTable(self, table_name: str) -> bool:
        """
        异步删除表

        :param table_name: 表名
        :return: 操作是否成功
        """
        ...

    @abstractmethod
    async def aHasTable(self, table_name: str) -> bool:
        """
        异步检查表是否存在

        :param table_name: 表名
        :return: 是否存在
        """
        ...

    # 异步事务

    def atransaction(self) -> "AbstractAsyncContextManager[_AsyncTransaction | None]":
        """
        异步事务上下文管理器

        事务块内的异步操作路由到事务专用连接，保证原子性。
        嵌套调用时复用外层事务（与同步版语义一致）。
        异常时自动回滚并向外传播。

        :return: 异步上下文管理器，yield 事务句柄

        :example:
        >>> async with storage.atransaction():
        ...     await storage.aset("key1", "value1")
        ...     await storage.aset("key2", "value2")
        """
        # 开启位置在同步调用瞬间采集：async with 表达式位于用户帧链上，
        # 协程/异步生成器边界会截断帧链，事务体内采集拿不到用户帧
        txn = _AsyncTransaction(self)
        txn._open_site = " <- ".join(_capture_user_frames(limit=2)) or "<未知调用点>"
        return self._atransaction_cm(txn)

    @asynccontextmanager
    async def _atransaction_cm(
        self, txn: _AsyncTransaction
    ) -> AsyncIterator[_AsyncTransaction | None]:
        """{!--< internal-use >!--} :meth:`atransaction` 的上下文管道（事务生命周期）"""
        if not self._is_ready():
            yield None
            return

        existing = _current_txn.get()
        if existing is not None:
            # 嵌套事务：复用外层，最外层统一提交
            yield existing
            return

        await txn.start()
        token = _current_txn.set(txn)
        try:
            yield txn
        except BaseException as exc:
            await txn.finish(exc)
            raise
        else:
            await txn.finish(None)
        finally:
            _current_txn.reset(token)

    # 同步兼容接口（桥接到异步实现）

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取存储项的值（同步兼容，桥接到 :meth:`aget`）

        :param key: 存储项键名，支持嵌套路径（如 "user.settings.theme"）
        :param default: 默认值（当键不存在时返回）
        :return: 存储项的值

        :example:
        >>> timeout = storage.get("network.timeout", 30)
        """
        conn = self._routing_conn()
        if conn is not None:
            return self._bridge_run(self.aget(key, default, conn=conn), cancel_on_timeout=True)
        return self._bridge_run(self.aget(key, default), cancel_on_timeout=True)

    def set(self, key: str, value: Any) -> bool:
        """
        设置存储项的值（同步兼容，桥接到 :meth:`aset`）

        :param key: 存储项键名，支持嵌套路径
        :param value: 存储项的值
        :return: 操作是否成功

        :example:
        >>> storage.set("app.name", "MyApp")
        """
        conn = self._routing_conn()
        if conn is not None:
            return self._bridge_run(self.aset(key, value, conn=conn))
        return self._bridge_run(self.aset(key, value))

    def delete(self, key: str) -> bool:
        """
        删除存储项（同步兼容，桥接到 :meth:`adelete`）

        :param key: 存储项键名，支持嵌套路径
        :return: 操作是否成功

        :example:
        >>> storage.delete("temp.session")
        """
        conn = self._routing_conn()
        if conn is not None:
            return self._bridge_run(self.adelete(key, conn=conn))
        return self._bridge_run(self.adelete(key))

    def get_all_keys(self) -> list[str]:
        """
        获取所有存储项的键名（同步兼容，桥接到 :meth:`aget_all_keys`）

        :return: 键名列表

        :example:
        >>> all_keys = storage.get_all_keys()
        """
        conn = self._routing_conn()
        if conn is not None:
            return self._bridge_run(self.aget_all_keys(conn=conn), cancel_on_timeout=True)
        return self._bridge_run(self.aget_all_keys(), cancel_on_timeout=True)

    def clear(self) -> bool:
        """
        清空所有存储项（同步兼容，桥接到 :meth:`aclear`）

        :return: 操作是否成功

        :example:
        >>> storage.clear()
        """
        conn = self._routing_conn()
        if conn is not None:
            return self._bridge_run(self.aclear(conn=conn))
        return self._bridge_run(self.aclear())

    def transaction(self) -> Any:
        """
        创建同步事务上下文（兼容层）

        事务块内的同步操作路由到事务专用连接，保证原子性。
        同步嵌套调用时复用外层事务。异常时自动回滚并向外传播。

        :return: 事务上下文管理器

        :example:
        >>> with storage.transaction():
        ...     storage.set("key1", "value1")
        ...     storage.set("key2", "value2")
        """
        if not self._is_ready():
            return _EmptyTransaction()

        if _has_running_loop():
            # 事件循环线程内开同步事务 = 整个持锁期冻结该循环
            # （比单条 sync-in-async 危害更大），纳入同款检测/严格模式
            _warn_sync_in_async()

        self._ensure_txn_state()
        registry = self._sync_txns
        if registry.get(threading.get_ident()) is not None:
            return _NestedTransaction()

        return _SyncTransaction(self)

    def CreateTable(self, table_name: str, columns: dict[str, str]) -> bool:
        """
        创建表（同步兼容，桥接到 :meth:`aCreateTable`）

        :param table_name: 表名
        :param columns: 列名到类型的映射
        :return: 操作是否成功

        :example:
        >>> storage.CreateTable("users", {
        ...     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        ...     "name": "TEXT NOT NULL"
        ... })
        """
        return self._bridge_run(self.aCreateTable(table_name, columns))

    def DropTable(self, table_name: str) -> bool:
        """
        删除表（同步兼容，桥接到 :meth:`aDropTable`）

        :param table_name: 表名
        :return: 操作是否成功

        :example:
        >>> storage.DropTable("users")
        """
        return self._bridge_run(self.aDropTable(table_name))

    def HasTable(self, table_name: str) -> bool:
        """
        检查表是否存在（同步兼容，桥接到 :meth:`aHasTable`）

        :param table_name: 表名
        :return: 是否存在

        :example:
        >>> if storage.HasTable("users"):
        ...     print("users 表已存在")
        """
        return self._bridge_run(self.aHasTable(table_name))

    # 批量操作（默认逐键桥接，后端可覆写为批量 SQL）

    def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取多个存储项的值

        仅返回存在的键。默认实现逐键调用 :meth:`get`，后端可覆写为单次批量查询。

        :param keys: 键名列表
        :return: 键值对字典
        """
        results = {}
        for key in keys:
            value = self.get(key, _SENTINEL)
            if value is not _SENTINEL:
                results[key] = value
        return results

    def set_multi(self, items: dict[str, Any]) -> bool:
        """
        批量设置多个存储项

        :param items: 键值对字典
        :return: 操作是否成功
        """
        return all(self.set(key, value) for key, value in items.items())

    def delete_multi(self, keys: list[str]) -> bool:
        """
        批量删除多个存储项

        :param keys: 键名列表
        :return: 操作是否成功
        """
        return all(self.delete(key) for key in keys)

    async def aget_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        异步批量获取多个存储项的值

        :param keys: 键名列表
        :return: 键值对字典
        """
        results = {}
        for key in keys:
            value = await self.aget(key, _SENTINEL)
            if value is not _SENTINEL:
                results[key] = value
        return results

    async def aset_multi(self, items: dict[str, Any]) -> bool:
        """
        异步批量设置多个存储项

        :param items: 键值对字典
        :return: 操作是否成功
        """
        for key, value in items.items():
            if not await self.aset(key, value):
                return False
        return True

    async def adelete_multi(self, keys: list[str]) -> bool:
        """
        异步批量删除多个存储项

        :param keys: 键名列表
        :return: 操作是否成功
        """
        for key in keys:
            if not await self.adelete(key):
                return False
        return True

    def keys(self) -> list[str]:
        """
        获取所有存储项的键名（代理到 get_all_keys）

        :return: 键名列表
        """
        return self.get_all_keys()

    # 资源释放

    async def aclose(self) -> None:
        """
        异步关闭当前事件循环上绑定的后端资源（连接/连接池）

        默认无操作，持有连接池的后端应覆写此方法。

        :example:
        >>> await storage.aclose()
        """
        return

    def close(self) -> None:
        """
        关闭当前事件循环上绑定的后端资源（同步兼容，桥接到 :meth:`aclose`）

        :example:
        >>> storage.close()
        """
        self._bridge_run(self.aclose())

    # 弃用兼容

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取模块/适配器配置项（委托给config模块）

        :param key: 配置项的键(支持点分隔符如"module.sub.key")
        :param default: 默认值
        :return: 配置项的值

        {!--< deprecated >!--} 请使用 `config.getConfig` 来获取配置项，这个API已弃用
        """
        try:
            from ..config import config

            return config.getConfig(key, default)
        except Exception:
            return default

    def setConfig(self, key: str, value: Any) -> bool:
        """
        设置模块/适配器配置（委托给config模块）

        :param key: 配置项键名(支持点分隔符如"module.sub.key")
        :param value: 配置项值
        :return: 操作是否成功

        {!--< deprecated >!--} 请使用 `config.setConfig` 来设置配置项，这个API已弃用
        """
        try:
            from ..config import config

            return config.setConfig(key, value)
        except Exception:
            return False

    # 属性式访问

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            raise AttributeError(
                i18n.t(
                    "core.storage.no_attribute",
                    classname=self.__class__.__name__,
                    key=key,
                )
            )
        value = self.get(key, _SENTINEL)
        if value is _SENTINEL:
            raise AttributeError(i18n.t("core.storage.item_not_exist", key=key))
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return
        self.set(key, value)


__all__ = [
    "AsyncBridge",
    "BaseQueryBuilder",
    "BaseStorage",
]
