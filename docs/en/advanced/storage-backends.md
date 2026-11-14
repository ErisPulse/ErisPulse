# Storage Backends

> [!TIP]
> **When to read this**: When switching between sqlite / mysql / postgres or custom storage backends. Skip if not needed, as it does not affect the use of other features.

ErisPulse ships with three native asynchronous storage backends, which can be switched with a single configuration change, **with a completely consistent API and zero code changes required**:

| Backend | Driver | Installation | Features |
|------|------|------|------|
| SQLite (default) | aiosqlite | Ready to use out of the box | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Suitable for existing MySQL infrastructure, shared across multiple instances |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction support, JSONB ecosystem, high concurrency |

{!--< tips >!--}
1. Asynchronous operations are the native main interface (`aget/aset/atransaction/aExecute`), while synchronous APIs serve as a compatibility layer.
2. All framework-level data persistence, session mailboxes, and conversation checkpoints use the same storage backend—switching the backend results in a full migration.
3. The `[mysql]` extra includes `cryptography`—required for MySQL 8's default `caching_sha2_password` authentication; failure to install will cause the connection pool initialization to fail.
{!--< /tips >!--}

## Backend Selection

Configure in `config/config.toml`:

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: use the global database data/config.db within the package
```

Environment variables are also supported for overriding (useful for Docker / 12-factor applications):

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

Environment variable naming convention: configuration paths are uppercase, and dots are replaced with underscores (`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`).

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
> Changes to connection parameters require a framework restart to take effect (hot configuration updates will log a restart reminder). Connection pools are created lazily per event loop, and transient failures (network fluctuations / database restart windows) are automatically retried with exponential backoff.

## Connection Failure Behavior

The framework does not depend on database reachability during startup or runtime—MySQL / PostgreSQL connection failures will not cause the framework to crash or fail to start:

1. Transient pool creation failures automatically retry with exponential backoff (default: 3 retries).
2. If retries are exhausted, a WARNING is logged (including the reason and cooldown duration), and the framework starts / continues running normally, with storage operations temporarily unavailable.
3. During the cooldown period (default: 30 seconds), subsequent storage operations fail quickly (without blocking or slowing down other features).
4. After cooldown ends, an automatic reconnection attempt is made—once the database is restored, storage operations resume without requiring a restart.

Log example: `mysql connection pool creation failed after 3 retries, automatic reconnection in 30 seconds; storage operations will fail quickly during this period, but other framework functions are unaffected`

## Failure Semantics (since 2.12)

| Scenario | Behavior |
|------|------|
| Operation execution failure (write lock timeout / SQL error / constraint violation) | **Raises `StorageOperationError`** (write paths: `aset / adelete / aclear / set_multi` and corresponding synchronous paths) — no longer silently returns `False`, important write failures must be visible |
| Connection-level unreachability (during cooldown period) | Returns `False` / `None` (Rule 26 framework resilience semantics, with `storage.unreachable` / `storage.recovered` events) |
| Transaction begin timeout (>30s) | Raises `StorageOperationError` (via `STORAGE_TXN_BEGIN_TIMEOUT_SECS`) |

Wrap important writes in try/except blocks and implement compensations; only pure DB operations should be placed inside transaction blocks.

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

Synchronous APIs (`get/set/transaction/Table(...).Execute()`) remain available, internally executed via an `AsyncBridge` background event loop—calling them from asynchronous handlers will briefly block the event loop, and a one-time warning is output on the first call ("suggest using a-prefixed asynchronous methods instead"). It is recommended to use a-prefixed asynchronous methods. Two boundaries must be known:

- **Do not call synchronous interfaces within the bridged thread**: Synchronous interfaces are executed in the bridged thread, and calling them again will raise a `RuntimeError` (to prevent reentrancy and avoid self-deadlock).
- **Calling after the bridged target loop is closed will fail**: After `uninit()`, do not call storage interfaces again.

For a complete method comparison, see [SQL Query Builder](sql-builder.md).

## Dialect Behavior Differences

All dialect differences are internalized within the framework, so calling code does not need to be aware:

| Difference | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| Placeholder | `?` | `%s` (automatically translated) | `$1..$n` (automatically translated) |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV value column type | `TEXT` | `LONGTEXT` | `TEXT` |
| Auto-increment primary key | Native support | `AUTO_INCREMENT` (automatically translated) | `SERIAL` (automatically translated) |

Table column types are uniformly defined using SQLite-style definitions (e.g., `"INTEGER PRIMARY KEY AUTOINCREMENT"`, `"TEXT NOT NULL"`, `"DOUBLE DEFAULT 0.0"`), which are automatically translated to equivalent syntax for the target backend.

## SQLite "database is locked" Troubleshooting

The framework's SQLite backend has built-in optimizations: **WAL journal mode** (read/write not mutually exclusive) + **busy_timeout 5000ms** (automatic waiting for write lock contention) + autocommit connections + multiple event loops each holding shared connections + **transaction `BEGIN IMMEDIATE`** (introduced in 2.12—acquires a write lock at transaction start, eliminating deferred transactions' "read then write" upgrade issues that cause `SQLITE_BUSY_SNAPSHOT`, which does not retry and cannot be resolved by `busy_timeout`, this is the root cause of intermittent locked issues in high-frequency read/write mixed scenarios).

In 2.12+, pure framework usage (storage / ORM / mixed dual paths interleaved writes) should no longer encounter locked issues; if you still encounter them, follow the troubleshooting steps below:

| Scenario | Diagnosis | Resolution |
|------|------|------|
| Slow operations within transactions | `atransaction` block contains slow operations (external HTTP, large computations), holding locks beyond busy_timeout | Only perform database operations within transaction blocks; move slow operations outside |
| Mixing a second ORM | Multiple ORMs (sqlmodel / SQLAlchemy / raw sqlite3) open connections to the same database file in the same process | **Use only one ORM for the same database file** (the built-in one is already asynchronous native), avoid mixing ORMs |
| Multiple processes accessing the same file | Multiple instances / Dashboard / database tools open the same SQLite file | Use separate `config/` directories for each instance; open management tools in read-only mode; switch to mysql / postgres for high-frequency write scenarios (configuration change only, zero code migration) |
| Old framework version | Deferred transaction upgrade issues from `<2.12` | Upgrade the framework |

> `busy_timeout` is currently a class constant `_SQLITE_BUSY_TIMEOUT_MS = 5000` (in `Core/storage/sqlite.py`); adjusting this requires source-level modification and is not exposed as a runtime configuration.

## Custom SQL Backend

A pure SQL backend can inherit from a shared base class, providing only connection management and dialect execution funnel:

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

For non-SQL backends (e.g., Redis), inherit `BaseStorage` to implement asynchronous KV interfaces, then use `KVQueryBuilder` to gain chainable table query capabilities (in-memory filtering, suitable for small to medium datasets).

## Related Documentation

- [SQL Query Builder](sql-builder.md) - Chainable query syntax and asynchronous API mapping
- [Core Module API](../api-reference/core-modules.md) - Complete API for the Storage module
- [Storage Base Class API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - Abstract interfaces for SQLStorageBase / SQLDialect