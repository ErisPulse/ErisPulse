"""
ErisPulse SQL 存储共享基类

提供 SQLite / MySQL / PostgreSQL 三种内置后端共享的通用 SQL 逻辑：
嵌套键 KV 存取、事务编排、DDL、查询构建与 ALTER TABLE。
方言差异（占位符、标识符引号、UPSERT、类型翻译等）收敛到
:class:`SQLDialect` 及其子类。

{!--< tips >!--}
1. 新增 SQL 后端只需：定义 Dialect 子类 + 继承 SQLStorageBase 实现连接管理与执行漏斗
2. KV 值统一以 JSON 文本存储，三种后端行为完全一致
{!--< /tips >!--}
"""

import asyncio
import json
import re
import threading
import time
import weakref
from abc import abstractmethod
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from ..constants import (
    DEFAULT_KV_TABLE_NAME,
    STORAGE_MAX_LIST_INDEX,
    STORAGE_POOL_CREATE_BACKOFF_SECS,
    STORAGE_POOL_CREATE_RETRIES,
    STORAGE_POOL_FAIL_COOLDOWN_SECS,
)
from ..i18n import i18n
from ..lifecycle import lifecycle
from ..logger import logger
from .errors import StorageUnreachableError
from .storage import _SENTINEL, BaseQueryBuilder, BaseStorage, _current_txn

# SQL 标识符（表名/列名）合法模式——用于 INSERT/UPDATE 列名、表名等必须为简单标识符的场景
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
# SQL 注入危险字符黑名单
_SQL_DANGEROUS_RE = re.compile(r"[;'\"\\]|--|/\*|\*/|\x00|\n|\r", re.IGNORECASE)
# 合法列类型首词白名单
_VALID_COLUMN_TYPES = {
    "TEXT", "INTEGER", "REAL", "BLOB", "NUMERIC", "BOOLEAN", "DATE", "DATETIME",
    "TIMESTAMP", "VARCHAR", "CHAR", "INT", "BIGINT", "SMALLINT", "TINYINT",
    "FLOAT", "DOUBLE", "DECIMAL", "CLOB", "NCHAR", "NVARCHAR", "NCLOB",
    "PRIMARY", "KEY", "AUTOINCREMENT", "NOT", "NULL", "DEFAULT", "UNIQUE",
    "CHECK", "FOREIGN", "REFERENCES", "CONSTRAINT",
}
# 自增主键定义（如 "INTEGER PRIMARY KEY AUTOINCREMENT"）
_AUTOINC_RE = re.compile(
    r"^(\w+)\s+PRIMARY\s+KEY\s+AUTOINCREMENT\s*(.*)$", re.IGNORECASE
)


def _validate_identifier(name: str, context: str = "identifier") -> None:
    """
    {!--< internal-use >!--}
    验证 SQL 标识符（表名/列名）是否安全

    :param name: 标识符名称
    :param context: 上下文描述（用于错误消息）
    :raises ValueError: 当标识符包含非法字符时
    """
    if not name or not _IDENTIFIER_RE.match(name):
        raise ValueError(
            i18n.t("core.storage.unsafe_identifier", context=context, name=name)
        )


def _validate_select_column(name: str, context: str = "column") -> None:
    """
    {!--< internal-use >!--}
    验证 SELECT/ORDER BY 列表达式是否安全

    采用黑名单模式：仅拦截 SQL 注入危险字符（; ' " -- /* */ \x00 换行），
    允许任意合法 SQL 列表达式，包括简单列名、聚合函数、别名、表达式等。

    :param name: 列表达式
    :param context: 上下文描述（用于错误消息）
    :raises ValueError: 当包含注入危险字符时
    """
    if not name or _SQL_DANGEROUS_RE.search(name):
        raise ValueError(
            i18n.t("core.storage.unsafe_identifier", context=context, name=name)
        )


def _validate_column_type(col_type: str) -> None:
    """
    {!--< internal-use >!--}
    验证列类型定义是否安全（防止通过类型定义注入 SQL）

    :param col_type: 列类型定义
    :raises ValueError: 当列类型包含潜在危险内容时
    """
    if not col_type or not col_type.strip():
        raise ValueError(i18n.t("core.storage.col_type_empty"))
    stripped = col_type.strip().upper()
    first_word = stripped.split()[0] if stripped.split() else ""
    if first_word.rstrip("(") not in _VALID_COLUMN_TYPES and not _IDENTIFIER_RE.match(
        first_word.rstrip("(")
    ):
        raise ValueError(i18n.t("core.storage.unsafe_col_type", type=col_type))
    dangerous_chars = (";", "--", "/*", "*/", "\x00")
    for char in dangerous_chars:
        if char in col_type:
            raise ValueError(
                i18n.t("core.storage.col_type_invalid_char", type=col_type)
            )


class _SingletonMixin:
    """{!--< internal-use >!--}进程级单例混入（``__new__`` 级去重，可 ``__new__`` 绕过用于测试）"""

    _instance: Any = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any):
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance


class SQLDialect:
    """
    SQL 方言基类

    收敛三种内置后端的方言差异：占位符翻译、标识符引号、UPSERT 语法、
    列类型翻译（含 AUTOINCREMENT 自增主键）、表存在性查询等。

    {!--< tips >!--}
    1. 构建期统一使用 ``?`` 占位符记号，由 :meth:`translate_sql` 翻译为方言样式
    2. 标识符一律经 :meth:`quote` 引用（列名/表名均先经合法性校验）
    {!--< /tips >!--}
    """

    name: str = ""
    # pip 安装 extras 名（驱动缺失提示用）
    extra_name: str = ""

    def translate_sql(self, sql: str) -> str:
        """
        将内部 ``?`` 占位符记号翻译为方言占位符

        :param sql: 内部记号 SQL
        :return: 方言 SQL
        """
        return sql

    def quote(self, name: str) -> str:
        """
        引用 SQL 标识符

        :param name: 已通过合法性校验的标识符
        :return: 带方言引号的标识符
        """
        return f'"{name}"'

    # KV 列类型

    key_column_type: str = "TEXT"
    value_column_type: str = "TEXT"

    def kv_table_ddl(self, table: str, key_col: str, value_col: str) -> str:
        """
        生成 KV 表建表 DDL

        :param table: 已引用的表名
        :param key_col: 已引用的键列名
        :param value_col: 已引用的值列名
        :return: CREATE TABLE 语句
        """
        return (
            f"CREATE TABLE IF NOT EXISTS {table} ("
            f"{key_col} {self.key_column_type} PRIMARY KEY, "
            f"{value_col} {self.value_column_type} NOT NULL)"
        )

    def upsert_kv_sql(self, table: str, key_col: str, value_col: str) -> str:
        """
        生成 KV UPSERT 语句（内部 ``?`` 占位符）

        :param table: 已引用的表名
        :param key_col: 已引用的键列名
        :param value_col: 已引用的值列名
        :return: UPSERT 语句
        """
        return (
            f"INSERT OR REPLACE INTO {table} ({key_col}, {value_col}) VALUES (?, ?)"
        )

    def has_table_sql(self, table_name: str) -> tuple[str, list[str]]:
        """
        生成表存在性查询

        :param table_name: 表名（未引用）
        :return: (SQL, 参数列表)
        """
        return (
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table_name],
        )

    # 列类型翻译

    # 首词类型映射（大小写不敏感，保留括号参数与后缀）
    _type_map: dict[str, str] = {}

    def autoincrement_column(self, base_type: str) -> str:
        """
        翻译自增主键定义（"INTEGER PRIMARY KEY AUTOINCREMENT" 中的类型部分）

        :param base_type: 自增列基础类型（INTEGER/BIGINT 等）
        :return: 方言等价定义
        """
        return f"{base_type} PRIMARY KEY AUTOINCREMENT"

    def _map_first_word(self, word: str) -> str:
        """{!--< internal-use >!--} 按首词映射列类型，保留括号参数与后缀"""
        name = word.split("(", 1)[0].upper()
        mapped = self._type_map.get(name)
        if mapped is None:
            return word
        return mapped + word[len(name):]

    def translate_column_type(self, col_type: str) -> str:
        """
        翻译列类型定义为方言等价写法

        处理自增主键重排与首词类型映射；无法识别的类型原样保留。

        :param col_type: 用户传入的列类型定义
        :return: 方言列类型定义
        """
        matched = _AUTOINC_RE.match(col_type.strip())
        if matched:
            base, rest = matched.group(1), matched.group(2)
            translated = self.autoincrement_column(base)
            return f"{translated} {rest}" if rest else translated
        words = col_type.split()
        if not words:
            return col_type
        words[0] = self._map_first_word(words[0])
        return " ".join(words)

    def is_missing_table_error(self, exc: BaseException) -> bool:
        """
        判断异常是否为"KV 表不存在"（用于自动重建后重试）

        :param exc: 捕获到的异常
        :return: 是否为缺表错误
        """
        return False


class SQLQueryBuilder(BaseQueryBuilder):
    """
    SQL 查询构建器（方言无关的共享实现）

    链式构建标准 SQL（内部 ``?`` 占位符），终止方法通过所属后端的
    :meth:`SQLStorageBase._execute_query` 漏斗执行，由方言完成占位符翻译。

    {!--< tips >!--}
    使用方式：
    1. await storage.Table("users").Insert({"name": "Alice"}).aExecute()
    2. storage.Table("users").Select("name").Where("age > ?", 18).Execute()
    {!--< /tips >!--}
    """

    def __init__(self, storage: "SQLStorageBase", table_name: str):
        _validate_identifier(table_name, "table")
        super().__init__(storage, table_name)

    # 构建逻辑（方言无关，标识符经方言引用）

    def _table_sql(self) -> str:
        return self._storage.dialect.quote(self._table)

    def _rows_to_dict(self, rows: list[tuple], columns: list[str] | None) -> Any:
        """{!--< internal-use >!--} 将 tuple 行列表转为字典列表（columns 不可用时原样返回）"""
        if not columns:
            return rows
        return [dict(zip(columns, row, strict=True)) for row in rows]

    async def aExecute(
        self, *, conn: Any = None
    ) -> "list[tuple] | list[dict[str, Any]] | int":
        """
        执行构建的查询

        - SELECT 返回 list[tuple]（调用 ToDict() 后为 list[dict]）
        - INSERT/UPDATE/DELETE 返回受影响行数 int

        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 查询结果或受影响行数

        :example:
        >>> rows = await storage.Table("users").Select("name", "age").aExecute()
        >>> affected = await storage.Table("users").Delete().Where("age < ?", 18).aExecute()
        """
        if self._operation == "insert_multi":
            return await self._aexecute_insert_multi(conn=conn)

        sql, params = self._build_sql()
        storage: SQLStorageBase = self._storage  # type: ignore[assignment]
        target = conn if conn is not None else storage._routing_conn()

        if self._operation == "select":
            rows, columns = await storage._execute_query(
                "select", sql, params, conn=target
            )
            if self._as_dict:
                return self._rows_to_dict(rows, columns)
            return rows

        return await storage._execute_query("dml", sql, params, conn=target)

    async def _aexecute_insert_multi(self, *, conn: Any = None) -> int:
        """{!--< internal-use >!--} 批量插入执行"""
        if not isinstance(self._data, list) or not self._data:
            raise ValueError(i18n.t("core.storage.insert_multi_empty"))

        columns = list(self._data[0].keys())
        for col in columns:
            _validate_identifier(col, "column")
        quote = self._storage.dialect.quote
        cols = ", ".join(quote(col) for col in columns)
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO {self._table_sql()} ({cols}) VALUES ({placeholders})"
        rows_params = [tuple(row.get(col) for col in columns) for row in self._data]

        storage: SQLStorageBase = self._storage  # type: ignore[assignment]
        target = conn if conn is not None else storage._routing_conn()
        return await storage._execute_query(
            "dml_multi", sql, rows_params, conn=target
        )

    async def aExecuteOne(
        self, *, conn: Any = None
    ) -> "tuple | dict[str, Any] | None":
        """
        执行查询并返回单条结果

        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 单行元组（调用 ToDict() 后为字典）或 None

        :example:
        >>> row = await storage.Table("users").Select("*").Where("id = ?", 1).aExecuteOne()
        """
        sql, params = self._build_sql()
        storage: SQLStorageBase = self._storage  # type: ignore[assignment]
        row, columns = await storage._execute_query(
            "one", sql, params, conn=conn if conn is not None else storage._routing_conn()
        )
        if row is not None and self._as_dict:
            rows = self._rows_to_dict([row], columns)
            return rows[0] if rows else None
        return row

    async def aCount(self, *, conn: Any = None) -> int:
        """
        执行 COUNT 查询

        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 匹配的行数

        :example:
        >>> total = await storage.Table("users").Where("age > ?", 18).aCount()
        """
        sql, params = self._build_count_sql()
        storage: SQLStorageBase = self._storage  # type: ignore[assignment]
        return await storage._execute_query(
            "count", sql, params, conn=conn if conn is not None else storage._routing_conn()
        )

    async def aExists(self, *, conn: Any = None) -> bool:
        """
        检查是否存在匹配的记录

        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 是否存在

        :example:
        >>> if await storage.Table("users").Where("name = ?", "Alice").aExists():
        """
        return await self.aCount(conn=conn) > 0

    def _build_sql(self) -> tuple[str, list[Any]]:
        if self._operation == "select":
            return self._build_select_sql()
        if self._operation == "insert":
            return self._build_insert_sql()
        if self._operation == "update":
            return self._build_update_sql()
        if self._operation == "delete":
            return self._build_delete_sql()
        raise ValueError(i18n.t("core.storage.no_op_type"))

    def _build_select_sql(self) -> tuple[str, list[Any]]:
        if self._columns:
            for col in self._columns:
                _validate_select_column(col)
        cols = ", ".join(self._columns) if self._columns else "*"
        sql = f"SELECT {cols} FROM {self._table_sql()}"
        params: list[Any] = []

        sql, params = self._apply_where(sql, params)
        sql = self._apply_order_by(sql)
        sql, params = self._apply_limit_offset(sql, params)

        return sql, params

    def _build_insert_sql(self) -> tuple[str, list[Any]]:
        data = self._data
        if not isinstance(data, dict):
            raise ValueError(i18n.t("core.storage.insert_needs_dict"))
        columns = list(data.keys())
        for col in columns:
            _validate_identifier(col, "column")
        quote = self._storage.dialect.quote
        placeholders = ", ".join(["?"] * len(columns))
        cols = ", ".join(quote(col) for col in columns)
        sql = f"INSERT INTO {self._table_sql()} ({cols}) VALUES ({placeholders})"
        params = list(data.values())
        return sql, params

    def _build_update_sql(self) -> tuple[str, list[Any]]:
        data = self._data
        if not isinstance(data, dict):
            raise ValueError(i18n.t("core.storage.update_needs_dict"))

        for k in data:
            _validate_identifier(k, "column")
        quote = self._storage.dialect.quote
        set_clause = ", ".join(f"{quote(k)} = ?" for k in data)
        sql = f"UPDATE {self._table_sql()} SET {set_clause}"
        params = list(data.values())

        sql, params = self._apply_where(sql, params)

        return sql, params

    def _build_delete_sql(self) -> tuple[str, list[Any]]:
        sql = f"DELETE FROM {self._table_sql()}"
        params: list[Any] = []

        sql, params = self._apply_where(sql, params)

        return sql, params

    def _build_count_sql(self) -> tuple[str, list[Any]]:
        sql = f"SELECT COUNT(*) FROM {self._table_sql()}"
        params: list[Any] = []
        sql, params = self._apply_where(sql, params)
        return sql, params

    def _apply_where(self, sql: str, params: list[Any]) -> tuple[str, list[Any]]:
        if self._where_clauses:
            where = " AND ".join(self._where_clauses)
            sql += f" WHERE {where}"
            params.extend(self._where_params)
        return sql, params

    def _apply_order_by(self, sql: str) -> str:
        if self._order_by:
            order_parts = []
            for col, desc in self._order_by:
                _validate_select_column(col, context="sort column")
                order_parts.append(f"{col} DESC" if desc else f"{col} ASC")
            sql += f" ORDER BY {', '.join(order_parts)}"
        return sql

    def _apply_limit_offset(self, sql: str, params: list[Any]) -> tuple[str, list[Any]]:
        if self._limit is not None:
            sql += " LIMIT ?"
            params.append(self._limit)
        if self._offset is not None:
            sql += " OFFSET ?"
            params.append(self._offset)
        return sql, params


class AlterTableBuilder:
    """
    ALTER TABLE 构建器

    链式收集表结构修改操作，``aExecute()`` 原生异步执行，
    ``Execute()`` 同步兼容桥接。

    {!--< tips >!--}
    使用方式：
    1. await storage.AlterTable("users").AddColumn("email", "TEXT").aExecute()
    2. storage.AlterTable("users").RenameTo("members").Execute()
    {!--< /tips >!--}
    """

    def __init__(self, storage: "SQLStorageBase", table_name: str):
        _validate_identifier(table_name, "table")
        self._storage = storage
        self._table_name = table_name
        self._operations: list[tuple[str, tuple[Any, ...]]] = []

    def AddColumn(self, column_name: str, column_type: str) -> "AlterTableBuilder":
        """
        添加列

        :param column_name: 列名
        :param column_type: 列类型（如 "TEXT", "INTEGER DEFAULT 0"）
        :return: self

        :example:
        >>> storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
        """
        _validate_identifier(column_name, "column")
        _validate_column_type(column_type)
        self._operations.append(("add_column", (column_name, column_type)))
        return self

    def RenameTo(self, new_name: str) -> "AlterTableBuilder":
        """
        重命名表

        :param new_name: 新表名
        :return: self

        :example:
        >>> storage.AlterTable("users").RenameTo("members").Execute()
        """
        _validate_identifier(new_name, "new table")
        self._operations.append(("rename", (new_name,)))
        return self

    async def aExecute(self) -> bool:
        """
        执行所有已收集的 ALTER TABLE 操作

        :return: 操作是否成功
        """
        if not self._operations:
            return True
        storage: SQLStorageBase = self._storage  # type: ignore[assignment]
        try:
            await storage._run_alter(
                self._table_name, self._operations, conn=storage._routing_conn()
            )
            return True
        except Exception as e:
            logger.error(
                i18n.t(
                    "core.storage.alter_table_failed", table=self._table_name, error=e
                )
            )
            return False

    def Execute(self) -> bool:
        """
        执行所有已收集的 ALTER TABLE 操作（同步兼容，桥接到 :meth:`aExecute`）

        :return: 操作是否成功
        """
        return self._storage._bridge_run(self.aExecute())


class SQLStorageBase(BaseStorage):
    """
    SQL 存储后端共享基类

    实现三种内置 SQL 后端共享的 KV 存取（含嵌套键）、批量操作、DDL、
    事务编排与 ALTER TABLE；子类只需提供连接管理与方言执行漏斗。

    {!--< tips >!--}
    子类必须实现：
    1. ``_create_loop_resource`` / ``_destroy_loop_resource``：每事件循环资源（连接池）
    2. ``_acquire_resource_conn`` / ``_release_resource_conn``：非事务连接获取/归还
    3. ``_open_txn_conn`` / ``_close_txn_conn``：事务专用连接获取/释放
    4. ``_exec_query_on``：方言执行漏斗（占位符翻译 + 游标语义）
    {!--< /tips >!--}
    """

    _SUPPORTS_CONN_ROUTING = True
    dialect: SQLDialect = SQLDialect()
    KV_TABLE_NAME: str = DEFAULT_KV_TABLE_NAME

    # 资源表访问锁（类级：仅用于保护各实例资源表的并发读写）
    _resources_lock = threading.Lock()

    def __init__(self) -> None:
        super().__init__()
        self._initialized = False
        # 每事件循环独立的连接资源（WeakKeyDictionary：循环销毁后自动清理）
        # 通过 _ensure_resource_state 懒初始化，兼容 __new__ 绕过 __init__ 的测试构造
        self._loop_resources: weakref.WeakKeyDictionary[Any, Any] = (
            weakref.WeakKeyDictionary()
        )
        # 建池失败冷却截止时间（monotonic）；0 表示未处于冷却
        self._resource_failed_until: float = 0.0

    def _ensure_resource_state(self) -> None:
        """{!--< internal-use >!--} 确保实例级资源表存在（__new__ 绕过构造时兜底）"""
        if not hasattr(self, "_loop_resources"):
            object.__setattr__(
                self, "_loop_resources", weakref.WeakKeyDictionary()
            )
        if not hasattr(self, "_resource_failed_until"):
            object.__setattr__(self, "_resource_failed_until", 0.0)

    # 生命周期

    def _is_ready(self) -> bool:
        """{!--< internal-use >!--} 检查存储后端是否已初始化完成"""
        return getattr(self, "_initialized", False)

    def _finish_init(self) -> None:
        """{!--< internal-use >!--} 子类完成后调用：标记就绪并订阅配置热更新告警"""
        self._initialized = True

    def _watch_storage_config(self, check: Callable[[], str | None]) -> None:
        """
        {!--< internal-use >!--}
        订阅存储配置热更新；check() 返回告警文案（None 表示无需告警）
        """
        def _on_storage_config_changed(_data: dict) -> None:
            try:
                message = check()
            except Exception:
                return
            if message:
                try:
                    logger.warning(message)
                except Exception:
                    pass

        try:
            from ..lifecycle import lifecycle

            lifecycle.register("config.updated", _on_storage_config_changed)
            lifecycle.register("config.set", _on_storage_config_changed)
        except Exception:
            pass

    def _default_project_path(self, filename: str) -> str:
        """{!--< internal-use >!--} 项目目录下的默认数据库文件路径"""
        return str(Path.cwd() / "config" / filename)

    # 每事件循环资源管理（子类实现）

    @abstractmethod
    async def _create_loop_resource(self) -> Any:
        """{!--< internal-use >!--} 为当前事件循环创建连接资源（连接池/共享连接）"""
        ...

    @abstractmethod
    async def _destroy_loop_resource(self, resource: Any) -> None:
        """{!--< internal-use >!--} 销毁事件循环连接资源"""
        ...

    @abstractmethod
    async def _acquire_resource_conn(self, resource: Any) -> Any:
        """{!--< internal-use >!--} 从资源获取非事务连接"""
        ...

    @abstractmethod
    async def _release_resource_conn(self, resource: Any, conn: Any) -> None:
        """{!--< internal-use >!--} 归还非事务连接"""
        ...

    @abstractmethod
    async def _open_txn_conn(self) -> Any:
        """{!--< internal-use >!--} 获取事务专用连接"""
        ...

    @abstractmethod
    async def _close_txn_conn(self, conn: Any) -> None:
        """{!--< internal-use >!--} 释放事务专用连接"""
        ...

    # 连接资源创建的瞬时失败重试参数（网络抖动/对端限流/数据库重启），取值见 Core/constants.py
    _RESOURCE_CREATE_RETRIES: int = STORAGE_POOL_CREATE_RETRIES
    _RESOURCE_CREATE_BACKOFF_SECS: float = STORAGE_POOL_CREATE_BACKOFF_SECS
    # 重试耗尽后的冷却期：期间后续操作快速失败（不再阻塞重试），冷却结束自动重连试探
    _RESOURCE_FAIL_COOLDOWN_SECS: float = STORAGE_POOL_FAIL_COOLDOWN_SECS

    async def _get_loop_resource(self) -> Any:
        """{!--< internal-use >!--} 获取当前事件循环的连接资源（惰性创建，幂等，瞬时失败自动重试）"""
        self._ensure_resource_state()
        loop = asyncio.get_running_loop()
        with self._resources_lock:
            resource = self._loop_resources.get(loop)
        if resource is not None:
            return resource

        # 冷却期内快速失败：连接不可达时不阻塞调用方（框架继续运行，仅存储暂不可用）
        failed_until = getattr(self, "_resource_failed_until", 0.0)
        was_cooling = failed_until > 0
        if failed_until > time.monotonic():
            logger.trace(
                i18n.t("core.storage.cooldown_fast_fail", backend=self.dialect.name)
            )
            raise StorageUnreachableError(
                i18n.t("core.storage.cooldown", backend=self.dialect.name),
                backend=self.dialect.name,
            )

        # 指数退避重试，规避远端瞬时拒绝（连接数限流、数据库重启窗口等）
        last_error: BaseException | None = None
        for attempt in range(self._RESOURCE_CREATE_RETRIES):
            try:
                resource = await self._create_loop_resource()
                break
            except Exception as e:
                last_error = e
                if attempt < self._RESOURCE_CREATE_RETRIES - 1:
                    logger.warning(
                        i18n.t(
                            "core.storage.pool_retry",
                            backend=self.dialect.name,
                            attempt=attempt + 1,
                            error=e,
                        )
                    )
                    await asyncio.sleep(
                        self._RESOURCE_CREATE_BACKOFF_SECS * (attempt + 1)
                    )
        else:
            # 重试耗尽：记录冷却期，期间后续操作快速失败（不再每次阻塞重试），
            # 框架继续运行（仅存储暂不可用），冷却结束后自动重连试探
            self._resource_failed_until = time.monotonic() + self._RESOURCE_FAIL_COOLDOWN_SECS
            logger.warning(
                i18n.t(
                    "core.storage.pool_exhausted",
                    backend=self.dialect.name,
                    retries=self._RESOURCE_CREATE_RETRIES,
                    cooldown=int(self._RESOURCE_FAIL_COOLDOWN_SECS),
                    error=last_error,
                )
            )
            await self._emit_storage_event(
                "storage.unreachable",
                backend=self.dialect.name,
                error=str(last_error),
                cooldown=self._RESOURCE_FAIL_COOLDOWN_SECS,
            )
            raise StorageUnreachableError(
                f"{self.dialect.name}: {last_error}",
                backend=self.dialect.name,
                cooldown=self._RESOURCE_FAIL_COOLDOWN_SECS,
            ) from last_error

        with self._resources_lock:
            existing = self._loop_resources.get(loop)
            if existing is not None:
                await self._destroy_loop_resource(resource)
                return existing
            self._loop_resources[loop] = resource
        # 建池成功：清除失败冷却（若曾进入冷却，此番重连试探成功即恢复）
        self._resource_failed_until = 0.0
        logger.debug(i18n.t("core.storage.pool_ready", backend=self.dialect.name))
        await self._emit_storage_event("storage.ready", backend=self.dialect.name)
        if was_cooling:
            logger.info(i18n.t("core.storage.recovered", backend=self.dialect.name))
            await self._emit_storage_event("storage.recovered", backend=self.dialect.name)
        return resource

    async def _emit_storage_event(self, event: str, **data: Any) -> None:
        """
        {!--< internal-use >!--}
        发出存储生命周期事件（``storage.ready`` / ``storage.unreachable`` /
        ``storage.recovered``），供外部感知连接状态变化（如 Dashboard 告警）。

        后台发射（fire）：存储操作绝不等待观测者；lifecycle 未就绪或
        处理异常时静默跳过，不影响存储操作本身。
        """
        try:
            lifecycle.fire(event, data)
        except Exception:
            pass

    @asynccontextmanager
    async def _acquire(self) -> AsyncIterator[Any]:
        """
        {!--< internal-use >!--}
        获取连接的统一入口：优先异步事务上下文绑定连接，否则走事件循环资源
        """
        txn = _current_txn.get()
        if txn is not None and txn.conn is not None:
            yield txn.conn
            return
        resource = await self._get_loop_resource()
        conn = await self._acquire_resource_conn(resource)
        try:
            yield conn
        finally:
            await self._release_resource_conn(resource, conn)

    async def _run_with_conn(
        self, impl: Callable[..., Any], *args: Any, conn: Any = None
    ) -> Any:
        """
        {!--< internal-use >!--}
        执行 ``impl(conn, *args)``：显式连接优先，否则自动获取并在退出时归还
        """
        if conn is not None:
            return await impl(conn, *args)
        async with self._acquire() as acquired:
            return await impl(acquired, *args)

    # 方言执行漏斗（子类实现）

    @abstractmethod
    async def _exec_query_on(
        self, kind: str, sql: str, params: Any, conn: Any
    ) -> Any:
        """
        {!--< internal-use >!--}
        方言执行漏斗：翻译占位符后按 kind 执行

        :param kind: "select" / "one" / "count" / "dml" / "dml_multi"
        :param sql: 内部 ``?`` 占位符 SQL
        :param params: 参数列表（dml_multi 为参数行列表）
        :param conn: 数据库连接
        :return: select/one 返回 (行, 列名列表或None)；其余返回受影响行数
        """
        ...

    async def _execute_query(
        self, kind: str, sql: str, params: Any, *, conn: Any = None
    ) -> Any:
        """{!--< internal-use >!--} 查询执行统一入口（连接路由 → 执行漏斗）"""
        if conn is not None:
            return await self._exec_query_on(kind, sql, params, conn)
        async with self._acquire() as acquired:
            return await self._exec_query_on(kind, sql, params, acquired)

    # 事务连接 hook

    async def _acquire_txn_conn(self) -> Any:
        """{!--< internal-use >!--} 获取事务专用连接"""
        return await self._open_txn_conn()

    async def _begin_txn(self, conn: Any) -> Any:
        """{!--< internal-use >!--} 开启事务（SQL BEGIN，方言可覆写）"""
        await self._execute_query("dml", "BEGIN", [], conn=conn)
        return None

    async def _commit_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} 提交事务"""
        await self._execute_query("dml", "COMMIT", [], conn=conn)

    async def _rollback_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} 回滚事务"""
        await self._execute_query("dml", "ROLLBACK", [], conn=conn)

    async def _release_txn_conn(self, conn: Any) -> None:
        """{!--< internal-use >!--} 释放事务专用连接"""
        await self._close_txn_conn(conn)

    async def _run_alter(
        self,
        table_name: str,
        operations: "list[tuple[str, tuple[Any, ...]]]",
        *,
        conn: Any = None,
    ) -> None:
        """{!--< internal-use >!--} 顺序执行 ALTER TABLE 操作"""
        dialect = self.dialect

        async def run_on(acquired: Any) -> None:
            for op_type, args in operations:
                if op_type == "add_column":
                    col_name, col_type = args
                    sql = (
                        f"ALTER TABLE {dialect.quote(table_name)} ADD COLUMN "
                        f"{dialect.quote(col_name)} {dialect.translate_column_type(col_type)}"
                    )
                elif op_type == "rename":
                    (new_name,) = args
                    sql = (
                        f"ALTER TABLE {dialect.quote(table_name)} RENAME TO "
                        f"{dialect.quote(new_name)}"
                    )
                else:
                    continue
                await self._execute_query("dml", sql, [], conn=acquired)

        await self._run_with_conn(run_on, conn=conn)

    # 嵌套键解析（与旧版行为一致）

    def _parse_nested_key(self, key: str) -> tuple[str, list[str]]:
        """
        {!--< internal-use >!--}
        解析嵌套键：点号(.)总是表示嵌套访问，即使根键不存在也会创建嵌套结构

        :param key: 键名，如 "user.settings.theme"
        :return: (根键名, 路径列表)
        """
        if "." not in key:
            return key, []
        parts = key.split(".", 1)
        return parts[0], parts[1].split(".")

    def _get_nested_value(self, obj: Any, key_path: list[str]) -> Any:
        """{!--< internal-use >!--} 从嵌套对象中获取值"""
        current = obj
        for key in key_path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        return current

    def _set_nested_value(self, obj: Any, key_path: list[str], value: Any) -> Any:
        """{!--< internal-use >!--} 在嵌套对象中设置值（中间层一律预创建为字典）"""
        if not key_path:
            return value

        if not isinstance(obj, (dict, list)):
            obj = {}

        current = obj
        for key in key_path[:-1]:
            child = None
            if isinstance(current, dict):
                child = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    child = current[index]
            else:
                # 当前节点是不可继续嵌套的标量，无法设置
                return obj

            if not isinstance(child, (dict, list)):
                child = {}
                if isinstance(current, dict):
                    current[key] = child
                elif isinstance(current, list):
                    index = int(key)
                    if index >= STORAGE_MAX_LIST_INDEX:
                        return obj
                    if index >= len(current):
                        current.extend([None] * (index - len(current) + 1))
                    current[index] = child

            current = child

        last_key = key_path[-1]
        if isinstance(current, dict):
            current[last_key] = value
        elif isinstance(current, list) and last_key.isdigit():
            index = int(last_key)
            if index >= STORAGE_MAX_LIST_INDEX:
                return obj
            if index >= len(current):
                current.extend([None] * (index - len(current) + 1))
            current[index] = value
        else:
            return obj

        return obj

    def _delete_nested_value(self, obj: Any, key_path: list[str]) -> tuple[Any, bool]:
        """{!--< internal-use >!--} 从嵌套对象中删除值，返回 (更新后的对象, 是否删除成功)"""
        if not key_path:
            return obj, False

        if len(key_path) == 1:
            if isinstance(obj, dict) and key_path[0] in obj:
                del obj[key_path[0]]
                return obj, True
            if isinstance(obj, list) and key_path[0].isdigit():
                index = int(key_path[0])
                if 0 <= index < len(obj):
                    obj.pop(index)
                    return obj, True
            return obj, False

        current = obj
        for i, key in enumerate(key_path[:-1]):
            if isinstance(current, dict) and key in current:
                if i == len(key_path) - 2:
                    last_key = key_path[-1]
                    if isinstance(current[key], dict) and last_key in current[key]:
                        del current[key][last_key]
                        return obj, True
                    if isinstance(current[key], list) and last_key.isdigit():
                        index = int(last_key)
                        if 0 <= index < len(current[key]):
                            current[key].pop(index)
                            return obj, True
                    return obj, False
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    if i == len(key_path) - 2:
                        last_key = key_path[-1]
                        if (
                            isinstance(current[index], dict)
                            and last_key in current[index]
                        ):
                            del current[index][last_key]
                            return obj, True
                        if isinstance(current[index], list) and last_key.isdigit():
                            last_index = int(last_key)
                            if 0 <= last_index < len(current[index]):
                                current[index].pop(last_index)
                                return obj, True
                        return obj, False
                    current = current[index]
                else:
                    return obj, False
            else:
                return obj, False

        return obj, False

    def _loads(self, raw: Any) -> Any:
        """{!--< internal-use >!--} JSON 反序列化（失败时返回原始文本）"""
        if isinstance(raw, (dict, list, int, float, bool)) or raw is None:
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    # KV 内部 SQL

    def _kv_table_sql(self) -> tuple[str, str, str]:
        """{!--< internal-use >!--} 返回 (已引用表名, 已引用键列, 已引用值列)"""
        dialect = self.dialect
        return (
            dialect.quote(self.KV_TABLE_NAME),
            dialect.quote("key"),
            dialect.quote("value"),
        )

    async def _init_kv_table(self) -> None:
        """{!--< internal-use >!--} 创建默认 KV 表"""
        table, key_col, value_col = self._kv_table_sql()
        await self._execute_query(
            "dml", self.dialect.kv_table_ddl(table, key_col, value_col), []
        )

    async def _recover_missing_table(self) -> None:
        """{!--< internal-use >!--} 缺表自动恢复"""
        await self._init_kv_table()

    # KV 异步原生实现

    async def _get_impl(self, conn: Any, key: str, default: Any) -> Any:
        table, key_col, value_col = self._kv_table_sql()
        root_key, nested_path = self._parse_nested_key(key)

        rows, _cols = await self._exec_query_on(
            "select", f"SELECT {value_col} FROM {table} WHERE {key_col} = ?", [root_key], conn
        )
        if rows:
            value = self._loads(rows[0][0])
            if nested_path:
                if isinstance(value, (dict, list)):
                    nested_value = self._get_nested_value(value, nested_path)
                    return nested_value if nested_value is not None else default
                return default
            return value

        # 尝试完整键名查找（向后兼容）
        if nested_path:
            rows, _cols = await self._exec_query_on(
                "select", f"SELECT {value_col} FROM {table} WHERE {key_col} = ?", [key], conn
            )
            if rows:
                return self._loads(rows[0][0])
        return default

    async def aget(self, key: str, default: Any = None, *, conn: Any = None) -> Any:
        """
        异步获取存储项的值

        支持嵌套键访问，如 "user.settings.theme" 会从存储的嵌套对象中获取值

        :param key: 存储项键名，支持嵌套路径
        :param default: 默认值（当键不存在时返回）
        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 存储项的值

        :example:
        >>> timeout = await storage.aget("network.timeout", 30)
        """
        if not self._is_ready():
            return default

        logger.trace(i18n.t("core.storage.kv_get", key=key))
        try:
            return await self._run_with_conn(self._get_impl, key, default, conn=conn)
        except Exception as e:
            if self.dialect.is_missing_table_error(e):
                await self._recover_missing_table()
                return await self._run_with_conn(self._get_impl, key, default, conn=conn)
            logger.error(i18n.t("core.storage.get_error", key=key, error=e))
            return default

    async def _set_impl(self, conn: Any, key: str, value: Any) -> bool:
        table, key_col, value_col = self._kv_table_sql()
        root_key, nested_path = self._parse_nested_key(key)

        if not nested_path:
            await self._exec_query_on(
                "dml",
                self.dialect.upsert_kv_sql(table, key_col, value_col),
                [key, json.dumps(value)],
                conn,
            )
            return True

        rows, _cols = await self._exec_query_on(
            "select", f"SELECT {value_col} FROM {table} WHERE {key_col} = ?", [root_key], conn
        )
        if rows:
            try:
                current_value = json.loads(rows[0][0])
            except json.JSONDecodeError:
                current_value = {}
        else:
            current_value = {}

        if not isinstance(current_value, (dict, list)):
            current_value = {}

        updated_value = self._set_nested_value(current_value, nested_path, value)
        await self._exec_query_on(
            "dml",
            self.dialect.upsert_kv_sql(table, key_col, value_col),
            [root_key, json.dumps(updated_value)],
            conn,
        )
        return True

    async def aset(self, key: str, value: Any, *, conn: Any = None) -> bool:
        """
        异步设置存储项的值

        支持嵌套键设置，如 "user.settings.theme" 会更新存储的嵌套对象中的对应字段

        :param key: 存储项键名，支持嵌套路径
        :param value: 存储项的值
        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 操作是否成功

        :example:
        >>> await storage.aset("user.settings.theme", "dark")
        """
        if not self._is_ready():
            return False
        try:
            result = await self._run_with_conn(self._set_impl, key, value, conn=conn)
            logger.trace(f"storage.set: key={key}")
            return result
        except Exception as e:
            logger.error(i18n.t("core.storage.set_failed", key=key, error=e))
            return False

    async def _delete_impl(self, conn: Any, key: str) -> bool:
        table, key_col, value_col = self._kv_table_sql()
        root_key, nested_path = self._parse_nested_key(key)

        if not nested_path:
            await self._exec_query_on(
                "dml", f"DELETE FROM {table} WHERE {key_col} = ?", [key], conn
            )
            return True

        rows, _cols = await self._exec_query_on(
            "select", f"SELECT {value_col} FROM {table} WHERE {key_col} = ?", [root_key], conn
        )
        if not rows:
            return False
        try:
            current_value = json.loads(rows[0][0])
        except json.JSONDecodeError:
            return False
        if not isinstance(current_value, (dict, list)):
            return False

        updated_value, deleted = self._delete_nested_value(current_value, nested_path)
        if not deleted:
            return False

        await self._exec_query_on(
            "dml",
            self.dialect.upsert_kv_sql(table, key_col, value_col),
            [root_key, json.dumps(updated_value)],
            conn,
        )
        return True

    async def adelete(self, key: str, *, conn: Any = None) -> bool:
        """
        异步删除存储项

        支持嵌套键删除，如 "user.settings.theme" 会删除嵌套对象中的对应字段

        :param key: 存储项键名，支持嵌套路径
        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 操作是否成功

        :example:
        >>> await storage.adelete("user.settings.theme")
        """
        if not self._is_ready():
            return False

        logger.trace(i18n.t("core.storage.kv_delete", key=key))
        try:
            return await self._run_with_conn(self._delete_impl, key, conn=conn)
        except Exception as e:
            logger.error(i18n.t("core.storage.delete_failed", key=key, error=e))
            return False

    async def _aget_all_keys_impl(self, conn: Any) -> list[str]:
        table, key_col, _value_col = self._kv_table_sql()
        rows, _cols = await self._exec_query_on(
            "select", f"SELECT {key_col} FROM {table}", [], conn
        )
        return [row[0] for row in rows]

    async def aget_all_keys(self, *, conn: Any = None) -> list[str]:
        """
        异步获取所有存储项的键名

        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 键名列表

        :example:
        >>> all_keys = await storage.aget_all_keys()
        """
        if not self._is_ready():
            return []
        try:
            return await self._run_with_conn(self._aget_all_keys_impl, conn=conn)
        except Exception as e:
            if self.dialect.is_missing_table_error(e):
                await self._recover_missing_table()
                return await self._run_with_conn(self._aget_all_keys_impl, conn=conn)
            logger.error(i18n.t("core.storage.get_keys_error", error=e))
            return []

    async def aclear(self, *, conn: Any = None) -> bool:
        """
        异步清空所有存储项

        :param conn: 内部参数：事务连接路由（勿手动传入）
        :return: 操作是否成功

        :example:
        >>> await storage.aclear()
        """
        if not self._is_ready():
            return False
        try:
            table, _key_col, _value_col = self._kv_table_sql()
            await self._run_with_conn(
                lambda c: self._exec_query_on("dml", f"DELETE FROM {table}", [], c),
                conn=conn,
            )
            return True
        except Exception as e:
            logger.error(i18n.t("core.storage.clear_failed", error=e))
            return False

    # 批量操作（单连接批量 SQL）

    async def _get_multi_impl(self, conn: Any, keys: list[str]) -> dict[str, Any]:
        if not keys:
            return {}
        table, key_col, value_col = self._kv_table_sql()
        placeholders = ",".join(["?"] * len(keys))
        rows, _cols = await self._exec_query_on(
            "select",
            f"SELECT {key_col}, {value_col} FROM {table} WHERE {key_col} IN ({placeholders})",
            list(keys),
            conn,
        )
        results: dict[str, Any] = {}
        for row in rows:
            results[row[0]] = self._loads(row[1])
        return results

    async def aget_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        异步批量获取多个存储项的值（单次 IN 查询，仅返回存在的键）

        :param keys: 键名列表
        :return: 键值对字典

        :example:
        >>> settings = await storage.aget_multi(["app.name", "app.version"])
        """
        if not self._is_ready():
            return {}
        try:
            return await self._run_with_conn(self._get_multi_impl, keys)
        except Exception as e:
            if self.dialect.is_missing_table_error(e):
                await self._recover_missing_table()
                return await self._run_with_conn(self._get_multi_impl, keys)
            logger.error(i18n.t("core.storage.get_multi_failed", error=e))
            return {}

    def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取多个存储项的值（同步兼容，桥接到 :meth:`aget_multi`）

        :param keys: 键名列表
        :return: 键值对字典

        :example:
        >>> settings = storage.get_multi(["app.name", "app.version"])
        """
        return self._bridge_run(self.aget_multi(keys))

    async def aset_multi(self, items: dict[str, Any]) -> bool:
        """
        异步批量设置多个存储项

        与旧版语义一致：键按**字面量**直写，不做点号嵌套解析
        （需要嵌套行为请逐键调用 :meth:`aset`）。

        :param items: 键值对字典
        :return: 操作是否成功

        :example:
        >>> await storage.aset_multi({"app.name": "MyApp", "app.debug": True})
        """
        if not self._is_ready():
            return False
        try:
            table, key_col, value_col = self._kv_table_sql()
            upsert = self.dialect.upsert_kv_sql(table, key_col, value_col)

            async def write_all(conn: Any) -> None:
                for key, value in items.items():
                    await self._exec_query_on(
                        "dml", upsert, [key, json.dumps(value)], conn
                    )

            await self._run_with_conn(write_all)
            return True
        except Exception as e:
            logger.error(i18n.t("core.storage.set_multi_failed", error=e))
            return False

    def set_multi(self, items: dict[str, Any]) -> bool:
        """
        批量设置多个存储项（同步兼容，桥接到 :meth:`aset_multi`）

        :param items: 键值对字典
        :return: 操作是否成功

        :example:
        >>> storage.set_multi({"app.name": "MyApp", "app.debug": True})
        """
        return self._bridge_run(self.aset_multi(items))

    async def _delete_multi_impl(self, conn: Any, keys: list[str]) -> bool:
        if not keys:
            return True
        table, key_col, _value_col = self._kv_table_sql()
        await self._exec_query_on(
            "dml_multi",
            f"DELETE FROM {table} WHERE {key_col} = ?",
            [[key] for key in keys],
            conn,
        )
        return True

    async def adelete_multi(self, keys: list[str]) -> bool:
        """
        异步批量删除多个存储项（单次批量 DELETE）

        :param keys: 键名列表
        :return: 操作是否成功

        :example:
        >>> await storage.adelete_multi(["temp.key1", "temp.key2"])
        """
        if not self._is_ready():
            return False
        try:
            return await self._run_with_conn(self._delete_multi_impl, keys)
        except Exception as e:
            logger.error(i18n.t("core.storage.delete_multi_failed", error=e))
            return False

    def delete_multi(self, keys: list[str]) -> bool:
        """
        批量删除多个存储项（同步兼容，桥接到 :meth:`adelete_multi`）

        :param keys: 键名列表
        :return: 操作是否成功

        :example:
        >>> storage.delete_multi(["temp.key1", "temp.key2"])
        """
        return self._bridge_run(self.adelete_multi(keys))

    # 表管理

    def Table(self, table_name: str) -> SQLQueryBuilder:
        """
        获取指定表的查询构建器

        :param table_name: 表名
        :return: SQLQueryBuilder 实例

        :example:
        >>> rows = await storage.Table("users").Select("name", "age").Where("age > ?", 18).aExecute()
        """
        return SQLQueryBuilder(self, table_name)

    async def aCreateTable(self, table_name: str, columns: dict[str, str]) -> bool:
        """
        异步创建表

        列类型支持 SQLite 风格定义（如 "INTEGER PRIMARY KEY AUTOINCREMENT"），
        由方言自动翻译为目标后端等价写法。

        :param table_name: 表名
        :param columns: 列名到类型的映射
        :return: 操作是否成功

        :example:
        >>> await storage.aCreateTable("users", {
        ...     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        ...     "name": "TEXT NOT NULL"
        ... })
        """
        if not self._is_ready():
            return False

        try:
            _validate_identifier(table_name, "table")
            for col_name, col_type in columns.items():
                _validate_identifier(col_name, "column")
                _validate_column_type(col_type)
        except ValueError as e:
            logger.error(
                i18n.t("core.storage.create_table_failed", table=table_name, error=e)
            )
            return False

        try:
            dialect = self.dialect
            col_defs = ", ".join(
                f"{dialect.quote(col)} {dialect.translate_column_type(typ)}"
                for col, typ in columns.items()
            )
            sql = f"CREATE TABLE IF NOT EXISTS {dialect.quote(table_name)} ({col_defs})"
            await self._execute_query("dml", sql, [])
            return True
        except Exception as e:
            logger.error(
                i18n.t("core.storage.create_table_failed", table=table_name, error=e)
            )
            return False

    async def aDropTable(self, table_name: str) -> bool:
        """
        异步删除表

        :param table_name: 表名
        :return: 操作是否成功

        :example:
        >>> await storage.aDropTable("users")
        """
        if not self._is_ready():
            return False

        try:
            _validate_identifier(table_name, "table")
        except ValueError as e:
            logger.error(i18n.t("core.storage.drop_table_failed", error=e))
            return False

        try:
            sql = f"DROP TABLE IF EXISTS {self.dialect.quote(table_name)}"
            await self._execute_query("dml", sql, [])
            return True
        except Exception as e:
            logger.error(
                i18n.t("core.storage.drop_table_name_failed", table=table_name, error=e)
            )
            return False

    async def aHasTable(self, table_name: str) -> bool:
        """
        异步检查表是否存在

        :param table_name: 表名
        :return: 是否存在

        :example:
        >>> if await storage.aHasTable("users"):
        """
        if not self._is_ready():
            return False

        try:
            sql, params = self.dialect.has_table_sql(table_name)
            row, _cols = await self._execute_query("one", sql, params)
            return row is not None
        except Exception as e:
            logger.error(i18n.t("core.storage.has_table_failed", table=table_name, error=e))
            return False

    def AlterTable(self, table_name: str) -> AlterTableBuilder:
        """
        获取 ALTER TABLE 构建器

        :param table_name: 表名
        :return: AlterTableBuilder 实例

        :example:
        >>> storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
        """
        return AlterTableBuilder(self, table_name)

    # 资源释放

    async def aclose(self) -> None:
        """
        异步关闭当前事件循环上绑定的连接资源（连接池/共享连接）

        事务专用连接不受影响（由事务自行管理）。

        :example:
        >>> await storage.aclose()
        """
        self._ensure_resource_state()
        loop = asyncio.get_running_loop()
        with self._resources_lock:
            resource = self._loop_resources.pop(loop, None)
        if resource is not None:
            try:
                await self._destroy_loop_resource(resource)
            except Exception as e:
                logger.trace(i18n.t("core.storage.aclose_failed", error=e))

    # 属性式访问（保留旧版就绪守卫语义）

    def __getattr__(self, key: str) -> Any:
        # 避免访问内置属性时出现问题
        if key.startswith("_"):
            raise AttributeError(
                i18n.t(
                    "core.storage.no_attribute",
                    classname=self.__class__.__name__,
                    key=key,
                )
            )

        if not self._is_ready():
            raise AttributeError(i18n.t("core.storage.not_initialized", key=key))

        try:
            value = self.get(key, _SENTINEL)
        except Exception as _err:
            raise AttributeError(
                i18n.t("core.storage.item_not_exist_error", key=key)
            ) from _err

        if value is _SENTINEL:
            raise AttributeError(i18n.t("core.storage.item_not_exist", key=key))
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        # 避免在初始化过程中出现问题
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return

        # 如果还未初始化完成，直接设置属性
        if not self._is_ready():
            object.__setattr__(self, key, value)
            return

        try:
            self.set(key, value)
        except Exception as e:
            logger.error(i18n.t("core.storage.set_failed", key=key, error=e))


__all__ = [
    "AlterTableBuilder",
    "SQLDialect",
    "SQLQueryBuilder",
    "SQLStorageBase",
]
