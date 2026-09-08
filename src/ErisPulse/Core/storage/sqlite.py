"""
ErisPulse SQLite 存储后端（aiosqlite 异步原生实现）

默认存储后端。数据库文件位于项目目录 ``config/config.db``；
启用 ``use_global_db`` 时使用包内全局数据库 ``data/config.db``。

{!--< tips >!--}
1. 非事务操作复用每事件循环的单个共享连接（autocommit 模式）
2. 事务使用专用连接（BEGIN/COMMIT/ROLLBACK），与共享连接互不干扰
3. WAL 日志模式 + busy_timeout，支持多事件循环（如同步桥接循环）并发访问
{!--< /tips >!--}
"""

import sqlite3
from pathlib import Path
from typing import Any

import aiosqlite

from ..Bases.sql_base import SQLDialect, SQLStorageBase, _SingletonMixin
from ..constants import (
    DEFAULT_USE_GLOBAL_DB,
    SQLITE_JOURNAL_MODE,
    SQLITE_SYNCHRONOUS_MODE,
)
from ..i18n import i18n
from ..logger import logger

# 多循环并发（同步桥接 + 用户异步循环）时的写等待上限
_SQLITE_BUSY_TIMEOUT_MS = 5000

__all__ = ["SQLiteDialect", "SQLiteStorage"]


class SQLiteDialect(SQLDialect):
    """SQLite 方言实现"""

    name = "sqlite"
    extra_name = "sqlite"

    key_column_type = "TEXT"
    value_column_type = "TEXT"

    def autoincrement_column(self, base_type: str) -> str:
        """{!--< internal-use >!--} SQLite 原生支持 AUTOINCREMENT 后缀"""
        return f"{base_type} PRIMARY KEY AUTOINCREMENT"

    _type_map: dict[str, str] = {}

    def is_missing_table_error(self, exc: BaseException) -> bool:
        """{!--< internal-use >!--} sqlite3.OperationalError: no such table"""
        return isinstance(exc, sqlite3.OperationalError) and "no such table" in str(exc)


class SQLiteStorage(_SingletonMixin, SQLStorageBase):
    """
    SQLite 存储管理器（aiosqlite 异步原生实现）

    单例模式实现，提供键值存储的增删改查、通用 SQL 链式查询和事务管理。

    支持两种数据库模式：
    1. 项目数据库（默认）：位于项目目录下的 config/config.db
    2. 全局数据库：位于包内的 data/config.db（``use_global_db`` 开启且文件存在时）

    {!--< tips >!--}
    1. 使用 get/set（或 aget/aset）方法操作键值存储项
    2. 使用 Table() 链式调用操作自定义表
    3. 使用 transaction/atransaction 上下文管理事务
    {!--< /tips >!--}
    """

    dialect: SQLDialect = SQLiteDialect()

    # 默认全局数据库放在包内的 data/config.db
    GLOBAL_DB_PATH = str(
        Path(__file__).resolve().parent.parent.parent / "data" / "config.db"
    )

    @staticmethod
    def _get_default_project_db_path() -> str:
        return str(Path.cwd() / "config" / "config.db")

    @property
    def DEFAULT_PROJECT_DB_PATH(self) -> str:
        return self._get_default_project_db_path()

    def __init__(self) -> None:
        # 避免重复初始化
        if getattr(self, "_initialized", False):
            return
        super().__init__()

        self._ensure_directories()

        # 根据配置决定使用哪个数据库
        from ...runtime import get_storage_config

        storage_config = get_storage_config()
        use_global_db = bool(storage_config.get("use_global_db", DEFAULT_USE_GLOBAL_DB))

        if use_global_db and Path(self.GLOBAL_DB_PATH).exists():
            self.db_path = self.GLOBAL_DB_PATH
        else:
            self.db_path = self.DEFAULT_PROJECT_DB_PATH

        logger.debug(i18n.t("core.storage.init_db", path=self.db_path))
        self._init_db()

        self._last_use_global_db = use_global_db
        self._finish_init()
        # use_global_db 决定数据库文件路径，已打开的句柄无法运行时安全切换；
        # 订阅配置变更，变化时明确告警需重启
        self._watch_storage_config(self._check_use_global_db_changed)

    def _check_use_global_db_changed(self) -> str | None:
        """{!--< internal-use >!--} use_global_db 配置变更检查"""
        from ...runtime import get_storage_config

        new_use_global = bool(
            get_storage_config().get("use_global_db", DEFAULT_USE_GLOBAL_DB)
        )
        if new_use_global != self._last_use_global_db:
            self._last_use_global_db = new_use_global
            return i18n.t("core.config.restart_required", key="storage.use_global_db")
        return None

    def _ensure_directories(self) -> None:
        """{!--< internal-use >!--} 确保必要的目录存在"""
        try:
            Path(self._get_default_project_db_path()).parent.mkdir(
                parents=True, exist_ok=True
            )
        except Exception as e:
            logger.trace(i18n.t("core.storage.ensure_dir_failed", error=e))

    def _init_db(self) -> None:
        """
        {!--< internal-use >!--}
        初始化数据库（创建默认 config 键值表）

        :raises sqlite3.OperationalError: 数据库文件无法创建或打开时
        """
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.trace(i18n.t("core.storage.ensure_dir_failed", error=e))

        try:
            self._bridge_run(self._init_kv_table())
        except sqlite3.OperationalError as e:
            logger.error(i18n.t("core.storage.cannot_open_db", error=e))
            raise
        except Exception as e:
            logger.error(i18n.t("core.storage.init_db_error", error=e))
            raise

    # 连接管理

    @staticmethod
    async def _apply_pragmas(conn: aiosqlite.Connection) -> None:
        """{!--< internal-use >!--} 应用标准 PRAGMA（WAL/synchronous/busy_timeout）"""
        await conn.execute(SQLITE_JOURNAL_MODE)
        await conn.execute(SQLITE_SYNCHRONOUS_MODE)
        await conn.execute(f"PRAGMA busy_timeout={_SQLITE_BUSY_TIMEOUT_MS}")

    async def _create_loop_resource(self) -> aiosqlite.Connection:
        """{!--< internal-use >!--} 当前事件循环的共享连接（autocommit 模式）"""
        conn = await aiosqlite.connect(self.db_path, isolation_level=None)
        try:
            await self._apply_pragmas(conn)
        except Exception:
            await conn.close()
            raise
        return conn

    async def _destroy_loop_resource(self, resource: aiosqlite.Connection) -> None:
        """{!--< internal-use >!--} 关闭共享连接"""
        await resource.close()

    async def _acquire_resource_conn(self, resource: aiosqlite.Connection) -> Any:
        """{!--< internal-use >!--} 共享连接直接复用（游标级并发安全）"""
        return resource

    async def _release_resource_conn(
        self, resource: aiosqlite.Connection, conn: Any
    ) -> None:
        """{!--< internal-use >!--} 共享连接无需归还"""

    async def _open_txn_conn(self) -> aiosqlite.Connection:
        """{!--< internal-use >!--} 事务使用专用连接（与共享连接互不干扰）"""
        conn = await aiosqlite.connect(self.db_path, isolation_level=None)
        try:
            await self._apply_pragmas(conn)
        except Exception:
            await conn.close()
            raise
        return conn

    async def _close_txn_conn(self, conn: aiosqlite.Connection) -> None:
        """{!--< internal-use >!--} 关闭事务专用连接"""
        await conn.close()

    # 事务控制

    async def _begin_txn(self, conn: Any) -> None:
        """{!--< internal-use >!--} BEGIN TRANSACTION"""
        logger.trace(i18n.t("core.storage.transaction_begin"))
        await conn.execute("BEGIN TRANSACTION")

    async def _commit_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} COMMIT"""
        logger.trace(i18n.t("core.storage.transaction_commit"))
        await conn.commit()

    async def _rollback_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} ROLLBACK"""
        logger.trace(i18n.t("core.storage.transaction_rollback", error=""))
        await conn.rollback()

    # 方言执行漏斗

    async def _exec_query_on(
        self, kind: str, sql: str, params: Any, conn: Any
    ) -> Any:
        """
        {!--< internal-use >!--}
        SQLite 执行漏斗

        :param kind: "select" / "one" / "count" / "dml" / "dml_multi"
        :return: select/one 返回 (行, 列名列表或None)；其余返回受影响行数
        """
        # SQLite 原生使用 ? 占位符，无需翻译
        if kind == "dml_multi":
            cursor = await conn.executemany(sql, params)
            return cursor.rowcount

        cursor = await conn.execute(sql, params)
        try:
            if kind == "dml":
                return cursor.rowcount

            description = cursor.description
            columns = (
                [col[0] for col in description] if description else None
            )
            if kind == "count":
                row = await cursor.fetchone()
                return row[0] if row else 0
            if kind == "one":
                return await cursor.fetchone(), columns
            rows = await cursor.fetchall()
            return rows, columns
        finally:
            await cursor.close()
