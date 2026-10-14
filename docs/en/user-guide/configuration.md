# Configuration File Guide

> [!NOTE]
> **L1 Core Must-Read** – One of the five core documents in the "Read Path" on the homepage, essential for module development.

> This document will introduce the framework's configuration file. If a third-party module requires configuration, please refer to the module's documentation.

ErisPulse uses a TOML-formatted configuration file `config/config.toml` to manage project configurations.

## Configuration File Location

The configuration file is located in the `config/` folder in the project root directory:

```
project/
├── config/
│   └── config.toml
├── main.py
```

### Multi-Instance Warning and Lock File

When the framework starts, it creates a `.erispulse_config.lock` lock file in the `config/` directory and holds it until the process exits (used to detect multiple instances sharing the configuration directory). If the log shows a warning like "Detected that the configuration file may be in use by another ErisPulse instance," it means that **two or more ErisPulse processes are writing to the same configuration file** (typical scenario: multiple containers mounted the same host `config/` directory) – concurrent writes will overwrite each other. Please use a separate configuration directory for each instance.

## Configuration Loading Error Handling

The framework distinguishes three error states when loading `config.toml` and provides **actionable diagnostic information** instead of silently reverting to default configuration:

| Error State | Trigger Condition | Framework Behavior |
|---------|---------|---------|
| File Missing | `config.toml` does not exist | On normal first startup, silently use empty configuration (no warning) |
| TOML Syntax Error | File exists but format is invalid (e.g., missing quotes, unclosed parentheses) | Output **line/column number and reason for error**, and **retain last valid configuration and continue running** (this file modification is not effective) |
| Permission/Other Error | No read permission, IO error, etc. | Output **clear reason**, and **retain last valid configuration and continue running** |

> **Note "last valid configuration" ≠ default configuration**: When the file is damaged, the framework uses the **last successfully parsed configuration from before this startup** (if the configuration file is hot-updated and damaged during runtime, the old value is used), rather than resetting all configuration items to factory defaults. When troubleshooting, do not assume "the configuration has been reset."

For example, if you accidentally write the configuration as `port = 8000` (missing quotes for a string), the log will output something like:

```
[ERROR] [Config] Configuration file config/config.toml has a syntax error (line 3, column 1): ...
[WARNING] [Config] Failed to read configuration file. Continuing to run with last valid configuration, this file modification is not effective – please fix and reload or restart
```

This allows you to immediately locate the problem at the **default INFO level** instead of being confused "why my modified configuration is not effective."

> **What if you modify the configuration file while the robot is running?** If you manually edit `config.toml` during robot operation and introduce a syntax error, the framework will output "Configuration file is damaged (syntax error, line X), cannot merge and write – please fix the configuration file and restart" when writing next time (instead of confusing "write failed"), and the configuration items to be written will be retained, not lost.

## Comment Retention and Minimal Disk Write

**Comments and key order in config.toml are fully retained after framework write**: Whether through code `setConfig()`, CLI configuration wizard save, or adapter/module first-generation configuration template, the framework only modifies the involved keys, and your written comments and arranged order will not be erased or rearranged (based on tomlkit comment-retaining roundtrip implementation).

The framework is restrained in writing disk content:

- **Framework default configuration is not automatically written to disk**: `gc`, `scope`, `transcript` and other built-in default values only reside in memory; `config.toml` only contains keys you explicitly set, keeping it minimal. Refer to `config/config.full.example` in the project for a complete list of configurable items. Copy it to `config.toml` and modify as needed (unconfigured items always use built-in defaults, behavior unchanged).
- **`config.full.example` is automatically maintained**: Regardless of whether `epsdk init` has been executed, as long as the framework is started (`epsdk run` / `main.py`), `config/config.full.example` will be automatically generated if missing. The file header is marked for framework maintenance; when the generator content is updated (such as new configuration items, newly installed components), the startup will refresh it once. If the header is deleted or modified, it will be manually taken over and the framework will no longer overwrite it.
- **Adapter/Module configuration templates**: When initialized for the first time, a template with comments is written to disk (field descriptions are comments); fields marked as `example` do not write to disk, only recorded in `config.full.example` for reference

## Environment Variable Override

The framework supports using environment variables to **override** `ErisPulse.*` configuration items (suitable for Docker / containerization / CI deployment, no need to modify `config.toml`).

Naming rule: Convert the dot-separated path `ErisPulse.<section>.<key>` to all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

Behavior description:
- **Highest priority**: Environment variables override "configuration file" and "default value", automatically converting to the original value type (bool / int / float / comma-separated list / string)
- **Non-persistent**: The override only takes effect during runtime and is not written back to `config.toml`
- **Supports hot update**: After modifying the environment variable during runtime, it can take effect by combining with configuration listening reload

```bash
# Docker deployment example: No need to modify config.toml, directly override the port
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: `ErisPulse.server.port` and other framework configurations are read through `get_server_config()` and other APIs, all affected by environment variable overrides.

### Module Configuration Environment Variable Binding (2.9.0+)

Module-specific declarative configuration (`ConfigClass`) supports field-level environment variable binding – declare `env` in `field(metadata=...)`:

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API key",
        "env": "MYMODULE_API_KEY",   # Environment variable binding
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

Behavior description:

- **Priority**: Environment variable > `config.toml` > declared default value (the priority remains the same even after configuration file hot update)
- **Type conversion**: Environment variable values are automatically converted according to field annotations – `str` as-is, `int` / `float` / `bool` (`true` / `1` / `yes` / `on`) automatically converted, `list` / `dict` parsed via JSON; if conversion fails, ignore the override (fallback to configuration file / default value) and output a warning
- **Declare once, used everywhere**: Configuration reading, hot update, validation use the same pipeline; the configuration panel Schema will mark the `env` name, and the `config.toml` template will also prompt available environment variables (the template does not write the actual value of the environment variable, to avoid leakage)
- **Fully compatible**: Fields without `env` declaration behave unchanged; directly instantiating ConfigClass (not through the framework configuration pipeline) is not affected by environment variables

```bash
# Docker deployment example: No need to modify config.toml, directly inject module key
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **Configuration class vs model field, which to choose?** The configuration class manages "how the module runs" (behavior parameters, hot update), while ORM's `Field()` manages "what data the user generates" (database table, query). Both share the same set of constraint words and validator engine; see the comparison table at
> [Data Model Layer · When to Use Which Declaration](../developer-guide/orm.md#when-to-use-which-declaration).

## Configuration Hot Update

Since version 2.7.0, the framework has provided **systematic support for configuration hot updates**. After external modification of `config.toml` (detected by the background watcher every 5 seconds), or after code calls `setConfig()`, each component automatically responds:

| Component | Hot-updatable Configuration | Behavior |
|------|----------------|------|
| **Logger** | `logger.level` / `log_files` / `log_dir` (including segmentation parameters) / `memory_limit` / `format` / `exclude_levels` | Automatically reapplies (with change detection) |
| **Command System** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter Concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphore and rebuilds according to new value |
| **Active GC** | `framework.proactive_gc_*` | Configuration changes immediately restart GC tasks, supporting runtime adjustment/disable/re-enable |
| **Master System** | `master.users` | Each `is_master()` check reads in real time, no need to restart |
| **Modules/Adapters Configuration** | Their own configuration items | Triggers `on_config_update(old, new)` callback |

**Configurations that require a restart** (cannot be safely hot-switched, warning is output when changed "needs to be effective after restarting the process"):

| Configuration | Reason |
|------|------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely hot-switched at runtime |
| `storage.use_global_db` | SQLite file handle is already opened at runtime, switching paths is unsafe |

> **What if editing and saving goes wrong midway?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, not broadcast an empty configuration to each component (avoiding `on_config_update` receiving empty values and mistakenly reverting to defaults).

### Internal Breakdown of Hot Update Chain

"How do components know when the configuration is changed?" – Behind this is a detection → reload → broadcast chain:

```mermaid
flowchart TD
    A["External edit config.toml"] --> B{"Who finds out first?"}
    B -->|"Background watcher thread<br/>Polls mtime every 5 seconds"| C["_check_file_change determines change"]
    B -->|"Code reads configuration<br/>Cache exceeds 60 seconds"| C
    C --> D["_load_config re-parses TOML"]
    D --> E{"Parsing successful?"}
    E -->|"No (syntax error)"| F["Retain last valid configuration<br/>Do not broadcast, output diagnostic logs"]
    E -->|"Yes"| G["lifecycle.emit config.updated<br/>Carries old_config / new_config"]
    G --> H["Components listen and respond<br/>(logger / scope / command / GC ... )"]
```

**Two detection paths** (either one is sufficient, both can serve as a fallback):

| Path | Mechanism | Trigger Timing |
|------|------|---------|
| Background watcher | Daemon thread `config-watcher` polls file `mtime` every **5 seconds** | Detects external file changes within at most 5 seconds |
| Lazy detection | Any `getConfig()` read, if cache exceeds **60 seconds**, first checks file | Next time configuration is read |

> **The framework will not mistakenly hit itself**: When `setConfig()` writes to disk, it records the "mtime written by itself", and the watcher excludes it when comparing, treating only **external edits** as changes.

**Two types of configuration change events**:

| Event | Trigger | Data | Typical Scenario |
|------|--------|------|---------|
| `config.set` | Code / Dashboard calls `setConfig()` | `{key, old_value, new_value}` | Single key write (template generation, status recording, runtime configuration change) |
| `config.updated` | External edit detected by watcher/lazy detection | `{old_config, new_config, config_file}` | Manual edit of `config.toml` |

> `setConfig()` defaults to **delayed disk write** (merges multiple writes) after 5 seconds; `immediate=True` writes immediately. The watcher detects external modifications and only updates the in-memory cache, **does not** write external changes back to the file.

**List of automatic response components** (both event types are usually subscribed, response content is consistent):

| Component | Listener | Response |
|------|------|------|
| Logger | `config.set` + `config.updated` | Reapply level/file/directory segmentation/memory limit/format/exclude level (with change detection, no change if unchanged) |
| Scope | `config.updated` | Rebuild scope binding cache |
| Command System | `config.updated` | Refresh prefix/case sensitivity/space prefix/must_at_bot parsing parameters, effective on next message |
| Adapter Concurrency | `config.set` + `config.updated` | Invalidate and rebuild semaphore for `handler_max_concurrency` |
| Active GC | `config.set` + `config.updated` | Immediately restart GC background task for `proactive_gc_*` |
| Adapter | Route to `on_config_update` | Each adapter's `on_config_update(old, new)` callback |
| Module | Route to `on_config_update` | Each module's `on_config_update(old, new)` callback |
| Storage | `config.updated` | `use_global_db` change only warns (needs restart) |
| Router | `config.updated` | `cors.*` / `security.*` change only warns (needs restart) |

## Configuration Reading and Deletion API

### getAllConfig: Full Configuration Snapshot

Instead of directly reading private `_cache` (external reading of private attributes is not protected by version compatibility):

```python
config = sdk.config.getAllConfig()     # Deep copy snapshot, in-place modification does not affect framework state
config["ErisPulse"]["server"]["port"]
```

The view口径 is consistent with `getConfig`: Unwritten `setConfig` / `delete` are already reflected, and the content is strictly consistent with the delayed disk-write file.

### delConfig: Delete Configuration Key

`setConfig(key, None)` only sets it to empty, the key remains in the file; `delConfig` removes the key from the file:

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # Delayed write
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # Write immediately
```

- Supports dot-separated paths; returns `False` if the key does not exist
- Disk write follows the comment-retaining path, the rest of the file content and order are unaffected
- Reuses the `config.set` event broadcast (`new_value=None`): Existing listeners of adapters/modules zero change to `on_config_update` can perceive the deletion

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
#   Master specified by platform: users = { yunhu = ["123456"], telegram = ["789012"] }
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
# In container / no file mount scenarios, PEM content can be inlined (prioritized over certfile/keyfile paths)
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
| auto_start | boolean | true | Whether to automatically start the routing server in `sdk.init()`. Set to `false` to skip routing server startup (pure event/no WebUI scenario) |
| ssl_certfile | string | empty | SSL certificate file path |
| ssl_keyfile | string | empty | SSL private key file path |
| ssl_cert | string | empty | **Inlined PEM certificate content** (not a path). Used with `ssl_key` to prioritize over `ssl_certfile`/`ssl_keyfile` paths; framework temporarily writes and builds SSL context, then immediately deletes the temporary file |
| ssl_key | string | empty | **Inlined PEM private key content** (not a path), semantics same as above |

> **Port occupation is not a fatal error**: If the framework detects that the `port` is already occupied at startup, it will skip routing server startup and issue a warning, **adapters and modules will continue to run normally** (only HTTP/WS/SSE routing and WebUI are unavailable). When troubleshooting "the robot can run but the WebUI cannot open", first confirm the port.

## Master System Configuration

The master system is used to identify the "framework master" account (such as Bot administrator). `master.users` supports two writing methods:

```toml
[ErisPulse.master]
# Method 1: Global master (effective on all platforms)
users = ["123456", "789012"]

# Method 2: Master specified by platform (dict)
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| users | array / object | empty | Master account list. `list` form is global master (effective on all platforms); `dict` form specifies by platform (key is platform name, value is the master account list for that platform) |

In code, check using `master.is_master(event)` or `master.is_master(platform, user_id)`, each call reads the configuration in real time (supports hot updates, no restart needed):

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("Hello master")
```

### Determination Chain and Runtime Add/Delete

The master determination chain is **configuration master → runtime record → provider chain**:

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Runtime add (default persistent; persist=False only in memory)
master.remove("yunhu", "123")                # Remove (default persistent)
master.list()                                # Aggregate: {"global": [...], "<platform>": [...]}
```

### Custom Identity Source (provider)

In addition to configuration, you can also register a custom identity source: `fn(platform, user_id) -> bool`, and if the built-in identity sources (configuration + runtime record) do not match, they are tried in sequence, and if any provider allows it, it is recognized as the master. Suitable for connecting adapter administrator interfaces, database roles, and other external identity systems.

The registration entry `master.provider` supports both decorator and function-style writing, and unregistration is done through the unregistered function's `fn.unregister()`:

```python
from ErisPulse.Core import master

# Method 1: Decorator (persistent identity source, recommended)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Method 2: Function-style (register during module load / unregister during unload)
fn = master.provider(admin_provider)
fn.unregister()
```

> Provider exceptions are caught and skipped, not blocking the identity determination chain.
> Binding instance methods cannot mount `unregister`, and scenarios requiring registration/unregistration pairing should use **module-level functions**.

### User Priority: Master Scope Determined by User

The `master=True` of a command is only the **developer's default**: The user can overwrite or loosen it in
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false` (see [Unified Event Override Configuration](#unified-event-override-configurationeventoverrides), user explicit configuration takes effect).

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # Explicit log file list (mutually exclusive with log_dir, higher priority)
log_dir = ""                  # Log output directory (auto-created). After setting, automatically segments and rotates logs into `erispulse.log` in the directory according to `log_rotation`; mutually exclusive with `log_files`, `log_files` has higher priority
log_rotation = "size"         # Segmentation method: "size" / "date" / "none"
log_max_size_mb = 10          # Single file size limit (MB) in size mode, rotates to `.1`/`.2` backup when exceeded
log_backup_count = 5          # Number of historical log files retained
log_rotation_when = "midnight"  # Date mode rotation cycle: S/M/H/D/midnight
memory_limit = 1000
exclude_levels = ["EVENT"]
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| level | string | INFO | Log level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed debugging information of the framework) |
| format | string | rich | Log output format: `rich` (colorful, default), `plain` (plain text without color, suitable for log collection/pipeline redirection), `json` (structured JSON, suitable for ELK, etc.) |
| log_files | array | empty | List of log output files (explicit paths, not segmented) |
| log_dir | string | empty | Log output directory (auto-created). After setting, writes to `erispulse.log` in the directory and automatically segments according to `log_rotation`; mutually exclusive with `log_files`, `log_files` has higher priority |
| log_rotation | string | size | Segmentation method: `size` (by size) / `date` (by time) / `none` (not segmented) |
| log_max_size_mb | float | 10 | Single file size limit (MB) in size mode, rotates to `.1`/`.2` backup when exceeded |
| log_backup_count | integer | 5 | Number of historical log files retained, oldest backups beyond this are automatically deleted |
| log_rotation_when | string | midnight | Date mode rotation cycle: `S`/`M`/`H`/`D`/`midnight` (default daily at midnight) |
| memory_limit | integer | 1000 | Number of log entries saved in memory |
| exclude_levels | array | empty | Levels to exclude. Logs of excluded levels are **completely discarded** (not written to memory, not pushed to Dashboard or other subscribers, not printed, not written to file). Supports hot updates |

You can also dynamically switch in code:

```python
from ErisPulse.Core import logger

# Segment by size: single file 10MB, retain 5 copies
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# Segment by time: rotate daily at midnight, retain 7 copies
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` and related segmentation configurations require ErisPulse **2.8.0+**.

> **Privacy Protection**: Message content is recorded at the **EVENT level** (value 21). Setting `exclude_levels = ["EVENT"]` allows the backend (such as the Dashboard log panel) to not see message content in each group/private chat, while not affecting logs of other levels.

> [!NOTE]
> The `exclude_levels` feature requires ErisPulse **2.8.0+**.

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
| uninit_timeout | integer | 30 | Graceful shutdown timeout (seconds), forcibly terminates after exceeding. 0 means no timeout |
| strict_mode | integer | 0 | Strict mode level, see below "Strict Mode" explanation |
| handler_max_concurrency | integer | 64 | Maximum concurrent Task count for event handlers, increasing improves throughput but increases memory usage |
| offline_bot_expiry | integer | 3600 | Automatic expiration time (seconds) for offline Bot records, 0 means never expires |

### Active GC Configuration

After SDK initialization, an active GC background task starts, periodically performing Python GC and internal resource recycling (such as cleaning up offline Bots). All parameters support hot updates, and the task restarts immediately when changes are made.

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | Recycling interval (seconds), supports decimals. 0 means disable active GC |
| proactive_gc_generation | integer | 0 | Regular round recycling generation (0/1/2, clamped to 0..2). Note that `gc.collect(2)` is equivalent to full recycling, default 0 keeps it lightweight; deep recycling is triggered periodically by `proactive_gc_full_every` |
| proactive_gc_full_every | integer | 20 | Full recycling every N rounds, 0 means disable periodic full recycling. Full recycling is constrained by the `proactive_gc_memory_growth_mb` threshold |
| proactive_gc_memory_growth_mb | integer | 32 | Full recycling memory growth threshold (MB): Compared with the memory baseline after the last full recycling (prioritizing tracemalloc, then RSS), full recycling is only performed when the growth reaches this value. 0 means no threshold |
| proactive_gc_idle_only | boolean | false | When enabled, skip Python GC during event peaks (when there are unfinished pending handlers) to avoid pauses and message processing competition; internal resource recycling is unaffected |
| proactive_gc_gen0_min | integer | 500 | Minimum garbage amount for regular round recycling of gen0: `gc.get_count()[0]` below this value is skipped directly (empty round nearly zero overhead). 0 means always recycle |

> **2.7.1 Change**: The default `proactive_gc_generation` is adjusted from `2` to `0`, and the default `proactive_gc_full_every` is adjusted from `0` to `20`. Previously `generation=2` meant full recycling every round; the new default maintains recycling coverage while significantly reducing empty round overhead. Explicitly configured old values still follow literal semantics.

### Strict Mode

The strict mode controls the handling strategy for modules/adapters when they are not compliant or fail during the loading phase. Modern modules/adapters should inherit the corresponding base classes (`BaseModule`/`BaseAdapter`); components that do not inherit base classes affect the framework's context system and fallback cleanup, potentially leading to resource leaks.

> **2.5.2 Change**: The default level is adjusted from `1` (skip) to `0` (lenient), to reduce loading issues for new users on first use. Components that do not inherit base classes will be warned and attempted to load, rather than directly rejected. If you need to restore the previous behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (default) | Violations are only warned, components that do not inherit base classes will still be attempted to load (compatible with old components) |
| 1 | Strict-Skip | Reject components that do not inherit base classes and skip them, other components start normally |
| 2 | Strict-Fatal | Collect all violations and report them together, then terminate the entire startup |

In all levels, component self-crashes during the loading/registration/initialization phase are always skipped; the difference is:

- **0 → 1**: The only behavioral change is that "not inheriting base class" changes from "still loading" to "skipping".
- **1 → 2**: All violations (not inheriting base class, loading failure, registration failure, initialization failure, etc.) are upgraded to fatal, collected at the startup check point and reported as a violation list, then terminated.

#### Exemption List

If certain components cannot be migrated for some reason (e.g., dependent old modules), you can add them to the exemption list. Components listed will be treated as lenient mode and continue loading, even if they are non-compliant:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly indicate how to resume loading (add to the exemption list or lower the level).

## Storage Configuration

Since version 2.8.0, the storage engine supports three asynchronous backends, with **completely consistent APIs and one-click configuration switching**:

| Backend | Driver | Installation | Features |
|------|------|------|------|
| SQLite (Default) | aiosqlite | Ready-to-use out of the box | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Existing MySQL infrastructure, multi-instance sharing |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction capability, high concurrency |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: Use the package's global database data/config.db instead of the project's independent database

[ErisPulse.storage.mysql]      # Applies when backend = "mysql"
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # Applies when backend = "postgres"
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
> - Before switching backends, use a verification script to check: `python tests/devs/test_storage_backend_verify.py --backend mysql`
> - For full details on transactions, dialect differences, and custom backends, see [Storage Backends](../advanced/storage-backends.md)

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
| case_sensitive | boolean | true | Whether to distinguish case (is `/Help` and `/help` different commands) |
| allow_space_prefix | boolean | false | Whether to allow space as prefix |
| must_at_bot | boolean | false | Whether to require @bot to trigger command (private chat is not restricted) |

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
| language | string | auto | The display language for built-in framework text. Set to `auto` to automatically detect the system language, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

## Module Configuration

Each module can define its own configuration in the configuration file:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

Read and write configuration in the module:

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

> `setConfig` uses delayed writing by default (batched saved to file every ~5 seconds), set `immediate=True` to persist immediately. Configuration changes trigger the `config.set` lifecycle event.

## Scope Configuration (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope declares "what range it is effective in" – which modules are available in what platform / Bot / session (① module dimension), whether events are received for what user / group / Bot / adapter (② identity dimension), and what outbound calls modules can initiate (③ outbound dimension):

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit deny in strict mode; does not affect outbound dimension)
cache_size = 1024           # LRU cache size

# ① Module dimension (priority: session > Bot > platform; entries support exact / glob / re: regex)
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# Sub-level binding with merge = true merges with lower priority entries (default overall overwrite)
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② Identity dimension (priority: user > session > Bot > adapter; only allow or deny one per level)
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # Discard all events on this platform at the entry
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ③ Outbound dimension (default all allowed; rules are inline tables, entries support exact / glob / re: regex)
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # Deny all sending
api = { allow = ["get_*"] }               # Allow only standard query APIs
request = { deny = true }                 # Deny request handling
```

| Configuration Item | Type | Description |
|---------|------|------|
| `scope.default_allow` | boolean | Global fallback: Allow or deny for modules/identity not matched by rules (`true`) |
| `scope.cache_size` | integer | LRU cache size (default 1024) |
| `scope.platforms / bots / sessions` | table | ① Three-level module binding: `{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② Four-level identity binding: `{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ Outbound rules: `{allow=[...], deny=true|[...]}` (actions are send / api / request) |

> For detailed explanations and runtime APIs (dimensional `sdk.scope.set_module()` / `set_identity()` / `set_action()`, determination `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`, and dictionary-style fallback `get()` / `set()` / `delete()`), see [Scope (scope)](../advanced/scope.md).

## Unified Event Override Configuration (event.overrides)

Unified override system: Overriding behavior of any module handler by **event type** without modifying module code. OneBot12 standard types (meta / message / notice / request) and extended types (command) each have their own overridable parameters:

```toml
[ErisPulse.event.overrides]

# message: Text trigger conditions (AND with code-side conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta: detail_type whitelist (entries support exact / glob / re: regex)
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command (extended type): Implement parameter override (user priority; disable via acl deny)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # Override to only framework master (false opens developers' master restriction)
hidden = true               # Hide in help list
aliases = ["rs"]            # Effective alias

# acl (command exclusive): User allow/deny lists (command names support glob / re: regex, exact keys take priority)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL fallback: Allow (true) or strictly deny (false) commands not configured with ACL
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
| `event.overrides.acl_default_allow` | boolean | ACL fallback: Allow (true) or strictly deny (false) commands not configured with ACL |

> Runtime API (after `from ErisPulse.Core.Event import overrides`, call by type sub-namespace `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` etc., or access via `sdk.Event.overrides`)
> See [Event Handling Introduction · Event Override](../getting-started/event-handling.md#event-override-no-code-modification-override-behavior-of-any-event-type).

## Command Parsing Configuration (event.command)

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn all command-line commands
- [Developer Guide](../developer-guide/) - Learn how to develop custom modules