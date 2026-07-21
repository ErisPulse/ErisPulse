"""
ErisPulse 存储管理模块

提供键值存储、通用 SQL 链式查询和事务支持，用于管理框架运行时数据。
基于 SQLite 实现持久化存储，支持复杂数据类型和原子操作。

{!--< tips >!--}
1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 提供链式调用风格的通用 SQL 查询构建器
{!--< /tips >!--}
"""

import json
import re
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeAlias

from .Bases.storage import BaseQueryBuilder, BaseStorage
from .constants import (
    DEFAULT_KV_TABLE_NAME,
    SQLITE_JOURNAL_MODE,
    SQLITE_SYNCHRONOUS_MODE,
    STORAGE_MAX_LIST_INDEX,
)
from .i18n import i18n

StorageKey: TypeAlias = str
StorageValue: TypeAlias = Any

# SQL 标识符（表名/列名）合法模式——用于 INSERT/UPDATE 列名、表名等必须为简单标识符的场景
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
# SQL 注入危险字符黑名单
_SQL_DANGEROUS_RE = re.compile(r"[;'\"\\]|--|/\*|\*/|\x00|\n|\r", re.IGNORECASE)
# SQLite 合法列类型
_VALID_COLUMN_TYPES = {
    "TEXT",
    "INTEGER",
    "REAL",
    "BLOB",
    "NUMERIC",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "TIMESTAMP",
    "VARCHAR",
    "CHAR",
    "INT",
    "BIGINT",
    "SMALLINT",
    "TINYINT",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
    "CLOB",
    "NCHAR",
    "NVARCHAR",
    "NCLOB",
    "PRIMARY",
    "KEY",
    "AUTOINCREMENT",
    "NOT",
    "NULL",
    "DEFAULT",
    "UNIQUE",
    "CHECK",
    "FOREIGN",
    "REFERENCES",
    "CONSTRAINT",
}


def _validate_identifier(name: str, context: str = "标识符") -> None:
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


class _EmptyTransaction:
    """{!--< internal-use >!--}空事务上下文（未就绪时使用）"""

    def __enter__(self) -> "_EmptyTransaction":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _NestedTransaction:
    """{!--< internal-use >!--}嵌套事务占位（复用外层连接）"""

    def __enter__(self) -> "_NestedTransaction":
        return self

    def __exit__(self, *args: object) -> None:
        pass


def _validate_select_column(name: str, context: str = "列名") -> None:
    """
    {!--< internal-use >!--}
    验证 SELECT/ORDER BY 列表达式是否安全

    采用黑名单模式：仅拦截 SQL 注入危险字符（; ' " -- /* */ \x00 换行），
    允许任意合法 SQL 列表达式，包括：
    - 简单列名、table.column、*、table.*
    - 聚合函数：COUNT(*)、SUM(col)
    - 别名：col AS alias
    - 表达式：col1 || col2

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
    # 检查类型定义的第一个词是否为已知类型
    first_word = stripped.split()[0] if stripped.split() else ""
    if first_word.rstrip("(") not in _VALID_COLUMN_TYPES and not _IDENTIFIER_RE.match(
        first_word.rstrip("(")
    ):
        raise ValueError(i18n.t("core.storage.unsafe_col_type", type=col_type))
    # 拒绝包含分号等危险字符的类型定义
    dangerous_chars = (";", "--", "/*", "*/", "\x00")
    for char in dangerous_chars:
        if char in col_type:
            raise ValueError(
                i18n.t("core.storage.col_type_invalid_char", type=col_type)
            )


class SQLiteQueryBuilder(BaseQueryBuilder):
    """
    SQLite 查询构建器

    链式调用风格的 SQL 查询构建器，配合 StorageManager 使用。

    {!--< tips >!--}
    使用方式：
    1. storage.Table("users").Insert({"name": "Alice"}).Execute()
    2. storage.Table("users").Select("name").Where("age > ?", 18).OrderBy("name").Limit(10).Execute()
    3. 通过 copy() 复用基础查询条件
    {!--< /tips >!--}
    """

    def __init__(self, storage: "StorageManager", table_name: str):
        _validate_identifier(table_name, "表名")
        super().__init__(storage, table_name)

    def Execute(self) -> list[tuple] | int:
        """
        执行构建的查询

        - SELECT 返回 list[tuple]
        - INSERT/INSERT_MULTI 返回受影响行数 int
        - UPDATE/DELETE 返回受影响行数 int

        :return: 查询结果列表或受影响行数

        :example:
        >>> rows = storage.Table("users").Select("name", "age").Execute()
        >>> affected = storage.Table("users").Delete().Where("age < ?", 18).Execute()
        """
        storage: StorageManager = self._storage  # type: ignore

        if self._operation == "insert_multi":
            return self._execute_insert_multi(storage)

        sql, params = self._build_sql()

        with storage._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)

            if self._operation == "select":
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
                storage._auto_commit(conn)

        return result

    def _execute_insert_multi(self, storage: "StorageManager") -> int:
        if not isinstance(self._data, list) or not self._data:
            raise ValueError(i18n.t("core.storage.insert_multi_empty"))

        columns = list(self._data[0].keys())
        for col in columns:
            _validate_identifier(col, "列名")
        cols = ", ".join(columns)
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"

        rows_params = [tuple(row.get(col) for col in columns) for row in self._data]

        with storage._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, rows_params)
            result = cursor.rowcount
            storage._auto_commit(conn)

        return result

    def ExecuteOne(self) -> tuple | None:
        """
        执行查询并返回单条结果

        :return: 单行元组或 None

        :example:
        >>> row = storage.Table("users").Select("*").Where("id = ?", 1).ExecuteOne()
        """
        storage: StorageManager = self._storage  # type: ignore
        sql, params = self._build_sql()

        with storage._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()

    def Count(self) -> int:
        """
        执行 COUNT 查询

        :return: 匹配的行数

        :example:
        >>> total = storage.Table("users").Where("age > ?", 18).Count()
        """
        storage: StorageManager = self._storage  # type: ignore
        sql, params = self._build_count_sql()

        with storage._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            result = cursor.fetchone()
            return result[0] if result else 0

    def Exists(self) -> bool:
        """
        检查是否存在匹配的记录

        :return: 是否存在

        :example:
        >>> if storage.Table("users").Where("name = ?", "Alice").Exists():
        >>>     print("Alice exists")
        """
        return self.Count() > 0

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
        sql = f"SELECT {cols} FROM {self._table}"
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
            _validate_identifier(col, "列名")
        placeholders = ", ".join(["?"] * len(columns))
        cols = ", ".join(columns)
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        params = list(data.values())
        return sql, params

    def _build_update_sql(self) -> tuple[str, list[Any]]:
        data = self._data
        if not isinstance(data, dict):
            raise ValueError(i18n.t("core.storage.update_needs_dict"))

        for k in data:
            _validate_identifier(k, "列名")
        set_clause = ", ".join(f"{k} = ?" for k in data)
        sql = f"UPDATE {self._table} SET {set_clause}"
        params = list(data.values())

        sql, params = self._apply_where(sql, params)

        return sql, params

    def _build_delete_sql(self) -> tuple[str, list[Any]]:
        sql = f"DELETE FROM {self._table}"
        params: list[Any] = []

        sql, params = self._apply_where(sql, params)

        return sql, params

    def _build_count_sql(self) -> tuple[str, list[Any]]:
        sql = f"SELECT COUNT(*) FROM {self._table}"
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
                _validate_select_column(col, context="排序列名")
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

    链式调用风格的表结构修改构建器。

    {!--< tips >!--}
    使用方式：
    1. storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
    2. storage.AlterTable("users").RenameTo("members").Execute()
    {!--< /tips >!--}
    """

    def __init__(self, storage: "StorageManager", table_name: str):
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
        _validate_identifier(column_name, "列名")
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
        _validate_identifier(new_name, "新表名")
        self._operations.append(("rename", (new_name,)))
        return self

    def Execute(self) -> bool:
        """
        执行所有已收集的 ALTER TABLE 操作

        :return: 操作是否成功
        """
        if not self._operations:
            return True

        try:
            with self._storage._get_connection() as conn:
                cursor = conn.cursor()
                for op_type, args in self._operations:
                    if op_type == "add_column":
                        col_name, col_type = args
                        cursor.execute(
                            f"ALTER TABLE {self._table_name} ADD COLUMN {col_name} {col_type}"
                        )
                    elif op_type == "rename":
                        (new_name,) = args
                        cursor.execute(
                            f"ALTER TABLE {self._table_name} RENAME TO {new_name}"
                        )
                self._storage._auto_commit(conn)
            return True
        except Exception as e:
            from .logger import logger

            logger.error(
                i18n.t(
                    "core.storage.alter_table_failed", table=self._table_name, error=e
                )
            )
            return False


class StorageManager(BaseStorage):
    """
    存储管理器（SQLite 实现）

    单例模式实现，提供键值存储的增删改查、通用 SQL 链式查询和事务管理。

    支持两种数据库模式：
    1. 项目数据库（默认）：位于项目目录下的 config/config.db
    2. 全局数据库：位于包内的 data/config.db

    {!--< tips >!--}
    1. 使用 get/set 方法操作键值存储项
    2. 使用 Table() 链式调用操作自定义表
    3. 使用 transaction 上下文管理事务
    {!--< /tips >!--}
    """

    _instance = None
    _instance_lock = threading.Lock()
    # 默认数据库放在项目下的 config/config.db
    GLOBAL_DB_PATH = str(
        Path(__file__).resolve().parent / "../data/config.db"
    )
    # KV 存储使用的表名（与建表 SQL 中的 'config' 保持一致；修改需同步迁移现有数据库）
    KV_TABLE_NAME: str = DEFAULT_KV_TABLE_NAME
    # 线程本地存储，用于跟踪活动事务的连接
    _local = threading.local()

    @staticmethod
    def _get_default_project_db_path() -> str:
        return str(Path.cwd() / "config" / "config.db")

    @property
    def DEFAULT_PROJECT_DB_PATH(self) -> str:
        return self._get_default_project_db_path()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return

        # 确保目录存在
        self._ensure_directories()

        # 根据配置决定使用哪个数据库
        from ..runtime import get_storage_config

        storage_config = get_storage_config()

        use_global_db = storage_config.get("use_global_db", False)

        if use_global_db and Path(self.GLOBAL_DB_PATH).exists():
            self.db_path = self.GLOBAL_DB_PATH
        else:
            self.db_path = self.DEFAULT_PROJECT_DB_PATH

        self._init_db()
        self._initialized = True

    def _is_ready(self) -> bool:
        """
        {!--< internal-use >!--}
        检查存储管理器是否已初始化完成

        :return: bool 反馈是否已初始化完成
        """
        return hasattr(self, "_initialized") and self._initialized

    def _auto_commit(self, conn) -> None:
        """
        {!--< internal-use >!--}
        非事务模式下自动提交更改

        :param conn: 数据库连接
        """
        if not (
            hasattr(self._local, "transaction_conn")
            and self._local.transaction_conn is not None
        ):
            conn.commit()

    def _open_connection(self) -> sqlite3.Connection:
        """
        {!--< internal-use >!--}
        打开一个新的 SQLite 连接并应用标准 PRAGMA

        - journal_mode=WAL：持久化在数据库文件头，重复设置无副作用
        - synchronous=NORMAL：per-connection 设置，必须在每个新连接上重新应用。
          此前仅在 _init_db 的临时连接上设置过一次，而该 PRAGMA 不跨连接持久化，
          导致事务外的 get/set 等高频操作实际回落到默认的 synchronous=FULL
          （每次 commit 都触发 fsync），与文档宣称的 WAL+NORMAL 提速不符。

        :return: 已应用标准 PRAGMA 的 sqlite3.Connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(SQLITE_JOURNAL_MODE)
        conn.execute(SQLITE_SYNCHRONOUS_MODE)
        return conn

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        {!--< internal-use >!--}
        获取数据库连接（支持事务）

        如果在事务中，返回事务的连接
        否则新建一个应用了标准 PRAGMA 的短生命周期连接

        :return: sqlite3.Connection 数据库连接
        """
        # 检查是否在线程本地存储中有活动事务连接
        if (
            hasattr(self._local, "transaction_conn")
            and self._local.transaction_conn is not None
        ):
            conn = self._local.transaction_conn
            should_close = False
        else:
            conn = self._open_connection()
            should_close = True

        try:
            yield conn
        finally:
            if should_close:
                conn.close()

    def _ensure_directories(self) -> None:
        """
        {!--< internal-use >!--}
        确保必要的目录存在
        """
        try:
            Path(self._get_default_project_db_path()).parent.mkdir(
                parents=True, exist_ok=True
            )
        except Exception:
            pass

    def _init_db(self) -> None:
        """
        {!--< internal-use >!--}
        初始化数据库

        创建默认 config 键值表
        """
        from .logger import logger

        logger.debug(i18n.t("core.storage.init_db", path=self.db_path))

        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass  # 如果无法创建目录，则继续尝试连接数据库

        try:
            # 连接创建统一走 _open_connection，确保 WAL/synchronous PRAGMA 一致应用
            conn = self._open_connection()

            cursor = conn.cursor()
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.KV_TABLE_NAME} (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            logger.error(i18n.t("core.storage.cannot_open_db", error=e))
            raise
        except Exception as e:
            logger.error(i18n.t("core.storage.init_db_error", error=e))
            raise

    def _get_nested_value(self, obj: Any, key_path: list[str]) -> Any:
        """
        从嵌套对象中获取值

        :param obj: 嵌套对象(dict/list)
        :param key_path: 键路径列表，如 ["user", "settings", "theme"]
        :return: 嵌套值或None
        """
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

    def _parse_nested_key(self, key: str, conn=None) -> tuple[str, list[str]]:
        """
        {!--< internal-use >!--}
        解析嵌套键

        点号(.)总是表示嵌套访问，即使根键不存在也会创建嵌套结构。
        如果根键存在但不是嵌套对象，会被覆盖为嵌套对象。

        {!--< tips >!--}
        此方法确保 '.' 始终作为嵌套访问分隔符，
        storage.set("user.name", "value") 会自动创建嵌套结构
        {!--< /tips >!--}

        :param key: [str] 键名，如 "user.settings.theme"
        :param conn: [sqlite3.Connection, optional] 数据库连接 (未使用，保留用于兼容性) (默认: None)
        :return:
            str: 根键名
            list[str]: 路径列表，如 ["settings", "theme"] 或 []
        """
        if "." not in key:
            return key, []

        parts = key.split(".", 1)
        root_key = parts[0]
        path = parts[1].split(".")
        return root_key, path

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取存储项的值

        支持嵌套键访问，如 "user.settings.theme" 会从存储的嵌套对象中获取值

        :param key: 存储项键名，支持嵌套路径（如 "user.settings.theme"）
        :param default: 默认值(当键不存在时返回)
        :return: 存储项的值

        :example:
        >>> timeout = storage.get("network.timeout", 30)
        >>> user_settings = storage.get("user.settings", {})
        >>> theme = storage.get("user.settings.theme", "light")  # 嵌套访问
        """
        if not self._is_ready():
            return default

        from .logger import logger

        logger.trace(i18n.t("core.storage.kv_get", key=key))

        try:
            with self._get_connection() as conn:
                # 解析嵌套键（传入连接对象以提高性能）
                root_key, nested_path = self._parse_nested_key(key, conn)

                cursor = conn.cursor()
                cursor.execute(f"SELECT value FROM {self.KV_TABLE_NAME} WHERE key = ?", (root_key,))
                if result := cursor.fetchone():
                    try:
                        value = json.loads(result[0])
                    except json.JSONDecodeError:
                        value = result[0]

                    # 如果有嵌套路径，尝试获取嵌套值
                    if nested_path:
                        if isinstance(value, (dict, list)):
                            nested_value = self._get_nested_value(value, nested_path)
                            return nested_value if nested_value is not None else default
                        return default
                    return value

                # 尝试完整键名查找（向后兼容）
                if nested_path:
                    cursor.execute(f"SELECT value FROM {self.KV_TABLE_NAME} WHERE key = ?", (key,))
                    if result := cursor.fetchone():
                        try:
                            return json.loads(result[0])
                        except json.JSONDecodeError:
                            return result[0]

                return default
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                self._init_db()
                return self.get(key, default)
            from .logger import logger

            logger.error(i18n.t("core.storage.db_op_error", error=e))
            return default
        except Exception as e:
            from .logger import logger

            logger.error(i18n.t("core.storage.get_error", key=key, error=e))
            return default

    def get_all_keys(self) -> list[str]:
        """
        获取所有存储项的键名

        :return: 键名列表

        :example:
        >>> all_keys = storage.get_all_keys()
        >>> print(f"共有 {len(all_keys)} 个存储项")
        """
        if not self._is_ready():
            return []

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT key FROM {self.KV_TABLE_NAME}")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            from .logger import logger

            logger.error(i18n.t("core.storage.get_keys_error", error=e))
            return []

    def keys(self) -> list[str]:
        """
        标准字典接口方法，返回所有存储项的键名 -> 代理 --> get_all_keys

        :return: 键名列表
        :example:
        >>> all_keys = storage.keys()
        >>> print(f"共有 {len(all_keys)} 个存储项")
        """
        return self.get_all_keys()

    def _set_nested_value(self, obj: Any, key_path: list[str], value: Any) -> Any:
        """
        在嵌套对象中设置值

        点分隔键路径的每一段本质上都是字典键，预创建中间层时始终使用字典，
        不会因为某一段为纯数字而误判为列表索引。仅当容器本身已经是列表
        且索引在合理范围内（小于 ``STORAGE_MAX_LIST_INDEX``）时，才按数组索引处理。

        :param obj: 嵌套对象(dict/list)
        :param key_path: 键路径列表，如 ["settings", "theme"]
        :param value: 要设置的值
        :return: 更新后的对象
        """
        if not key_path:
            return value

        # 根对象不是可变容器时，创建新的字典
        if not isinstance(obj, (dict, list)):
            obj = {}

        current = obj
        # 遍历到倒数第二个键，确保中间层为字典（点分隔路径语义为嵌套字典）
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

            # 子节点不是容器时，用字典替换（保证可继续嵌套）
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

        # 设置最后一个键的值
        last_key = key_path[-1]
        if isinstance(current, dict):
            current[last_key] = value
        elif isinstance(current, list) and last_key.isdigit():
            index = int(last_key)
            if index >= STORAGE_MAX_LIST_INDEX:
                # 索引过大，避免内存爆炸，放弃设置
                return obj
            if index >= len(current):
                current.extend([None] * (index - len(current) + 1))
            current[index] = value
        else:
            # 当前节点是不可设置的标量，无法写入
            return obj

        return obj

    def _delete_nested_value(self, obj: Any, key_path: list[str]) -> tuple[Any, bool]:
        """
        从嵌套对象中删除值

        :param obj: 嵌套对象(dict/list)
        :param key_path: 键路径列表，如 ["settings", "theme"]
        :return: (更新后的对象, 是否删除成功)
        """
        if not key_path:
            return obj, False

        if len(key_path) == 1:
            # 删除根级别的键
            if isinstance(obj, dict) and key_path[0] in obj:
                del obj[key_path[0]]
                return obj, True
            if isinstance(obj, list) and key_path[0].isdigit():
                index = int(key_path[0])
                if 0 <= index < len(obj):
                    obj.pop(index)
                    return obj, True
            return obj, False

        # 递归删除嵌套值
        current = obj
        for i, key in enumerate(key_path[:-1]):
            if isinstance(current, dict) and key in current:
                if i == len(key_path) - 2:
                    # 到达倒数第二层，删除最后一层的键
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
                        # 到达倒数第二层，删除最后一层的键
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

    def set(self, key: str, value: Any) -> bool:
        """
        设置存储项的值

        支持嵌套键设置，如 "user.settings.theme" 会更新存储的嵌套对象中的对应字段

        :param key: 存储项键名，支持嵌套路径（如 "user.settings.theme"）
        :param value: 存储项的值
        :return: 操作是否成功

        :example:
        >>> storage.set("app.name", "MyApp")
        >>> storage.set("user.settings", {"theme": "dark"})
        >>> storage.set("user.settings.theme", "light")  # 嵌套设置
        """
        if not self._is_ready():
            return False

        try:
            with self._get_connection() as conn:
                # 解析嵌套键（传入连接对象以提高性能）
                root_key, nested_path = self._parse_nested_key(key, conn)

                # 如果不是嵌套键，直接设置
                if not nested_path:
                    serialized_value = json.dumps(value)
                    cursor = conn.cursor()
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {self.KV_TABLE_NAME} (key, value) VALUES (?, ?)",
                        (key, serialized_value),
                    )
                    self._auto_commit(conn)
                    return True

                # 处理嵌套键
                cursor = conn.cursor()

                # 获取现有的根键值
                cursor.execute(f"SELECT value FROM {self.KV_TABLE_NAME} WHERE key = ?", (root_key,))
                result = cursor.fetchone()

                if result:
                    try:
                        current_value = json.loads(result[0])
                    except json.JSONDecodeError:
                        # 如果现有值不是JSON，无法进行嵌套操作
                        current_value = {}
                else:
                    # 根键不存在，创建新的嵌套结构
                    current_value = {}

                # 确保值是字典或列表，以便进行嵌套操作
                if not isinstance(current_value, (dict, list)):
                    current_value = {}

                # 设置嵌套值
                updated_value = self._set_nested_value(
                    current_value, nested_path, value
                )

                # 存储更新后的值
                serialized_value = json.dumps(updated_value)
                cursor.execute(
                    f"INSERT OR REPLACE INTO {self.KV_TABLE_NAME} (key, value) VALUES (?, ?)",
                    (root_key, serialized_value),
                )
                self._auto_commit(conn)

            from .logger import logger

            logger.trace(f"storage.set: key={key}")
            return True
        except Exception as e:
            from .logger import logger

            logger.error(i18n.t("core.storage.set_failed", key=key, error=e))
            return False

    def set_multi(self, items: dict[str, Any]) -> bool:
        """
        批量设置多个存储项

        :param items: 键值对字典
        :return: 操作是否成功

        :example:
        >>> storage.set_multi({
        ...     "app.name": "MyApp",
        ...     "app.version": "1.0.0",
        ...     "app.debug": True
        ... })
        """
        if not self._is_ready():
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for key, value in items.items():
                    serialized_value = json.dumps(value)
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {self.KV_TABLE_NAME} (key, value) VALUES (?, ?)",
                        (key, serialized_value),
                    )
                self._auto_commit(conn)

            return True
        except Exception:
            return False

    def getConfig(self, key: str, default: Any = None) -> Any:
        """
        获取模块/适配器配置项（委托给config模块）

        :param key: 配置项的键(支持点分隔符如"module.sub.key")
        :param default: 默认值
        :return: 配置项的值

        {!--< deprecated >!--} 请使用 `config.getConfig` 来获取配置项，这个API已弃用
        """
        try:
            from .config import config

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
            from .config import config

            return config.setConfig(key, value)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """
        删除存储项

        支持嵌套键删除，如 "user.settings.theme" 会删除嵌套对象中的对应字段

        :param key: 存储项键名，支持嵌套路径（如 "user.settings.theme"）
        :return: 操作是否成功

        :example:
        >>> storage.delete("temp.session")
        >>> storage.delete("user.settings.theme")  # 删除嵌套字段
        """
        if not self._is_ready():
            return False

        from .logger import logger

        logger.trace(i18n.t("core.storage.kv_delete", key=key))

        try:
            with self._get_connection() as conn:
                # 解析嵌套键（传入连接对象以提高性能）
                root_key, nested_path = self._parse_nested_key(key, conn)

                # 如果不是嵌套键，直接删除
                if not nested_path:
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {self.KV_TABLE_NAME} WHERE key = ?", (key,))
                    self._auto_commit(conn)
                    return True

                # 处理嵌套键删除
                cursor = conn.cursor()

                # 获取现有的根键值
                cursor.execute(f"SELECT value FROM {self.KV_TABLE_NAME} WHERE key = ?", (root_key,))
                result = cursor.fetchone()

                if not result:
                    return False

                try:
                    current_value = json.loads(result[0])
                except json.JSONDecodeError:
                    # 如果现有值不是JSON，无法进行嵌套操作
                    return False

                # 确保值是字典或列表，以便进行嵌套操作
                if not isinstance(current_value, (dict, list)):
                    return False

                # 删除嵌套值
                updated_value, deleted = self._delete_nested_value(
                    current_value, nested_path
                )

                if not deleted:
                    return False

                # 存储更新后的值
                serialized_value = json.dumps(updated_value)
                cursor.execute(
                    f"INSERT OR REPLACE INTO {self.KV_TABLE_NAME} (key, value) VALUES (?, ?)",
                    (root_key, serialized_value),
                )
                self._auto_commit(conn)

            return True
        except Exception:
            return False

    def delete_multi(self, keys: list[str]) -> bool:
        """
        批量删除多个存储项

        :param keys: 键名列表
        :return: 操作是否成功

        :example:
        >>> storage.delete_multi(["temp.key1", "temp.key2"])
        """
        if not self._is_ready():
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    f"DELETE FROM {self.KV_TABLE_NAME} WHERE key = ?", [(k,) for k in keys]
                )
                self._auto_commit(conn)

            return True
        except Exception:
            return False

    def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取多个存储项的值

        :param keys: 键名列表
        :return: 键值对字典

        :example:
        >>> settings = storage.get_multi(["app.name", "app.version"])
        """
        if not self._is_ready():
            return {}

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                placeholders = ",".join(["?"] * len(keys))
                cursor.execute(
                    f"SELECT key, value FROM {self.KV_TABLE_NAME} WHERE key IN ({placeholders})", keys
                )
                results = {}
                for row in cursor.fetchall():
                    try:
                        results[row[0]] = json.loads(row[1])
                    except json.JSONDecodeError:
                        results[row[0]] = row[1]
                return results
        except Exception as e:
            from .logger import logger

            logger.error(i18n.t("core.storage.get_multi_failed", error=e))
            return {}

    def transaction(self) -> "StorageManager._Transaction | _EmptyTransaction | _NestedTransaction":
        """
        创建事务上下文

        :return: 事务上下文管理器

        :example:
        >>> with storage.transaction():
        ...     storage.set("key1", "value1")
        ...     storage.set("key2", "value2")
        """
        if not self._is_ready():
            # 返回一个空的事务对象
            return _EmptyTransaction()

        # 如果已经在事务中（嵌套事务），返回一个空事务，复用现有连接
        if (
            hasattr(self._local, "transaction_conn")
            and self._local.transaction_conn is not None
        ):
            from .logger import logger

            logger.trace(i18n.t("core.storage.transaction_nested"))

            return _NestedTransaction()

        return self._Transaction(self)

    class _Transaction:
        """
        事务上下文管理器

        {!--< internal-use >!--}
        确保多个操作的原子性
        """

        def __init__(self, storage_manager: "StorageManager"):
            self.storage_manager = storage_manager
            self.conn = None
            self.cursor = None

        def __enter__(self) -> "StorageManager._Transaction":
            """
            进入事务上下文

            :return: 事务对象
            """
            from .logger import logger

            logger.trace(i18n.t("core.storage.transaction_begin"))
            self.conn = self.storage_manager._open_connection()
            self.cursor = self.conn.cursor()
            self.cursor.execute("BEGIN TRANSACTION")
            # 将连接存储到线程本地存储，供其他方法复用
            self.storage_manager._local.transaction_conn = self.conn
            return self

        def __exit__(
            self, exc_type: type[Exception], exc_val: Exception, exc_tb: Any
        ) -> None:
            """
            退出事务上下文

            :param exc_type: 异常类型
            :param exc_val: 异常对象
            :param exc_tb: 异常堆栈

            :return: None
            """
            # 清除线程本地存储中的连接引用
            if hasattr(self.storage_manager._local, "transaction_conn"):
                self.storage_manager._local.transaction_conn = None

            if self.conn is not None:
                try:
                    if exc_type is None:
                        if hasattr(self.conn, "commit"):
                            from .logger import logger

                            logger.trace(i18n.t("core.storage.transaction_commit"))
                            self.conn.commit()
                    else:
                        if hasattr(self.conn, "rollback"):
                            from .logger import logger

                            logger.trace(
                                i18n.t("core.storage.transaction_rollback", error=exc_val)
                            )
                            self.conn.rollback()
                        from .logger import logger

                        logger.error(
                            i18n.t("core.storage.transaction_failed", error=exc_val)
                        )
                finally:
                    if hasattr(self.conn, "close"):
                        self.conn.close()

    def clear(self) -> bool:
        """
        清空所有存储项

        :return: 操作是否成功

        :example:
        >>> storage.clear()
        """
        if not self._is_ready():
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self.KV_TABLE_NAME}")
                self._auto_commit(conn)

            return True
        except Exception:
            return False

    def Table(self, table_name: str) -> SQLiteQueryBuilder:
        """
        获取指定表的查询构建器

        :param table_name: 表名
        :return: SQLiteQueryBuilder 实例

        :example:
        >>> rows = storage.Table("users").Select("name", "age").Where("age > ?", 18).Execute()
        >>> storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        """
        _validate_identifier(table_name, "表名")
        return SQLiteQueryBuilder(self, table_name)

    def CreateTable(self, table_name: str, columns: dict[str, str]) -> bool:
        """
        创建表

        :param table_name: 表名
        :param columns: 列定义字典（列名 → SQL 类型定义）
        :return: 操作是否成功

        :example:
        >>> storage.CreateTable("users", {
        ...     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        ...     "name": "TEXT NOT NULL",
        ...     "age": "INTEGER DEFAULT 0"
        ... })
        """
        if not self._is_ready():
            return False

        # 验证表名和列名/类型
        try:
            _validate_identifier(table_name, "表名")
            for col_name, col_type in columns.items():
                _validate_identifier(col_name, "列名")
                _validate_column_type(col_type)
        except ValueError as e:
            from .logger import logger

            logger.error(
                i18n.t("core.storage.create_table_failed", table=table_name, error=e)
            )
            return False

        try:
            col_defs = ", ".join(f"{col} {typ}" for col, typ in columns.items())
            sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})"

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                self._auto_commit(conn)
            return True
        except Exception as e:
            from .logger import logger

            logger.error(
                i18n.t("core.storage.create_table_failed", table=table_name, error=e)
            )
            return False

    def DropTable(self, table_name: str) -> bool:
        """
        删除表

        :param table_name: 表名
        :return: 操作是否成功

        :example:
        >>> storage.DropTable("users")
        """
        if not self._is_ready():
            return False

        try:
            _validate_identifier(table_name, "表名")
        except ValueError as e:
            from .logger import logger

            logger.error(i18n.t("core.storage.drop_table_failed", error=e))
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                self._auto_commit(conn)
            return True
        except Exception as e:
            from .logger import logger

            logger.error(
                i18n.t("core.storage.drop_table_name_failed", table=table_name, error=e)
            )
            return False

    def HasTable(self, table_name: str) -> bool:
        """
        检查表是否存在

        :param table_name: 表名
        :return: 是否存在

        :example:
        >>> if storage.HasTable("users"):
        ...     print("users 表已存在")
        """
        if not self._is_ready():
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,),
                )
                return cursor.fetchone() is not None
        except Exception:
            return False

    def AlterTable(self, table_name: str) -> AlterTableBuilder:
        """
        获取 ALTER TABLE 构建器

        :param table_name: 表名
        :return: AlterTableBuilder 实例

        :example:
        >>> storage.AlterTable("users").AddColumn("email", "TEXT").Execute()
        >>> storage.AlterTable("users").RenameTo("members").Execute()
        """
        _validate_identifier(table_name, "表名")
        return AlterTableBuilder(self, table_name)

    def __getattr__(self, key: str) -> Any:
        """
        通过属性访问存储项

        :param key: 存储项键名
        :return: 存储项的值

        :raises AttributeError: 当存储项不存在时抛出

        :example:
        >>> app_name = storage.app_name
        """
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

        # 检查键是否存在
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT value FROM {self.KV_TABLE_NAME} WHERE key = ?", (key,))
                if (result := cursor.fetchone()) is None:
                    raise AttributeError(i18n.t("core.storage.item_not_exist", key=key))
        except AttributeError:
            raise
        except Exception as _err:
            raise AttributeError(i18n.t("core.storage.item_not_exist_error", key=key)) from _err

        # 解析并返回值
        try:
            return json.loads(result[0])
        except json.JSONDecodeError:
            return result[0]

    def __setattr__(self, key: str, value: Any) -> None:
        """
        通过属性设置存储项

        :param key: 存储项键名
        :param value: 存储项的值

        :example:
        >>> storage.app_name = "MyApp"
        """
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
            from .logger import logger

            logger.error(i18n.t("core.storage.set_failed", key=key, error=e))


storage: StorageManager = StorageManager()

__all__ = ["storage"]
