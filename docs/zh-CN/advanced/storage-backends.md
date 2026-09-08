# 存储后端

ErisPulse 内置三种异步原生存储后端，通过配置一键切换，**API 完全一致、切换零代码改动**：

| 后端 | 驱动 | 安装 | 特点 |
|------|------|------|------|
| SQLite（默认） | aiosqlite | 开箱即用 | 零配置、单文件、WAL 并发 |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | 适合已有 MySQL 基础设施、多实例共享 |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | 事务能力强、JSONB 生态、高并发 |

{!--< tips >!--}
1. 异步是原生主接口（`aget/aset/atransaction/aExecute`），同步 API 为兼容层
2. 框架自身的配置持久化、会话收件箱、对话检查点等全部走同一存储后端——切换后端即整体迁移
{!--< /tips >!--}

## 后端选择

在 `config/config.toml` 中配置：

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite"（默认）/ "mysql" / "postgres"
use_global_db = false     # 仅 SQLite：使用包内全局数据库 data/config.db
```

也支持环境变量覆盖（Docker / 12-factor）：

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

环境变量命名规则：配置路径大写、点号换下划线
（`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`）。

## 连接参数

### MySQL（`ErisPulse.storage.mysql`）

```toml
[ErisPulse.storage.mysql]
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
charset = "utf8mb4"
pool_min = 1
pool_max = 10
```

### PostgreSQL（`ErisPulse.storage.postgres`）

```toml
[ErisPulse.storage.postgres]
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
pool_min = 1
pool_max = 10
```

> [!NOTE]
> 连接参数变更后需重启框架生效（配置热更新时会输出重启提醒日志）。
> 连接池按事件循环惰性创建，创建瞬时失败（网络抖动 / 数据库重启窗口）自动指数退避重试。

## 异步原生 API

```python
# KV 操作
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()

# 表操作
await sdk.storage.aCreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})
rows = await sdk.storage.Table("users").Select("name").ToDict().aExecute()

# 异步事务
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

同步 API（`get/set/transaction/Table(...).Execute()`）继续可用，内部经
`AsyncBridge` 后台事件循环桥接执行——在异步 handler 中调用会短暂阻塞
该事件循环，推荐优先使用 a 前缀异步方法。完整方法对照见
[SQL 查询构建器](sql-builder.md)。

## 方言行为差异

方言差异全部收敛在框架内部，调用代码无需感知：

| 差异点 | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| 占位符 | `?` | `%s`（自动翻译） | `$1..$n`（自动翻译） |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV 值列类型 | `TEXT` | `LONGTEXT` | `TEXT` |
| 自增主键 | 原生支持 | `AUTO_INCREMENT`（自动翻译） | `SERIAL`（自动翻译） |

建表列类型统一使用 SQLite 风格定义（如 `"INTEGER PRIMARY KEY AUTOINCREMENT"`、
`"TEXT NOT NULL"`、`"DOUBLE DEFAULT 0.0"`），由方言自动翻译为目标后端等价写法。

## 自定义 SQL 后端

纯 SQL 后端可继承共享基类，只需提供连接管理与方言执行漏斗：

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # 覆写：占位符翻译 / 标识符引用 / UPSERT / 类型映射 ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # 连接池
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # 执行漏斗
```

非 SQL 后端（如 Redis）继承 `BaseStorage` 实现 KV 异步接口后，
可直接使用 `KVQueryBuilder` 获得链式表查询能力（内存过滤，适合中小数据量）。

## 相关文档

- [SQL 查询构建器](sql-builder.md) - 链式查询语法与异步 API 对照
- [核心模块 API](../api-reference/core-modules.md) - Storage 模块完整 API
- [存储基类 API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect 抽象接口
