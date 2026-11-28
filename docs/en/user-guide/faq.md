# Frequently Asked Questions (FAQ)

> [!TIP]
> **When to read this**: When running into issues like "bot not responding / messages lost / database is locked / memory keeps increasing", first check here to match symptoms with causes and troubleshooting paths; if not found, refer to the corresponding topic documentation.

## Messages and Events

### The robot was mentioned in a group but did not respond?

Check in order:

1. **Multiple account deployment + `cross_account_policy = "drop"`**: The account copy that was mentioned receives priority (always allowed), but please confirm the identity of the target account—binding table/ownership determination uses both `self.user_id` and `self.account_id` (see [Cross-Account Duplicate Handling](../developer-guide/adapters/core-concepts.md)).
2. **`ignore_self`**: Events are filtered when the sender is the same as the receiving account (default enabled), confirm it is not your own echo.
3. **Handler conditions**: Whether the `detail_type` / text conditions registered in `on()` match the actual fields of the event; when the event lacks `detail_type`, handlers with declared conditions will no longer match.
4. **Module sleep/lazy loading**: Modules that have not triggered `activate_on` will not be loaded (see [Lazy Loading and Sleep](../advanced/lazy-loading.md)).

### Why did the robot reply twice to the same message?

- **Multiple accounts in the same group**: Each account receives a separate copy—enable `cross_account_policy` (content-level deduplication) or configure `session_accounts` (precise session ownership, see [Configuration](configuration.md)).
- **Multiple handlers with the same priority matching the same event**: Each handler executes independently in parallel, and only `mark_processed` will block subsequent handlers—check your handler registration conditions.

## Storage and Database

### Is the `database is locked` error recurring?

SQLite's locking mechanism only applies between **writes** (reads and writes are not mutually exclusive under WAL). When the error occurs frequently, check in the following order:

1. **Long-running transactions**: The framework outputs a warning for transactions holding locks for more than 1 second, including the location where the transaction started (`Transaction holding lock for x.xx s ...`) — move slow operations out of the transaction block based on the warning.
2. **Blocking synchronous API calls**: The warning `Synchronous storage API called in asynchronous context` indicates the call site; migrate it to an asynchronous method with the `a` prefix (`set` → `aset`) — handler timeouts have the same root cause and resolution, see steps 1 and 2 of this section.
3. **Be patient with write lock queuing**: Increase `ErisPulse.storage.sqlite.busy_timeout` (requires a restart to take effect).
4. If the issue persists → see the full troubleshooting matrix at [Storage Backends](../advanced/storage-backends.md)

### After upgrading, writing reports a `StorageOperationError`?

Starting from version 2.12.0, write failures **throw an exception instead of silently returning `False`** — refer to the [Upgrade Migration Guide](migration.md) and change the code to use try/except.

## Runtime

### What if event handlers frequently timeout / the bot intermittently stops responding?

Typical root cause: **Synchronous storage API calls within handlers** (each call blocks the event loop until completion). Characteristics: Rate-limiting alerts for "Synchronous storage API called in asynchronous context" and concentrated handler timeouts. Resolution: Migrate the calls to `aset` / `aget` / `aExecute` at the alert locations (see [Upgrade Migration Guide](migration.md)).

### What if memory usage keeps increasing?

1. Enable `ErisPulse.framework.memory_tracing = true` (enable for troubleshooting, disable in production) — `/metrics` and memory snapshots will output traced memory and top allocation points.
2. Observe snapshot trends in GC cycle logs (`log_snapshot`); the framework's proactive GC task automatically performs full memory collection based on memory growth.
3. After heavy use of hot reload, memory increases: Since version 2.12.1, the unload path will thaw and reclaim memory (the blind spot of `gc.freeze` in older versions has been fixed) — upgrade the framework.
4. Unbounded growth of module-specific containers is the module's responsibility — register ownership using the owner context (see [Ownership System](../advanced/ownership.md)).

### Why does the module "disappear" after hot reload?

During hot reload unloading, ownership tasks are canceled and ownership resources are reclaimed. If a module creates tasks/threads outside of `on_unload` and does not register ownership, the framework cannot handle it — use `self.spawn()` / `spawn_background(owner=...)` for unified creation (see [Ownership System](../advanced/ownership.md)).

## Configuration and Deployment

### Why didn't my configuration changes take effect?

- Keys that support hot reloading (such as `cross_account_policy`, `event_dedupe`, `memory_tracing`, and GC parameters) take effect immediately upon change.
- Keys that require a restart (such as `storage.use_global_db`, `storage.sqlite.busy_timeout`, router cors/security) will trigger a warning message when changed: "Process restart required for changes to take effect." When you see this warning, restart the process. Changes to `storage.backend` also require a restart (currently there is no warning message, remember to restart after making changes).
- If there is a syntax error during editing: the framework retains the last valid configuration and outputs a diagnostic message (it will not broadcast an empty configuration).

### Why did the container exit when running `epsdk restart` inside the container?

In the container (PID 1), `restart` has been changed to send `SIGUSR1` to trigger an internal soft restart of the process—please upgrade to version 2.12.0+ if you need this behavior. The container's restart policy should handle full process restarts.

## Next Steps

- Symptoms not matched → [Storage Backend Troubleshooting Matrix](../advanced/storage-backends.md) · [Performance Benchmarks and Tuning](../advanced/performance.md)  
- Suspected framework bug → [Bug Tracker](../bug-tracker.md) · Run `ep doctor` before submitting an issue  
- Version behavior differences check → [Upgrade Migration Guide](migration.md)