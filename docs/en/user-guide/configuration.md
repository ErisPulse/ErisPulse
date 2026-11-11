# Configuration File Documentation

> [!NOTE]
> **L1 Core Must-Read** — One of the five core documents in the homepage "Reading Path", essential for module development.

> This document explains the framework's own configuration file `config/config.toml`: what each section manages, which settings support hot reload, and how to override them with environment variables. For third-party module configuration items, please refer to the module's own documentation.

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

When the framework starts, it creates a `config.lock` lock file in the project root's runtime status directory **`.erispulse/`** and holds it until the process exits (used to detect multiple instances sharing the configuration directory; in versions 2.10 and earlier, the `.erispulse_config.lock` in the `config/` directory would be automatically cleared after upgrade and first startup). If the log shows a warning like "Detected that the configuration file may be in use by another ErisPulse instance," it means there are **two or more ErisPulse processes writing to the same configuration file** (typical scenario: multiple containers mounting the same host `config/` directory) — concurrent writes will overwrite each other. Please use a separate configuration directory for each instance.

### Sensitive Configuration Not in Repository

The configuration file contains tokens (token/API key) and other sensitive information: the framework initialization and `epsdk init` automatically generate a `.gitignore` in the `config/` directory (with only one line `*` — **all files in the directory are not included in version control, including the ignore file itself**). Existing `.gitignore` files will not be overwritten. The `.erispulse/` runtime status directory (instance lock, CLI runtime status files) is considered local machine state, and the project template's `.gitignore` already defaults to ignoring it.

## Configuration Loading Error Handling

When the framework loads `config.toml`, it distinguishes three error states and provides **actionable diagnostic information** instead of silently reverting to default configuration:

| Error State | Trigger Condition | Framework Behavior |
|---------|---------|---------|
| File Missing | `config.toml` does not exist | On normal first startup, silently uses empty configuration (no warning) |
| TOML Syntax Error | File exists but format is invalid (e.g., missing quotes, un-closed brackets) | Outputs **line/column number and reason for error**, and **retains last valid configuration to continue running** (this file modification does not take effect) |
| Permission/Other Error | No read permission, IO error, etc. | Outputs **clear reason**, and **retains last valid configuration to continue running** |

> **Note "last valid configuration" ≠ default configuration**: When the file is damaged, the framework uses the **last successfully parsed configuration before this startup** (if a running hot update modifies the file badly, it uses the old value), rather than resetting all configuration items to factory defaults. When troubleshooting, do not assume "configuration has been reset."

For example, if you accidentally write the configuration as `port = 8000` (missing quotes for a string), the log will output something like:

```
[ERROR] [Config] Configuration file config/config.toml has a syntax error (line 3, column 1): ...
[WARNING] [Config] Failed to read configuration file. Continuing to run using the last valid configuration, this file modification did not take effect — please fix and reload or restart
```

This allows you to immediately locate the issue at the **default INFO level** instead of being confused "why my modified configuration did not take effect."

> **Modified configuration file while running?** If you manually edit `config.toml` during robot operation and introduce a syntax error, the framework will output "Configuration file has been damaged (syntax error, line X), cannot merge and write — please fix the configuration file and restart" when it next writes (merges configuration), rather than a confusing "write failed." The configuration items to be written will be retained and not lost.

## Comment Preservation and Minimal Disk Write

The **comments and key order** in config.toml are **fully preserved** after the framework writes: whether through code `setConfig()`, CLI configuration wizard save, or adapter/module first-generation configuration template, the framework only modifies the involved keys, your written comments and organized order will not be erased or rearranged (based on tomlclass's lossless TOML engine, untouched content is preserved byte-for-byte, and the file's original CRLF/LF line endings are not changed).

The framework keeps disk writes minimal:

- **Framework default configuration is not automatically written to disk**: `gc`, `scope`, `transcript` and other built-in default values only reside in memory, `config.toml` only contains keys you explicitly set, keeping it minimal. For a complete list of configurable items, refer to `config/config.full.example` in the project, copy and modify as needed (unconfigured items always use built-in defaults, behavior unchanged)
- **`config.full.example` is automatically maintained**: Regardless of whether `epsdk init` has been executed, as long as the framework is started (`epsdk run` / `main.py`), `config/config.full.example` will be automatically generated if missing; the first line of the file is a framework-maintained marker, generator content updates (such as new configuration items, newly installed components) will refresh once on startup, deleting/modifying the first line switches to manual takeover, and the framework will no longer overwrite
- **Adapter/Module Configuration Templates**: First initialization saves templates with comments (field descriptions are comments); fields marked as `example` are not written to disk, only recorded in `config.full.example` for reference
- **Declarative Comments Readback**: Comments in the configuration file are documentation itself — `ep doctor` and configuration validation failure messages will reference the original comment text of the field in the file (even if you manually modified the comment, the message follows the current file state), no need to refer to the documentation to find the field meaning when reporting errors

## Environment Variable Override

The framework supports overriding `ErisPulse.*` configuration items with **environment variables** (suitable for Docker/containerization/CI deployment, no need to modify `config.toml`).

Naming rule: Change the dot-separated path `ErisPulse.<section>.<key>` to all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

Behavior description:

- **Highest Priority**: Environment variables override "configuration file" and "default values," automatically converting to the original value type (bool/int/float/comma-separated list/string)
- **Not Persistent**: Override only takes effect during runtime and is not written back to `config.toml`
- **Support Hot Reload**: After modifying environment variables during runtime, configuration listening reload can take effect

```bash
# Docker deployment example: no need to modify config.toml, directly override port
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: `ErisPulse.server.port` and other framework configurations accessed through `get_server_config()` and similar APIs are affected by environment variable overrides.

### Module Configuration Environment Variable Binding (2.9.0+)

Modules' own declarative configurations (`ConfigClass`) support field-level environment variable binding — declare `env` in `field(metadata=...)`:

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

- **Priority**: Environment variable > `config.toml` > declared default value (configuration file hot update still maintains this priority)
- **Type Conversion**: Environment variable values are automatically converted according to field annotations — `str` as original, `int`/`float`/`bool` (`true`/`1`/`yes`/`on`) automatically converted, `list`/`dict` parsed via JSON; if conversion fails, ignore the override (fallback to configuration file/default value) and output a warning
- **Declare Once, Apply Everywhere**: Configuration reading, hot update, and validation use the same pipeline; configuration panel Schema will mark `env` names, and `config.toml` template comments will also prompt available environment variables (template does not write actual values of environment variables to avoid leakage)
- **Fully Compatible**: Fields without `env` declaration behave unchanged; directly instantiating ConfigClass (without framework configuration pipeline) is not affected by environment variables

```bash
# Docker deployment example: no need to modify config.toml, directly inject module key
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **Configuration Class vs Model Field When to Use Which?** Configuration class manages "how the module runs" (behavior parameters, hot reload), ORM's `Field()` manages "what data the user generates" (database table, query). Both share the same constraint vocabulary and validator engine; see the comparison table at [Data Model Layer · When to Use Which Declaration](../developer-guide/orm.md#when-to-use-which-declaration).

## Configuration Hot Reload

Starting from version 2.7.0, the framework provides **systematic support for configuration hot reload**. After external modification of `config.toml` (background watcher checks every 5 seconds), or code calls `setConfig()`, each component automatically responds:

| Component | Configuration Supporting Hot Reload | Behavior |
|------|----------------|------|
| **Logger** | `logger.level` / `log_files` / `log_dir` (including segmentation parameters) / `memory_limit` / `format` / `exclude_levels` | Automatically reapplies (with change detection) |
| **Command System** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter Concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphore, rebuilds with new value |
| **Proactive GC** | `framework.proactive_gc_*` | Config change immediately restarts GC task, supports runtime adjustment/disable/re-enable |
| **Master System** | `master.users` | Each `is_master()` check reads in real time, no restart needed |
| **Module/Adapter Configuration** | Their own configuration items | Triggers `on_config_update(old, new)` callback |

**Configuration that Requires Restart** (cannot be safely hot switched, warning is output when changed "requires restart of process to take effect"):

| Configuration | Reason |
|------|------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely hot switched at runtime |
| `storage.use_global_db` | SQLite file handle is already open at runtime, switching path is unsafe |

> **Error during mid-edit save?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, and will not broadcast an empty configuration to each component (to avoid `on_config_update` receiving empty values and mistakenly reverting to defaults).

### Internal Breakdown of Hot Reload Chain

"How do components know when the configuration is changed?" — Behind the scenes is a detection → reload → broadcast chain:

```mermaid
flowchart TD
    A["External edit config.toml"] --> B{"Who first detects it?"}
    B -->|"Background watcher thread<br/>Polls mtime every 5 seconds"| C["_check_file_change determines change"]
    B -->|"When reading configuration<br/>Cache exceeds 60 seconds"| C
    C --> D["_load_config re-parses TOML"]
    D --> E{"Parsing successful?"}
    E -->|"No (syntax error)"| F["Retain last valid configuration<br/>Do not broadcast, output diagnostic log"]
    E -->|"Yes"| G["lifecycle.emit config.updated<br/>Carries old_config / new_config"]
    G --> H["Each component listener responds<br/>(logger / scope / command / GC ... )"]
```

**Two Detection Paths** (either one is sufficient, both can serve as a fallback):

| Path | Mechanism | Trigger Timing |
|------|------|---------|
| Background watcher | Daemon thread `config-watcher` polls file `mtime` every **5 seconds** in `wait` | At most 5 seconds after external file modification |
| Lazy Detection | Any `getConfig()` read, if cache exceeds **60 seconds**, first checks file | Next time configuration is read |

> **Framework will not hurt itself**: When `setConfig()` writes to disk, it records the "mtime written by itself," and the watcher excludes it when comparing, recognizing only **external edits** as changes.

**Two Types of Configuration Change Events**:

| Event | Trigger | Data | Typical Scenario |
|------|--------|------|---------|
| `config.set` | Code / Dashboard calls `setConfig()` | `{key, old_value, new_value}` | Single key write (template generation, status recording, runtime config change) |
| `config.updated` | External edit after watcher/lazy detection captures | `{old_config, new_config, config_file}` | Manually editing `config.toml` |

> `setConfig()` defaults to **delayed write to disk** (merges multiple writes), `immediate=True` writes immediately. After the watcher detects an external modification, it only updates the in-memory cache and **does not** write the external change back to the file.

**List of Automatic Response Parties** (both event types usually subscribe, response content is consistent):

| Component | Listener | Response |
|------|------|------|
| Logger | `config.set` + `config.updated` | Level/file/directory segmentation/memory limit/format/exclude level reapply (with change detection, no change does not move) |
| Scope | `config.updated` | Scope binding cache rebuild |
| Command System | `config.updated` | Prefix/case sensitivity/space prefix/must_at_bot parse parameter refresh, takes effect on next message |
| Adapter Concurrency | `config.set` + `config.updated` | `handler_max_concurrency` invalidates and rebuilds semaphore |
| Proactive GC | `config.set` + `config.updated` | `proactive_gc_*` immediately restarts GC background task |
| Adapter | Route to `on_config_update` | Each adapter's `on_config_update(old, new)` callback |
| Module | Route to `on_config_update` | Each module's `on_config_update(old, new)` callback |
| Storage | `config.updated` | `use_global_db` change **only warns** (requires restart) |
| Router | `config.updated` | `cors.*` / `security.*` change **only warns** (requires restart) |

## Configuration Reading and Deletion API

### getAllConfig: Full Configuration Snapshot

Instead of directly reading private `_cache` (external reading of private attributes is not protected by version compatibility):

```python
config = sdk.config.getAllConfig()     # Deep copy snapshot, in-place modification does not affect framework state
config["ErisPulse"]["server"]["port"]
```

The view口径 is consistent with `getConfig`: `setConfig` / `delete` that have not been written to disk are already reflected, and the content strictly matches the file after delayed write.

### delConfig: Delete Configuration Key

`setConfig(key, None)` only sets it to empty, the key remains in the file; `delConfig` will **remove the key from the file**:

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # Delayed write
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # Write immediately
```

- Supports dot-separated paths; returns `False` if the key does not exist
- Writes follow the comment preservation path, the rest of the file content and order are unaffected
- Reuses `config.set` event broadcast (with `new_value=None`): existing listeners for adapters/modules zero changes can perceive deletion

## Complete Configuration Example

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users support two writing methods (choose one):
#   Global master (effective for all platforms): users = ["123456", "789012"]
#   Specify master per platform: users = { yunhu = ["123456"], telegram = ["789012"] }
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
# For container / no file mounting scenarios, PEM content can be inlined (prioritized over certfile/keyfile path)
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
| auto_start | boolean | true | Whether to automatically start the routing server at `sdk.init()`. Set to `false` to skip routing server startup (pure event/no WebUI scenario) |
| ssl_certfile | string | empty | SSL certificate file path |
| ssl_keyfile | string | empty | SSL private key file path |
| ssl_cert | string | empty | **Inlined PEM certificate content** (not a path). When used together with `ssl_key`, it takes precedence over `ssl_certfile`/`ssl_keyfile` paths; the framework temporarily writes and builds the SSL context, then immediately deletes the temporary file |
| ssl_key | string | empty | **Inlined PEM private key content** (not a path), same semantics as above |

> **Port occupancy is not a fatal error**: If the framework detects that the `port` is already occupied at startup, it will skip starting the routing server and issue a warning, **adapters and modules will still run normally** (only HTTP/WS/SSE routing and WebUI are unavailable). When troubleshooting "the robot can run but the WebUI cannot open," first confirm the port.

## Master System Configuration

The master system is used to identify the "master" account of the framework (such as the bot administrator). `master.users` supports three writing methods:

```toml
[ErisPulse.master]
# Writing method one: global master (effective for all platforms, including newly added platforms)
users = ["123456", "789012"]

# Writing method two: specify master only per platform (dict)
# users = { yunhu = ["123456"], telegram = ["789012"] }

# Writing method three: global + platform-specific coexistence — the global key in dict is the global master bucket
# users = { global = ["123456"], yunhu = ["789012"] }
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| users | array / object | empty | List of master account IDs. `list` form is global master (effective for all platforms); `dict` form specifies per platform (key is platform name, `global` key is the global master bucket), value is the list of master account IDs for that platform |

> **Regarding new platforms**: Both `list` form and `global` bucket in `dict` are "defined once, effective for all platforms," no need to modify the configuration when new platforms are added later; platform-specific entries only take effect for platforms with the same name (including prefix/wildcard tolerance). `master.add(None, uid)` persists to the `global` bucket, existing platform entries are unaffected.

In code, check using `master.is_master(event)` or `master.is_master(platform, user_id)`, each call reads the configuration in real time (supports hot reload, no restart needed):

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("Hello, Master")
```

### Determination Chain and Runtime Add/Delete

The master determination chain is **configuration master → runtime record → provider chain**:

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Add at runtime (default persists; persist=False only in-memory)
master.remove("yunhu", "123")                # Remove (default persists)
master.list()                                # Aggregate: {"global": [...], "<platform>": [...]}
```

### Custom Identity Source (provider)

In addition to configuration, custom identity sources can be registered: `fn(platform, user_id) -> bool`, built-in identity sources (configuration + runtime record) are not matched, they are tried in sequence, and any provider that allows is recognized as the master. Suitable for connecting adapter administrator interfaces, database roles, and other external identity systems.

The registration entry `master.provider` supports both decorator and function-style writing, and unregistration is done through the unregistration function on the registered function:

```python
from ErisPulse.Core import master

# Method one: decorator (recommended for persistent identity source)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Method two: function-style (register during module loading / unregister during unloading)
fn = master.provider(admin_provider)
fn.unregister()
```

> Provider exceptions are caught and skipped, not blocking the identity determination chain. Binding instance methods cannot attach `unregister`, for scenarios requiring paired registration/unregistration, use **module-level functions**.

### User Priority: Master Effect Range is Ultimately Decided by the User

The `master=True` of a command is only a **developer default**: the user can override or tighten or loosen it in
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false` (see [Unified Event Override Configuration](#unified-event-override-configuration-eventoverrides), user explicit configuration takes effect).

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # Explicit list of log files (mutually exclusive with log_dir, higher priority)
log_dir = ""                  # Log directory (automatic segment rotation enabled)
log_rotation = "size"         # Segmenting method: "size" / "date" / "none"
log_max_size_mb = 10          # Maximum size per file in size mode (MB)
log_backup_count = 5          # Number of historical log files to retain
log_rotation_when = "midnight"  # Rotation cycle in date mode: S/M/H/D/midnight
memory_limit = 1000             # Maximum number of log entries per module in memory (0 = disable memory log copy)
total_memory_limit = 5000       # Total number of log entries across all modules in memory (0 = unlimited)
exclude_levels = ["EVENT"]
```

| Configuration Item | Type | Default Value | Description |
|---------------------|------|---------------|-------------|
| level | string | INFO | Log level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed internal debugging information) |
| format | string | rich | Log output format: `rich` (colored, default), `plain` (plain text without color, suitable for log collection/pipeline redirection), `json` (JSON structured, suitable for ELK, etc.) |
| log_files | array | empty | List of explicit log file paths (no segmentation) |
| log_dir | string | empty | Log output directory (automatically created). When set, logs are written into `erispulse.log` in the directory and segmented automatically based on `log_rotation`; mutually exclusive with `log_files`, `log_files` takes precedence |
| log_rotation | string | size | Segmentation method: `size` (by size) / `date` (by time) / `none` (no segmentation) |
| log_max_size_mb | float | 10 | Maximum file size in size mode (MB); when exceeded, the file rotates to `.1`/`.2` backups |
| log_backup_count | integer | 5 | Number of historical log files to retain; oldest backups beyond this limit are automatically deleted |
| log_rotation_when | string | midnight | Rotation cycle in date mode: `S`/`M`/`H`/`D`/`midnight` (default is midnight each day) |
| memory_limit | integer | 1000 | Number of log entries saved in memory per module; `0` means disable memory log copy (no new entries are written to memory, but existing records are retained) |
| total_memory_limit | integer | 5000 | Total number of log entries across all modules in memory; `0` means unlimited. When exceeded, the oldest records are discarded according to the rotation policy (prioritizing modules with the most entries), independent of the single-module `memory_limit` |
| exclude_levels | array | empty | Levels to exclude. Logs of excluded levels are **completely discarded** (not written to memory, not pushed to Dashboard or other subscribers, not printed, not written to files). Supports hot update |

You can also dynamically switch in code:

```python
from ErisPulse.Core import logger

# Segment by size: single file 10MB, retain 5 copies
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# Segment by time: rotate at midnight daily, retain 7 copies
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]  
> `log_dir` and related segmentation configurations require ErisPulse **2.8.0+**.

> **Privacy Protection**: Message send/receive content is logged at the **EVENT** level (value 21). Setting `exclude_levels = ["EVENT"]` ensures that backend components (such as the Dashboard log panel) cannot see message content from groups or private chats, while not affecting logs of other levels.

In addition to configuration files (supporting hot updates), you can also switch at runtime using code—no need to write configuration when making management commands like `/privacy on|off`:

```python
from ErisPulse import logger

logger.exclude_level("EVENT")        # Temporarily exclude a log level at runtime (same semantics as exclude_levels configuration)
logger.allow_level("EVENT")          # Restore this level
logger.list_excluded_levels()        # View currently excluded levels
logger.set_format("json")            # Switch output to JSON line protocol (same effect as format configuration key)
```

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
| enable_lazy_loading | boolean | true | Whether to enable module lazy loading |
| uninit_timeout | integer | 30 | Graceful shutdown total timeout (seconds), force termination after exceeding. 0 means no timeout set |
| strict_mode | integer | 0 | Strict mode level, see below "Strict Mode" explanation |
| handler_max_concurrency | integer | 64 | Maximum concurrent Task count for event handler, set larger to increase throughput but increase memory usage |
| handler_queue_max_pending | integer | 4096 | Event surge backpressure: maximum pending handler Task count per platform, new event Task is discarded and WARNING is recorded when exceeded (discard count can be checked in troubleshoot); `0` means unlimited |
| offline_bot_expiry | integer | 3600 | Automatic expiration time (seconds) for offline Bot records, 0 means never expire |
| plugins_dir | string / list | "plugins" | Local plugin folder (relative to project root); new/removed/modified plugin files are automatically discovered by hot reload watcher |
| watch_ignore_dirs | list | built-in list | Directories ignored by hot reload file monitoring (`.venv`/`.git`/`__pycache__` etc.); non-empty list **replaces** built-in list, `[]` means ignore no directories |
| watch_include_plugin_dirs | boolean | true | Whether `epsdk run --reload` hands plugin directories over to plugin hot reload watcher for precise handling (single module reload), and excludes from full monitoring |
| event_dedupe | boolean | true | Event idempotent deduplication: duplicate event id only distributes once (repeated delivery from connection layer/retransmission from gateway) |
| cross_account_policy | string | "off" | Cross-account duplicate handling policy: when the same physical message is received by multiple accounts in sequence, the processing — `off` does not associate (events are distributed as usual); `mark` injects the top-level `multi_receipt` field (pointing to the first accepted event) after distribution, modules read this field to decide themselves; `drop` drops the copy at the distribution entrance (framework-level deduplication, modules are unaware) |

### Proactive GC Configuration

After SDK initialization, a proactive GC background task is started, periodically executing Python GC and internal resource cleanup (offline Bot cleanup, etc.). All parameters support hot reload, and the task is restarted immediately when changed.

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | Recycling interval (seconds), supports decimal. 0 means disable proactive GC |
| proactive_gc_generation | integer | 0 | Regular round recycling generation (0/1/2, clamped to 0..2). Note `gc.collect(2)` is equivalent to full recycling, default 0 keeps lightweight; deep recycling is triggered periodically by `proactive_gc_full_every` |
| proactive_gc_full_every | integer | 20 | Full recycling every N rounds, 0 means disable periodic full recycling. Full recycling is constrained by the `proactive_gc_memory_growth_mb` threshold |
| proactive_gc_memory_growth_mb | integer | 32 | Full recycling memory growth threshold (MB): compared with the last full recycling's memory baseline (prioritizing tracemalloc, then RSS), full recycling is only executed when the growth reaches this value. 0 means no threshold |
| proactive_gc_idle_only | boolean | false | When enabled, Python GC is skipped in event surges (there are unfinished pending handlers), avoiding pauses and message processing competition; internal resource recycling is unaffected |
| proactive_gc_gen0_min | integer | 500 | Lower bound of garbage quantity for regular round recycling: `gc.get_count()[0]` below this value directly skips (empty round is almost zero overhead). 0 means always recycle |

> **2.7.1 Change**: The default `proactive_gc_generation` is adjusted from `2` to `0`, and the default `proactive_gc_full_every` is adjusted from `0` to `20`. Previously, `generation=2` meant full recycling every round; the new default keeps recycling coverage while significantly reducing idle round overhead. Explicitly configured old values still take literal semantics.

### Strict Mode

The strict mode controls the handling strategy for modules/adapters when they are not compliant or fail during the loading phase. Modern modules/adapters should inherit corresponding base classes (`BaseModule`/`BaseAdapter`); components that do not inherit base classes affect the framework's context system and fallback cleanup, potentially causing resource leaks.

> **2.5.2 Change**: The default level is adjusted from `1` (skip) to `0` (lenient), to reduce loading issues for new users. Components that do not inherit base classes are still attempted to load with a WARNING, rather than being directly rejected. To restore the previous behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (default) | Violations are only warned, components that do not inherit base classes are still attempted to load (compatibility with old components) |
| 1 | Strict-Skip | Reject components that do not inherit base classes and skip them, other normal startup |
| 2 | Strict-Fatal | Collect all violations and report them uniformly, then terminate the entire startup |

Under all levels, component self-crashes during the loading/registration/initialization phase are always skipped; the difference is:

- **0 → 1**: The only behavioral change is that "not inheriting base class" changes from "still loaded" to "skipped."
- **1 → 2**: All violations (not inheriting base class, loading failure, registration failure, initialization failure, etc.) are upgraded to fatal, collected at the startup checkpoint and reported as a violation list before termination.

#### Exception List

If certain components temporarily cannot migrate (for example, dependent on old modules), they can be added to the exception list. Components listed will be treated as lenient mode and continue loading even if they are non-compliant:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly prompt how to resume loading (add to the exception list or lower the level).

#### Integration with CLI

The `epsdk run` startup pre-check (config file parseability, component required configuration completeness) defaults to follow this configuration: if not 0, check failure will refuse startup, 0 will only warn and continue. You can also temporarily switch without changing the configuration: `epsdk run --strict` will enable self-check and strict level for this run (level only increases, propagated to the running process via `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable), `--no-strict` temporarily lowers to lenient and only warns.

## Storage Configuration

Since version 2.8.0, the storage engine supports three asynchronous backends, **with completely consistent APIs and one-click configuration switching**:

| Backend | Driver | Installation | Characteristics |
|------|------|------|------|
| SQLite (default) | aiosqlite | Ready-to-use out of the box | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Existing MySQL infrastructure, multi-instance sharing |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction capability, high concurrency |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: use the global database data/config.db inside the package

[ErisPulse.storage.mysql]      #生效 when backend = "mysql"
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   #生效 when backend = "postgres"
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
| backend | string | sqlite | Storage backend: `sqlite` / `mysql` / `postgres`, switch with zero code changes |
| use_global_db | boolean | false | Only for SQLite: whether to use the global database inside the package rather than the project-specific database |
| storage.mysql.* | table | see above | MySQL connection parameters (host / port / user / password / database / charset / pool) |
| storage.postgres.* | table | see above | PostgreSQL connection parameters (host / port / user / password / database / pool) |

Environment variables are also supported for overriding (Docker / 12-factor): `ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`.

> [!TIP]
> - Connection parameter changes require a framework restart to take effect; transient connection pool creation failures will automatically retry with exponential backoff
> - Before switching backends, use a verification script to self-check: `python tests/devs/test_storage_backend_verify.py --backend mysql`
> - Transactions / dialect differences / custom backends, etc., complete explanations are available at [Storage Backends](../advanced/storage-backends.md)

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
| case_sensitive | boolean | true | Whether to distinguish case (`/Help` and `/help` are different commands) |
| allow_space_prefix | boolean | false | Whether to allow space as prefix |
| must_at_bot | boolean | false | Whether to require @bot to trigger command (private chat is not restricted) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| ignore_self | boolean | true | Whether to ignore the robot's own messages |

> Event deduplication has three layers, each handling a different type of duplicate: `event_dedupe` (framework, duplicate event ID) → `ignore_self` (this section, robot's own message) → `cross_account_policy` (framework, content-level duplicates from multiple accounts). The layered responsibilities are detailed in [Adapter Core Concepts](../developer-guide/adapters/core-concepts.md).

## Session Inbox Configuration (transcript)

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| enabled | boolean | true | Whether to automatically record incoming/outgoing messages (after disabling, history can still be queried) |
| max_per_session | int | 50 | Number of entries retained per session (0 = disable session trimming) |
| ttl_hours | float | 168.0 | Global retention duration (hours, 0 = never clean up) |
| self_echo | string | bot | Incoming bot echo (if `self.user_id == user_id`, such as OneBot `report-self-message`) handling: `bot` = record as bot and mark `meta.self_echo`; `skip` = do not record; `user` = record as user (old behavior) |

> The risks and audits of retention policies are detailed in [Session Inbox](../advanced/transcript.md); attribution fields (`sender` / `meta`) and outbound ownership (`meta.module`) are also detailed in that document.

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| language | string | auto | The display language for framework-built-in text. Set to `auto` to automatically detect the system language, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

## Module Configuration

Each module can define its own configuration in the configuration file:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

In the module, read and write configuration:

```python
from ErisPulse import sdk

# Read configuration
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# Write configuration at runtime (delayed save)
sdk.config.setConfig("MyModule.timeout", 60)

# Save immediately to file
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` defaults to delayed writing (about every 5 seconds batched to file), set `immediate=True` to save immediately. Configuration changes trigger the `config.set` lifecycle event.

## Scope Configuration (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope declares "**within what range it takes effect**" — which modules are available in a platform/Bot/session (① module dimension), which events are received by a user/group/Bot/adapter (② identity dimension), and which outbound calls a module can initiate (③ outbound dimension):

```toml
[ErisPulse.scope]
default_allow = true        # Global default (false = implicit deny strict mode; does not affect outbound dimension)
cache_size = 1024           # LRU cache size

# ① Module dimension (priority: session > Bot > platform; entries support exact / glob / re: regex)
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# Sub-level binding with merge = true merges with lower priority entries (default is overall overwrite)
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② Identity dimension (priority: user > session > Bot > adapter; each level only allows or denies one)
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # All events of this platform are discarded at the entry
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ③ Outbound dimension (default allows all; rules are inline tables, entries support exact / glob / re: regex)
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # Deny all sending
api = { allow = ["get_*"] }               # Allow only standard query APIs
request = { deny = true }                 # Deny request handling
```

| Configuration Item | Type | Description |
|---------|------|------|
| `scope.default_allow` | boolean | Global default: allow/deny for modules/identity not matched by rules (`true`) |
| `scope.cache_size` | integer | LRU cache size (default 1024) |
| `scope.platforms / bots / sessions` | table | ① Module three-level binding: `{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② Identity four-level binding: `{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ Outbound rules: `{allow=[...], deny=true|[...]}` (actions are send / api / request) |

> Detailed explanation and runtime API (dimensional `sdk.scope.set_module()` / `set_identity()` / `set_action()`, determination `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`, and dictionary-style fallback `get()` / `set()` / `delete()`) are available in [Scope (scope)](../advanced/scope.md).

## Unified Event Override Configuration (event.overrides)

Unified override system: Override behavior of any module processor by **event type** without modifying module code. OneBot12 standard types (meta / message / notice / request) and extended types (command) each have their own overridable parameters:

```toml
[ErisPulse.event.overrides]

# message: text trigger conditions (AND with code-level conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta: detail_type whitelist (entries support exact / glob / re: regex)
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command (extended type): implement parameter override (user priority; disable via acl deny)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # Override to only allow framework master (false opens developer's master restriction)
hidden = true               # Hide in help list
aliases = ["rs"]            # Effective alias

# acl (command exclusive): user whitelist/blacklist for commands (command names support glob / re: regex, exact keys take precedence)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL default: allow (true) / strictly deny (false) commands without ACL configuration
acl_default_allow = true
```

| Configuration Item | Type | Description |
|---------|------|------|
| `event.overrides.message.<module>` | table | Text condition: `{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | Module-level parameter override (scalar flags like `hidden = true`) |
| `event.overrides.command.<module>.<command>` | table | Command-level override (command-level takes precedence) |
| `event.overrides.acl.<command name>` | table | User whitelist/blacklist: `{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL default: allow commands without ACL configuration (true) / strictly deny (false) |

> Runtime API (after `from ErisPulse.Core.Event import overrides`, call `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` by type sub-namespace, or access via `sdk.Event.overrides`) is available in [Event Handling Introduction · Event Override](../getting-started/event-handling.md#event-override-does-not-modify-module-code-to-override-the-behavior-of-any-event-type).

## Next Steps

- **Continue following the L1 path**: Next article [Exception Handling](../advanced/errors.md), learn how to write error handling that does not crash the framework
- **Don't want to write TOML manually**: Use `epsdk config` interactive wizard to fill in declarative configuration items, see [CLI Commands Reference · config](cli-reference.md#config)
- **Don't want to modify configuration file during deployment**: Use environment variables to override configuration items, combined with the [Deployment Guide](deployment.md) for Docker usage