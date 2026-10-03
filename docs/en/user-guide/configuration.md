# Configuration File Guide
> This document introduces the framework's configuration file. For third-party module configuration, please refer to the module's documentation.

ErisPulse uses a TOML-formatted configuration file `config/config.toml` to manage project configurations.

## Configuration File Location

The configuration file is located in the `config/` folder at the project root:

```
project/
├── config/
│   └── config.toml
├── main.py
```

### Multi-Instance Warning and Lock File

When the framework starts, it creates a `.erispulse_config.lock` lock file in the `config/` directory and holds it until the process exits (used to detect multiple instances sharing the configuration directory). If the log shows a warning like "Detected that the configuration file may be in use by another ErisPulse instance," it means there are **two or more ErisPulse processes writing to the same configuration file** (typical scenario: multiple containers mounted the same host `config/` directory) — concurrent writes will overwrite each other. Please use separate configuration directories for each instance.

## Configuration Loading Error Handling

When loading `config.toml`, the framework distinguishes three error states and provides **actionable diagnostic information**, rather than silently falling back to default configurations:

| Error State | Trigger Condition | Framework Behavior |
|---------|---------|---------|
| File Missing | `config.toml` does not exist | Normal on first startup, silently uses empty configuration (no warning) |
| TOML Syntax Error | File exists but format is invalid (e.g., missing quotes, unclosed parentheses) | Outputs **line/column number and reason for error**, and **retains the last valid configuration to continue running** (this file modification is not effective) |
| Permission/Other Errors | No read permission, IO errors, etc. | Outputs **clear reason**, and **retains the last valid configuration to continue running** |

> **Note:** "Last valid configuration" ≠ Default configuration: When the file is damaged, the framework uses the **last successfully parsed configuration before this startup** (if the configuration file is modified and broken during runtime, the old value is retained), rather than resetting all configuration items to factory defaults. Do not assume that "the configuration has been reset" during troubleshooting.

For example, if you accidentally write the configuration as `port = 8000` (missing quotes around the string), the log will output something like:

```
[ERROR] [Config] Configuration file config/config.toml has a syntax error (line 3, column 1): ...
[WARNING] [Config] Failed to read configuration file. Continuing to run with the last valid configuration. This file modification is not effective — please fix and reload or restart.
```

This allows you to immediately locate the issue at the **default INFO level** without confusion about "why my modified configuration is not effective."

> **What if I modify the configuration file while the robot is running?** If you manually edit `config.toml` during robot operation and introduce a syntax error, the framework will output "Configuration file is damaged (syntax error, line X), unable to merge and write — please fix the configuration file and restart" when attempting to write next time, instead of an confusing "write failed." The configuration items to be written are retained and not lost.

## Comment Retention and Minimal Disk Write

**Comments and key order in config.toml are fully retained after framework write:** Whether through code `setConfig()`, CLI configuration wizard save, or adapter/module first-generation configuration template, the framework only modifies the involved keys. Your comments and sorted order are not erased or rearranged (based on tomlkit comment-retaining round-trip implementation).

The framework is restrained about what is written to disk:

- **Framework default configurations are not automatically written to disk:** `gc`, `scope`, `transcript`, etc., built-in defaults only reside in memory; config.toml only contains keys you explicitly set, keeping it minimal. Refer to `config/config.full.example` in the project for a complete list of configurable items. Copy and modify as needed (unconfigured items always default to built-in values, behavior unchanged).
- **`config.full.example` is automatically maintained:** Whether or not `epsdk init` is executed, as long as the framework is started (`epsdk run` / `main.py`), `config/config.full.example` will be automatically generated if missing. The file's first line is a framework-maintained marker; the generator content updates (e.g., new configuration items, newly installed components) when the startup refreshes once. If the first line is deleted or modified, it becomes manually managed, and the framework no longer overwrites.
- **Adapter/Module configuration templates:** First initialization saves a template with comments (field descriptions are comments); fields marked as `example` do not write to disk, only recorded in `config.full.example` for reference.

## Environment Variable Override

The framework supports **overriding** `ErisPulse.*` configuration items with environment variables (suitable for Docker/containerized/CI deployment, no need to modify `config.toml`).

Naming rule: Convert the dot-separated path `ErisPulse.<section>.<key>` to all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

Behavior description:

- **Highest priority:** Environment variables override "configuration file" and "default values," automatically converting to the original value type (`bool` / `int` / `float` / comma-separated `list` / string)
- **Non-persistent:** The override only takes effect during runtime and is not written back to `config.toml`
- **Supports hot update:** After modifying environment variables during runtime, combined with configuration listener reload, it takes effect

```bash
# Docker deployment example: No need to modify config.toml, directly override the port
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: `ErisPulse.server.port` and other framework configurations accessed via `get_server_config()` and similar APIs are affected by environment variable overrides.

### Module Configuration Environment Variable Binding (2.9.0+)

Modules' own declarative configurations (`ConfigClass`) support field-level environment variable binding—declare `env` in `field(metadata=...)`:

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API Key",
        "env": "MYMODULE_API_KEY",   # Environment variable binding
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

Behavior description:

- **Priority:** Environment variable > `config.toml` > declared default value (the same priority holds after configuration file hot update)
- **Type conversion:** Environment variable values are automatically converted according to field annotations—`str` as-is, `int` / `float` / `bool` (`true` / `1` / `yes` / `on`) automatically converted, `list` / `dict` parsed via JSON; if conversion fails, ignore the override (fall back to configuration file / default value) and output a warning
- **Declare once, apply everywhere:** The configuration read, hot update, and validation use the same pipeline; the configuration panel Schema will mark the `env` name, and `config.toml` template comments will also prompt available environment variables (the template does not write the actual value of environment variables to avoid leaks)
- **Fully compatible:** Fields without `env` declaration behave unchanged; directly instantiating ConfigClass (without framework configuration pipeline) is not affected by environment variables

```bash
# Docker deployment example: No need to modify config.toml, directly inject module key
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **Configuration class vs. model field: which to choose?** The configuration class manages "how the module operates" (behavior parameters, hot update), while ORM's `Field()` manages "what data the user generates" (database table, query). Both share the same constraint vocabulary and validator engine; the comparison table is available at
> [Data Model Layer · When to Use Which Declaration](../developer-guide/orm.md#when-to-use-which-declaration).

## Configuration Hot Update

Since version 2.7.0, the framework has provided **systematic support for configuration hot updates**. After external modification of `config.toml` (background watcher checks every 5 seconds), or code calls `setConfig()`, each component automatically responds:

| Component | Hot-updatable Configurations | Behavior |
|------|----------------|------|
| **Logger** | `logger.level` / `log_files` / `log_dir` (including segmentation parameters) / `memory_limit` / `format` / `exclude_levels` | Automatically reapplies (with change detection) |
| **Command System CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter Concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphore and rebuilds according to new value |
| **Active GC** | `framework.proactive_gc_*` | Configuration changes immediately restart GC tasks, supporting runtime adjustment/disable/re-enable |
| **Master System Master** | `master.users` | Each `is_master()` check reads in real-time, no restart needed |
| **Modules/Adapters Configurations** | Their respective configuration items | Triggers `on_config_update(old, new)` callback |

**Configurations requiring restart** (cannot be safely hot-switched, warning is output when changed "restart process to take effect"):

| Configuration | Reason |
|------|------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely hot-switched at runtime |
| `storage.use_global_db` | SQLite file handle is already opened at runtime, switching paths is unsafe |

> **What if editing and saving the configuration file fails midway?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, without broadcasting an empty configuration to each component (avoiding `on_config_update` receiving empty values and mistakenly reverting to default).

### Internal Breakdown of Hot Update Chain

"How do components know when the configuration is changed?" — Behind this is a detection → reload → broadcast chain:

```mermaid
flowchart TD
    A["External edit of config.toml"] --> B{"Who detects first?"}
    B -->|"Background watcher thread<br/>Polls mtime every 5 seconds"| C["_check_file_change determines change"]
    B -->|"Code reads configuration<br/>Cache exceeds 60 seconds"| C
    C --> D["_load_config re-parses TOML"]
    D --> E{"Parsing successful?"}
    E -->|"No (syntax error)"| F["Retains last valid configuration<br/>Does not broadcast, outputs diagnostic logs"]
    E -->|"Yes"| G["lifecycle.emit config.updated<br/>Carries old_config / new_config"]
    G --> H["Components listen and respond<br/>(logger / scope / command / GC ... )"]
```

**Two detection paths** (either one suffices, both can serve as fallback):

| Path | Mechanism | Trigger Timing |
|------|------|---------|
| Background watcher | Daemon thread `config-watcher` polls file `mtime` every **5 seconds** | Detects external file changes within at most 5 seconds |
| Lazy detection | Any `getConfig()` read checks file if cache exceeds **60 seconds** | Next time configuration is read |

> **The framework does not accidentally harm itself:** When `setConfig()` writes to disk, it records the "mtime written by itself," and the watcher excludes it when comparing, treating only **external edits** as changes.

**Two types of configuration change events:**

| Event | Trigger | Data | Typical Scenario |
|------|--------|------|---------|
| `config.set` | Code / Dashboard calls `setConfig()` | `{key, old_value, new_value}` | Single key write (template generation, status recording, runtime configuration change) |
| `config.updated` | External edit detected by watcher/lazy detection | `{old_config, new_config, config_file}` | Manual edit of `config.toml` |

> `setConfig()` defaults to **delayed write to disk after 5 seconds** (merges multiple writes); `immediate=True` writes immediately. The watcher detects external modifications and only updates the in-memory cache, **does not** write the external changes back to the file.

**List of automatic response components** (both event types are typically subscribed to, with consistent response content):

| Component | Listener | Response |
|------|------|------|
| Logger | `config.set` + `config.updated` | Reapplies level/file/directory segmentation/memory limit/format/exclude levels (with change detection, no change means no action) |
| Scope | `config.updated` | Rebuilds scope binding cache |
| Command System | `config.updated` | Refreshes prefix/case sensitivity/space prefix/must_at_bot parsing parameters, effective on next message |
| Adapter Concurrency | `config.set` + `config.updated` | Invalidates and rebuilds handler_max_concurrency semaphore |
| Active GC | `config.set` + `config.updated` | Immediately restarts GC background task |
| Adapter | Routes to `on_config_update` | Each adapter's `on_config_update(old, new)` callback |
| Module | Routes to `on_config_update` | Each module's `on_config_update(old, new)` callback |
| Storage | `config.updated` | `use_global_db` change **only warns** (requires restart) |
| Router | `config.updated` | `cors.*` / `security.*` change **only warns** (requires restart) |

## Configuration Reading and Deletion API

### getAllConfig: Full Configuration Snapshot

Use instead of directly reading private `_cache` (external reading of private attributes is not protected by version compatibility):

```python
config = sdk.config.getAllConfig()     # Deep copy snapshot, in-place modification does not affect framework state
config["ErisPulse"]["server"]["port"]
```

The view口径 is consistent with `getConfig`: Unwritten `setConfig` / `delete` are already reflected, and the content is strictly consistent with the delayed write to disk.

### delConfig: Delete Configuration Key

`setConfig(key, None)` only sets it to empty, the key remains in the file; `delConfig` removes the key from the file:

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # Delayed write
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # Write immediately
```

- Supports dot-separated paths; returns `False` if the key does not exist
- Writes to disk via comment-retaining path, file content and order remain unaffected
- Reuses `config.set` event broadcast (`new_value=None`): Existing listeners for adapters/modules zero change can perceive deletion

## Complete Configuration Example

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users supports two writing methods (choose one):
#   Global master (effective on all platforms): users = ["123456", "789012"]
#   Master per platform: users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = ""
log_rotation = "size"
log_max_size_mb = 10
log_backup_count = 5
log_rotation_when = "midnight"
memory_limit = 1000
exclude_levels = []

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
backend = "sqlite"
use_global_db = false

[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
must_at_bot = false

[ErisPulse.event.message]
ignore_self = true

[ErisPulse.i18n]
language = "auto"
```

## Server Configuration

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
# In container / no file mounting scenarios, PEM content can be inlined (prioritized over certfile/keyfile paths)
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| host | string | 0.0.0.0 | Listening address, 0.0.0.0 means all interfaces |
| port | integer | 8000 | Listening port number |
| auto_start | boolean | true | Whether to automatically start the routing server at `sdk.init()`. Set to `false` to skip the routing server startup (pure event/no WebUI scenario) |
| ssl_certfile | string | empty | SSL certificate file path |
| ssl_keyfile | string | empty | SSL private key file path |
| ssl_cert | string | empty | **Inlined PEM certificate content** (not a path). Used together with `ssl_key` to prioritize over `ssl_certfile`/`ssl_keyfile` paths; the framework temporarily writes to disk to build the SSL context and immediately deletes the temporary file |
| ssl_key | string | empty | **Inlined PEM private key content** (not a path), semantic same as above |

> **Port occupation is not a fatal error**: If the framework detects that the `port` is already occupied at startup, it will skip the routing server startup and issue a warning, **adapters and modules will still run normally** (only HTTP/WS/SSE routing and WebUI are unavailable). When troubleshooting "the robot can run but the WebUI cannot open," first confirm the port.

## Master System Configuration

The master system is used to identify the "framework master" account (such as Bot administrator). `master.users` supports two writing methods:

```toml
[ErisPulse.master]
# Writing method one: Global master (effective on all platforms)
users = ["123456", "789012"]

# Writing method two: Specify master per platform (dict)
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| users | array / object | empty | List of master accounts. `list` form is global master (effective on all platforms); `dict` form specifies per platform (key is platform name, value is the list of master account IDs for that platform) |

Code checks using `master.is_master(event)` or `master.is_master(platform, user_id)`, each call reads the configuration in real-time (supports hot update, no restart needed):

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("Hello Master")
```

### Decision Chain and Runtime Add/Delete

The master decision chain is **configuration master → runtime record → provider chain**:

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Add at runtime (default persistent; persist=False is only in-memory)
master.remove("yunhu", "123")                # Remove (default persistent)
master.list()                                # Aggregate: {"global": [...], "<platform>": [...]}
```

### Custom Identity Source (provider)

In addition to configuration, custom identity sources can be registered: `fn(platform, user_id) -> bool`, and if the built-in identity sources (configuration + runtime record) do not match, they are tried in sequence, and if any provider allows it, it is recognized as a master. Suitable for integrating adapter administrator interfaces, database roles, and other external identity systems.

Registration entry `master.provider` supports both decorator and function-style writing; unregistration is done through the unregistered function's `fn.unregister()`:

```python
from ErisPulse.Core import master

# Writing method one: Decorator (persistent identity source, recommended)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Writing method two: Function-style (register during module loading / unregister during module unloading)
fn = master.provider(admin_provider)
fn.unregister()
```

> Provider exceptions are caught and skipped, not blocking the identity determination chain. Binding instance methods cannot attach `unregister`, and scenarios requiring registration/unregistration pairing should use **module-level functions**.

### User Priority: Master Effect Scope Decided by User

The `master=True` of commands is only a **developer default**: Users can override or tighten or loosen it in `ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false` (see [Unified Event Override Configuration](#unified-event-override-configurationeventoverrides), user explicit configuration takes effect).

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # Explicit list of log files (mutually exclusive with log_dir, higher priority)
log_dir = ""                  # Log output directory (auto-created). If set, automatically segments and rotates logs into `erispulse.log` in the directory according to `log_rotation`; mutually exclusive with `log_files`, `log_files` has higher priority
log_rotation = "size"         # Segmentation method: "size" / "date" / "none"
log_max_size_mb = 10          # Single file size limit (MB) for size mode, rotates to `.1`/`.2` backup when exceeded
log_backup_count = 5          # Number of historical log files to retain
log_rotation_when = "midnight"  # Date mode rotation cycle: S/M/H/D/midnight
memory_limit = 1000
exclude_levels = ["EVENT"]
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| level | string | INFO | Log level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed framework internal debugging information) |
| format | string | rich | Log output format: `rich` (colored, default), `plain` (plain text without color, suitable for log collection/pipeline redirection), `json` (JSON structured, suitable for ELK, etc.) |
| log_files | array | empty | List of log output files (explicit paths, no segmentation) |
| log_dir | string | empty | Log output directory (auto-created). If set, writes to `erispulse.log` in the directory and automatically segments according to `log_rotation`; mutually exclusive with `log_files`, `log_files` has higher priority |
| log_rotation | string | size | Segmentation method: `size` (by size) / `date` (by time) / `none` (no segmentation) |
| log_max_size_mb | float | 10 | Single file size limit (MB) for size mode, rotates to `.1`/`.2` backup when exceeded |
| log_backup_count | integer | 5 | Number of historical log files to retain, oldest backups beyond this are automatically deleted |
| log_rotation_when | string | midnight | Date mode rotation cycle: `S`/`M`/`H`/`D`/`midnight` (default is midnight daily) |
| memory_limit | integer | 1000 | Number of log entries saved in memory |
| exclude_levels | array | empty | Levels to exclude. Logs of excluded levels are **completely discarded** (not written to memory, not pushed to Dashboard or other subscribers, not printed, not written to file). Supports hot update |

You can also dynamically switch in code:

```python
from ErisPulse.Core import logger

# Size-based segmentation: Single file 10MB, retain 5 copies
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# Time-based segmentation: Rotate daily at midnight, retain 7 copies
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` and related segmentation configurations require ErisPulse **2.8.0+**.

> **Privacy Protection**: Message sending and receiving content is recorded at the **EVENT level** (value 21). Setting `exclude_levels = ["EVENT"]` allows the backend (such as the Dashboard log panel) to not see message content from groups/private chats, while not affecting logs of other levels.

> [!NOTE]
> This `exclude_levels` feature requires ErisPulse **2.8.0+**.

## Framework Configuration

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | Whether to enable lazy loading of modules |
| uninit_timeout | integer | 30 | Graceful shutdown timeout (seconds), forcibly terminates if exceeded. 0 means no timeout set |
| strict_mode | integer | 0 | Strict mode level, see "Strict Mode" below |
| handler_max_concurrency | integer | 64 | Maximum number of concurrent Task for event handlers, increasing allows higher throughput but increases memory usage |
| offline_bot_expiry | integer | 3600 | Automatic expiration time (seconds) for offline Bot records, 0 means no expiration |

### Active GC Configuration

After SDK initialization, an active GC background task is started, periodically performing Python GC and internal resource recycling (cleaning offline Bots, etc.). All parameters support hot updates, and tasks are immediately restarted upon changes.

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | Recycling interval (seconds), supports decimals. 0 means disable active GC |
| proactive_gc_generation | integer | 0 | Regular round recycling generation (0/1/2, clamped to 0..2). Note that `gc.collect(2)` is equivalent to full recycling, default 0 keeps it lightweight; deep recycling is triggered periodically by `proactive_gc_full_every` |
| proactive_gc_full_every | integer | 20 | Do a full recycling every N rounds, 0 means disable periodic full recycling. Full recycling is subject to the `proactive_gc_memory_growth_mb` threshold |
| proactive_gc_memory_growth_mb | integer | 32 | Full recycling memory growth threshold (MB): Compared with the memory baseline after the last full recycling (prioritizing tracemalloc, then RSS), full recycling is only performed when the growth reaches this value. 0 means no threshold set |
| proactive_gc_idle_only | boolean | false | When enabled, skip Python GC during event peaks (pending handlers exist) to avoid pauses and message processing competition; internal resource recycling is unaffected |
| proactive_gc_gen0_min | integer | 500 | Minimum garbage amount for regular round recycling: `gc.get_count()[0]` below this value directly skips (empty rounds nearly zero overhead). 0 means always recycle |

> **2.7.1 Change**: The default `proactive_gc_generation` is adjusted from `2` to `0`, and `proactive_gc_full_every` from `0` to `20`. Previously `generation=2` meant a full heavy recycling every round; the new default maintains recycling coverage while significantly reducing idle round overhead. Explicitly configured old values still behave as worded.

### Strict Mode

Strict mode controls the handling strategy for non-compliant or failed loading of modules/adapters during the loading phase. Modern modules/adapters should inherit corresponding base classes (`BaseModule`/`BaseAdapter`), components that do not inherit base classes affect the framework's context system and fallback cleanup, potentially causing resource leaks.

> **2.5.2 Change**: The default level is adjusted from `1` (skip) to `0` (lenient), to reduce loading issues for new users on initial use. Components that do not inherit base classes will be warned and attempted to load, rather than directly rejected. To restore old behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (Default) | Non-compliant only warns, components that do not inherit base classes will still be attempted to load (compatible with old components) |
| 1 | Strict-Skip | Rejects components that do not inherit base classes and skips them, other normal startup |
| 2 | Strict-Fatal | Collects all violations and reports them collectively, then terminates the entire startup |

In all levels, "loading/registration/initialization phase errors" such as component self-crashes are always skipped; the difference lies in:

- **0 → 1**: The only behavioral change is that "not inheriting base class" changes from "still loading" to "skipping."
- **1 → 2**: All violations (not inheriting base class, loading failure, registration failure, initialization failure, etc.) are upgraded to fatal, collected at the startup checkpoint and reported as a violation list before termination.

#### Exemption List

If certain components cannot be migrated temporarily (e.g., dependencies on old modules), they can be added to the exemption list. Components listed will be treated leniently even if non-compliant, and continue to be loaded:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly indicate how to restore loading (add to the exemption list or lower the level).

## Storage Configuration

Since version 2.8.0, the storage engine supports three asynchronous backends, with **identical APIs and one-click configuration switching**:

| Backend | Driver | Installation | Characteristics |
|------|------|------|------|
| SQLite (Default) | aiosqlite | Ready-to-use | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Existing MySQL infrastructure, multi-instance sharing |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction capability, high concurrency |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: Use the package's global database data/config.db

[ErisPulse.storage.mysql]      # Only effective when backend = "mysql"
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # Only effective when backend = "postgres"
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
# pool_min = 1
# pool_max = 10
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| backend | string | sqlite | Storage backend: `sqlite` / `mysql` / `postgres`, switching requires zero code changes |
| use_global_db | boolean | false | Only for SQLite: Whether to use the package's global database instead of the project's independent database |
| storage.mysql.* | table | See above | MySQL connection parameters (host / port / user / password / database / charset / pool) |
| storage.postgres.* | table | See above | PostgreSQL connection parameters (host / port / user / password / database / pool) |

Environment variables are also supported for overriding (Docker / 12-factor): `ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`.

> [!TIP]
> - Connection parameter changes require a framework restart to take effect; transient connection pool creation failures will automatically retry with exponential backoff
> - Use a verification script before switching backends: `python tests/devs/test_storage_backend_verify.py --backend mysql`
> - Transaction / dialect differences / custom backends, etc., are fully described in [Storage Backends](../advanced/storage-backends.md)

## Event Configuration

### Command Configuration

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| prefix | string | / | Command prefix |
| case_sensitive | boolean | true | Whether to distinguish case (whether `/Help` and `/help` are different commands) |
| allow_space_prefix | boolean | false | Whether to allow spaces as prefix |
| must_at_bot | boolean | false | Whether to require mentioning the bot to trigger the command (private chats are not restricted) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| ignore_self | boolean | true | Whether to ignore the bot's own messages |

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| language | string | auto | The display language for the framework's built-in text. Set to `auto` for automatic system language detection, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

## Module Configuration

Each module can define its own configuration in the configuration file:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

In the module, read and write the configuration:

```python
from ErisPulse import sdk

# Read configuration
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# Write configuration at runtime (delayed save)
sdk.config.setConfig("MyModule.timeout", 60)

# Immediately save to file
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` defaults to delayed write (about every 5 seconds batch save to file), set `immediate=True` to immediately persist. Configuration changes trigger the `config.set` lifecycle event.

## Scope Configuration (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope declares "the **scope of effect**"—which modules are available in what platform/Bot/session (① module level), whether events are received for what user/group/Bot/adapter (② identity level), and what outbound calls a module can initiate (③ outbound level):

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit deny strict mode; does not affect outbound level)
cache_size = 1024           # LRU cache size

# ① Module level (priority: session > Bot > platform; entries support exact / glob / re: regex)
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# Sub-level binding with merge = true merges entries with lower priority (default overall overwrite)
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② Identity level (priority: user > session > Bot > adapter; only allow or deny per level)
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # Discard all events on this platform at the entry
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ③ Outbound level (default all allowed; rules are inline tables, entries support exact / glob / re: regex)
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # Deny all sending
api = { allow = ["get_*"] }               # Allow only standard query APIs
request = { deny = true }                 # Deny request handling
```

| Configuration Item | Type | Description |
|---------|------|------|
| `scope.default_allow` | boolean | Global fallback: Allow or deny for modules/identity not matched by rules (true) |
| `scope.cache_size` | integer | LRU cache size (default 1024) |
| `scope.platforms / bots / sessions` | table | ① Module three-level binding: `{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② Identity four-level binding: `{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ Outbound rules: `{allow=[...], deny=true|[...]}` (actions are send / api / request) |

> For detailed explanations and runtime APIs (dimensional `sdk.scope.set_module()` / `set_identity()` / `set_action()`, determination `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`, and dictionary-style fallback `get()` / `set()` / `delete()`), see [Scope (scope)](../advanced/scope.md).

## Unified Event Override Configuration (event.overrides)

Unified override system: Overriding behavior of any module handler by **event type** without modifying module code. OneBot12 standard types (meta / message / notice / request) and extended types (command) each have dedicated overridable parameters:

```toml
[ErisPulse.event.overrides]

# message: Text trigger conditions (AND with code-side conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta: detail_type whitelist (entries support exact / glob / re: regex)
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command (extended type): Override command parameters (user priority; disable via acl deny)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # Override to only allow framework master (false to relax developer's master restriction)
hidden = true               # Hide in help list
aliases = ["rs"]            # Effective alias

# acl (command-specific): User allow/deny lists for commands (command names support glob / re: regex, exact keys take precedence)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL fallback: Allow (true) / strictly deny (false) commands without ACL configuration
acl_default_allow = true
```

| Configuration Item | Type | Description |
|---------|------|------|
| `event.overrides.message.<module>` | table | Text condition: `{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | Module-level parameter override (scalar values like `hidden = true`) |
| `event.overrides.command.<module>.<command>` | table | Command-level override (command-level takes precedence) |
| `event.overrides.acl.<command name>` | table | User allow/deny lists: `{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL fallback: Allow (true) / strictly deny (false) commands without ACL configuration |

> Runtime API (after `from ErisPulse.Core.Event import overrides`, call `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` by type sub-namespace, or access via `sdk.Event.overrides`)
> See [Event Handling Introduction · Event Override](../getting-started/event-handling.md#event-override-does-not-modify-module-code-override-behavior-of-any-event-type)

## Command Parsing Configuration (event.command)

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn all command-line commands
- [Developer Guide](../developer-guide/) - Learn how to develop custom modules