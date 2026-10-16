# Configuration File Guide

> [!NOTE]
> **L1 Core Reading** — One of the five core documents in the "Reading Path" on the homepage, essential for module development.

> This document introduces the framework's configuration file. If a third-party module requires configuration, please refer to the module's documentation.

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

When the framework starts, it creates a `.erispulse_config.lock` lock file in the `config/` directory and holds it until the process exits (used to detect multiple instances sharing the same configuration directory). If the log shows a warning "Detected that the configuration file may be in use by another ErisPulse instance," it means there are **two or more ErisPulse processes writing to the same configuration file** (typical scenario: multiple containers mounted the same host `config/` directory) — concurrent writes will overwrite each other. Please use a separate configuration directory for each instance.

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
log_dir = ""                  # Log output directory (automatically creates). Setting it automatically segments and rotates logs into `erispulse.log` in the directory, with `log_rotation` auto-segmenting; mutually exclusive with `log_files`, `log_files` takes precedence
log_rotation = "size"         # Segmentation method: "size" / "date" / "none"
log_max_size_mb = 10          # Single file size limit in size mode (MB), rotates to .1/.2 backups when exceeded
log_backup_count = 5          # Number of retained historical log files, oldest backups are automatically deleted when exceeded
log_rotation_when = "midnight"  # Date mode rotation cycle: S/M/H/D/midnight
memory_limit = 1000
exclude_levels = ["EVENT"]
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| level | string | INFO | Log level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed internal debugging information) |
| format | string | rich | Log output format: `rich` (colorful, default), `plain` (plain text without color, suitable for log collection/pipeline redirection), `json` (structured JSON, suitable for ELK, etc.) |
| log_files | array | empty | List of log output files (explicit paths, no segmentation) |
| log_dir | string | empty | Log output directory (automatically created). Setting it writes to `erispulse.log` in the directory and automatically segments according to `log_rotation`. Mutually exclusive with `log_files`, `log_files` takes precedence |
| log_rotation | string | size | Segmentation method: `size` (by size) / `date` (by time) / `none` (no segmentation) |
| log_max_size_mb | float | 10 | Single file size limit in size mode (MB), rotates to .1/.2 backups when exceeded |
| log_backup_count | integer | 5 | Number of retained historical log files, oldest backups are automatically deleted when exceeded |
| log_rotation_when | string | midnight | Date mode rotation cycle: S/M/H/D/midnight (default daily at midnight) |
| memory_limit | integer | 1000 | Number of log entries kept in memory |
| exclude_levels | array | empty | Levels to exclude. Logs of excluded levels are **completely discarded** (not written to memory, not pushed to Dashboard or other subscribers, not printed, not written to file). Supports hot updates |

You can also dynamically switch in code:

```python
from ErisPulse.Core import logger

# Segment by size: Single file 10MB, retain 5 copies
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# Segment by time: Rotate daily at midnight, retain 7 copies
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` and segmentation-related configurations require ErisPulse **2.8.0+**.

> **Privacy Protection**: Message sending and receiving content is logged at the **EVENT level** (value 21). Setting `exclude_levels = ["EVENT"]` allows the backend (such as the Dashboard log panel) to not see message content in groups or private chats, while not affecting logs of other levels.

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
| strict_mode | integer | 0 | Strict mode level, see below "Strict Mode" section |
| handler_max_concurrency | integer | 64 | Maximum concurrent task count for event handlers, increasing improves throughput but increases memory usage |
| offline_bot_expiry | integer | 3600 | Automatic expiration time (seconds) for offline Bot records, 0 means no expiration |

### Active GC Configuration

After SDK initialization, an active GC background task is started, periodically executing Python GC and internal resource recycling (cleaning offline Bots, etc.). All parameters support hot updates, and the task is restarted immediately when changes occur.

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | Recycling interval (seconds), supports decimals. 0 means disable active GC |
| proactive_gc_generation | integer | 0 | Regular round recycling generation (0/1/2, clamped to 0..2). Note that `gc.collect(2)` is equivalent to full recycling, default 0 keeps it lightweight; deep recycling is triggered periodically by `proactive_gc_full_every` |
| proactive_gc_full_every | integer | 20 | Full recycling every N rounds, 0 means disable periodic full recycling. Full recycling is constrained by the `proactive_gc_memory_growth_mb` threshold |
| proactive_gc_memory_growth_mb | integer | 32 | Memory growth threshold (MB) for full recycling: Compared to the memory baseline after the last full recycling (prioritizing tracemalloc, then RSS), full recycling is only performed if the growth reaches this value. 0 means no threshold |
| proactive_gc_idle_only | boolean | false | When enabled, Python GC is skipped in this round during event peaks (pending handlers exist), avoiding pauses and message processing competition; internal resource recycling is unaffected |
| proactive_gc_gen0_min | integer | 500 | Lower bound for triggering regular round recycling of gen0 garbage: `gc.get_count()[0]` below this value directly skips (empty round has near-zero overhead). 0 means always recycle |

> **2.7.1 Change**: The default `proactive_gc_generation` was adjusted from `2` to `0`, and `proactive_gc_full_every` was adjusted from `0` to `20`. Previously `generation=2` meant full recycling every round; the new default maintains recycling coverage while significantly reducing empty round overhead. Explicitly configured old values still follow literal semantics.

### Strict Mode

The strict mode controls the handling strategy for non-compliant or failed components during the loading phase. Modern modules/adapters should inherit the corresponding base classes (`BaseModule`/`BaseAdapter`); components not inheriting base classes affect the framework's context system and fallback cleanup, potentially causing resource leaks.

> **2.5.2 Change**: The default level was adjusted from `1` (skip) to `0` (lenient), to reduce loading issues for new users. Components not inheriting base classes will be warned and attempted to load, rather than directly rejected. To restore old behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (Default) | Violations only warn, components not inheriting base classes are still attempted to load (compatible with old components) |
| 1 | Strict-Skip | Reject components not inheriting base classes and skip them, other components start normally |
| 2 | Strict-Fatal | Collect all violations and report them together, then terminate the entire startup |

In all levels, component self-crashes during the loading/registration/initialization phase are always skipped; the difference lies in:

- **0 → 1**: The only behavioral change is that "not inheriting base class" changes from "still loading" to "skipping."
- **1 → 2**: All violations (not inheriting base class, loading failure, registration failure, initialization failure, etc.) are upgraded to fatal, collected at the startup checkpoint and reported as a violation list, then terminated.

#### Exemption List

If certain components cannot migrate temporarily (for example, dependent old modules), they can be added to the exemption list. Components listed here will be treated as lenient mode even if non-compliant, and continue loading:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly prompt how to resume loading (add to the exemption list or lower the level).

#### Integration with CLI

The startup pre-check of `epsdk run` (parsing of configuration file, completeness of component required configuration) defaults to follow this configuration: If not 0, failure in the check will refuse startup, and if 0, only warnings continue. It can also be temporarily switched without changing the configuration: `epsdk run --strict` will enable both self-check and strict level this time (level only increases, not decreases, and is transmitted to the running process via the `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable), `--no-strict` temporarily lowers to lenient and only warns.

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

## Command Parsing Configuration (event.command)

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn all command-line commands
- [Developer Guide](../developer-guide/) - Learn how to develop custom modules