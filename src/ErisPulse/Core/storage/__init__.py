"""
ErisPulse 存储管理模块

提供键值存储、通用 SQL 链式查询和事务支持，用于管理框架运行时数据。
内置三种异步原生后端，通过 ``ErisPulse.storage.backend`` 配置项选择：
1. sqlite（默认）：aiosqlite，项目目录 config/config.db
2. mysql：aiomysql，配置见 ``ErisPulse.storage.mysql``
3. postgres：asyncpg，配置见 ``ErisPulse.storage.postgres``

三种后端 API 完全一致，切换后端无需修改调用代码。
mysql / postgres 连接失败时快速失败（冷却后自动重连），不影响框架运行。

{!--< tips >!--}
1. 支持JSON序列化存储复杂数据类型
2. 提供事务支持确保数据一致性
3. 提供链式调用风格的通用 SQL 查询构建器
{!--< /tips >!--}
"""

from ..Bases.sql_base import (
    AlterTableBuilder,
    SQLDialect,
    SQLQueryBuilder,
    SQLStorageBase,
)
from ..Bases.storage import BaseStorage
from ..constants import DEFAULT_STORAGE_BACKEND
from ..i18n import i18n
from ..logger import logger
from .mysql import MySQLDialect, MySQLStorage
from .postgres import PostgresDialect, PostgresStorage
from .sqlite import SQLiteDialect, SQLiteStorage

# 后端别名（配置容错）
_BACKEND_ALIASES = {"postgresql": "postgres"}


def create_storage() -> BaseStorage:
    """
    根据配置创建存储后端实例

    读取 ``ErisPulse.storage.backend`` 配置项，实例化对应后端。
    驱动缺失时报错并提示安装命令。

    :return: 存储后端实例
    :raises ValueError: 配置了未知的后端名称时

    :example:
    >>> storage = create_storage()
    """
    from ...runtime import get_storage_config

    backend = str(
        get_storage_config().get("backend", DEFAULT_STORAGE_BACKEND)
    ).lower()
    backend = _BACKEND_ALIASES.get(backend, backend)

    if backend == "sqlite":
        return SQLiteStorage()
    if backend == "mysql":
        return MySQLStorage()
    if backend == "postgres":
        return PostgresStorage()

    logger.error(i18n.t("core.storage.backend_unknown", backend=backend))
    raise ValueError(i18n.t("core.storage.backend_unknown", backend=backend))


storage: BaseStorage = create_storage()

# 向后兼容别名：多后端重构前 SQLite 实现的原类名
StorageManager = SQLiteStorage

__all__ = [
    "AlterTableBuilder",
    "BaseStorage",
    "MySQLDialect",
    "MySQLStorage",
    "PostgresDialect",
    "PostgresStorage",
    "SQLDialect",
    "SQLQueryBuilder",
    "SQLStorageBase",
    "SQLiteDialect",
    "SQLiteStorage",
    "StorageManager",
    "create_storage",
    "storage",
]
