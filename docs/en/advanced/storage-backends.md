# Storage Backends

> [!TIP]
> **When to read this**: When switching between sqlite / mysql / postgres or customizing the storage backend. Otherwise you can skip it — it does not affect the use of any other features.

ErisPulse ships with three async-native storage backends that can be switched with a single config change — **the API is completely identical, and switching requires zero code changes**:

| Backend | Driver | Installation | Highlights |
|------|------|------|------|
| SQLite (default) | aiosqlite | Out of the box | Zero config, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Ideal for existing MySQL infrastructure, multi-instance sharing |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transactional capability, JSONB ecosystem, high concurrency |

{!--< tips >!--}
1. Async is the native primary interface (`aget/aset/atransaction/aExecute`); the sync API is a compatibility layer
2. The framework's own config persistence, session inbox, conversation checkpoints, and so on all go through the same storage backend — switching the backend migrates everything at once
3. The `[mysql]` extra already includes `cryptography` — required for MySQL 8's default `caching_sha2_password` authentication; without it, connection pool initialization will fail
{!--< /tips >!--}

## Backend Selection

Configure it in `config/config.toml`:

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # SQLite only: use the package-global database at data/config.db
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
> Connection parameter changes require a framework restart to take effect (a restart reminder is logged on config hot-reload).
> Connection pools are created lazily per event loop; transient creation failures (network jitter / database restart windows) are retried automatically with exponential backoff.

## Connection Failure Behavior

Framework startup and operation **do not depend on database reachability** — MySQL / PostgreSQL connection failures will not crash the framework or prevent it from starting:

1. Transient pool creation failures are retried automatically with exponential backoff (3 times by default)
2. Retries exhausted → a WARNING is logged (including the reason and cooldown duration); the framework starts / keeps running as usual, with only storage operations temporarily unavailable
3. During the cooldown period (30 seconds by default), subsequent storage operations **fail fast** (no blocking, no slowdown of other features)
4. After the cooldown ends, a reconnect probe is attempted automatically — once the database recovers, storage recovers with it; no restart needed

Log example: `mysql connection pool creation failed permanently (3 retries exhausted), auto-reconnect in 30 seconds; storage operations will fail fast in the meantime, other framework features are unaffected`

## Failure Semantics (since 2.12)

| Scenario | Behavior |
|------|------|
| Operation execution failure (write lock timeout / SQL error / constraint violation) | **Raises `StorageOperationError`** (write paths: aset / adelete / aclear / set_multi and the same paths via the sync bridge) — no longer silently returns `False`; failures of important writes must be visible |
| Connection-level unreachability (fast-fail during cooldown) | Returns `False` / `None` (Rule 26 framework resilience semantics; `storage.unreachable` / `storage.recovered` events are also emitted) |
| Transaction begin timeout (>30s) | Raises `StorageOperationError` (`STORAGE_TXN_BEGIN_TIMEOUT_SECS`) |

Wrap important writes in try/except with compensation logic; keep only pure DB operations inside transaction blocks.

## Async-Native API

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

The sync API (`get/set/transaction/Table(...).Execute()`) remains available; internally it is bridged for execution through the `AsyncBridge` background event loop — **using the a-prefixed async methods everywhere is recommended**
(`aget` / `aset` / `adelete` / `atransaction` / `aExecute`): calling the sync interface inside an async handler blocks that event loop until the storage operation completes (under high-frequency calls this manifests as
handler timeouts and stalled event processing). The framework emits rate-limited warnings per call site (including the
`file:line (function name)` call site, with per-site cooldown to prevent spam) — upon receiving such a warning, migrate the corresponding call
to the a-prefixed async method. Two boundaries must be known:

- **Never call the sync interface from within the bridge thread**: the sync interface executes on the bridge thread; calling the
  sync interface again from there raises `RuntimeError` (re-entrancy protection to avoid self-deadlock)
- **Calls fail after the bridge target loop is closed**: do not call storage interfaces after `uninit()`

For the complete method mapping, see [SQL Query Builder](sql-builder.md).

## Dialect Behavior Differences

All dialect differences are encapsulated inside the framework; calling code does not need to be aware of them:

| Difference | SQLite | MySQL | PostgreSQL |
|------|------|------|------|
| Placeholders | `?` | `%s` (auto-translated) | `$1..$n` (auto-translated) |
| KV UPSERT | `INSERT OR REPLACE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` |
| KV value column type | `TEXT` | `LONGTEXT` | `TEXT` |
| Auto-increment primary key | Native support | `AUTO_INCREMENT` (auto-translated) | `SERIAL` (auto-translated) |

Table column types are always defined in SQLite style (e.g. `"INTEGER PRIMARY KEY AUTOINCREMENT"`,
`"TEXT NOT NULL"`, `"DOUBLE DEFAULT 0.0"`); the dialect automatically translates them into the equivalent form for the target backend.

## SQLite "database is locked" Troubleshooting

The framework's SQLite backend has built-in: **WAL journal mode** (reads and writes don't block each other) + **busy_timeout** (automatic waiting on write-lock contention, 5000ms by default, configurable — see below) + autocommit connections + shared connections held per event loop + **transaction `BEGIN IMMEDIATE`** (since 2.12 — the write lock is acquired at transaction start, eliminating `SQLITE_BUSY_SNAPSHOT` when deferred transactions upgrade from "read first, write later"; this busy is not retried and `busy_timeout` cannot mitigate it, and it was the in-framework root cause of intermittent locked errors under mixed high-frequency reads and writes).

With 2.12+ pure-framework usage (storage / ORM / interleaved writes across both paths), locked errors should no longer occur; if you still encounter them, troubleshoot in the following order:

| Scenario | Diagnosis | Remediation |
|------|------|------|
| Slow operations inside transactions | Slow work inside the `atransaction` block (external HTTP, heavy computation) holds the lock beyond busy_timeout — the framework warns about transactions holding the lock longer than 1s (`STORAGE_TXN_SLOW_WARN_SECS`) together with the opening location, so you can pinpoint it directly | Keep only DB operations inside transaction blocks; move slow work out |
| Sync API blocking the event loop | Massive event-handler timeouts + per-call-site "storage sync API called in async context" warnings | Migrate the call sites named in the warnings to a-prefixed async methods (`set` → `aset`, etc.) |
| Mixing in a second ORM | sqlmodel / SQLAlchemy / raw sqlite3 opening their own connections to write the same database file within the same process | **Use only one ORM per database file** (the built-in one is already async-native); don't mix during a transition |
| Multiple processes on the same file | Multiple instances / Dashboard / database tools opening the same sqlite file | Give each instance its own `config/` directory; open admin tools in read-only mode; for high-frequency write scenarios switch to mysql / postgres (one config change, zero code migration) |
| Older framework version | deferred transaction upgrade issues in `<2.12` | Upgrade the framework |

Lock mutual exclusion matrix (WAL mode): **reads vs. reads and reads vs. writes do not exclude each other**; mutual exclusion occurs only between **writes and writes** — the transaction-dedicated connection (`BEGIN IMMEDIATE` holds the lock until commit) and the write operations of the shared connections on each event loop compete for the same write lock. Long-running transactions are the prime suspect for write-wait timeouts.

> `busy_timeout` is configured via `ErisPulse.storage.sqlite.busy_timeout` (milliseconds, default 5000); increasing it extends the patience for write-lock queuing. Changes require a restart to take effect (the PRAGMA is applied when connections are established).

## Custom SQL Backend

Pure SQL backends can inherit from the shared base class; you only need to provide connection management and the dialect execution funnel:

```python
from ErisPulse.Core.Bases.sql_base import SQLDialect, SQLStorageBase

class MyDialect(SQLDialect):
    name = "mydb"
    # Overrides: placeholder translation / identifier quoting / UPSERT / type mapping ...

class MyStorage(SQLStorageBase):
    dialect = MyDialect()

    async def _create_loop_resource(self): ...   # connection pool
    async def _destroy_loop_resource(self, r): ...
    async def _acquire_resource_conn(self, r): ...
    async def _release_resource_conn(self, r, c): ...
    async def _open_txn_conn(self): ...
    async def _close_txn_conn(self, c): ...
    async def _exec_query_on(self, kind, sql, params, conn): ...  # execution funnel
```

Non-SQL backends (e.g. Redis), after inheriting `BaseStorage` and implementing the KV async interfaces,
can use `KVQueryBuilder` directly to gain chained table query capabilities (in-memory filtering, suitable for small-to-medium data volumes).

## Related Documentation

- [SQL Query Builder](sql-builder.md) - Chained query syntax and async API mapping
- [Core Modules API](../api-reference/core-modules.md) - Full Storage module API
- [Storage Base Class API](../api-reference/auto_api/ErisPulse/Core/Bases/sql_base.md) - SQLStorageBase / SQLDialect abstract interfaces