"""
ErisPulse 存储管理模块

提供键值存储、通用 SQL 链式查询和事务支持，用于管理框架运行时数据。
内置三种异步原生后端，通过 ``ErisPulse.storage.backend`` 配置项选择：
1. sqlite（默认）：aiosqlite，项目目录 config/config.db
2. mysql：aiomysql，配置见 ``ErisPulse.storage.mysql``
3. postgres：asyncpg，配置见 ``ErisPulse.storage.postgres``

三种后端 API 完全一致，切换后端无需修改调用代码。

后端可插拔：外部包经 entry-points 组 ``erispulse.storage.backends`` 注册
（模块导入时调用 :func:`register_storage_backend`，声明自己的驱动依赖与
ConfigClass），``ErisPulse.storage.backend`` 填注册名即启用——驱动自动
安装、报错指引、线程桥接等行为整套继承，框架零改动。
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
import importlib.metadata

from ..constants import DEFAULT_STORAGE_BACKEND
from ..i18n import i18n
from ..logger import logger
from .mysql import MySQLDialect, MySQLStorage
from .postgres import PostgresDialect, PostgresStorage
from .sqlite import SQLiteDialect, SQLiteStorage

# 后端别名（配置容错）
_BACKEND_ALIASES = {"postgresql": "postgres"}

# 后端注册表：名称 -> 存储类（内置三后端 + 外部包经 entry-points 注册）
_REGISTRY: "dict[str, type[SQLStorageBase]]" = {}
_ENTRYPOINTS_LOADED = False

def register_storage_backend(name: str, storage_cls: "type[SQLStorageBase]") -> None:
    """
    注册存储后端（可插拔机制）

    外部包在模块导入时调用本函数自注册；``ErisPulse.storage.backend`` 填
    注册名即启用，驱动自动安装（方言声明 ``driver_requires``）、线程桥接
    （``_SUPPORTS_THREAD_BRIDGE``）、ConfigClass 表单等行为整套继承。

    :param name: 后端注册名（配置 ``storage.backend`` 用）
    :param storage_cls: 存储类（SQLStorageBase 子类）
    """
    _REGISTRY[name.lower()] = storage_cls


def get_registered_backends() -> "list[str]":
    """
    列出已注册的后端名（交互式配置/向导的枚举来源）

    :return: 后端名列表（含内置与外部注册）
    """
    _load_entrypoint_backends()
    return sorted(_REGISTRY)


def _load_entrypoint_backends() -> None:
    """{!--< internal-use >!--} 扫描 entry-points 组并加载外部后端包（幂等）"""
    global _ENTRYPOINTS_LOADED
    if _ENTRYPOINTS_LOADED:
        return
    _ENTRYPOINTS_LOADED = True
    try:
        eps = importlib.metadata.entry_points(group="erispulse.storage.backends")
    except Exception:
        return
    for ep in eps:
        try:
            ep.load()
        except Exception as e:
            logger.warning(
                i18n.t("core.storage.backend_plugin_failed", name=ep.name, error=e)
            )


# 内置三后端自注册（外部包经 entry-points 组 erispulse.storage.backends 同款注册）
register_storage_backend("sqlite", SQLiteStorage)
register_storage_backend("mysql", MySQLStorage)
register_storage_backend("postgres", PostgresStorage)


def create_storage() -> SQLStorageBase:
    """
    根据配置创建存储后端实例

    读取 ``ErisPulse.storage.backend`` 配置项，从注册表实例化对应后端；
    创建前扫描 entry-points 装载外部后端包（时序解法：注册发生在首次
    创建时，晚于框架启动的模块加载阶段）。驱动缺失时按方言声明自动安装。

    :return: 存储后端实例
    :raises ValueError: 配置了未注册的后端名称时（附可用后端列表）

    :example:
    >>> storage = create_storage()
    """
    from ...runtime import get_storage_config

    _load_entrypoint_backends()

    backend = str(
        get_storage_config().get("backend", DEFAULT_STORAGE_BACKEND)
    ).lower()
    backend = _BACKEND_ALIASES.get(backend, backend)

    storage_cls = _REGISTRY.get(backend)
    if storage_cls is None:
        available = ", ".join(sorted(_REGISTRY))
        logger.error(
            i18n.t(
                "core.storage.backend_unknown",
                backend=f"{backend}（可用: {available}）",
            )
        )
        raise ValueError(i18n.t("core.storage.backend_unknown", backend=backend))
    return storage_cls()


storage: SQLStorageBase = create_storage()

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
    "get_registered_backends",
    "register_storage_backend",
    "storage",
]
