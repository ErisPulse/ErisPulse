"""
ErisPulse PostgreSQL 存储后端（asyncpg 异步原生实现）

通过 ``ErisPulse.storage.backend = "postgres"``（或 "postgresql"）启用，
连接参数来自 ``ErisPulse.storage.postgres`` 配置节。需安装可选依赖：
``pip install ErisPulse[postgres]``

{!--< tips >!--}
1. 连接池按事件循环惰性创建（同步桥接循环与用户异步循环各自独立）
2. 事务使用 ``conn.transaction()`` 句柄管理（asyncpg 推荐方式）
{!--< /tips >!--}
"""

import re
from typing import Any

from ..Bases.errors import StorageUnreachableError
from ..Bases.sql_base import SQLDialect, SQLStorageBase, _SingletonMixin
from ..constants import (
    DEFAULT_STORAGE_PG_DATABASE,
    DEFAULT_STORAGE_PG_HOST,
    DEFAULT_STORAGE_PG_PASSWORD,
    DEFAULT_STORAGE_PG_POOL_MAX,
    DEFAULT_STORAGE_PG_POOL_MIN,
    DEFAULT_STORAGE_PG_PORT,
    DEFAULT_STORAGE_PG_USER,
)
from ..i18n import i18n
from ..logger import logger

__all__ = ["PostgresDialect", "PostgresStorage"]


class PostgresDialect(SQLDialect):
    """PostgreSQL 方言实现"""

    name = "postgres"
    extra_name = "postgres"

    key_column_type = "TEXT"
    value_column_type = "TEXT"

    def translate_sql(self, sql: str) -> str:
        """{!--< internal-use >!--} ``?`` → ``$1..$n``（asyncpg 序号参数风格）"""
        counter = 0

        def _replace(_match: re.Match[str]) -> str:
            nonlocal counter
            counter += 1
            return f"${counter}"

        return re.sub(r"\?", _replace, sql)

    def upsert_kv_sql(self, table: str, key_col: str, value_col: str) -> str:
        """{!--< internal-use >!--} ON CONFLICT DO UPDATE 形式的 UPSERT"""
        return (
            f"INSERT INTO {table} ({key_col}, {value_col}) VALUES (?, ?) "
            f"ON CONFLICT ({key_col}) DO UPDATE SET {value_col} = EXCLUDED.{value_col}"
        )

    def has_table_sql(self, table_name: str) -> tuple[str, list[str]]:
        """{!--< internal-use >!--} information_schema 查询当前 schema"""
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = ?",
            [table_name],
        )

    def autoincrement_column(self, base_type: str) -> str:
        """{!--< internal-use >!--} ``SERIAL/BIGSERIAL PRIMARY KEY``"""
        base = "BIGSERIAL" if base_type.upper().startswith("BIG") else "SERIAL"
        return f"{base} PRIMARY KEY"

    _type_map: dict[str, str] = {
        "DOUBLE": "DOUBLE PRECISION",
        "CLOB": "TEXT",
        "NCLOB": "TEXT",
        "NVARCHAR": "VARCHAR",
        "NCHAR": "CHAR",
        "TINYINT": "SMALLINT",
        "DATETIME": "TIMESTAMP",
        "LONGTEXT": "TEXT",
        "MEDIUMTEXT": "TEXT",
    }

    def is_missing_table_error(self, exc: BaseException) -> bool:
        """{!--< internal-use >!--} asyncpg UndefinedTableError（按类名判定，避免强依赖驱动）"""
        return type(exc).__name__ == "UndefinedTableError"


class PostgresStorage(_SingletonMixin, SQLStorageBase):
    """
    PostgreSQL 存储管理器（asyncpg 异步原生实现）

    单例模式实现，接口与 SQLite / MySQL 后端完全一致，可通过
    ``ErisPulse.storage.backend`` 配置项无感切换。

    {!--< tips >!--}
    1. 连接参数见 ``ErisPulse.storage.postgres`` 配置节
    2. 缺少驱动时提示安装 ``pip install ErisPulse[postgres]``
    {!--< /tips >!--}
    """

    dialect: SQLDialect = PostgresDialect()
    KV_TABLE_NAME = "config"

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__()

        from ...runtime import get_storage_config

        section = get_storage_config().get("postgres", {})
        self._pg_config = {
            "host": section.get("host", DEFAULT_STORAGE_PG_HOST),
            "port": int(section.get("port", DEFAULT_STORAGE_PG_PORT)),
            "user": section.get("user", DEFAULT_STORAGE_PG_USER),
            "password": section.get("password", DEFAULT_STORAGE_PG_PASSWORD),
            "database": section.get("database", DEFAULT_STORAGE_PG_DATABASE),
            "pool_min": int(section.get("pool_min", DEFAULT_STORAGE_PG_POOL_MIN)),
            "pool_max": int(section.get("pool_max", DEFAULT_STORAGE_PG_POOL_MAX)),
        }

        logger.info(i18n.t("core.storage.backend_init", backend="postgres"))
        try:
            self._init_db()
        except StorageUnreachableError as e:
            # 数据库不可达：框架照常启动（存储未就绪，操作快速失败），
            # 冷却结束后自动重连；已由 _get_loop_resource 记录 WARNING
            logger.error(i18n.t("core.storage.init_db_error", error=e))
            return
        self._finish_init()
        # 连接参数无法运行时热切换，变更时告警需重启
        self._watch_storage_config(self._check_config_changed)

    def _check_config_changed(self) -> str | None:
        """{!--< internal-use >!--} postgres 连接配置变更检查"""
        from ...runtime import get_storage_config

        section = get_storage_config().get("postgres", {})
        current = {
            "host": section.get("host", DEFAULT_STORAGE_PG_HOST),
            "port": int(section.get("port", DEFAULT_STORAGE_PG_PORT)),
            "user": section.get("user", DEFAULT_STORAGE_PG_USER),
            "password": section.get("password", DEFAULT_STORAGE_PG_PASSWORD),
            "database": section.get("database", DEFAULT_STORAGE_PG_DATABASE),
            "pool_min": int(section.get("pool_min", DEFAULT_STORAGE_PG_POOL_MIN)),
            "pool_max": int(section.get("pool_max", DEFAULT_STORAGE_PG_POOL_MAX)),
        }
        if current != self._pg_config:
            self._pg_config = current
            return i18n.t("core.config.restart_required", key="storage.postgres")
        return None

    def _init_db(self) -> None:
        """{!--< internal-use >!--} 初始化数据库（创建默认 config 键值表）"""
        try:
            self._bridge_run(self._init_kv_table())
        except Exception as e:
            logger.error(i18n.t("core.storage.init_db_error", error=e))
            raise

    # 驱动管理

    def _require_driver(self) -> Any:
        """{!--< internal-use >!--} 惰性导入 asyncpg，缺失时给出安装指引"""
        try:
            import asyncpg
        except ImportError as e:
            raise RuntimeError(
                i18n.t(
                    "core.storage.driver_missing",
                    backend="postgres",
                    extra=self.dialect.extra_name,
                )
            ) from e
        return asyncpg

    # 连接池管理

    async def _create_loop_resource(self) -> Any:
        """{!--< internal-use >!--} 当前事件循环的连接池"""
        asyncpg = self._require_driver()
        cfg = self._pg_config
        try:
            return await asyncpg.create_pool(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                min_size=cfg["pool_min"],
                max_size=cfg["pool_max"],
            )
        except Exception as e:
            logger.error(
                i18n.t("core.storage.pool_init_failed", backend="postgres", error=e)
            )
            raise

    async def _destroy_loop_resource(self, resource: Any) -> None:
        """{!--< internal-use >!--} 优雅关闭连接池"""
        await resource.close()

    async def _acquire_resource_conn(self, resource: Any) -> Any:
        """{!--< internal-use >!--} 从池中获取连接"""
        return await resource.acquire()

    async def _release_resource_conn(self, resource: Any, conn: Any) -> None:
        """{!--< internal-use >!--} 归还连接到池"""
        await resource.release(conn)

    async def _open_txn_conn(self) -> Any:
        """{!--< internal-use >!--} 事务使用池内专用连接（获取与释放在同一事件循环上）"""
        resource = await self._get_loop_resource()
        return await resource.acquire()

    async def _close_txn_conn(self, conn: Any) -> None:
        """{!--< internal-use >!--} 归还事务专用连接"""
        resource = await self._get_loop_resource()
        await resource.release(conn)

    # 事务控制（asyncpg 推荐使用 transaction() 句柄）

    async def _begin_txn(self, conn: Any) -> Any:
        """{!--< internal-use >!--} 开启事务，返回 transaction 句柄"""
        logger.trace(i18n.t("core.storage.transaction_begin"))
        tx = conn.transaction()
        await tx.start()
        return tx

    async def _commit_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} COMMIT"""
        logger.trace(i18n.t("core.storage.transaction_commit"))
        if handle is not None:
            await handle.commit()

    async def _rollback_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} ROLLBACK"""
        logger.trace(i18n.t("core.storage.transaction_rollback", error=""))
        if handle is not None:
            await handle.rollback()

    # 方言执行漏斗

    async def _exec_query_on(self, kind: str, sql: str, params: Any, conn: Any) -> Any:
        """
        {!--< internal-use >!--}
        PostgreSQL 执行漏斗

        :param kind: "select" / "one" / "count" / "dml" / "dml_multi"
        :return: select/one 返回 (行, 列名列表或None)；其余返回受影响行数
        """
        sql = self.dialect.translate_sql(sql)

        if kind == "dml_multi":
            await conn.executemany(sql, params)
            return len(params)

        if kind == "select":
            records = await conn.fetch(sql, *params)
            rows = [tuple(record.values()) for record in records]
            columns = list(records[0].keys()) if records else None
            return rows, columns

        if kind == "one":
            record = await conn.fetchrow(sql, *params)
            if record is None:
                return None, None
            return tuple(record.values()), list(record.keys())

        if kind == "count":
            record = await conn.fetchrow(sql, *params)
            return record[0] if record else 0

        # dml：asyncpg execute 返回状态串（如 "UPDATE 3" / "CREATE TABLE"）
        status = await conn.execute(sql, *params)
        try:
            return int(status.rsplit(" ", 1)[-1])
        except (ValueError, AttributeError):
            return 0
