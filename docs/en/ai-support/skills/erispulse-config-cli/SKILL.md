---
name: erispulse-config-cli
description: "适用于：配置声明式 schema、排查配置问题、使用 epsdk 命令行与部署。覆盖场景：- Connection parameters need to be restarted after changes; transient connection pool creation failures will automatically retry with exponential backoff。When you forget the parameters of a `epsdk` command, want to script component management, or need to control the behavior of `run` / `stop` / `restart`, consult this section. For daily use of just `init` / `install` / `run`, remember one thing: `epsdk <command> --help` always provides parameter descriptions, so you don't need to read this entire document.。Read this when you need to choose an installation method (pip / uv / Docker / ErisPulse-App client) or troubleshoot a failed installation. If you just want to get up and running as quickly as possible, the [5-Minute Quick Start](../quick-start.md) already covers the simplest process — skip this page if that's all you need.。When the bot needs to run long-term—Docker deployment, systemd / Supervisor process supervision, reverse proxy and SSL, backup and upgrade ..."
---

# ErisPulse 配置系统与 CLI 工具链

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 配置系统

> 来源: `docs/en/user-guide/configuration.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/user-guide/configuration.md）

# Configuration File Guide

> [!NOTE]
> **L1 Core Required Reading** — One of the five core documents in the "Reading Path" on the homepage, essential for module development.

> This document covers the framework's own configuration file `config/config.toml`: what each configuration section controls, which ones support hot-reloading, and how to override them with environment variables. For configuration options of third-party modules, please refer to each module's own documentation.

ErisPulse uses the TOML-format configuration file `config/config.toml` to manage project configuration.

## Configuration File Location

The configuration file is located in the `config/` folder at the project root:

```
project/
├── config/
│   └── config.toml
├── main.py
```

### Multi-Instance Notes and Lock Files

When the framework starts, it creates a `config.lock` lock file in the runtime status directory **`.erispulse/`** at the project root and holds it until the process exits (used to detect multiple instances sharing the configuration directory; prior to version 2.10, the `.erispulse_config.lock` file located in the `config/` directory will be automatically cleared during the first startup after an upgrade). If the log shows the warning "Detected that the configuration file may be in use by another ErisPulse instance," it means that **two or more ErisPulse processes are writing to the same configuration file** (typical scenario: multiple containers mounted with the same host `config/` directory) — concurrent writes will overwrite each other. Please use separate configuration directories for each instance.

### Sensitive Configuration Not Stored in Repository

The configuration file contains sensitive information such as tokens (token / API key): the framework initialization and `epsdk init` will automatically generate a `.gitignore` file in the `config/` directory (with a single line `*` — **all files in the directory are excluded from version control, and the ignore file itself is also excluded**); existing `.gitignore` files will not be overwritten. The `.erispulse/` runtime status directory (instance lock, CLI runtime status files) is considered local machine state, and the project template's `.gitignore` already defaults to ignoring it.

## Configuration Loading Error Handling

When loading `config.toml`, the framework distinguishes three error states and provides **actionable diagnostic information** instead of silently falling back to default configurations:

| Error State | Trigger Condition | Framework Behavior |
|---------|---------|---------|
| File Missing | `config.toml` does not exist | On normal first startup, silently use empty configuration (no warning) |
| TOML Syntax Error | File exists but format is invalid (e.g., missing quotes, unbalanced parentheses) | Output **line/column number and reason** of the error, and **retain the last valid configuration to continue running** (this file modification is not effective) |
| Permission/Other Errors | No read permission, IO errors, etc. | Output **clear reason**, and **retain the last valid configuration to continue running** |

> **Note:** "Last valid configuration" ≠ Default configuration: When a file is damaged, the framework uses the **last successfully parsed configuration from before this startup** (if the file is edited and corrupted during runtime, the old value is used), rather than resetting all configuration items to factory defaults. When troubleshooting, do not assume "the configuration has been reset."

For example, if you accidentally write the configuration as `port = 8000` (missing quotes for a string), the log will output something like:

```
[ERROR] [Config] Configuration file config/config.toml has a syntax error (line 3, column 1): ...
[WARNING] [Config] Failed to read configuration file. Continuing with the last valid configuration, this file modification is not effective — please fix and reload or restart.
```

This allows you to immediately locate the issue at the **default INFO level** instead of wondering "why my modified configuration is not effective."

> **What if you edit the configuration file while the robot is running?** If you manually edit `config.toml` during robot operation and introduce a syntax error, the framework will output "Configuration file has been damaged (syntax error, line X), unable to merge and write — please fix the configuration file and restart" when it next writes (merges configuration), rather than a confusing "write failed." The configuration items to be written are retained and not lost.

## Comment Retention and Minimal Disk Write

**Comments and key order in config.toml are fully retained after framework write:** Whether through code `setConfig()`, CLI configuration wizard save, or adapter/module first-generation configuration template, the framework only modifies the involved keys. Your comments and sorted order are not erased or rearranged (based on the tomlclass lossless TOML engine, untouched content is preserved byte-for-byte, and the original CRLF/LF line endings are not changed).

The framework maintains restraint over disk-written content:

- **Framework default configuration is not automatically written to disk:** `gc`, `scope`, `transcript`, etc. built-in defaults only reside in memory; config.toml only contains keys you explicitly set, keeping it minimal. Refer to `config/config.full.example` in the project for a complete list of configurable items. Copy and modify as needed (unconfigured items always follow built-in defaults, behavior unchanged).
- **`config.full.example` is automatically maintained:** Regardless of whether `epsdk init` has been executed, as long as the framework starts (via `epsdk run` / `main.py`), `config/config.full.example` will be automatically generated if missing. The first line is a framework-maintained marker; if the generator content is updated (e.g., new configuration items, newly installed components), it will refresh once on startup. If the first line is deleted or modified, it switches to manual management, and the framework will no longer overwrite.
- **Adapter/Module Configuration Templates:** On first initialization, a template with comments is written to disk (field descriptions are comments); fields marked as `example` do not write to disk, only recorded in `config.full.example` for reference.
- **Declarative Comments Readback:** Comments in the configuration file are documentation itself — `ep doctor` and configuration validation failure messages will reference the original comments of the field in the file (even if you manually modified the comments, the message follows the current file state), so you don't need to refer back to the documentation to find the field meaning when reporting errors.

## Environment Variable Override

The framework supports overriding `ErisPulse.*` configuration items using environment variables (suitable for Docker/containerized/CI deployment, without modifying `config.toml`).

Naming convention: Replace the dot-separated path `ErisPulse.<section>.<key>` with all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

Behavior description:
- **Highest Priority:** Environment variables override "configuration file" and "default values," automatically converting to the original value type (bool / int / float / comma-separated list / string).
- **Not Persistent:** The override is only effective during runtime and is not written back to `config.toml`.
- **Supports Hot Update:** After modifying the environment variable during runtime, combined with configuration listening reload, it can take effect.

```bash
# Docker deployment example: Do not modify config.toml, directly override the port
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: `ErisPulse.server.port` and other framework configurations accessed via `get_server_config()` and similar APIs are affected by environment variable overrides.

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

- **Priority:** Environment variable > `config.toml` > declared default value (the priority remains the same after configuration file hot update).
- **Type Conversion:** The environment variable value is automatically converted according to the field annotation — `str` is original, `int` / `float` / `bool` (`true` / `1` / `yes` / `on`) is automatically converted, `list` / `dict` is parsed via JSON; if conversion fails, the override is ignored (fall back to configuration file / default value) and a warning is output.
- **Declare Once, Use Everywhere:** Configuration reading, hot update, and validation use the same pipeline; the configuration panel Schema will mark the `env` name, and the `config.toml` template comments will also prompt available environment variables (the template does not write the actual value of the environment variable to avoid leaks).
- **Fully Compatible:** Fields without `env` declaration behave unchanged; `ConfigClass` instantiated directly (without framework configuration pipeline) is not affected by environment variables.

```bash
# Docker deployment example: Do not modify config.toml, directly inject module key
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **Configuration Class vs Model Field:** The configuration class manages "how the module operates" (behavior parameters, hot update), while ORM's `Field()` manages "what data the user generated" (database table, query). Both share the same constraint vocabulary and validator engine; the comparison table is available at [Data Model Layer · When to Use Which Declaration](../developer-guide/orm.md#when-to-use-which-declaration).

## Configuration Hot Update

Since version 2.7.0, the framework has provided **systematic support for configuration hot updates**. After external modification of `config.toml` (detected every 5 seconds by the background watcher), or code calls `setConfig()`, components automatically respond:

| Component | Hot-updated Configuration | Behavior |
|------|----------------|------|
| **Logger** | `logger.level` / `log_files` / `log_dir` (including segmentation parameters) / `memory_limit` / `format` / `exclude_levels` | Automatically reapplies (with change detection) |
| **Command System** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter Concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphore, rebuilds according to new value |
| **Active GC** | `framework.proactive_gc_*` | Configuration change immediately restarts GC task, supports runtime adjustment/disable/re-enable |
| **Master System** | `master.users` | `is_master()` checks are read in real-time each time, no restart needed |
| **Module/Adapter Configuration** | Their respective configuration items | Triggers `on_config_update(old, new)` callback |

**Configurations that require restart** (cannot be safely hot-switched, warnings are output when changed "restart process to take effect"):

| Configuration | Reason |
|------|------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely hot-switched at runtime |
| `storage.use_global_db` | SQLite file handle is already open at runtime, switching paths is unsafe |

> **What if editing and saving goes wrong midway?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, instead of broadcasting an empty configuration to all components (avoiding `on_config_update` receiving empty values and mistakenly reverting to default).

### Internal Breakdown of Hot Update Chain

"How do components know when the configuration is changed?" — Behind this is a detection → reload → broadcast chain:

```mermaid
flowchart TD
    A["External edit of config.toml"] --> B{"Who detects first?"}
    B -->|"Background watcher thread<br/>Polls mtime every 5 seconds"| C["_check_file_change determines change"]
    B -->|"When reading configuration<br/>Cache exceeds 60 seconds"| C
    C --> D["_load_config re-parses TOML"]
    D --> E{"Parsing successful?"}
    E -->|"No (syntax error)"| F["Retain last valid configuration<br/>Do not broadcast, output diagnostic logs"]
    E -->|"Yes"| G["lifecycle.emit config.updated<br/>Carrying old_config / new_config"]
    G --> H["Component listeners respond<br/>(logger / scope / command / GC ... )"]
```

**Two detection paths** (either one is sufficient, both provide fallback):

| Path | Mechanism | Trigger Timing |
|------|------|---------|
| Background watcher | Daemon thread `config-watcher` polls file `mtime` every **5 seconds** | Maximum of 5 seconds after external file edit |
| Lazy detection | Any `getConfig()` read, if cache exceeds **60 seconds** then checks file first | Next time configuration is read |

> **The framework will not harm itself:** When `setConfig()` writes to disk, it records the "mtime written by itself," and the watcher excludes it when comparing, only treating **external edits** as changes.

**Two types of configuration change events:**

| Event | Trigger | Data | Typical Scenario |
|------|--------|------|---------|
| `config.set` | Code / Dashboard calls `setConfig()` | `{key, old_value, new_value}` | Single key write (template generation, status recording, runtime configuration change) |
| `config.updated` | External edit detected by watcher/lazy detection | `{old_config, new_config, config_file}` | Manual edit of `config.toml` |

> `setConfig()` defaults to **delayed writing to disk after 5 seconds** (merges multiple writes), `immediate=True` writes immediately. The watcher detects external modifications and only updates the in-memory cache, **does not** write the external changes back to the file.

**List of automatic responders** (both event types are usually subscribed to, response content is consistent):

| Component | Listener | Response |
|------|------|------|
| Logger | `config.set` + `config.updated` | Reapplies level/file/directory segmentation/memory limit/format/exclude levels (with change detection, no change means no action) |
| Scope | `config.updated` | Rebuilds scope binding cache |
| Command System | `config.updated` | Refreshes prefix/case sensitivity/space prefix/must_at_bot parsing parameters, takes effect on the next message |
| Adapter Concurrency | `config.set` + `config.updated` | Invalidates and rebuilds signal for `handler_max_concurrency` |
| Active GC | `config.set` + `config.updated` | Immediately restarts the GC background task |
| Adapter | Route to `on_config_update` | Each adapter's `on_config_update(old, new)` callback |
| Module | Route to `on_config_update` | Each module's `on_config_update(old, new)` callback |
| Storage | `config.updated` | `use_global_db` change only **warns** (requires restart) |
| Router | `config.updated` | `cors.*` / `security.*` change only **warns** (requires restart) |

## Configuration Reading and Deletion API

### getAllConfig: Full Configuration Snapshot

Instead of directly reading private `_cache` (external reading of private attributes is not protected by version compatibility):

```python
config = sdk.config.getAllConfig()     # Deep copy snapshot, in-place modification does not affect framework state
config["ErisPulse"]["server"]["port"]
```

The view口径 is consistent with `getConfig`: Unwritten `setConfig` / `delete` are reflected, and it strictly matches the content after delayed disk write.

### delConfig: Delete Configuration Key

`setConfig(key, None)` only clears the value, the key remains in the file; `delConfig` removes the key from the file:

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # Delayed write
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # Immediate write
```

- Supports dot-separated paths; returns `False` if the key does not exist
- Disk write follows the comment retention path, the rest of the file content and order are unaffected
- Reuses `config.set` event broadcast (`new_value=None`): Existing listeners of adapters/modules zero change to perceive deletion

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
#   Global master (生效 on all platforms): users = ["123456", "789012"]
#   Specify master by platform: users = { yunhu = ["123456"], telegram = ["789012"] }
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
# For container / no file mounting scenarios, PEM content can be inlined (prioritized over certfile/keyfile paths)
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
| ssl_cert | string | empty | **Inlined PEM certificate content** (not a path). When used together with `ssl_key`, it prioritizes over `ssl_certfile`/`ssl_keyfile` paths; the framework temporarily writes and builds the SSL context, then immediately deletes the temporary file |
| ssl_key | string | empty | **Inlined PEM private key content** (not a path), same semantics as above |

> **Port occupation is not a fatal error**: If the framework detects that the `port` is already occupied at startup, it will skip routing server startup and issue a warning, **adapters and modules will still run normally** (only HTTP/WS/SSE routing and WebUI are unavailable). When troubleshooting "the robot can run but the WebUI cannot open," first confirm the port.

## Master System Configuration

The master system is used to identify the "master account" of the framework (such as the Bot administrator). `master.users` supports two writing methods:

```toml
[ErisPulse.master]
# Writing method one: Global master (生效 on all platforms)
users = ["123456", "789012"]

# Writing method two: Specify master by platform (dict)
# users = { yunhu = ["123456"], telegram = ["789012"] }
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| users | array / object | empty | List of master account IDs. `list` form is global master (生效 on all platforms); `dict` form specifies by platform (key is platform name, value is a list of master account IDs for that platform) |

In code, check using `master.is_master(event)` or `master.is_master(platform, user_id)`, each call reads the configuration in real time (supports hot updates, no restart needed):

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("Hello, master")
```

### Master Determination Chain and Runtime Add/Delete

The master determination chain is **configuration master → runtime record → provider chain**:

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Runtime addition (default persistent; persist=False only in memory)
master.remove("yunhu", "123")                # Removal (default persistent)
master.list()                                # Aggregation: {"global": [...], "<platform>": [...]}
```

### Custom Identity Source (provider)

In addition to configuration, you can register a custom identity source: `fn(platform, user_id) -> bool`, and if the built-in identity sources (configuration + runtime record) do not match, they are tried in sequence, and if any provider allows it, it is recognized as a master. Suitable for connecting to adapter administrator interfaces, database roles, and other external identity systems.

The registration entry `master.provider` supports both decorator and function-style writing, and unregistration is done through the unregistered function: `fn.unregister()`:

```python
from ErisPulse.Core import master

# Writing method one: Decorator (persistent identity source, recommended)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Writing method two: Function-style (register during module load / unregister during unload)
fn = master.provider(admin_provider)
fn.unregister()
```

> Provider exceptions are caught and skipped, not blocking the identity determination chain. Binding instance methods cannot attach `unregister`, and for scenarios requiring registration/unregistration pairing, use a **module-level function**.

### User Priority: Master Scope Controlled by User

The `master=True` of a command is only the **developer's default**: The user can override and tighten or loosen it in `ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false` (see [Unified Event Override Configuration](#unified-event-override-configurationeventoverrides), where the user's explicit configuration takes effect).

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # Explicit list of log files (mutually exclusive with log_dir, higher priority)
log_dir = ""                  # Log directory (automatic segment rotation enabled)
log_rotation = "size"         # Segmenting method: "size" / "date" / "none"
log_max_size_mb = 10          # Maximum single file size limit in MB for size mode
log_backup_count = 5          # Number of historical log files to retain
log_rotation_when = "midnight"  # Rotation period for date mode: S/M/H/D/midnight
memory_limit = 1000             # Maximum number of log entries per module in memory (0 = disable memory log copy)
total_memory_limit = 5000       # Total memory log entries limit for all modules (0 = unlimited)
exclude_levels = ["EVENT"]
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| level | string | INFO | Logging level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed internal debugging information) |
| format | string | rich | Logging output format: `rich` (colored, default), `plain` (plain text without color, suitable for log collection/pipeline redirection), `json` (JSON structured, suitable for ELK, etc.) |
| log_files | array | empty | List of log output files (explicit paths, no segmentation) |
| log_dir | string | empty | Log output directory (automatically created). When set, logs are written into `erispulse.log` inside the directory and automatically segmented based on `log_rotation`; mutually exclusive with `log_files`, `log_files` has higher priority |
| log_rotation | string | size | Segmenting method: `size` (by size) / `date` (by date) / `none` (no segmentation) |
| log_max_size_mb | float | 10 | Maximum file size limit in MB for size mode; files are rotated to `.1`/`.2` backups when exceeded |
| log_backup_count | integer | 5 | Number of historical log files to retain; oldest backups beyond this limit are automatically deleted |
| log_rotation_when | string | midnight | Rotation period for date mode: `S`/`M`/`H`/`D`/`midnight` (default is midnight each day) |
| memory_limit | integer | 1000 | Number of log entries saved in memory per module; `0` means disable memory log copies (no longer write to memory, existing records are retained) |
| total_memory_limit | integer | 5000 | Total memory log entries limit for all modules; `0` means unlimited. When exceeded, oldest records are discarded according to the rotation strategy (prioritizing modules with the most entries), independent of the single module `memory_limit` |
| exclude_levels | array | empty | Excluded log levels. Logs of excluded levels are **completely discarded** (not written to memory, not pushed to Dashboard or other subscribers, not printed, not written to file). Supports hot updates |

You can also dynamically switch in code:

```python
from ErisPulse.Core import logger

# Segment by size: 10MB per file, retain 5 copies
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# Segment by date: rotate at midnight daily, retain 7 copies
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` and related segmentation configurations require ErisPulse **2.8.0+**.

> **Privacy Protection**: Message sending and receiving content is logged at the **EVENT level** (value 21). Setting `exclude_levels = ["EVENT"]` prevents the backend (such as the Dashboard log panel) from seeing message content in groups/private chats, while not affecting logs of other levels.

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
| uninit_timeout | integer | 30 | Total timeout (seconds) for graceful shutdown; if exceeded, termination is forced. 0 means no timeout is set |
| strict_mode | integer | 0 | Strict mode level; see the "Strict Mode" section below |
| handler_max_concurrency | integer | 64 | Maximum concurrent Task count for event handlers; increasing this value improves throughput but increases memory usage |
| handler_queue_max_pending | integer | 4096 | Backpressure for event burst: the maximum number of pending handler Tasks per platform. If exceeded, new event handler Tasks are discarded and a WARNING is logged (the discard count can be checked in troubleshoot). `0` means unlimited |
| offline_bot_expiry | integer | 3600 | Automatic expiration time (seconds) for offline Bot records; 0 means no expiration |
| plugins_dir | string / list | "plugins" | Local plugin folder (relative to project root); changes to plugin files (addition, deletion, modification) are automatically discovered by the hot-reload watcher |
| watch_ignore_dirs | list | Built-in list | Directories to ignore in hot-reload file monitoring (e.g., `.venv`, `.git`, `__pycache__`); a non-empty list **replaces** the built-in list entirely; `[]` means no directories are ignored |
| watch_include_plugin_dirs | boolean | true | Whether `epsdk run --reload` should hand over plugin directories to the plugin hot-reload watcher for precise handling (single-module reload) and exclude them from full monitoring |

### Proactive GC Configuration

After SDK initialization, a background task for proactive garbage collection (GC) is started, periodically executing Python GC and internal resource cleanup (such as offline Bot cleanup). All parameters support hot updates, and the task is restarted immediately when changes occur.

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | Recycle interval (seconds), supports decimals. 0 means proactive GC is disabled |
| proactive_gc_generation | integer | 0 | Regular round of generation recycling (0/1/2, clamped to 0..2). Note that `gc.collect(2)` is equivalent to full recycling; the default of 0 keeps it lightweight. Deep recycling is triggered periodically by `proactive_gc_full_every` |
| proactive_gc_full_every | integer | 20 | Perform a full recycling every N rounds; 0 means periodic full recycling is disabled. Full recycling is constrained by the `proactive_gc_memory_growth_mb` threshold |
| proactive_gc_memory_growth_mb | integer | 32 | Full recycling memory growth threshold (MB): compared to the memory baseline after the last full recycling (preferring tracemalloc, then RSS), full recycling is only performed if the growth reaches this value. 0 means no threshold is set |
| proactive_gc_idle_only | boolean | false | When enabled, skip Python GC during event bursts (when there are unfinished pending handlers) to avoid pauses and message processing competition; internal resource recycling is unaffected |
| proactive_gc_gen0_min | integer | 500 | Minimum garbage amount for triggering regular round recycling of gen0: if `gc.get_count()[0]` is below this value, the round is skipped directly (near-zero overhead for empty rounds). 0 means recycling is always performed |

> **Change in 2.7.1**: The default `proactive_gc_generation` is adjusted from `2` to `0`, and the default `proactive_gc_full_every` is adjusted from `0` to `20`. Previously, `generation=2` meant that every round performed the heaviest full recycling; the new default maintains recycling coverage while significantly reducing idle round overhead. Explicitly configured old values still function as intended.

### Strict Mode

Strict mode controls the handling strategy for modules/adapters that are non-compliant or fail during the loading phase. Modern modules/adapters should inherit corresponding base classes (`BaseModule`/`BaseAdapter`); components that do not inherit base classes affect the framework's context system and fallback cleanup, potentially leading to resource leaks.

> **Change in 2.5.2**: The default level is adjusted from `1` (skip) to `0` (lenient) to reduce loading issues for new users. Components that do not inherit base classes will be warned and still attempted to load, rather than directly rejected. To restore the old behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (default) | Violations only issue warnings; components that do not inherit base classes will still be attempted to load (compatible with old components) |
| 1 | Strict-Skip | Reject components that do not inherit base classes and skip them; other components start normally |
| 2 | Strict-Fatal | Collect all violations and report them together, then terminate the entire startup process |

In all levels, component crashes during the loading/registration/initialization phase are always skipped; the differences are as follows:

- **0 → 1**: The only behavioral change is that components that do not inherit base classes change from "still loaded" to "skipped".
- **1 → 2**: All violations (not inheriting base classes, loading failure, registration failure, initialization failure, etc.) are upgraded to fatal, and a violation list is output together at the startup checkpoint before terminating.

#### Exception List

If certain components cannot be migrated temporarily (e.g., old modules they depend on), they can be added to the exception list. Components listed here will be treated as if in lenient mode, even if they are non-compliant, and continue to be loaded:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly indicate how to restore loading (add to the exception list or lower the level).

#### Integration with CLI

The pre-start self-check of `epsdk run` (configuration file parseability, completeness of required component configurations) follows this configuration by default: if not 0, startup is refused if the check fails; if 0, warnings are issued and startup continues. It can also be temporarily switched without changing the configuration: `epsdk run --strict` enables both self-check and strict level for this run (the level only increases, propagated to the running process via the `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable), and `--no-strict` temporarily lowers it to lenient and only issues warnings.

## Storage Configuration

Since version 2.8.0, the storage engine supports three asynchronous backends, with **completely consistent APIs and one-click configuration switching**:

| Backend | Driver | Installation | Characteristics |
|------|------|------|------|
| SQLite (Default) | aiosqlite | Ready-to-use out of the box | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Existing MySQL infrastructure, multi-instance sharing |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transaction capability, high concurrency |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # Only for SQLite: Use the global database in the package data/config.db instead of a project-specific database

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
| backend | string | sqlite | Storage backend: `sqlite` / `mysql` / `postgres`, zero code change when switching |
| use_global_db | boolean | false | Only for SQLite: Whether to use the global database in the package rather than a project-specific database |
| storage.mysql.* | table | See above | MySQL connection parameters (host / port / user / password / database / charset / pool) |
| storage.postgres.* | table | See above | PostgreSQL connection parameters (host / port / user / password / database / pool) |

Environment variables are also supported for overriding (Docker / 12-factor): `ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`.

> [!TIP]
> - Connection parameters need to be restarted after changes; transient connection pool creation failures will automatically retry with exponential backoff
> - Use a verification script to self-check before switching backends: `python tests/devs/test_storage_backend_verify.py --backend mysql`
> - For details on transactions, dialect differences, and custom backends, see [Storage Backends](../advanced/storage-backends.md)

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
| allow_space_prefix | boolean | false | Whether to allow space as a prefix |
| must_at_bot | boolean | false | Whether to require @ bot to trigger the command (private chat is not restricted) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| ignore_self | boolean | true | Whether to ignore the robot's own messages |

## Transcript Inbox Configuration

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| Configuration | Type | Default | Description |
|---------------|------|---------|-------------|
| enabled | boolean | true | Whether to automatically record inbound/outbound messages (disabling stops writing, but historical data remains queryable) |
| max_per_session | int | 50 | Number of entries to retain per session (0 = disable session trimming) |
| ttl_hours | float | 168.0 | Global retention duration (in hours, 0 = never clean up) |
| self_echo | string | "bot" | Inbound bot echo handling (when `self.user_id == user_id`, e.g., OneBot `report-self-message`):<br>`bot` = record as bot and mark `meta.self_echo`;<br>`skip` = do not record;<br>`user` = record as user (old behavior) |

> See [Transcript Inbox](../advanced/transcript.md) for risk and audit information about retention policies; attribution fields (`sender` / `meta`) and outbound attribution (`meta.module`) are also described in that document.

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| language | string | auto | The display language for the framework's built-in text. Set to `auto` to automatically detect the system language, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

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

# Immediately save to file
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` uses delayed writing by default (about every 5 seconds batch save to file), set `immediate=True` to persist immediately. Configuration changes trigger the `config.set` lifecycle event.

## Scope Configuration (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scope declares "what scope it applies to" — which modules are available in what platform / Bot / session (① module dimension), which events are received in what user / group / Bot / adapter (② identity dimension), and which outbound calls a module can initiate (③ outbound dimension):

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit deny strict mode; does not affect outbound dimension)
cache_size = 1024           # LRU cache size

# ① Module dimension (priority: session > Bot > platform; entries support exact / glob / re: regex)
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# Sub-level binding with merge = true merges each entry with lower priority (default overall override)
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② Identity dimension (priority: user > session > Bot > adapter; only allow or deny one per level)
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # Discard all events from this platform at the entry point
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ③ Outbound dimension (default all allowed; rules are inline tables, entries support exact / glob / re: regex)
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # Completely deny sending
api = { allow = ["get_*"] }               # Only allow standard query APIs
request = { deny = true }                 # Deny processing requests
```

| Configuration Item | Type | Description |
|---------|------|------|
| `scope.default_allow` | boolean | Global fallback: Allow or deny for modules/identity not matched by rules (`true`) |
| `scope.cache_size` | integer | LRU cache size (default 1024) |
| `scope.platforms / bots / sessions` | table | ① Module three-level binding: `{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② Identity four-level binding: `{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ Outbound rules: `{allow=[...], deny=true|[...]}` (actions are send / api / request) |

> Detailed explanation and runtime API (dimensional `sdk.scope.set_module()` / `set_identity()` / `set_action()`, determination `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`, and dictionary-style fallback `get()` / `set()` / `delete()`) are available at [Scope (scope)](../advanced/scope.md).

## Unified Event Override Configuration (event.overrides)

Unified override system: Overwrite behavior of any module handler by **event type** without modifying module code. OneBot12 standard types (meta / message / notice / request) and extension types (command) each have their own configurable parameters:

```toml
[ErisPulse.event.overrides]

# message: Text trigger conditions (AND with code-side conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice / request / meta: detail_type whitelist (entries support exact / glob / re: regex)
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command (extension type): Overwrite command parameters (user priority; disable via acl deny)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # Overwrite to only allow framework master (false opens developer's master restriction)
hidden = true               # Hide in help list
aliases = ["rs"]            # Effective alias

# acl (command-specific): User allow/deny lists (command names support glob / re: regex, exact keys have priority)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL fallback: Allow (true) or strictly deny (false) commands without ACL configuration
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
| `event.overrides.acl_default_allow` | boolean | ACL fallback: Allow (true) or strictly deny (false) commands without ACL configuration |

> Runtime API (after `from ErisPulse.Core.Event import overrides`, call sub-namespace methods like `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()` or access via `sdk.Event.overrides`) is available at [Event Handling Introduction · Event Override](../getting-started/event-handling.md#event-override-no-modify-module-code-overwrite-behavior-of-any-event-type).

## CLI 参考

> 来源: `docs/en/user-guide/cli-reference.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/user-guide/cli-reference.md）

# CLI Command Reference

> [!TIP]
> **When to read this**: When you forget the parameters of a `epsdk` command, want to script component management, or need to control the behavior of `run` / `stop` / `restart`, consult this section. For daily use of just `init` / `install` / `run`, remember one thing: `epsdk <command> --help` always provides parameter descriptions, so you don't need to read this entire document.

`epsdk` is ErisPulse's command-line tool: it initializes projects, installs/upgrades modules and adapters, interactively configures components, runs and stops robots, and diagnoses environments, all within a single command.

> **Tip**: The main help for `epsdk` (without a command) is grouped by category: **Project** (`init` / `create` / `run`), **Component Management** (`install` / `uninstall` / `upgrade` / `list` / `list-remote` / `types`), **Configuration and Diagnosis** (`config` / `doctor` / `i18n`), and **Others** (`self-update` / `version`).

## Package Management Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | Install modules/adapters |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | Uninstall modules/adapters |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | Upgrade specified modules or all |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | Update the SDK itself |

## Diagnostic Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | Diagnose environment and output health report; `--fix` attempts automatic repair |

### install

Installs ErisPulse modules or adapter packages. If no package name is specified, enters interactive installation interface.

**Aliases:** `i`, `add`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[package]...` | | Packages to install, can specify multiple |
| `--upgrade` | `-U` | Upgrade to the latest version during installation |
| `--pre` | | Allow installation of pre-release versions |
| `--editable` | `-e` | Install in editable mode (requires specifying path) |
| `--user` | | Install to user site-packages directory |
| `--no-deps` | | Do not install dependencies |
| `--target` | `-t` | Install to specified directory |
| `--index-url` | | Specify PyPI mirror source address |
| `--extra-index-url` | | Additional PyPI mirror source address (can be specified multiple times) |
| `--no-cache-dir` | | Disable cache |
| `--requirement` | `-r` | Install from requirements file |
| `--constraint` | `-c` | Install from constraint file |
| `--force-reinstall` | | Force reinstallation |
| `--ignore-installed` | | Ignore already installed packages |
| `--compile` | | Compile .pyc files after installation |
| `--no-compile` | | Do not compile .pyc files after installation |
| `--prefix` | | Install to specified prefix directory |
| `--src` | | Source code directory used for editable installation |
| `--config-settings` | | Pass configuration to build backend (can be specified multiple times) |
| `--no-binary` | | Restrict not to use binary packages (format like `:all:`) |
| `--only-binary` | | Restrict to use only binary packages (format like `:all:`) |
| `--prefer-binary` | | Prefer binary packages |
| `--build-isolation` | | Enable build isolation |
| `--no-build-isolation` | | Disable build isolation |
| `--upgrade-strategy` | | Upgrade strategy: `eager`, `only-if-needed`, `to-satisfy-only` |
| `--break-system-packages` | | Allow modification of system package manager managed Python packages |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Install from mirror source and upgrade
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Editable mode installation (development mode)
epsdk install -e ./my-adapter
```

### uninstall

Uninstalls installed ErisPulse modules or adapter packages. If no package name is specified, enters interactive uninstallation interface.

**Aliases:** `rm`, `remove`

**Parameters:**

| Parameter | Description |
|------|------|
| `<package>...` | Packages to uninstall, can specify multiple |
| `--no-uv` | Use pip instead of uv |

**Examples:**

```bash
# Uninstall a single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### upgrade

Upgrades installed ErisPulse components. If no package name is specified, upgrades all interactively.

**Aliases:** `up`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[package]...` | | Packages to upgrade, can specify multiple |
| `--force` | `-f` | Force upgrade, skip confirmation |
| `--pre` | | Allow upgrade to pre-release versions |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Upgrade all packages
epsdk upgrade

# Upgrade specified package
epsdk upgrade Weather

# Force upgrade (skip confirmation)
epsdk upgrade -f
```

### self-update

Updates the ErisPulse SDK to the latest version.

**Aliases:** `su`, `update`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[version]` | | Target version number to update to |
| `--pre` | | Allow update to pre-release version |
| `--force` | `-f` | Force update, skip confirmation |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Update to the latest stable version
epsdk self-update

# Update to a specified version
epsdk self-update 1.2.3

# Allow pre-release version
epsdk self-update --pre

# Force update
epsdk self-update -f
```

> [!NOTE]
> When installed via `uv tool install ErisPulse`, this command automatically switches to `uv tool upgrade ErisPulse` (if version is specified, it becomes `uv tool install ErisPulse==<version> --force`). Direct pip upgrades will have tool environment overwritten by uv’s manifest restore.
> On Windows, updates occur in a new console window: the current CLI must exit first to release file locks on tool environment, and the terminal can be reopened after the prompt completes.

---

## Information Query Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | List installed components |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | List remote available components |
| `version` | `ver` | | Display SDK and Python version information (equivalent to `-V`) |

### list

Lists installed ErisPulse modules and adapters.

**Aliases:** `l`, `ls`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--outdated` | `-o` | Only show upgradable packages |

**Examples:**

```bash
# List all installed components
epsdk list

# Only list modules
epsdk list -t modules

# Only list adapters
epsdk list -t adapters

# Only show upgradable packages
epsdk list -o
```

### list-remote

Lists ErisPulse modules and adapters available in the remote repository.

**Aliases:** `lsr`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--refresh` | `-r` | Force refresh remote package list cache |

**Examples:**

```bash
# List all remote available components
epsdk list-remote

# Only list remote modules
epsdk list-remote -t modules

# Force refresh cache and list
epsdk list-remote -r
```

---

## Configuration Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | Interactive configuration of adapter/module declarative configuration items |

### config

Interactive filling of adapter/module declarative configuration items. The wizard is driven by the adapter/module declared configuration class (`ConfigClass` / `AccountConfigClass`), automatically generating forms and validating, without manually writing `config.toml`.

Adapters additionally support multi-account (bot account) management: add/edit/delete accounts, and enable/disable switches.

**Aliases:** `cfg`, `conf`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[name]` | | Target name (adapter platform name or module name), leave empty to enter interactive selection |
| `--list` | `-l` | Only list configuration status of all targets, do not enter wizard |
| `--json` | | Output configuration status of all targets in JSON format (for CI / script consumption), do not enter wizard |

**Examples:**

```bash
# View configuration status of all adapters/modules
epsdk config --list

# Output configuration status in JSON format (for CI / script consumption)
epsdk config --json

# Interactive selection of target for configuration
epsdk config

# Directly configure specified adapter
epsdk config yunhu

# Directly configure specified module
epsdk config MyModule
```

**Explanation:**

- Configuration status is divided into four levels: `Ready` (validation passed), `Incomplete` (missing or validation failed required fields), `Not Configured` (never generated), `No Configuration` (target did not declare configuration class)
- Field values are marked with source information: existing configurations show `（Current: value）`, unconfigured fields show schema default value `（Default: value）`; pressing Enter retains the value
- Secret-type fields (declared `secret`) do not echo input, pressing Enter retains the set value
- In interactive selection mode, after completing a single wizard, it returns to the selection menu (status refreshed), allowing continuous configuration of multiple targets, leaving empty to exit
- Global form validation fails and re-entry is abandoned, this wizard terminates and does not write any configuration (to avoid generating "enabled but incomplete configuration" semi-finished states)
- After saving, immediately writes to `config/config.toml`, visible in Dashboard and running SDK; running adapters need to restart the process to apply new account configurations
- `epsdk install` (interactive installation) and `epsdk init` after successful adapter installation, if configuration declaration is detected, automatically guides into this wizard; command-line direct package installation only prints configuration prompt

---

## Control Commands

> [!TIP]
> `epsdk run` will automatically detect and use the `.venv` virtual environment in the project directory to run the robot
> (the interpreter can also be explicitly specified via the `ERISPULSE_PYTHON` environment variable). `epsdk install` /
> `uninstall` / `upgrade` / `list` also act on the project's virtual environment.

| Command | Alias | Parameters | Description |
|---------|-------|------------|-------------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | Run a specified script or SDK |
| `stop` | — | `[--force] [--pid PID]` | Stop a running instance (started by `epsdk run`) |
| `restart` | — | `[--force] [--pid PID]` | Restart a running instance (stop and restart with original parameters) |

### run

Run an ErisPulse project script or directly start the SDK. Hot-reload mode is supported.

**Alias:** `r`

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `[script]` | The script file to run; if unspecified, run the SDK |
| `--reload` | Enable hot-reload mode, monitoring file changes to automatically trigger component-level code hot-reload (linked with the hot-reload system, no full process restart required) |
| `--strict` / `--no-strict` | Temporarily enable/disable strict mode (effective only for this run, not written to configuration); defaults to follow `ErisPulse.framework.strict_mode` |

**Examples:**

```bash
# Directly run the SDK
epsdk run

# Run a specified script file
epsdk run main.py

# Run with hot-reload mode (automatic code-level hot-reload triggered on file changes)
epsdk run main.py --reload

# SDK hot-reload mode
epsdk run --reload

# Temporary strict mode: exit if pre-check fails before startup, framework strict level temporarily raised to at least 1 for this run
epsdk run main.py --strict

# Temporary relaxed mode (strict_mode is enabled in configuration but want to run this time)
epsdk run main.py --no-strict
```

**Pre-start self-check:** Before `run` starts, the system quickly checks the parseability of `config/config.toml` and the completeness of required configurations for installed components. The strictness defaults to follow `ErisPulse.framework.strict_mode` (if non-zero, check failure results in exit; if zero, only a warning is issued and continues). Missing configuration files are considered normal for first-time startup, only a prompt is issued without failure evaluation. `--strict` temporarily enables: pre-check failure results in exit, and the framework strict level is temporarily raised to at least 1 (skipping non-compliant components, propagated via `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable to the running process, not written to configuration file); `--no-strict` temporarily relaxes. If self-check itself encounters an exception, it is automatically skipped, excluding network detection, and will not block startup.

### stop

Stop a running ErisPulse instance (started by `epsdk run` and executed in the same project directory).
When `run` starts, it writes the supervisor process PID, current framework subprocess PID, and the original startup command to
`.erispulse/runtime.json`. `stop` uses this to locate the instance.

**Stop sequence:** On POSIX systems, first send SIGINT to the supervisor process (same as Ctrl+C, an elegant shutdown path—
the finally chain automatically terminates the framework subprocess), escalating to SIGTERM / SIGKILL if timeout occurs; on Windows, there is no process signal semantics, so first terminate the framework subprocess and then the supervisor process (to avoid the supervisor mistakenly interpreting forced termination as a crash and restarting).

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `--force` | Skip graceful stop and directly force terminate |
| `--pid PID` | Directly specify the target process PID (overrides the runtime status file, used for non-standard startup methods) |

**Examples:**

```bash
# Stop the running instance of the current project
epsdk stop

# Force terminate
epsdk stop --force
```

### restart

Restart a running ErisPulse instance: after stopping according to the semantics of `stop`, restart using the **original startup command** recorded in the status file (foreground takes over the current terminal, and the new instance writes a new runtime status file).

**Parameters:** Same as `stop` (`--force` / `--pid PID`).

**Example:**

```bash
# Graceful restart (useful after pip upgrade of adapter/module to make code changes effective; code-level hot reload via sdk.reload_module / sdk.adapter.reload is also possible during runtime, no restart required)
epsdk restart
```

> [!NOTE]
> Startup methods such as `python main.py` that bypass `epsdk run` do not write runtime status files—processes started this way should be managed using system tools, or stopped by specifying the PID with `epsdk stop --pid <PID>`.

---

## Project Management Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | Initialize an ErisPulse project |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | Create module/adapter scaffolding; `pack` converts local plugins into publishable projects |

### init

Initialize a new ErisPulse project. Supports interactive and quick mode, generates `pyproject.toml` (dependency list) since 2.8.4, optionally creates project `.venv` virtual environment and installs framework and adapters, and supports **specifying any directory**.

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[path]` | | Target path (can include parent directory, e.g. `../apps/mybot`; pure name equivalent to `--project-name`) |
| `--project-name` | `-n` | Project name |
| `--path` | | Project parent directory (combined with `-n` to specify creation location) |
| `--adapter` | `-a` | Pre-selected adapters to install (can be passed multiple times or separated by commas), skips adapter inquiry and selection when passed |
| `--quick` | `-q` | Quick mode, skips interactive wizard (default creates `.venv` and installs dependencies) |
| `--force` | `-f` | Force overwrite existing configuration files |
| `--here` | | Initialize in current directory, do not create subdirectory |
| `--no-uv` | | Use pip instead of uv |
| `--no-venv` | | Skip virtual environment creation and dependency installation |

**Examples:**

```bash
# Interactive initialization
epsdk init

# Quick initialization (creates my_bot/ in current directory, with pyproject.toml + .venv)
epsdk init -q -n my_bot

# Quick initialization and pre-install adapters (skips interactive, for scripts / CI scenarios)
epsdk init -q -n my_bot --adapter yunhu,telegram

# Initialize in any specified directory (../apps/mybot)
epsdk init ../apps/mybot

# Combine parent directory and project name
epsdk init -n my_bot --path ../apps

# Force overwrite existing configuration
epsdk init -f

# Initialize in current directory
epsdk init --here -n my_bot

# Generate project structure only, skip virtual environment creation
epsdk init --no-venv -n my_bot
```

init output: `main.py`, `pyproject.toml` (dependency list), `config/config.toml` + `config.full.example`, `config/ssl/`, `logs/`, `.gitignore`, `README.md`; if virtual environment creation is selected, additionally generates `.venv` and installs `erispulse` and selected adapters in it.

> [!NOTE]
> `.gitignore` is a grouped template: Python bytecode and build artifacts, virtual environment and `.env`, tool cache, editor and system files, and **excludes `config/` and `logs/` runtime directories as a whole**—`config.toml` contains sensitive information such as adapter tokens, not recommended for repository; share configuration skeleton using `config.full.example`.

> [!WARNING]
> **Do not use `uv run epsdk run` to run the bot**. `uv run` creates a **one-time isolated environment** when executed in a directory without `pyproject.toml`—adapters installed via `epsdk install` in it will not persist. Please use `epsdk run` in the project directory (automatically uses project `.venv`), or activate the virtual environment first before running.

### create

Creates scaffolding for ErisPulse modules or adapters; the `pack` subcommand converts local plugins (`plugins/` directory) into publishable standard projects.

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `{module,adapter,pack}` | | Type to create: `module` / `adapter` / `pack` (plugin to project) |
| `--name` | `-n` | Project name (PascalCase) |
| `--description` | `-d` | Project description |
| `--author` | `-a` | Author name |
| `--email` | `-e` | Author email |
| `--homepage` | | Project homepage URL |
| `--output` | `-o` | Output directory (default is current directory) |
| `--force` | `-f` | Force overwrite existing directories |
| `--local` | | Create local plugin (available for `module` / `adapter`): generates `plugins/<name>/` package structure,免打包安装 (no packaging installation) |

**Examples:**

```bash
# Interactive creation (guides selection of type and filling information)
epsdk create

# Directly create Module project
epsdk create module -n MyModule

# Create local plugin (placed in project plugins/ directory, automatically discovered on startup)
epsdk create module -n MyModule --local

# Create local adapter plugin (same as above, no packaging development)
epsdk create adapter -n MyAdapter --local

# Directly create Adapter project
epsdk create adapter -n MyAdapter

# Convert local plugin to publishable project (interactive selection of plugin → complete metadata → generate standard project)
epsdk create pack

# Complete parameters
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Specify output directory
epsdk create module -n MyModule -o ./projects

# Force overwrite existing directory
epsdk create module -n MyModule -f
```

---

## Language Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | View or switch CLI display language |

### i18n

View current CLI language, list supported languages, switch display language. If no parameter is specified, enter interactive selection interface.

**Aliases:** `language`, `lang`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[lang]` | | Language code to switch to (e.g., `zh-CN`, `en`, `ja`, `ru`) |
| `--list` | `-l` | List all supported languages |

**Examples:**

```bash
# Interactive language selection
epsdk i18n

# Switch to English
epsdk i18n en

# Switch to Japanese
epsdk i18n ja

# List all supported languages
epsdk i18n --list
```

---

## Type Stub Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | Generate type stub files to enable IDE completion |

### types

Scans installed ErisPulse modules and adapters, generates `.pyi` type stub files for them, enabling accurate code completion and type checking support in IDEs.

**Aliases:** `t`, `stub`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `--output` | `-o` | Output path (default is `ep-stubs/` in current directory) |
| `--force` | | Force overwrite existing stub files |
| `--adapters-only` | | Generate type stubs only for adapters |
| `--modules-only` | | Generate type stubs only for modules |

> **Note:** `--adapters-only` and `--modules-only` are mutually exclusive; if both are specified, the latter takes precedence.

**Examples:**

```bash
# Generate type stubs for all installed modules and adapters
epsdk types

# Generate type stubs only for adapters
epsdk types --adapters-only

# Output to specified directory
epsdk types -o ./typings

# Force overwrite existing files
epsdk types --force
```

---

## Global Parameters

The following parameters apply to all commands:

| Parameter | Short | Description |
|------|--------|------|
| `--help` | `-h` | Display help information |
| `--version` | `-V` | Display version information |
| `--verbose` | `-v` | Display detailed output (can be stacked with `-vv`/`-vvv`) |
| `--no-color` | | Disable colored output (suitable for CI / log collection) |
| `--no-banner` | | Skip startup Banner (scripted calls / CI scenarios; non-interactive terminals and `ERISPULSE_NO_BANNER=1` automatically silent) |
| `--yes` | `-y` | Automatically confirm all interactive prompts (non-interactive runs) |

---

## Environment Diagnostics

### doctor

> [!NOTE]
> This command requires ErisPulse **2.7.0+**.

Diagnoses the current CLI runtime environment and outputs a health report. Used to troubleshoot issues like "why can't it be installed / connected".

| Parameter | Description |
|------|------|
| `--verbose` | Display detailed diagnostic information |
| `--fix` | Attempt to automatically fix repairable issues after diagnosis |

**Check items**:
- **Python**: Interpreter version and path
- **Installation backend**: Whether `uv` or `pip` is used
- **Target interpreter**: The actual Python environment where packages are installed
- **Configuration file**: Whether `config/config.toml` exists
- **Component configuration**: Completeness of declarative configuration for installed components ("installed but can't run" often due to missing required fields)
- **PyPI connectivity**: Whether PyPI can be accessed (and displays the number of discovered components)
- **System proxy**: Whether a proxy is detected

**Automatic repair (with `--fix`)**:
- `config.toml` missing → Generate initial configuration file according to current language (same source as `init` project creation)
- Component configuration "incomplete" → Launch interactive configuration wizard one by one to complete required fields (non-interactive environments prompt to use `epsdk config <name>`)
- Issues such as low Python version, PyPI access failure, requiring manual intervention → Only output action suggestions

```bash
# Environment diagnosis
epsdk doctor

# Using alias
epsdk diag

# Diagnose and attempt automatic repair
epsdk doctor --fix
```

---

## Interactive Installation

Running `epsdk install` without specifying a package name enters interactive installation:

```bash
epsdk install
```

The interactive interface provides:
1. Adapter selection
2. Module selection
3. Custom installation

## Common Usage

### Install Modules

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Upgrade module
epsdk install Weather -U
```

### List Components

```bash
# List all components
epsdk list

# List only adapters
epsdk list -t adapters

# List only upgradable components
epsdk list -o

# View remote available components
epsdk list-remote
```

### Uninstall Components

```bash
# Uninstall a single component
epsdk uninstall Weather

# Uninstall multiple components
epsdk uninstall Yunhu Weather
```

### Configure Components

```bash
# View configuration status
epsdk config --list

# Interactive selection of target configuration
epsdk config

# Configure specified adapter
epsdk config yunhu
```

### Upgrade Components

```bash
# Upgrade all components
epsdk upgrade

# Upgrade specified component
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Run Project

```bash
# Run normally
epsdk run main.py

# Hot-reload mode
epsdk run main.py --reload
```

### Switch Language

```bash
# Interactive language selection
epsdk i18n

# Directly switch to English
epsdk i18n en

# List supported languages
epsdk i18n --list
```

### Generate Type Stubs

```bash
# Generate all type stubs
epsdk types

# Generate only module type stubs
epsdk types --modules-only
```

### Initialize Project

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot
```

### Create Scaffolding

```bash
# Interactive creation (guides selection of type and filling information)
epsdk create

# Directly create Module project
epsdk create module -n MyModule

# Directly create Adapter project
epsdk create adapter -n MyAdapter

# Complete parameters
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Force overwrite existing directory
epsdk create module -n MyModule -f
```

## 安装

> 来源: `docs/en/user-guide/installation.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/user-guide/installation.md）

# Installation Reference

> [!TIP]
> **When to read this**: Read this when you need to choose an installation method (pip / uv / Docker / ErisPulse-App client) or troubleshoot a failed installation. If you just want to get up and running as quickly as possible, the [5-Minute Quick Start](../quick-start.md) already covers the simplest process — skip this page if that's all you need.

## System Requirements

- Python 3.10 – 3.14 (the 3.14t free-threading / no-GIL build is supported experimentally; the framework continuously monitors it via experimental CI smoke tests, without a formal commitment)
- pip or uv (recommended)
- Sufficient disk space (at least 100MB)

## Installation Methods

### Method 1: Install with pip

```bash
# Install ErisPulse
pip install ErisPulse

# Upgrade to the latest version
pip install ErisPulse --upgrade
```

### Method 2: Install with uv (Recommended)

uv is a faster Python toolchain, recommended for development environments.

#### Install uv

```bash
# Install uv with pip
pip install uv

# Verify installation
uv --version
```

#### Create a Virtual Environment

```bash
# Create a project directory
mkdir my_bot && cd my_bot

# Install Python 3.12
uv python install 3.12

# Create a virtual environment
uv venv
```

#### Activate the Virtual Environment

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### Install ErisPulse

```bash
# Install ErisPulse
uv pip install ErisPulse --upgrade
```

### Method 3: Install with uv tool (Global CLI, Recommended)

If you only want to use `epsdk` as a global command-line tool, `uv tool install` is the cleanest approach—epsdk runs in an isolated tool environment, without polluting any project environment:

```bash
# Install (epsdk is immediately available, no need to activate any virtual environment)
uv tool install ErisPulse

# Upgrade (or use `epsdk self-update`, which automatically uses this channel)
uv tool upgrade ErisPulse
```

> [!NOTE]
> The epsdk in the tool environment will automatically detect the project’s `.venv` when running within the project directory:
> `epsdk install` will install components into the project environment, and `epsdk run` will use the project environment to run the bot.
> The framework itself remains provided by the tool environment, with no interference between the two.
>
> The one-click installation script (`get.erisdev.com/install.sh` / `install.ps1`) also provides a "Global CLI Installation (uv tool)" option in its menu, which automatically installs uv and guides you through the setup.

## Project Initialization and Module Installation

After installation, the complete workflow for project initialization, module installation, and execution is detailed in [5-Minute Quick Start](../quick-start.md).

### Method 4: Using the ErisPulse-App Client (No Terminal Required)

Don't want to install a Python environment? [ErisPulse-App](../ecosystem/app.md) is the official cross-platform client (Android / Windows / Linux / macOS), allowing you to **run directly on your mobile device**. The desktop version supports minimizing to the system tray for background operation. It includes a built-in Python runtime and ErisPulse SDK, eliminating the need for terminal commands or manual configuration:

- Download the appropriate version from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases) based on your platform (Android `online`/`offline` APK, Windows `setup.exe`/`zip`, Linux `tar.gz`, macOS `zip`)
- Create and launch an instance within the App, managing adapters and modules through the native interface and browsing the module store

> For complete instructions, see [ErisPulse-App Installation and Usage](../ecosystem/app.md).

## Verification of Installation

### Check Installation

```bash
# Check ErisPulse version
epsdk --version
```

### Run Tests

```bash
# Run the project
epsdk run main.py
```

If you see output similar to the following, the installation was successful:

```
[INFO] Initializing ErisPulse...
[INFO] Adapter loaded: Yunhu
[INFO] Module loaded: MyModule
[INFO] ErisPulse initialization complete
```

## FAQ

### Installation Failure

1. Check that your Python version is within the supported range (3.10 – 3.14 is supported; 3.14t free-threaded / no-GIL builds are experimentally supported without a formal commitment)
2. Try using `uv pip install ErisPulse` instead of `pip install`
3. If a permission error occurs, try `pip install --user ErisPulse` or use a virtual environment
4. If you encounter SSL certificate errors in a corporate proxy environment, try `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ErisPulse`
5. Ensure your network connection is working and the pip index is accessible

### Configuration Errors

1. Check that the `config.toml` syntax is correct (TOML format is sensitive to indentation and quotation marks)
2. Confirm that all required configuration items have been filled in
3. Check the terminal logs for detailed error messages
4. Use `epsdk init` to regenerate the configuration file

### Module Installation Failure

1. Confirm that the module name is spelled correctly (case-sensitive)
2. Check your network connection
3. Use `epsdk list-remote` to view the list of available modules
4. Confirm that the module is compatible with your current SDK version

### Windows PowerShell Execution Policy

If PowerShell shows "cannot be loaded... because running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Debian/Ubuntu Virtual Environment Creation Failure

If the installation script reports "virtual environment creation failed" and the error message contains `ensurepip is not available`, it is because Debian/Ubuntu does not install `python3-venv` by default (the system Python's `ensurepip` is disabled):

```bash
sudo apt install python3.13-venv   # Install the corresponding package for your actual Python version
# Or install the generic metapackage:
sudo apt install python3-venv
```

After installation, simply re-run the installation script. The newer installation script will proactively prompt and attempt to automatically install the corresponding system package when this issue is detected; you can also switch to uv instead (`uv venv` does not depend on `ensurepip`).

## 部署

> 来源: `docs/en/user-guide/deployment.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/user-guide/deployment.md）

# Deployment Guide

> [!TIP]
> **When to read this**: When the bot needs to run long-term—Docker deployment, systemd / Supervisor process supervision, reverse proxy and SSL, backup and upgrade are all covered here. Skip during local development and debugging.

After developing the bot, deployment is just the beginning. This guide covers three deployment methods required to run it stably on a server (Docker / systemd / Supervisor), as well as reverse proxy, security hardening, and backup.

## Docker Deployment (Recommended)

ErisPulse provides an official Docker image, which includes the ErisPulse framework and Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

### Quick Start

```bash
# Pull the image
docker pull erispulse/erispulse:latest

# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard login token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

After starting, access `http://localhost:8000/Dashboard` and use the set token as the password to log in.

### Domestic Mirror Acceleration

If Docker Hub cannot be accessed, you can pull the image from GitHub Container Registry:

```bash
docker pull ghcr.io/erispulse/erispulse:latest
```

When using the ghcr.io image, you need to modify the image in `docker-compose.yml`:

```yaml
services:
  erispulse:
    image: ghcr.io/erispulse/erispulse:latest
```

### docker-compose.yml

```yaml
services:
  erispulse:
    image: erispulse/erispulse:${ERISPULSE_TAG:-latest}
    container_name: ${CONTAINER_NAME:-erispulse}
    ports:
      - "${ERISPULSE_PORT:-8000}:8000"
    volumes:
      - ./config:/app/config
      # Persistent Python package directory
      - ./config/.packages:/usr/local/lib/python3.13/site-packages
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - LANG=${LANG:-en_US.UTF-8}
      - ERISPULSE_LANG=${ERISPULSE_LANG:-}
      - ERISPULSE_DASHBOARD_TOKEN=${ERISPULSE_DASHBOARD_TOKEN:-}
    init: true
    # Graceful shutdown is handled by the framework's signal handling (SIGTERM), this only controls the grace period
    stop_grace_period: 30s
    restart: on-failure:5
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

> The above is consistent with the [docker-compose.yml](https://github.com/ErisPulse/ErisPulse/blob/main/docker-compose.yml) in the repository root (the repository version has additional comments on mirror acceleration and environment variable explanations at the top), and it is recommended to download and use it directly.

### Environment Variables

| Variable | Default | Description |
|------|--------|------|
| `ERISPULSE_PORT` | `8000` | Dashboard port mapping |
| `ERISPULSE_TAG` | `latest` | Image tag (set to a specific version number if you need to lock the version) |
| `CONTAINER_NAME` | `erispulse` | Container name (useful to distinguish instances in multi-instance deployment) |
| `ERISPULSE_DASHBOARD_TOKEN` | auto-generated | Dashboard login token (strongly recommended to set) |
| `TZ` | `Asia/Shanghai` | Timezone |
| `LANG` | `en_US.UTF-8` | System language, automatically detects the language of the startup interface |
| `ERISPULSE_LANG` | empty | Force the startup interface language: `zh` / `zh_TW` / `en` / `ja` / `ru` (overrides `LANG`) |

### Data Persistence

The `./config` directory mounts configuration files and the database, including:

- `config/config.toml` — configuration file
- `config/config.db` — SQLite storage database
- `config/.packages` — persistent Python site-packages volume, saves framework, adapters, and installed modules (automatically initialized from the image's built-in backup on the first startup, and subsequent module installations and framework hot-updates are written to this directory)

> **Framework upgrade (including pre/rc) and image self-healing**: The entrypoint performs a core package integrity self-check on every container startup. If damaged, it repairs according to the "user-installed version priority" principle—explicitly installed/upgraded versions in the persistent volume (such as pre versions installed in the Dashboard) will be reinstalled from PyPI with the same version, without silent rollback to the image's built-in version. Therefore, after the Dashboard upgrades the framework, any container restart should maintain the target version.

## Dashboard Management Panel

The ErisPulse Docker image includes the Dashboard module, providing a web-based visual management interface.

### Feature Overview

| Feature | Description |
|------|------|
| Dashboard | System overview, CPU/memory monitoring, uptime, event statistics |
| Bot Management | View online status and information of bots on each platform |
| Event Viewer | Real-time event stream, supports filtering by type and platform |
| Log Viewer | Log viewer with filtering by module and level |
| Module Management | View, load, and unload installed modules and adapters |
| Module Store | Browse remote available packages and install them with one click |
| Configuration Editor | Edit `config.toml` online |
| Storage Manager | Browse and edit Key-Value storage data |
| Backup | Export/import configuration and storage data |
| Audit Log | Records all management operations |

### Installing Modules via Dashboard

The Dashboard integrates the module store feature, allowing you to:

1. **Install from the store**: Browse the list of remote modules and install the desired ones with one click
2. **Upload local packages**: Directly upload `.whl` or `.zip` files for installation, which is convenient for testing personal-developed modules

> **Quick testing process for module developers**: After deploying with Docker, you can directly upload your built `.whl` file in the Dashboard's "Upload local package" feature for testing, without manually operating the container.

## Process Supervision and Hard Restart

ErisPulse's hard restart (`sdk.hard_restart()`) relies on an **external supervisor** to restart the process when the exit code is 42—the SDK itself does not restart a new process. In production environments, you must configure a supervisor; otherwise, the process will not automatically recover after a hard restart:

- Docker: The official compose uses `restart: on-failure:5`—restarts on any non-zero exit code (overriding the hard restart exit code 42), with a limit of 5 consecutive attempts to prevent dead loops; to allow unlimited attempts, you can change it to `unless-stopped`
- systemd: `Restart=on-failure` + `RestartForceExitStatus=42`
- PM2 / supervisord: Add 42 to the list of restartable exit codes
- Pure Python custom supervisor: Use a loop with `Popen` and check `returncode == 42`

Complete configuration examples for each supervisor and the exit code 42 contract are available in [Startup Flow → Supervisor Guide](../advanced/startup.md#Supervisor-Guide).

## Health Check

The SDK includes a built-in health check endpoint:

```bash
# Health check
curl http://localhost:8000/health
```

The official `docker-compose.yml` already includes the following health check; when writing your own compose file, you can reference it:

```yaml
services:
  erispulse:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')"]
      interval: 30s
      timeout: 5s
      start_period: 20s
      retries: 3
```

## Reverse Proxy

If you need to expose the Dashboard through a reverse proxy like Nginx:

```nginx
server {
    listen 80;
    server_name bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket support (required for Dashboard's real-time event stream)
    location /Dashboard/ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

SSL can be used with Let's Encrypt:

```bash
sudo certbot --nginx -d bot.example.com
```

## Manual Deployment (pip)

If you do not use Docker, you can also deploy manually.

### Production Environment Configuration

```toml
# config/config.toml

[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"
log_files = ["app.log"]
memory_limit = 5000

[ErisPulse.framework]
enable_lazy_loading = true
```

### systemd (Linux)

Create `/etc/systemd/system/erispulse-bot.service`:

```ini
[Unit]
Description=ErisPulse Bot
After=network.target

[Service]
Type=simple
User=bot
WorkingDirectory=/opt/erispulse-bot
ExecStart=/opt/erispulse-bot/venv/bin/epsdk run main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Management:

```bash
sudo systemctl daemon-reload
sudo systemctl start erispulse-bot
sudo systemctl enable erispulse-bot
sudo journalctl -u erispulse-bot -f
```

### Supervisor

Create `/etc/supervisor/conf.d/erispulse-bot.conf`:

```ini
[program:erispulse-bot]
command=/opt/erispulse-bot/venv/bin/python -m ErisPulse run main.py
directory=/opt/erispulse-bot
user=bot
autostart=true
autorestart=true
stderr_logfile=/var/log/erispulse-bot/err.log
stdout_logfile=/var/log/erispulse-bot/out.log
```

### uv tool Separated Deployment (CLI and Project Environment Isolation)

`uv tool install` installs `epsdk` as an **independent tool environment**, completely isolating the CLI from project dependencies: upgrading the CLI does not affect the project `.venv`, and changes in project dependencies do not affect the CLI.

```bash
# 1. Install CLI globally (automatically exposes epsdk / ep commands)
uv tool install ErisPulse

# 2. Only keep robot dependencies in the project (the .venv is managed by uv)
cd /opt/erispulse-bot
uv add erispulse ErisPulse-Adapter-Yunhu   # Add adapters as needed

# 3. Run with CLI (automatically detects and uses the interpreter in the project .venv)
epsdk run main.py
```

Behavior points:

- The target interpreter resolution order for `epsdk run`: `ERISPULSE_PYTHON` environment variable → project `.venv` → current interpreter; the tool environment only hosts the CLI, and components (adapters/modules) should be installed into the project `.venv`
- `epsdk install` / `uninstall` / `upgrade` / `list` also affect the project `.venv`, without polluting the tool environment
- Upgrade CLI: `uv tool upgrade ErisPulse` (or directly `epsdk self-update`, uv tool environment automatically changes to `uv tool upgrade`); upgrade project dependencies: execute `uv sync` / `uv add` in the project directory, the two do not affect each other
- In server scenarios, the tool environment is managed uniformly by uv (use `uv tool list` to view, `uv tool upgrade --all` to upgrade in bulk), without manual maintenance of global pip packages
- If `uv run epsdk ...` is executed in a directory without a project, it falls into a **one-time isolated environment** (installed components are not persisted); on servers, always use `epsdk` directly or first `cd` into the project directory

## Security Recommendations

1. **Set a Dashboard token**: Use a strong random token, do not use the default value
2. **Do not expose ports to the public network**: Unless using a reverse proxy + SSL, restrict the Dashboard port to the internal network
3. **Protect the data directory**: The `config/` directory contains configuration and database, set appropriate file permissions
4. **Regular updates**: Use `epsdk self-update` or pull the latest Docker image
5. **Do not run as root**: Create a dedicated user when deploying manually
6. **Use Docker restart policies**: The official compose's `restart: on-failure:5` ensures automatic restart after abnormal exit (including hard restart exit code 42)

## Multi-Instance Deployment

When running multiple robot instances:

1. Each instance uses a separate project directory and `docker-compose.yml`
2. Use different port numbers: `ERISPULSE_PORT=8001`
3. Use different container names: `container_name: erispulse-bot2`

## Update and Maintenance

### Docker Method

```bash
# Pull the latest image
docker compose pull

# Restart to use the new image
docker compose up -d
```

### pip Method

```bash
epsdk self-update
epsdk upgrade
```

### uv tool Method

```bash
# Upgrade CLI tool environment
uv tool upgrade ErisPulse

# Upgrade project dependencies (execute within the project directory)
uv sync
```

### Runtime Hot Reload Server Configuration

After modifying the listening address / port / SSL certificate, there is no need to restart the process. In any coroutine, call `router.reload()`:

```python
await sdk.router.reload(port=9000)                                # Change port
await sdk.router.reload(ssl_cert=new_pem, ssl_key=new_key)        # Hot swap certificate (certificate renewal scenario)
await sdk.router.reload(host="0.0.0.0", port=9000)                # Default parameters use current configuration
```

- Reuse the same FastAPI application, all HTTP / WebSocket / SSE routes registered by modules are retained
- Validate new configurations first (certificate can be built, port is available) before switching; if it fails, restore to the old configuration and return `False`, ensuring that returning `False` means the old service remains available
- Return `False` if the server is not running (use `sdk.router.start()` for the first startup)

### Backup

Regularly back up the `config/` directory:

```bash
# Docker deployment
tar czf erispulse-backup-$(date +%Y%m%d).tar.gz config/

# Or use the "Backup" feature in the Dashboard to export
```
