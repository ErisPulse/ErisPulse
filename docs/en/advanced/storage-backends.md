# Storage Backends

ErisPulse comes with three built-in asynchronous native storage backends, switchable with a single configuration change. **The API is completely consistent, requiring zero code changes when switching backends.**

| Backend | Driver | Installation | Features |
|---------|--------|--------------|----------|
| SQLite (default) | aiosqlite | Ready to use out-of-the-box | Zero configuration, single-file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Suitable for existing MySQL infrastructure, shared across multiple instances |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction support, JSONB ecosystem, high concurrency |

{!--< tips >!--}
1. Asynchronous operations are the native primary interface (`aget/aset/atransaction/aExecute`), while synchronous APIs serve as a compatibility layer.
2. The framework's own configuration persistence, session inbox, and conversation checkpoints all use the same storage backend—switching the backend results in a full migration.
{!--< /tips >!--}

## Backend Selection

Configure in `config/config.toml`:

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: use the package's global database data/config.db
```

Environment variables are also supported for overriding (useful for Docker / 12-factor applications):

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

Environment variable naming convention: Configuration paths are uppercase, and dots are replaced with underscores.
(e.g., `ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`).

## Connection Parameters

### MySQL (`ErisPulse.storage.mysql`)

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

### PostgreSQL (`ErisPulse.storage.postgres`)

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
> Changes to connection parameters require a framework restart to take effect (a restart reminder log is output during hot configuration updates).
> Connection pools are lazily created per event loop, and transient connection failures (e.g., network fluctuations or database restart windows) are automatically retried with exponential backoff.

## Native Asynchronous API

```python
# KV operations
await sdk.storage.aset("app.name", "MyApp")
value = await sdk.storage.aget("app.name")
keys = await sdk.storage.aget_all_keys()

# Table operations
await sdk.storage.aCreateTable("users", {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "name": "TEXT NOT NULL",
})
rows = await sdk.storage.Table("users").Select("name").ToDict().aExecute()

# Asynchronous transaction
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

Synchronous APIs (`get/set/transaction/Table(...).Execute()`) remain available, internally executed in the background event loop via `AsyncBridge`. However, calling them within asynchronous handlers will briefly block the event loop; prefer the `a`-prefixed asynchronous methods. For a complete method comparison, see [SQL Query Builder](sql-builder.md).

## Dialect Behavior Differences

All dialect differences are encapsulated within the framework, so calling code does not need to be aware:

| Difference | SQLite | MySQL | PostgreSQL |
|------------|--------|-------|------------|
| Placeholder | `?` | `%s` (automatically translated) | `$1..$n` (automatically translated) |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV Value Column Type | `TEXT` | `LONGTEXT` | `TEXT` |
| Auto-increment Primary Key | Native support | `AUTO_INCREMENT` (automatically translated) | `SERIAL` (automatically translated) |

Table column types are defined uniformly in SQLite style (e.g., `"INTEGER PRIMARY KEY AUTOINCREMENT"`, `"TEXT NOT NULL"`, `"DOUBLE DEFAULT 0.0"`), with dialects automatically translating these into equivalent syntax for the target backend.

## Custom SQL Backend

For pure SQL backends, you can inherit and share the base class, providing only connection management and dialect execution funnel:

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # Override: placeholder translation / identifier quoting / UPSERT / type mapping ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # Connection pool
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # Execution funnel
```

For non-SQL backends (e.g., Redis), inherit `BaseStorage` to implement asynchronous KV interface, then directly use `KVQueryBuilder` to gain chainable table query capabilities (in-memory filtering, suitable for small to medium datasets).

## Related Documentation

- [SQL Query Builder](sql-builder.md) - Chainable query syntax and asynchronous API comparison
- [Core Module API](../api-reference/core-modules.md) - Full API for the Storage module
- [Storage Base Class API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - Abstract interfaces for SQLStorageBase / SQLDialect