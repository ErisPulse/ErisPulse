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
import threading
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from concurrent.futures import TimeoutError as _FutureTimeout
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

from ..i18n import i18n

# 哨兵值，用于区分"键不存在"和"值为 None"
_SENTINEL = object()

# 当前任务上下文中绑定的活动异步事务（async with atransaction() 内可见）
_current_txn: ContextVar["_AsyncTransaction | None"] = ContextVar(
    "erispulse_storage_current_txn", default=None
)

# 同步接口在异步上下文中调用的警告只提示一次（进程级）
_sync_in_loop_warned = False


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
            atexit.register(self.close)

    def _run_loop(self) -> None:
        """{!--< internal-use >!--} 桥接线程入口：启动常驻事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        try:
            self._loop.run_forever()
        finally:
            try:
                self._loop.close()
            except Exception:
                pass

    def run(self, coro: Any, timeout: float | None = None) -> Any:
        """
        在桥接事件循环上执行协程并阻塞等待结果

        :param coro: 要执行的协程对象（所有权移交本方法）
        :param timeout: 可选超时秒数（默认无限等待）
        :return: 协程的返回值
        :raises RuntimeError: 桥接已关闭或在桥接线程内重入调用时
        """
        loop = self._loop
        if loop is None or loop.is_closed():
            coro.close()
            raise RuntimeError(i18n.t("core.storage.bridge_closed"))
        if self._thread is threading.current_thread():
            coro.close()
            raise RuntimeError(i18n.t("core.storage.bridge_reentrant"))

        global _sync_in_loop_warned
        if not _sync_in_loop_warned and _has_running_loop():
            _sync_in_loop_warned = True
            try:
                from ..logger import logger

                logger.warning(i18n.t("core.storage.sync_in_loop_warn"))
            except Exception:
                pass

        future = asyncio.run_coroutine_threadsafe(coro, loop)
        try:
            return future.result(timeout)
        except _FutureTimeout:
            future.cancel()
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
            thread.join(timeout=5)


class _AsyncTransaction:
    """
    {!--< internal-use >!--}
    异步事务句柄

    由 :meth:`BaseStorage.atransaction` 与同步兼容事务共同驱动，
    连接的获取/提交/回滚/释放委托给后端的对应 hook。
    """

    __slots__ = ("conn", "handle", "storage")

    def __init__(self, storage: "BaseStorage"):
        self.storage = storage
        self.conn: Any = None
        self.handle: Any = None

    async def start(self) -> None:
        """获取专用连接并开启事务"""
        self.conn = await self.storage._acquire_txn_conn()
        self.handle = await self.storage._begin_txn(self.conn)

    async def finish(self, exc: BaseException | None) -> None:
        """
        结束事务：无异常时提交，有异常时回滚，最后释放连接

        :param exc: 触发回滚的异常（None 表示正常提交）
        """
        conn, self.conn = self.conn, None
        handle, self.handle = self.handle, None
        if conn is None:
            return
        try:
            if exc is None:
                await self.storage._commit_txn(conn, handle)
            else:
                await self.storage._rollback_txn(conn, handle)
        finally:
            await self.storage._release_txn_conn(conn)


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
        txn = storage._bridge_run(storage._new_async_transaction_and_start())
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
        storage._bridge_run(txn.finish(exc_val))
        # 不吞异常：与旧版 _Transaction 一致，异常照常向外传播


class BaseQueryBuilder(ABC):
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

    def __init__(self, storage: "BaseStorage", table: str):
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

    def ToDict(self) -> "BaseQueryBuilder":
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

    def Select(self, *columns: str) -> "BaseQueryBuilder":
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

    def Insert(self, data: dict[str, Any]) -> "BaseQueryBuilder":
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

    def InsertMulti(self, data: list[dict[str, Any]]) -> "BaseQueryBuilder":
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

    def Update(self, data: dict[str, Any]) -> "BaseQueryBuilder":
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

    def Delete(self) -> "BaseQueryBuilder":
        """
        删除行

        :return: self

        :example:
        >>> storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
        """
        self._operation = "delete"
        return self

    def Where(self, condition: str, *params: Any) -> "BaseQueryBuilder":
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

    def OrderBy(self, column: str, desc: bool = False) -> "BaseQueryBuilder":
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

    def Limit(self, count: int) -> "BaseQueryBuilder":
        """
        限制返回条数

        :param count: 最大返回条数
        :return: self

        :example:
        >>> storage.Table("users").Limit(10).Execute()
        """
        self._limit = count
        return self

    def Offset(self, count: int) -> "BaseQueryBuilder":
        """
        设置偏移量

        :param count: 跳过的条数
        :return: self

        :example:
        >>> storage.Table("users").Limit(10).Offset(20).Execute()
        """
        self._offset = count
        return self

    def copy(self) -> "BaseQueryBuilder":
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

    def clear(self) -> "BaseQueryBuilder":
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

    def __init__(self) -> None:
        # 同步事务登记表：调用线程 ID → 事务句柄
        self._sync_txns: dict[int, _AsyncTransaction] = {}
        self._sync_txns_lock = threading.Lock()

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

    def _bridge_run(self, coro: Any, timeout: float | None = None) -> Any:
        """
        {!--< internal-use >!--}
        将协程提交到桥接事件循环并阻塞等待结果（同步兼容层的执行入口）

        :param coro: 要执行的协程对象
        :param timeout: 可选超时秒数
        :return: 协程的返回值
        """
        return AsyncBridge().run(coro, timeout)

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
    def Table(self, table_name: str) -> BaseQueryBuilder:
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

    @asynccontextmanager
    async def atransaction(self) -> AsyncIterator[_AsyncTransaction | None]:
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
        if not self._is_ready():
            yield None
            return

        existing = _current_txn.get()
        if existing is not None:
            # 嵌套事务：复用外层，最外层统一提交
            yield existing
            return

        txn = _AsyncTransaction(self)
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
            return self._bridge_run(self.aget(key, default, conn=conn))
        return self._bridge_run(self.aget(key, default))

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
            return self._bridge_run(self.aget_all_keys(conn=conn))
        return self._bridge_run(self.aget_all_keys())

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
