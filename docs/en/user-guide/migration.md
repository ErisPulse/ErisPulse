# Upgrade Migration Guide

> [!TIP]
> **When to read this**: Before upgrading from an older version, check **breaking changes** that require code modifications or deployment verification. Read the corresponding section based on your current version; patch-level updates (x.y.Z) do not contain migration actions. The complete change log for each version is available in the [CHANGELOG](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md).

Versioning policy: **Patch versions (x.y.Z) do not include migration actions**; changes that require code modifications only appear in minor versions (x.Y.0). This page covers all breaking changes since version 2.0.0 (2.5.0 is the first production-ready version; migration from 1.x to 2.0.0 is documented in the 2.0.0 entry of the CHANGELOG).

## 2.0.x → 2.5.0 (Production Readiness Threshold)

- **⚠️ Strict mode enabled by default (Level 1)**: Old components that do not inherit from `BaseModule` / `BaseAdapter` are **rejected by default** during loading — exceptions are listed in `[ErisPulse.framework] strict_mode_exceptions.modules/adapters`, or use `strict_mode = 0` for relaxed mode.
- **First launch language confirmation interaction** (i18n with five languages): For automated deployment, pre-set the language using the `ERISPULSE_LANG` environment variable or configuration.
- Removed third-party dependencies containing C extensions (watchdog / packaging) — improved aarch64/ARM installation compatibility; deployments with locked requirements must also clean up these dependencies.

## Breaking Changes within the 2.5.x Series

- **CLI Alias Governance (2.5.5)**: The `ini` alias has been removed (too close to `install`), and `lr` has been changed to `lsr`—deployment scripts need to be synchronized.
- **Configuration Schema Refactoring (2.5.5)**: `BaseConfig` is now the general base class (`AdapterConfig` is an alias for compatibility), and `description` supports i18n format; **the `AccountConfig` alias has been removed**—custom configuration classes that inherit from it need to be reviewed.
- **Adapter Configuration Access Refactoring (2.5.5)**: `self.cfg` now reads in real time (`self.config` is an alias for compatibility), and the `_load_config()` / `_load_accounts()` caching methods have been removed—adapters that directly call these private methods need to switch to using `self.cfg`.
- **Component Discovery Enabled by Default (2.5.5)**: Newly installed components now default to `enabled=true`.

## 2.6.x

- **Removed the entire `Core/web_status/` package**, external mascot images, and the `/status-assets` static mount — deployments depending on these routes must migrate to Dashboard.

## 2.7.x

- **Port in use is a fatal error (2.7.1)**: Pre-check is performed synchronously before startup. `sdk.init()` returns `False`, and port conflicts are no longer silently deferred—deployment scripts must ensure the port is free.
- **Storage abstraction layer switched to asynchronous native contract (2.7.1)**: Asynchronous interfaces (`aget` / `aset` / `aExecute` / `atransaction`) become the native primary interfaces, while synchronous APIs are now a built-in compatibility layer—**existing synchronous calls require no modification**; **custom storage backends must migrate to the a-prefixed asynchronous methods** (synchronous abstract methods have been removed).
- **`Core/storage` refactored into a package**: SQLite is moved to `Core/storage/sqlite.py`, with MySQL / PostgreSQL pre-configured; `StorageManager` retains a compatibility alias.
- **2.8.0**: `sdk.reload_plugin` renamed to `sdk.reload_module`; independent event access system `Core/access.py` merged into `scope.identity` (configuration section `ErisPulse.access` removed, moved to `ErisPulse.scope.identity`); command ACL independent configuration section merged into `event.command.acl`; bind system scope APIs consolidated into dictionary-style configuration.
- **Removed**: Root/administrator forced confirmation in installation scripts.

## 2.8.0 → 2.9.0

There are no breaking changes (all are declarative increments); code that catches `RuntimeError` / `ValueError` from shadow modules must be adjusted according to the 2.9.0 notes.

## 2.9.0 → 2.10.0

- Configuration writing engine migration from tomlkit → **tomlclass** (zero-dependency, lossless TOML editing): Comments, key order, and blank lines are preserved with semantic integrity — external toolchains directly importing tomlkit to manipulate `config.toml` must be migrated.
- `uvicorn` locked to `>=0.35.0,<1.0` (capability detection via `Server._serve()`, falling back to public `serve()` if missing).
- **2.10.0**: `epsdk init` / `create` template removes the `enabled` configuration field — module enable/disable is now managed uniformly by the framework; `ConfigClass` only carries business parameters.

## 2.10.x → 2.11.0

- **`sdk.restart()` semantics upgraded** to component-level hot reload (module hot reload pipeline + adapter code-level reload); use `hard_restart()` for framework self-update and entry-point addition/removal scenarios
- Instance lock migrated to `.erispulse/config.lock`—deployment with cleanup script for old lock (original `config/config.lock`) needs to synchronize the path

## 2.11.0 → 2.11.2

- **The adapter for `AccountConfigClass` no longer automatically generates the `default` account template**—Accounts are now created by users via the Dashboard account wizard. Deployments that rely on having a "default" account at startup must explicitly add it.
- `reload()` / `restart()` behavior tightened (mutual exclusion and merging), transparent to normal usage

## 2.11.x → 2.12.0

**① Tightened semantics for storage write failures (breaking change):** Write operations that fail (write lock contention timeout / SQL error / constraint conflict) now raise `StorageOperationError` (`aset` / `adelete` / `aclear` / `set_multi` and their synchronous bridge `set` / `delete` on the same path), **no longer silently returning `False`**; rapid failure for connection-level unavailability (cooling period) remains unchanged (returning `False` / `None`).

```python
# Old: rely on return value to determine write failure
if not storage.set("key", "value"):
    ...

# New: use try/except
try:
    storage.set("key", "value")
except StorageOperationError:
    ...
```

**② When `run_main_loop` has no available main loop:** now enqueues and returns `None`, no longer creates a temporary event loop—callers relying on temporary loop behavior should switch to `spawn_background` (scheduling back to the registered main loop).

**③ `epsdk restart` inside container:** now sends `SIGUSR1` to trigger an in-process soft restart, no longer terminates and relaunches—container deployments should verify restart policies (entire process restart is delegated to the container).

**④ Dependency upgrade:** `tomlclass >=0.4.0,<0.5`.

**⑤ Default behavior changes (2.12.0 / 2.12.1):**

- Automatic reconnection self-healing: automatically rebuilds cached connections when connection-level damage is detected (2.12.0)
- Component discovery is now enabled by default, and pre-checks for `reload()` / `restart()` are tightened (2.11 series)
- 2.12.1: Event idempotency deduplication key includes platform dimension, handler matching is centralized (handlers declaring `detail_type` conditions no longer propagate when the event lacks that dimension; native event paths remain permissive), session binding supports `detail_type:` prefix key

## 2.12.1 (Patch)

No migration actions. All changes are bug fixes and internal improvements. Default behavior change: **Log file output is now enabled by default** (`log_dir` defaults to `"logs"`, writing to `logs/erispulse.log`, with size/date rotation and bounded limits) — deployments that do not need file logging should set `[ErisPulse.logger] log_dir = ""`; explicitly disabling (switching from enabled to disabled) will automatically clean up the file handler, ensuring no residual writes remain.

---

## General Recommendations

- Read the CHANGELOG's "Notes" section before upgrading to a specific version; patch versions (x.y.Z) can be safely upgraded.
- Always use try/except for important storage writes (a good practice independent of semantics and version).
- Custom backends / deeply integrated components should pay attention to the "Changes/Removals" section of minor versions.

## Next Steps

- Details about a specific change's behavior → [Storage Backends](../advanced/storage-backends.md) · [Configuration File Reference](configuration.md)  
- Behavior not as expected after an upgrade → [FAQ](faq.md) · `ep doctor`  
- Complete details by version → [CHANGELOG](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)