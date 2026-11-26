# Storage Backends

> [!TIP]
> **When to read this**: When switching between sqlite / mysql / postgres or customizing the storage backend. Skip if not needed, it does not affect the use of other features.

ErisPulse provides three built-in asynchronous native storage backends, which can be switched with configuration in one click. **The API is completely consistent, and switching requires zero code changes**:

| Backend | Driver | Installation | Features |
|---------|--------|--------------|----------|
| SQLite (default) | aiosqlite | Ready to use out-of-the-box | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Suitable for existing MySQL infrastructure, shared across multiple instances |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction support, JSONB ecosystem, high concurrency |

{!--< tips >!--}
1. Asynchronous is the native main interface (`aget/aset/atransaction/aExecute`), synchronous API is a compatibility layer
2. The framework's own configuration persistence, session inbox, and conversation checkpoints all use the same storage backend—switching the backend means overall migration
3. `[mysql]` extra includes `cryptography`—MySQL 8's default `caching_sha2_password` authentication requires it, missing it will cause the connection pool initialization to fail
{!--< /tips >!--}

## Backend Selection

Configure in `config/config.toml`:

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: use the package's global database data/config.db
```

Environment variables are also supported for overriding (Docker / 12-factor):

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

Environment variable naming rule: configuration path in uppercase, dots replaced with underscores
(`ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`).

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
> After changing connection parameters, restart the framework to take effect (configuration hot updates will output a restart reminder log).
> Connection pools are created lazily by event loop; transient failures (network jitter / database restart window) during creation are automatically retried with exponential backoff.

## Connection Failure Behavior

The framework startup and operation **do not depend on database reachability**—MySQL / PostgreSQL connection failures do not cause framework crashes or inability to start:

1. Instant pool creation failures are automatically retried with exponential backoff (default 3 times)
2. After exhausting retries → record a WARNING (including reason and cooldown duration), the framework starts / continues running as usual, only storage operations are temporarily unavailable
3. During the cooldown period (default 30 seconds), subsequent storage operations **fail quickly** (do not block, do not slow down other features)
4. After cooldown, automatic reconnection attempts are made—storage resumes when the database recovers, no restart is required

Log example: `mysql connection pool creation ultimately failed (retried 3 times), automatic reconnection after 30 seconds; during this period storage operations will fail quickly, other framework features are unaffected`

## Process Exit

Processes that end without calling `sdk.uninit()` (standalone scripts, cleanup after interruption) automatically close storage during interpreter shutdown: first complete storage-dependent exit flush (inbox buffer), then stop all database connections, and finally stop the background bridging loop. SQLite connection threads do not automatically end with process exit; the framework completes these three steps before the interpreter recycles threads; `atexit` callbacks run after thread recycling, so do not access storage in them.

## Failure Semantics (from 2.12)

| Scenario | Behavior |
|----------|----------|
| Operation execution failure (write lock timeout / SQL error / constraint conflict) | **Raise `StorageOperationError`** (write path: `aset / adelete / aclear / set_multi` and synchronous bridge same path) — no longer silently return `False`, important write failures must be visible |
| Connection-level unreachability (fast failure during cooldown) | Return `False` / `None` (fast failure during connection-level unreachability, accompanied by `storage.unreachable` / `storage.recovered` events) |
| Transaction begin timeout (>30s) | Raise `StorageOperationError` (`STORAGE_TXN_BEGIN_TIMEOUT_SECS`) |

Wrap important writes in try/except and handle compensations; put only pure DB operations inside transaction blocks.

## Asynchronous Native API

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

## Synchronous Methods (Use with Caution)

Each asynchronous method with an `a` prefix has a corresponding synchronous form (`aget`→`get`, `aset`→`set`, `atransaction`→`transaction`, `aExecute`→`Execute`), executed internally via a background event loop bridge—**they block the calling thread**:

- **Calling them in asynchronous handlers blocks the entire event loop** until the storage operation completes: frequent calls result in handler timeouts, event processing stalling, web lag, and may chain-trigger `database is locked` (write wait timeout). The framework outputs rate-limited warnings (with `file:line number (function name)`) for each call point; receive a warning and migrate the corresponding call to an `a`-prefixed asynchronous method
- In development, enable `ErisPulse.framework.strict.sync_in_async = true`: synchronous calls are no longer allowed, directly raising `StrictModeError` (with call point and migration guidance), exposing issues immediately rather than relying on lag after deployment
- In runtime, for mitigation: the default maximum wait time for bridge in asynchronous contexts is 10s (`ErisPulse.framework.sync_in_async_bridge_wait`), after which the caller receives `None` as a fail-soft return; queued write operations are **not discarded** (still completed in the background, with failures reported as WARNING), and synchronous transaction commits / connection releases are completed as well; a transaction begin timeout raises `StorageOperationError`—but this is a fallback, not a permission

**Please ensure you know what you are doing, otherwise do not use synchronous forms.** In pure synchronous threads (no event loop), calls are unrestricted and are legitimate scenarios (such as synchronous entry scripts, bridging waits for transaction commits).

`asyncio.to_thread` / thread pool execution of synchronous drivers is similar, and can be effective in specific scenarios: **when the backend supports true concurrent connections** (PostgreSQL / MySQL—each thread has an independent connection, server-side MVCC concurrency), moving synchronous drivers out of the event loop is a reasonable approach. However, do **not** do this under SQLite—thread connections compete for the same write lock with the framework's aiosqlite connections, expanding the race surface and potentially causing write failures or even data loss.

**MySQL / PostgreSQL backends do not require manual to_thread**: the framework automatically routes synchronous calls within asynchronous contexts to a bounded thread pool for true-concurrency backends (`_SUPPORTS_THREAD_BRIDGE` capability), with each worker having an independent event loop, not queuing each other; the main loop block duration equals the operation's own duration; the waiting limit and fail-soft semantics are the same as above. SQLite backends maintain a single bridging loop serially (write lock model required). Custom backends declare this capability based on the write lock model (single write engine defaults to False).

Complete method comparison is available in [SQL Query Builder](sql-builder.md).

## Dialect Behavior Differences

All dialect differences are internally consolidated, and calling code does not need to be aware:

| Difference | SQLite | MySQL | PostgreSQL |
|------------|--------|-------|------------|
| Placeholder | `?` | `%s` (automatically translated) | `$1..$n` (automatically translated) |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV value column type | `TEXT` | `LONGTEXT` | `TEXT` |
| Auto-increment primary key | Native support | `AUTO_INCREMENT` (automatically translated) | `SERIAL` (automatically translated) |

Table column types are uniformly defined in SQLite style (e.g., `"INTEGER PRIMARY KEY AUTOINCREMENT"`, `"TEXT NOT NULL"`, `"DOUBLE DEFAULT 0.0"`), and dialects automatically translate them into equivalent expressions for the target backend.

## SQLite "database is locked" Troubleshooting

The framework's SQLite backend has built-in features: **WAL log mode** (read and write are not mutually exclusive) + **busy_timeout** (automatic wait for write lock contention, default 5000ms, see configuration item below) + autocommit connection + multiple event loops each holding shared connections + **transaction `BEGIN IMMEDIATE`** (from 2.12 onwards—acquires a write lock at transaction start, eliminating deferred transactions' "read before write" upgrade causing `SQLITE_BUSY_SNAPSHOT`, which does not retry and cannot be mitigated by `busy_timeout`, and is the root cause of intermittent locked issues in high-frequency read-write mixed scenarios within the framework).

In 2.12+ pure framework usage (storage / ORM / mixed dual paths interleaved writes), locked issues should no longer occur; if still encountered, follow the troubleshooting steps below:

| Scenario | Diagnosis | Resolution |
|----------|-----------|------------|
| Slow operations within transaction | `atransaction` block contains slow operations (external HTTP, large computations), holding the lock beyond `busy_timeout`—the framework outputs warnings for transactions holding locks beyond 1s (`STORAGE_TXN_SLOW_WARN_SECS`) and includes the opening location, which can be directly located | Move slow operations outside the transaction block |
| Synchronous API blocking event loop | Frequent event handler timeouts + warnings at call points for "storage synchronous API called in asynchronous context" | Migrate the call points indicated by warnings to `a`-prefixed asynchronous methods (`set` → `aset`, etc.) |
| Mixing a second ORM | Multiple ORMs (sqlmodel / SQLAlchemy / raw sqlite3) open connections to the same database file within the same process | **Use only one ORM for the same database file** (the built-in is already asynchronous native), do not mix them |
| Multiple processes accessing the same file | Multiple instances / Dashboard / database tools open the same sqlite file | Each instance uses a separate `config/` directory; management tools open in read-only mode; switch to mysql / postgres for high-frequency writes (configuration change with zero code migration) |
| Old framework version | Deferred transaction upgrade issues from `<2.12` | Upgrade the framework |

Lock mutual exclusion matrix (WAL mode): **Read and read, read and write are not mutually exclusive**; mutual exclusion only occurs between **write and write**—transaction-specific connections (`BEGIN IMMEDIATE` holding locks until commit) and shared connections from each event loop compete for the same write lock; long transactions are the primary suspect for write wait timeouts.

> `busy_timeout` is configured via `ErisPulse.storage.sqlite.busy_timeout` (milliseconds, default 5000); increasing it extends the patience for write lock queuing, changes require a restart to take effect (PRAGMA applied at connection establishment).

## Backend Registration (Pluggable)

Backends are discovered through a registration table, not limited to the built-in three:

```python
from ErisPulse.Core.storage import get_registered_backends

print(get_registered_backends())   # ['mysql', 'postgres', 'sqlite', ... external registered backends]
```

| Item / Item | Description / Description |
|-------------|---------------------------|
| Register / Register | External packages call `register_storage_backend(name, cls)` upon module import; `ErisPulse.storage.backend` enables it by filling the registered name |
| Discovery / Discovery | External packages declare entry-points group `erispulse.storage.backends` in `pyproject.toml`, and the framework scans and loads them before creating storage instances |
| Driver Declaration / Driver | Dialects declare the driver import name via `driver_module` (empty = zero dependency built-in driver). **Driver dependencies are declared by the backend package's `pyproject.toml` and installed with the package**—the framework does not install any dependencies at runtime, and missing dependencies directly raise errors with installation instructions |
| Capability Declaration / Capability | Backends declare capabilities via class attributes, and the framework routes based on them: `_SUPPORTS_THREAD_BRIDGE` (true-concurrency backends, sync-in-async goes through a bounded thread pool), `_SUPPORTS_CONN_ROUTING` (synchronous transaction connection routing) |
| Unregistered Backend | Raises an error and lists the currently available backends |

Built-in backends also follow this registration table (`sqlite` / `mysql` / `postgres` self-register upon import), and external backends have the same status as built-in ones.

## Custom SQL Backend

A pure SQL backend can inherit a shared base class, only requiring connection management and dialect execution funnel:

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

Non-SQL backends (such as Redis) can inherit `BaseStorage` to implement asynchronous KV interfaces, and then directly use `KVQueryBuilder` to obtain chainable table query capabilities (in-memory filtering, suitable for small to medium datasets).

## Related Documentation

- [SQL Query Builder](sql-builder.md) - Chainable query syntax and asynchronous API comparison
- [Core Module API](../api-reference/core-modules.md) - Complete API for Storage module
- [Storage Base Class API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - Abstract interfaces for SQLStorageBase / SQLDialect