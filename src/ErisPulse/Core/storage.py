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

import os
import json
import sqlite3
import threading
from typing import Any, TypeAlias
from contextlib import contextmanager

from .Bases.storage import BaseStorage, BaseQueryBuilder

StorageKey: TypeAlias = str
StorageValue: TypeAlias = Any


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
        storage: "StorageManager" = self._storage  # type: ignore

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
            raise ValueError("InsertMulti 需要非空列表类型数据")

        columns = list(self._data[0].keys())
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
        storage: "StorageManager" = self._storage  # type: ignore
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
        storage: "StorageManager" = self._storage  # type: ignore
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
        elif self._operation == "insert":
            return self._build_insert_sql()
        elif self._operation == "update":
            return self._build_update_sql()
        elif self._operation == "delete":
            return self._build_delete_sql()
        else:
            raise ValueError("未设置操作类型，请先调用 Select/Insert/Update/Delete")

    def _build_select_sql(self) -> tuple[str, list[Any]]:
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
            raise ValueError("Insert 需要字典类型数据")
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        cols = ", ".join(columns)
        sql = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        params = list(data.values())
        return sql, params

    def _build_update_sql(self) -> tuple[str, list[Any]]:
        data = self._data
        if not isinstance(data, dict):
            raise ValueError("Update 需要字典类型数据")

        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
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

            logger.error(f"修改表 {self._table_name} 失败: {e}")
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
    # 默认数据库放在项目下的 config/config.db
    DEFAULT_PROJECT_DB_PATH = os.path.join(os.getcwd(), "config", "config.db")
    # 包内全局数据库路径
    GLOBAL_DB_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/config.db")
    )
    # 线程本地存储，用于跟踪活动事务的连接
    _local = threading.local()

    def __new__(cls, *args, **kwargs):
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

        if use_global_db and os.path.exists(self.GLOBAL_DB_PATH):
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

    @contextmanager
    def _get_connection(self) -> sqlite3.Connection:    # type: ignore
        """
        {!--< internal-use >!--}
        获取数据库连接（支持事务）

        如果在事务中，返回事务的连接
        否则创建新连接

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
            conn = sqlite3.connect(self.db_path)
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
        # 确保项目数据库目录存在
        try:
            os.makedirs(os.path.dirname(self.DEFAULT_PROJECT_DB_PATH), exist_ok=True)
        except Exception:
            pass  # 如果无法创建项目目录，则跳过

    def _init_db(self) -> None:
        """
        {!--< internal-use >!--}
        初始化数据库

        创建默认 config 键值表
        """
        from .logger import logger

        logger.info(f"初始化数据库: {self.db_path}")

        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        except Exception:
            pass  # 如果无法创建目录，则继续尝试连接数据库

        try:
            conn = sqlite3.connect(self.db_path)

            # 启用WAL模式提高并发性能
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")

            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            logger.error(f"无法创建或打开数据库文件: {e}")
            raise
        except Exception as e:
            logger.error(f"初始化数据库时发生未知错误: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取存储项的值

        :param key: 存储项键名
        :param default: 默认值(当键不存在时返回)
        :return: 存储项的值

        :example:
        >>> timeout = storage.get("network.timeout", 30)
        >>> user_settings = storage.get("user.settings", {})
        """
        if not self._is_ready():
            return default

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
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
            else:
                from .logger import logger

                logger.error(f"数据库操作错误: {e}")
                return default
        except Exception as e:
            from .logger import logger

            logger.error(f"获取存储项 {key} 时发生错误: {e}")
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
                cursor.execute("SELECT key FROM config")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            from .logger import logger

            logger.error(f"获取所有键名时发生错误: {e}")
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

    def set(self, key: str, value: Any) -> bool:
        """
        设置存储项的值

        :param key: 存储项键名
        :param value: 存储项的值
        :return: 操作是否成功

        :example:
        >>> storage.set("app.name", "MyApp")
        >>> storage.set("user.settings", {"theme": "dark"})
        """
        if not self._is_ready():
            return False

        try:
            serialized_value = json.dumps(value)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    (key, serialized_value),
                )
                self._auto_commit(conn)

            return True
        except Exception as e:
            from .logger import logger

            logger.error(f"设置存储项 {key} 失败: {e}")
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
                        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
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

        :param key: 存储项键名
        :return: 操作是否成功

        :example:
        >>> storage.delete("temp.session")
        """
        if not self._is_ready():
            return False

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM config WHERE key = ?", (key,))
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
                    "DELETE FROM config WHERE key = ?", [(k,) for k in keys]
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
                    f"SELECT key, value FROM config WHERE key IN ({placeholders})", keys
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

            logger.error(f"批量获取存储项失败: {e}")
            return {}

    def transaction(self) -> "StorageManager._Transaction":
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
            class EmptyTransaction:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return EmptyTransaction()

        # 如果已经在事务中（嵌套事务），返回一个空事务，复用现有连接
        if (
            hasattr(self._local, "transaction_conn")
            and self._local.transaction_conn is not None
        ):

            class NestedTransaction:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return NestedTransaction()

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
            self.conn = sqlite3.connect(self.storage_manager.db_path)
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
                            self.conn.commit()
                    else:
                        if hasattr(self.conn, "rollback"):
                            self.conn.rollback()
                        from .logger import logger

                        logger.error(f"事务执行失败: {exc_val}")
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
                cursor.execute("DELETE FROM config")
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

            logger.error(f"创建表 {table_name} 失败: {e}")
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
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                self._auto_commit(conn)
            return True
        except Exception as e:
            from .logger import logger

            logger.error(f"删除表 {table_name} 失败: {e}")
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
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            )

        if not self._is_ready():
            raise AttributeError(f"存储尚未初始化完成: {key}")

        # 检查键是否存在
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
                if (result := cursor.fetchone()) is None:
                    raise AttributeError(f"存储项 {key} 不存在")
        except AttributeError:
            raise
        except Exception:
            raise AttributeError(f"存储项 {key} 不存在或访问出错")

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

            logger.error(f"设置存储项 {key} 失败: {e}")


storage: StorageManager = StorageManager()

__all__ = ["storage"]
