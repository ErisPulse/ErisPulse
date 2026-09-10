"""
ErisPulse MySQL 存储后端（aiomysql 异步原生实现）

通过 ``ErisPulse.storage.backend = "mysql"`` 启用，连接参数来自
``ErisPulse.storage.mysql`` 配置节。需安装可选依赖：
``pip install ErisPulse[mysql]``

{!--< tips >!--}
1. 连接池按事件循环惰性创建（同步桥接循环与用户异步循环各自独立）
2. 池连接 autocommit 模式；事务使用池内专用连接（BEGIN/COMMIT/ROLLBACK）
{!--< /tips >!--}
"""

import warnings
from typing import Any

from ..Bases.errors import StorageUnreachableError
from ..Bases.sql_base import SQLDialect, SQLStorageBase, _SingletonMixin
from ..constants import (
    DEFAULT_STORAGE_MYSQL_CHARSET,
    DEFAULT_STORAGE_MYSQL_DATABASE,
    DEFAULT_STORAGE_MYSQL_HOST,
    DEFAULT_STORAGE_MYSQL_PASSWORD,
    DEFAULT_STORAGE_MYSQL_POOL_MAX,
    DEFAULT_STORAGE_MYSQL_POOL_MIN,
    DEFAULT_STORAGE_MYSQL_PORT,
    DEFAULT_STORAGE_MYSQL_USER,
)
from ..i18n import i18n
from ..logger import logger

__all__ = ["MySQLDialect", "MySQLStorage"]


class MySQLDialect(SQLDialect):
    """MySQL 方言实现"""

    name = "mysql"
    extra_name = "mysql"

    key_column_type = "VARCHAR(255)"
    value_column_type = "LONGTEXT"

    def translate_sql(self, sql: str) -> str:
        """{!--< internal-use >!--} ``?`` → ``%s``（PyMySQL 参数风格）"""
        return sql.replace("?", "%s")

    def quote(self, name: str) -> str:
        """{!--< internal-use >!--} 反引号引用（``key`` 为 MySQL 保留字，必须引用）"""
        return f"`{name}`"

    def upsert_kv_sql(self, table: str, key_col: str, value_col: str) -> str:
        """{!--< internal-use >!--} ON DUPLICATE KEY UPDATE 形式的 UPSERT"""
        return (
            f"INSERT INTO {table} ({key_col}, {value_col}) VALUES (?, ?) "
            f"ON DUPLICATE KEY UPDATE {value_col} = VALUES({value_col})"
        )

    def has_table_sql(self, table_name: str) -> tuple[str, list[str]]:
        """{!--< internal-use >!--} information_schema 查询当前数据库"""
        return (
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = ?",
            [table_name],
        )

    def autoincrement_column(self, base_type: str) -> str:
        """{!--< internal-use >!--} ``INT/BIGINT AUTO_INCREMENT PRIMARY KEY``"""
        base = "INT" if base_type.upper() in ("INTEGER", "INT") else base_type.upper()
        return f"{base} AUTO_INCREMENT PRIMARY KEY"

    _type_map: dict[str, str] = {
        "CLOB": "LONGTEXT",
        "NCLOB": "LONGTEXT",
    }

    def is_missing_table_error(self, exc: BaseException) -> bool:
        """{!--< internal-use >!--} MySQL 错误码 1146: ER_NO_SUCH_TABLE"""
        args = getattr(exc, "args", ())
        return bool(args) and args[0] == 1146


class MySQLStorage(_SingletonMixin, SQLStorageBase):
    """
    MySQL 存储管理器（aiomysql 异步原生实现）

    单例模式实现，接口与 SQLite 后端完全一致，可通过
    ``ErisPulse.storage.backend`` 配置项无感切换。

    {!--< tips >!--}
    1. 连接参数见 ``ErisPulse.storage.mysql`` 配置节
    2. 缺少驱动时提示安装 ``pip install ErisPulse[mysql]``
    {!--< /tips >!--}
    """

    dialect: SQLDialect = MySQLDialect()
    KV_TABLE_NAME = "config"

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__()

        from ...runtime import get_storage_config

        section = get_storage_config().get("mysql", {})
        self._mysql_config = {
            "host": section.get("host", DEFAULT_STORAGE_MYSQL_HOST),
            "port": int(section.get("port", DEFAULT_STORAGE_MYSQL_PORT)),
            "user": section.get("user", DEFAULT_STORAGE_MYSQL_USER),
            "password": section.get("password", DEFAULT_STORAGE_MYSQL_PASSWORD),
            "database": section.get("database", DEFAULT_STORAGE_MYSQL_DATABASE),
            "charset": section.get("charset", DEFAULT_STORAGE_MYSQL_CHARSET),
            "pool_min": int(section.get("pool_min", DEFAULT_STORAGE_MYSQL_POOL_MIN)),
            "pool_max": int(section.get("pool_max", DEFAULT_STORAGE_MYSQL_POOL_MAX)),
        }

        logger.info(
            i18n.t("core.storage.backend_init", backend="mysql")
        )
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
        """{!--< internal-use >!--} mysql 连接配置变更检查"""

        from ...runtime import get_storage_config

        section = get_storage_config().get("mysql", {})
        current = {
            "host": section.get("host", DEFAULT_STORAGE_MYSQL_HOST),
            "port": int(section.get("port", DEFAULT_STORAGE_MYSQL_PORT)),
            "user": section.get("user", DEFAULT_STORAGE_MYSQL_USER),
            "password": section.get("password", DEFAULT_STORAGE_MYSQL_PASSWORD),
            "database": section.get("database", DEFAULT_STORAGE_MYSQL_DATABASE),
            "charset": section.get("charset", DEFAULT_STORAGE_MYSQL_CHARSET),
            "pool_min": int(section.get("pool_min", DEFAULT_STORAGE_MYSQL_POOL_MIN)),
            "pool_max": int(section.get("pool_max", DEFAULT_STORAGE_MYSQL_POOL_MAX)),
        }
        if current != self._mysql_config:
            self._mysql_config = current
            return i18n.t("core.config.restart_required", key="storage.mysql")
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
        """{!--< internal-use >!--} 惰性导入 aiomysql，缺失时给出安装指引"""
        try:
            import aiomysql
        except ImportError as e:
            raise RuntimeError(
                i18n.t(
                    "core.storage.driver_missing",
                    backend="mysql",
                    extra=self.dialect.extra_name,
                )
            ) from e
        return aiomysql

    # 连接池管理

    async def _create_loop_resource(self) -> Any:
        """{!--< internal-use >!--} 当前事件循环的连接池（autocommit 模式）"""
        aiomysql = self._require_driver()
        cfg = self._mysql_config
        try:
            return await aiomysql.create_pool(
                host=cfg["host"],
                port=cfg["port"],
                user=cfg["user"],
                password=cfg["password"],
                db=cfg["database"],
                charset=cfg["charset"],
                minsize=cfg["pool_min"],
                maxsize=cfg["pool_max"],
                autocommit=True,
            )
        except Exception as e:
            logger.error(i18n.t("core.storage.pool_init_failed", backend="mysql", error=e))
            raise

    async def _destroy_loop_resource(self, resource: Any) -> None:
        """{!--< internal-use >!--} 优雅关闭连接池"""
        resource.close()
        await resource.wait_closed()

    async def _acquire_resource_conn(self, resource: Any) -> Any:
        """{!--< internal-use >!--} 从池中获取连接"""
        return await resource.acquire()

    async def _release_resource_conn(self, resource: Any, conn: Any) -> None:
        """{!--< internal-use >!--} 归还连接到池"""
        resource.release(conn)

    async def _open_txn_conn(self) -> Any:
        """{!--< internal-use >!--} 事务使用池内专用连接（获取与释放在同一事件循环上）"""
        resource = await self._get_loop_resource()
        return await resource.acquire()

    async def _close_txn_conn(self, conn: Any) -> None:
        """{!--< internal-use >!--} 归还事务专用连接"""
        resource = await self._get_loop_resource()
        resource.release(conn)

    # 事务控制

    async def _begin_txn(self, conn: Any) -> None:
        """{!--< internal-use >!--} BEGIN"""
        logger.trace(i18n.t("core.storage.transaction_begin"))
        await conn.begin()

    async def _commit_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} COMMIT"""
        logger.trace(i18n.t("core.storage.transaction_commit"))
        await conn.commit()

    async def _rollback_txn(self, conn: Any, handle: Any = None) -> None:
        """{!--< internal-use >!--} ROLLBACK"""
        logger.trace(i18n.t("core.storage.transaction_rollback", error=""))
        await conn.rollback()

    # 方言执行漏斗

    async def _exec_query_on(self, kind: str, sql: str, params: Any, conn: Any) -> Any:
        """
        {!--< internal-use >!--}
        MySQL 执行漏斗

        :param kind: "select" / "one" / "count" / "dml" / "dml_multi"
        :return: select/one 返回 (行, 列名列表或None)；其余返回受影响行数
        """
        sql = self.dialect.translate_sql(sql)
        cursor = await conn.cursor()
        try:
            if kind == "dml_multi":
                await cursor.executemany(sql, params)
                return cursor.rowcount

            # CREATE/DROP TABLE IF EXISTS 命中已有表时服务器回 NOTE 级警告，
            # aiomysql 依 DB-API 转为 Python Warning——属预期幂等行为，抑制之
            head = sql.lstrip()[:12].upper()
            if head.startswith(("CREATE TABLE", "DROP TABLE")):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    await cursor.execute(sql, params or None)
            else:
                await cursor.execute(sql, params or None)

            if kind == "dml":
                return cursor.rowcount

            description = cursor.description
            columns = [col[0] for col in description] if description else None
            if kind == "count":
                row = await cursor.fetchone()
                return row[0] if row else 0
            if kind == "one":
                return await cursor.fetchone(), columns
            rows = await cursor.fetchall()
            return rows, columns
        finally:
            await cursor.close()
