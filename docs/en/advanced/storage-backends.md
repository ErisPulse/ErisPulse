# Storage Backends

> [!TIP]
> **When to read this**: When switching to sqlite / mysql / postgres or a custom storage backend. Skip it otherwise—this does not affect the use of any other features.


ErisPulse ships with three natively asynchronous storage backends that can be switched with a single configuration change—**identical APIs, zero code changes when switching**:

| Backend | Driver | Installation | Highlights |
|------|------|------|------|
| SQLite (default) | aiosqlite | Works out of the box | Zero config, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Ideal for existing MySQL infrastructure, shared across multiple instances |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction support, JSONB ecosystem, high concurrency |

{!--< tips >!--}
1. The async interface is the native primary interface (`aget/aset/atransaction/aExecute`); the sync API is a compatibility layer
2. The framework's own config persistence, session inbox, conversation checkpoints, and more all go through the same storage backend—switching the backend migrates everything at once
3. The `[mysql]` extra already includes `cryptography`—required for MySQL 8's default `caching_sha2_password` authentication; without it, connection pool initialization fails
{!--< /tips >!--}

## Backend Selection

Configure in `config/config.toml`:

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # SQLite only: use the package-level global database data/config.db
```

Environment variable overrides are also supported (Docker / 12-factor):

```bash
ERISPULSE_STORAGE_BACKEND=postgres
ERISPULSE_STORAGE_POSTGRES_HOST=db.example.com
ERISPULSE_STORAGE_POSTGRES_PASSWORD=secret
```

Environment variable naming rule: uppercase the config path and replace dots with underscores
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
> Connection parameter changes require a framework restart to take effect (a restart reminder is logged during hot config reloads).
> Connection pools are created lazily per event loop; transient creation failures (network jitter / database restart windows) are automatically retried with exponential backoff.

## Connection Failure Behavior

Framework startup and operation **do not depend on database availability**—MySQL / PostgreSQL connection failures will not crash the framework or prevent it from starting:

1. Transient pool creation failures are automatically retried with exponential backoff (3 attempts by default)
2. Retries exhausted → a WARNING is logged (including the cause and cooldown duration); the framework starts / keeps running as usual, with only storage operations temporarily unavailable
3. Subsequent storage operations during the cooldown period (30 seconds by default) **fail fast** (no blocking, no slowdown of other features)
4. When the cooldown ends, an automatic reconnection attempt is made—once the database recovers, storage recovers along with it; no restart required

Log example: `mysql connection pool creation ultimately failed (retried 3 times), auto-reconnecting in 30 seconds; storage operations will fail fast in the meantime, other framework features are unaffected`

## Failure Semantics (as of 2.12)

| Scenario | Behavior |
|------|------|
| Operation execution failure (write lock timeout / SQL error / constraint violation) | **Raises `StorageOperationError`** (write paths: aset / adelete / aclear / set_multi, and the sync bridge follows the same paths)—no longer silently returns `False`; failures of important writes must be visible |
| Connection-level unreachability (fail fast during cooldown) | Returns `False` / `None` (fails fast when the connection is unreachable, accompanied by `storage.unreachable` / `storage.recovered` events) |
| Transaction begin timeout (>30s) | Raises `StorageOperationError` (`STORAGE_TXN_BEGIN_TIMEOUT_SECS`) |

Wrap important writes in try/except with compensation handling; keep transaction blocks to pure DB operations only.

## Native Async API

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

# Async transactions
async with sdk.storage.atransaction():
    await sdk.storage.aset("key1", "value1")
    await sdk.storage.Table("users").Insert({"name": "Alice"}).aExecute()
```

The sync API (`get/set/transaction/Table(...).Execute()`) remains available, executed internally via
the `AsyncBridge` background event loop—**we recommend using the `a`-prefixed async methods exclusively**
(`aget` / `aset` / `adelete` / `atransaction` / `aExecute`): calling sync interfaces inside
async handlers blocks that event loop until the storage operation completes (under high-frequency calls this manifests
as handler timeouts and stalled event processing). The framework emits a rate-limited warning per call site
(including the `file:line (function name)` call site, with per-site cooldown to prevent spamming)—upon receiving a warning, migrate the corresponding call
to the `a`-prefixed async method. Two boundaries must be understood:

- **Do not call sync interfaces from within the bridge thread**: sync interfaces execute on the bridge thread; calling a
  sync interface again there raises `RuntimeError` (re-entrancy protection to avoid self-deadlock)
- **Calls fail after the bridged target loop is closed**: do not call storage interfaces after `uninit()`

For the complete method mapping, see [SQL Query Builder](sql-builder.md).

## Dialect Behavior Differences

All dialect differences are absorbed inside the framework; calling code does not need to be aware of them:

| Difference | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| Placeholders | `?` | `%s` (auto-translated) | `$1..$n` (auto-translated) |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV value column type | `TEXT` | `LONGTEXT` | `TEXT` |
| Auto-increment primary key | Natively supported | `AUTO_INCREMENT` (auto-translated) | `SERIAL` (auto-translated) |

Table creation column types are uniformly specified in SQLite style (e.g. `"INTEGER PRIMARY KEY AUTOINCREMENT"`,
`"TEXT NOT NULL"`, `"DOUBLE DEFAULT 0.0"`), and the dialect automatically translates them into the equivalent syntax for the target backend.

## SQLite "database is locked" Troubleshooting

The framework's SQLite backend already has built in: **WAL journal mode** (reads and writes don't block each other) + **busy_timeout** (automatic waiting on write lock contention, 5000ms by default, see config option below) + autocommit connections + per-event-loop shared connections + **transactions with `BEGIN IMMEDIATE`** (as of 2.12—acquires the write lock at transaction start, eliminating the `SQLITE_BUSY_SNAPSHOT` that occurs when a deferred transaction upgrades from "read first, write later"; this busy error is not retried and `busy_timeout` cannot mitigate it—it is the in-framework root cause of intermittent locked errors under mixed high-frequency reads and writes).

With 2.12+, pure framework usage (storage / ORM / mixed dual-path interleaved writes) should no longer produce locked errors; if you still encounter them, troubleshoot in the following order:

| Scenario | Diagnosis | Resolution |
|------|------|------|
| Slow operations within transactions | Slow work inside an `atransaction` block (external HTTP, heavy computation) holds the lock beyond busy_timeout—the framework emits a warning for transactions holding the lock longer than 1s (`STORAGE_TXN_SLOW_WARN_SECS`), including where the transaction began, allowing direct pinpointing | Keep transaction blocks to DB operations only; move slow operations out |
| Sync API blocking the event loop | Massive event handler timeouts + per-call-site "storage sync API called in an async context" warnings | Migrate the call sites flagged by the warnings to `a`-prefixed async methods (`set` → `aset`, etc.) |
| Mixing in a second ORM | sqlmodel / SQLAlchemy / raw sqlite3 in the same process opening their own connections to write the same database file | **Use only one ORM per database file** (the built-in one is natively async anyway); do not use a mixed setup as an interim measure |
| Multiple processes on the same file | Multiple instances / Dashboard / database tools opening the same sqlite file | Give each instance its own `config/` directory; open admin tools in read-only mode; for high-frequency write scenarios switch to mysql / postgres (a config change migrates with zero code changes) |
| Older framework version | Deferred transaction upgrade issues in `<2.12` | Upgrade the framework |

Lock mutual-exclusion matrix (WAL mode): **read-read and read-write do not exclude each other**; mutual exclusion only occurs between **write and write**—the transaction-dedicated connection (holding the lock from `BEGIN IMMEDIATE` until commit) competes with the write operations of each event loop's shared connection for the same write lock; long transactions are the prime suspect for write-wait timeouts.

> `busy_timeout` is configured via `ErisPulse.storage.sqlite.busy_timeout` (milliseconds, default 5000); increasing it extends how long write lock requests will wait in queue. Changes require a restart to take effect (the PRAGMA is applied when the connection is established).

## Custom SQL Backend

Pure SQL backends can inherit from the shared base class, needing only to provide connection management and the dialect execution funnel:

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

Non-SQL backends (such as Redis), after inheriting `BaseStorage` and implementing the KV async interfaces,
can directly use `KVQueryBuilder` to gain chained table query capabilities (in-memory filtering; suitable for small to medium data volumes).

## Related Documents

- [SQL Query Builder](sql-builder.md) - Chained query syntax and async API comparison
- [Core Modules API](../api-reference/core-modules.md) - Complete Storage module API
- [Storage Base Class API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect abstract interfaces