# Configuration File Reference

> [!NOTE]
> **L1 Core Must-Read** — one of the five core documents in the homepage "Reading Path", essential for module development.

> This document covers the framework's own configuration file `config/config.toml`: what each configuration section controls, which ones support hot reload, and how to override them with environment variables. For third-party module configuration options, please refer to each module's own documentation.

ErisPulse uses the TOML-formatted configuration file `config/config.toml` to manage project configuration.

## Configuration File Location

The configuration file is located in the `config/` folder at the project root:

```
project/
├── config/
│   └── config.toml
├── main.py
```

### Multi-Instance Warning and Lock File

On startup, the framework creates a `config.lock` lock file under the runtime state directory **`.erispulse/`** at the project root and holds it until the process exits (used to detect multiple instances sharing a configuration directory; the `.erispulse_config.lock` file located in the `config/` directory in 2.10 and earlier is automatically removed on first startup after upgrading). If the log shows the warning "Detected that the configuration file may be in use by another ErisPulse instance simultaneously", it means **more than one ErisPulse process is writing to the same configuration** (typical scenario: multiple containers mounting the same host `config/` directory) — concurrent writes will overwrite each other, so please use a separate configuration directory for each instance.

### Sensitive Configuration Stays Out of Version Control

The configuration file contains sensitive information such as tokens (token / API key): framework initialization and `epsdk init` automatically generate a `.gitignore` in the `config/` directory (containing only a single line `*` — **all files in the directory are excluded from version control, and the ignore file itself is also within the exclusion scope**); an existing `.gitignore` will not be overwritten. The `.erispulse/` runtime state directory (instance locks, CLI runtime state files) is likewise machine-local state, and is ignored by default in the project template's `.gitignore`.

## Configuration Loading Error Handling

When loading `config.toml`, the framework distinguishes three error states and provides **actionable diagnostic information**, instead of silently falling back to the default configuration:

| Error State | Trigger Condition | Framework Behavior |
|---------|---------|---------|
| Missing file | `config.toml` does not exist | Normal first startup; silently uses an empty configuration (no warning) |
| TOML syntax error | File exists but the format is invalid (e.g., missing quotes, unclosed brackets) | Outputs the **error line/column number and reason**, and **keeps the last valid configuration and continues running** (this file modification does not take effect) |
| Permission/other errors | No read permission, IO errors, etc. | Outputs an **explicit reason**, and **keeps the last valid configuration and continues running** |

> **Note that "last valid configuration" ≠ default configuration**: when the file is corrupted, the framework continues with **the last configuration that was successfully parsed before this startup** (if a hot reload corrupts the file during runtime, the old values are kept), rather than resetting all configuration items to factory defaults. Do not assume "configuration has been reset" when handling failures.

For example, if you accidentally write the configuration as `port = 8000` (a string missing quotes), the log will output something like:

```
[ERROR] [Config] Configuration file config/config.toml syntax error (line 3, column 1): ...
[WARNING] [Config] Failed to read the configuration file. Continuing with the last valid configuration; this file modification did not take effect — please fix it and reload or restart
```

This way you can pinpoint the problem immediately at the **default INFO level**, without wondering "why didn't my configuration change take effect".

> **Corrupted the configuration file while running?** If you manually edit `config.toml` while the bot is running and introduce a syntax error, on the next write (merging configuration) the framework will output "Configuration file is corrupted (syntax error, line X), unable to merge-write — please fix the configuration file first and restart", rather than a confusing "write failed". The configuration items pending write are retained and will not be lost.

## Comment Preservation and Minimal Disk Writes

**Comments and key order in config.toml are fully preserved after framework writes**: whether via code `setConfig()`,
CLI configuration wizard saves, or adapters/modules generating a configuration template for the first time, the framework only modifies the keys involved;
the comments you wrote and the order you arranged are not erased or reordered (based on the tomlclass lossless TOML engine —
untouched content is preserved byte-for-byte, and the file's original CRLF/LF line-ending style is not changed either).

The framework is restrained about what it writes to disk:

- **Framework default configuration is not automatically written to disk**: built-in defaults such as `gc`, `scope`, and `transcript` reside only in memory;
  config.toml only contains the keys you explicitly set, staying minimal. For the full list of configurable items, refer to
  `config/config.full.example` in the project; copy items into config.toml and modify as needed (unconfigured items always use built-in defaults, so behavior is unchanged)
- **`config.full.example` is automatically maintained**: regardless of whether `epsdk init` has been executed, as long as the framework starts
  (`epsdk run` / `main.py`), a complete configuration reference is automatically generated when `config/config.full.example` is missing;
  the first line of the file is a framework-maintained marker. When the generator content updates (e.g., new configuration items, newly installed
  components), startup refreshes it once; deleting/modifying the first line switches to manual takeover and the framework no longer overwrites
- **Adapter/module configuration templates**: written to disk as annotated templates on first initialization (field descriptions serve as comments);
  fields declared with the `example` flag are not written to disk, only recorded in config.full.example for reference
- **Declarative comment read-back**: comments in the configuration file are themselves documentation — `ep doctor` and configuration
  validation failure messages quote the original comment text for that field in the file (even if you manually edited the comment, the message follows
  the file's current state), so there is no need to dig through documentation for field meanings when errors occur

## Environment Variable Overrides

The framework supports using environment variables to **override** `ErisPulse.*` configuration items (suitable for Docker / containerized / CI deployments, with no need to modify `config.toml`).

Naming rule: convert the dotted path `ErisPulse.<section>.<key>` to all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|--------|---------|--------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `2` |

Behavior notes:
- **Highest priority**: environment variables override both the "configuration file" and "default values", automatically converted according to the original value type (`bool` / `int` / `float` / comma-separated `list` / string)
- **Not persisted**: overrides only take effect at runtime and are not written back to `config.toml`
- **Supports hot reload**: after modifying environment variables during runtime, a reload with configuration listening takes effect

```bash
# Docker deployment example: override the port directly without modifying config.toml
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: framework configurations like `ErisPulse.server.port` are read via APIs such as `get_server_config()`, and all are affected by environment variable overrides.

### Environment Variable Binding for Module Configuration (2.9.0+)

A module's own declarative configuration (`ConfigClass`) supports field-level environment variable binding — declare `env` inside `field(metadata=...)`:

```python
@dataclass
class MyConfig(BaseConfig):
    api_key: str = field(default="", metadata={
        "description": "API key",
        "env": "MYMODULE_API_KEY",   # Environment variable binding
    })
    retries: int = field(default=3, metadata={"env": "MYMODULE_RETRIES"})
```

Behavior notes:

- **Priority**: environment variables > `config.toml` > declared defaults (this priority is maintained even after configuration file hot reload)
- **Type conversion**: environment variable values are automatically converted according to field annotations — `str` as-is; `int` / `float` / `bool` (`true` / `1` / `yes` / `on`) auto-converted; `list` / `dict` parsed via JSON; on conversion failure, the override is ignored (falls back to configuration file / defaults) and a warning is output
- **Declare once, effective everywhere**: configuration reading, hot reload, and validation use the same pipeline; the configuration panel Schema annotates the `env` name, and `config.toml` template comments also hint at available environment variables (templates do not write the actual values of environment variables, to avoid leaks)
- **Fully compatible**: fields without a declared `env` behave unchanged; directly instantiating ConfigClass (bypassing the framework configuration pipeline) is unaffected by environment variables

```bash
# Docker deployment example: inject the module secret directly without modifying config.toml
MYMODULE_API_KEY=sk-xxx docker compose up -d
```

> **Config class vs model field — how to choose?** The config class governs "how the module operates" (behavior parameters, hot reload),
> while the ORM's `Field()` governs "what data the user produces" (database tables, queries). Both share the same
> constraint vocabulary and validator engine; for a comparison table see
> [Data Model Layer · When to Use Which Declaration](../developer-guide/orm.md#when-to-use-which-declaration).

## Configuration Hot Reload

Since 2.7.0, the framework has provided **systematic support** for configuration hot reload. After `config.toml` is modified externally (a background watcher checks every 5 seconds), or after code calls `setConfig()`, components respond automatically:

| Component | Configurations Supporting Hot Reload | Behavior |
|------|----------------|------|
| **Logger** | `logger.level` / `log_files` / `log_dir` (including segmentation parameters) / `memory_limit` / `total_memory_limit` / `format` / `exclude_levels` | Automatically re-applied (with change detection) |
| **Command system CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter concurrency** | `framework.handler_max_concurrency` | Invalidates the cached semaphore and rebuilds it with the new value |
| **Proactive GC** | `framework.proactive_gc_*` | Restarts the GC task immediately on configuration change; supports runtime adjustment/disable/re-enable |
| **Event deduplication/cross-account** | `framework.event_dedupe` / `cross_account_policy` | Lazy cache invalidation; the next event re-reads with the new value |
| **Session account binding** | `framework.session_accounts` | Read in real time per event; changes take effect immediately |
| **Memory tracing** | `framework.memory_tracing` | Takes effect on the next proactive GC round (tracemalloc cannot safely hot-reset frame counts) |
| **Master system** | `master.users` | Read in real time at each `is_master()` check; no restart needed |
| **Module/adapter configuration** | Their own configuration items | Triggers the `on_config_update(old, new)` callback |

**Configurations requiring restart** (cannot be safely hot-switched; a warning "takes effect after restarting the process" is emitted on change):

| Configuration | Reason |
|------|------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup; cannot be safely hot-switched at runtime |
| `storage.use_global_db` | The SQLite file handle is already open at runtime; switching paths is unsafe |
| `storage.sqlite.busy_timeout` | busy_timeout is applied via PRAGMA when the connection is established; already-open connections do not refresh with configuration |

> **Transient error while editing and saving?** If a transient syntax error occurs while editing `config.toml`, the framework **keeps the last valid configuration** and outputs diagnostic logs; it does not broadcast an empty configuration to components (avoiding `on_config_update` receiving empty values and mistakenly falling back to defaults).

### Hot Reload Pipeline Internal Breakdown

"After changing configuration, how do the components know?" — Behind it is a detect → reload → broadcast pipeline:

```mermaid
flowchart TD
    A["External edit of config.toml"] --> B{"Who detects it first?"}
    B -->|"Background watcher thread<br/>polls mtime every 5 seconds"| C["_check_file_change determines change"]
    B -->|"When code reads configuration<br/>cache older than 60 seconds"| C
    C --> D["_load_config re-parses TOML"]
    D --> E{"Parse succeeded?"}
    E -->|"No (syntax error)"| F["Keep the last valid configuration<br/>no broadcast, log diagnostics"]
    E -->|"Yes"| G["lifecycle.emit config.updated<br/>carrying old_config / new_config"]
    G --> H["Component listeners respond<br/>(logger / scope / commands / GC ...)"]
```

**Two detection paths** (either one suffices; both act as safety nets):

| Path | Mechanism | Trigger Timing |
|------|------|---------|
| Background watcher | Daemon thread `config-watcher` polls the file `mtime` via `wait` every **5 seconds** | Within at most 5 seconds after an external file change |
| Lazy detection | On any `getConfig()` read, if the cache is older than **60 seconds**, the file is checked first | At the next configuration read |

> **The framework won't trigger itself**: when `setConfig()` writes to disk it records "the mtime of its own write"; the watcher excludes it when comparing, treating only **external edits** as changes.

**Two types of configuration change events:**

| Event | Trigger | Data | Typical Scenario |
|------|--------|------|---------|
| `config.set` | Code / Dashboard calling `setConfig()` | `{key, old_value, new_value}` | Single-key writes (template generation, state recording, runtime configuration changes) |
| `config.updated` | Captured by watcher/lazy detection after external edits | `{old_config, new_config, config_file}` | Manually editing `config.toml` |

> `setConfig()` by default **delays disk writes by 5 seconds** (merging multiple writes); `immediate=True` writes immediately. After the watcher detects an external modification, it only updates the in-memory cache and **does not** write external changes back to the file.

**List of automatic responders** (usually subscribed to both event types, with identical responses):

| Component | Listens To | Response |
|------|------|------|
| Logger | `config.set` + `config.updated` | Re-applies level/files/directory segmentation/memory limits/format/excluded levels (with change detection; no change means no action) |
| Scope | `config.updated` | Rebuilds the scope binding cache |
| Command system | `config.updated` | Refreshes parsing parameters for prefix/case/space prefix/must_at_bot; takes effect on the next message |
| Adapter concurrency | `config.set` + `config.updated` | Invalidates `handler_max_concurrency` and rebuilds the semaphore |
| Proactive GC | `config.set` + `config.updated` | Restarts the GC background task immediately on `proactive_gc_*` changes |
| Adapters | Routed to `on_config_update` | Each adapter's `on_config_update(old, new)` callback |
| Modules | Routed to `on_config_update` | Each module's `on_config_update(old, new)` callback |
| Storage | `config.updated` | `use_global_db` change **warning only** (restart required) |
| Router | `config.updated` | `cors.*` / `security.*` changes **warning only** (restart required) |

## Configuration Read and Delete APIs

### getAllConfig: Full Configuration Snapshot

Replaces reading the private `_cache` directly (external reads of private attributes are not covered by version compatibility guarantees):

```python
config = sdk.config.getAllConfig()     # Deep-copy snapshot; in-place modification does not affect framework state
config["ErisPulse"]["server"]["port"]
```

The view is consistent with `getConfig`: un-flushed `setConfig` / `delete` operations are already reflected,
strictly matching the file content after the delayed flush.

### delConfig: Delete a Configuration Key

`setConfig(key, None)` only clears the value — the key remains in the file; `delConfig` **removes** the key from the file:

```python
sdk.config.delConfig("ErisPulse.modules.status.OldModule")            # Delayed write
sdk.config.delConfig("OneBot.deprecated_key", immediate=True)         # Immediate flush to disk
```

- Supports dotted paths; returns `False` when the key does not exist
- Writes go through the comment-preserving path; the rest of the file's content and order are unaffected
- Reuses the `config.set` event broadcast (`new_value=None`): existing listeners such as adapters' / modules'
  `on_config_update` can perceive the deletion with zero changes

## Complete Configuration Example

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
auto_start = true
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.master]
# users supports two forms (choose one):
#   Global masters (effective on all platforms): users = ["123456", "789012"]
#   Per-platform masters: users = { yunhu = ["123456"], telegram = ["789012"] }
users = {}

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
log_dir = "logs"
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
# For container / no-file-mount scenarios, PEM content can be inlined (takes priority over certfile/keyfile paths)
# ssl_cert = """-----BEGIN CERTIFICATE-----
# ...
# -----END CERTIFICATE-----"""
# ssl_key = """-----BEGIN PRIVATE KEY-----
# ...
# -----END PRIVATE KEY-----"""
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| host | string | 0.0.0.0 | Listen address; 0.0.0.0 means all interfaces |
| port | integer | 8000 | Listening port number |
| auto_start | boolean | true | Whether to automatically start the router server on `sdk.init()`. Set to `false` to skip starting the router server (pure event / no-WebUI scenarios) |
| ssl_certfile | string | empty | SSL certificate file path |
| ssl_keyfile | string | empty | SSL private key file path |
| ssl_cert | string | empty | **Inline PEM certificate content** (not a path). When used together with `ssl_key`, it takes priority over `ssl_certfile`/`ssl_keyfile`; the framework temporarily writes it to disk to build the SSL context and deletes the temporary file immediately afterward |
| ssl_key | string | empty | **Inline PEM private key content** (not a path); semantics as above |

> **Port occupation is not a fatal error**: if the `port` is detected as occupied at startup, the framework skips starting the router server and issues a warning; **adapters and modules run as usual** (only HTTP/WS/SSE routes and the WebUI are unavailable). When troubleshooting "the bot runs but the WebUI won't open", check the port first.

## Master System Configuration

The master system is used to identify "framework master" accounts (such as Bot administrators). `master.users` supports three forms:

```toml
[ErisPulse.master]
# Form one: global masters (effective on all platforms, including platforms added later)
users = ["123456", "789012"]

# Form two: per-platform masters only (dict)
# users = { yunhu = ["123456"], telegram = ["789012"] }

# Form three: global + per-platform coexistence — the global key in the dict is the global master bucket
# users = { global = ["123456"], yunhu = ["789012"] }
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| users | array / object | empty | Master account list. The `list` form is global masters (effective on all platforms); the `dict` form specifies per platform (keys are platform names, the `global` key is the global master bucket), with values being the master account list for that platform |

> **About new platforms**: both the `list` form and the `global` bucket in the `dict` are "define once, effective on all platforms";
> new platforms integrated later require no further configuration changes; per-platform entries only apply to platforms with matching names (including lenient prefix/wildcard matching).
> `master.add(None, uid)` writes to the `global` bucket when persisted; existing platform entries are unaffected.

In code, check via `master.is_master(event)` or `master.is_master(platform, user_id)`; each call reads the configuration in real time (supports hot reload, no restart needed):

```python
from ErisPulse.Core import master

if master.is_master(event):
    await event.reply("Hello, master")
```

### Determination Chain and Runtime Add/Remove

The master determination chain is **configured masters → runtime records → provider chain**:

```python
from ErisPulse.Core import master

master.is_master(event)                      # Determine from the event
master.is_master("yunhu", "123")             # Explicit determination
master.add("yunhu", "123")                   # Add at runtime (persisted by default; persist=False keeps it in memory only)
master.remove("yunhu", "123")                # Remove (persisted by default)
master.list()                                # Summary: {"global": [...], "<platform>": [...]}
```

### Custom Identity Sources (provider)

Besides configuration, custom identity sources can be registered: `fn(platform, user_id) -> bool`.
They are tried in order when the built-in identity sources (configuration + runtime records) do not match; any provider that grants access identifies the user as a master.
Suitable for integrating with adapter admin interfaces, database roles, and other external identity systems.

The registration entry `master.provider` supports both decorator / functional styles;
unregistration uniformly goes through `fn.unregister()` on the registered function:

```python
from ErisPulse.Core import master

# Form one: decorator (persistent identity source, recommended)
@master.provider
def admin_provider(platform, user_id):
    return user_id in {"999"}     # Custom determination logic

master.is_master("yunhu", "999")   # True
admin_provider.unregister()        # Unregister when no longer needed

# Form two: functional (register at module load / unregister at unload)
fn = master.provider(admin_provider)
fn.unregister()
```

> Provider exceptions are caught and skipped, without blocking the identity determination chain.
> Bound instance methods cannot carry `unregister`; for scenarios requiring paired registration/unregistration, use **module-level functions**.

### User Priority: The Master Scope Is Ultimately Decided by the User

A command's `master=True` is only the **developer default**: users can override it to tighten or relax via
`ErisPulse.event.overrides.command.<module>.<cmd>.master = true/false`
(see [Unified Event Override Configuration](#unified-event-override-configuration-eventoverrides); explicit user configuration takes effect immediately).

## Logger Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = []                # Explicit log file list (mutually exclusive with log_dir; higher priority)
log_dir = "logs"                  # Log directory (automatic segmented rotation once set)
log_rotation = "size"         # Segmentation method: "size" / "date" / "none"
log_max_size_mb = 10          # Per-file size limit in size mode (MB)
log_backup_count = 5          # Number of historical log files retained
log_rotation_when = "midnight"  # Rotation period in date mode: S/M/H/D/midnight
memory_limit = 1000             # Per-module in-memory log entry limit (0 = disable in-memory log copies)
total_memory_limit = 5000       # Total in-memory log entry limit across all modules (0 = unlimited)
exclude_levels = ["EVENT"]
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| level | string | INFO | Log level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputting detailed framework internal debug information) |
| format | string | rich | Log output format: `rich` (colored, default), `plain` (plain text without color, suitable for log collection / pipe redirection), `json` (JSON structured, suitable for ELK etc.) |
| log_files | array | empty | List of log output files (explicit paths, no segmentation) |
| log_dir | string | "logs" | Log output directory (created automatically). Once set, writes `erispulse.log` in the directory and automatically segments per `log_rotation`; mutually exclusive with `log_files`, `log_files` takes priority |
| log_rotation | string | size | Segmentation method: `size` (by size) / `date` (by time) / `none` (no segmentation) |
| log_max_size_mb | float | 10 | Per-file size limit in size mode (MB); when exceeded, rotates into `.1`/`.2` backups |
| log_backup_count | integer | 5 | Number of historical log files retained; the oldest backups beyond this are automatically deleted |
| log_rotation_when | string | midnight | Rotation period in date mode: `S`/`M`/`H`/`D`/`midnight` (defaults to midnight daily) |
| memory_limit | integer | 1000 | Number of log entries kept in memory per module; `0` disables in-memory log copies (no longer written to memory; existing records retained) |
| total_memory_limit | integer | 5000 | Total in-memory log entry limit across all modules; `0` means unlimited. When exceeded, the oldest records are evicted per rotation strategy (prioritizing trimming the module queue with the most entries); operates independently of per-module `memory_limit` |
| exclude_levels | array | empty | Excludes specified log levels. Logs of excluded levels are **completely discarded** (not written to memory, not pushed to Dashboard or other subscribers, not printed, not written to files). Supports hot reload |

You can also switch dynamically in code:

```python
from ErisPulse.Core import logger

# Segment by size: 10MB per file, keep 5 copies
logger.set_output_dir("logs", rotation="size", max_size_mb=10, backup_count=5)

# Segment by time: rotate at midnight daily, keep 7 copies
logger.set_output_dir("logs", rotation="date", backup_count=7)
```

> [!NOTE]
> `log_dir` and segmentation-related configuration require ErisPulse **2.8.0+**.

> **Privacy protection**: message send/receive content is logged at the **EVENT level** (numeric value 21). Setting `exclude_levels = ["EVENT"]` prevents backends (such as the Dashboard log panel) from seeing message content in groups/private chats, without affecting logs of other levels.

Besides the configuration file (supporting hot reload), the same capability can be switched via code at runtime — no need to write configuration
when implementing `/privacy on|off` style admin commands:

```python
from ErisPulse import logger

logger.exclude_level("EVENT")        # Exclude a level at runtime (same semantics as the exclude_levels configuration)
logger.allow_level("EVENT")          # Restore that level
logger.list_excluded_levels()        # View currently excluded levels
logger.set_format("json")            # Switch output to the JSON line protocol (same effect as the format configuration key)
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

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | Whether to enable module lazy loading |
| uninit_timeout | integer | 30 | Total timeout (seconds) for graceful shutdown; forced termination after exceeding. 0 means no timeout |
| strict_mode | integer | 0 | Strict mode level; see the "Strict Mode" section below |
| handler_max_concurrency | integer | 64 | Maximum number of concurrent handler Tasks for events; larger values improve throughput but increase memory usage |
| handler_queue_max_pending | integer | 4096 | Enqueue backpressure for event floods: per-platform cap on pending handler Tasks; when exceeded, handler Tasks for new events are dropped outright and a WARNING is logged (drop counts can be viewed in troubleshoot diagnostics); `0` means unlimited |
| offline_bot_expiry | integer | 3600 | Auto-expiry time for offline Bot records (seconds); 0 means no expiry |
| plugins_dir | string / list | "plugins" | Local plugin folder (relative to the project root); added/deleted/modified plugin files are automatically discovered by the hot reload watcher |
| watch_ignore_dirs | list | built-in list | Directory names ignored by hot reload file monitoring (`.venv`/`.git`/`__pycache__` etc.); a non-empty list **wholesale replaces** the built-in list, `[]` means no directories are ignored |
| watch_include_plugin_dirs | boolean | true | Whether `epsdk run --reload` hands plugin directories to the plugin hot reload watcher for precise handling (single-module reload), excluding them from full monitoring |
| event_dedupe | boolean | true | Event idempotent deduplication: duplicate deliveries with the same event id (connection-layer re-push / gateway re-send) are dispatched only once |
| cross_account_policy | string | "off" | Cross-account duplicate acceptance policy: handling when the same physical message arrives via multiple accounts one after another — `off` no association (events dispatched one by one as usual, default); `mark` a top-level `multi_receipt` field is injected into the copy (pointing to the first accepted event) and it is dispatched as usual; modules read that field and decide themselves; `drop` copies are dropped directly at the dispatch entry (framework-level deduplication, invisible to modules). Copies whose mention targets hit the receiving account itself (`user_id` / `account_id`) do not participate in association (at-mention priority preserved); the policy supports hot reload and changes take effect immediately |
| session_accounts | table | {} | Session account binding: `{"platform_name": {"session_id": "account bot_id"}}` precisely binds a session to a single owning account — bound sessions are dispatched only by the owning account, and copies from other accounts are dropped (takes effect independently of `cross_account_policy`, enabled once configured; at-mention priority preserved). Session IDs are recommended in the `"group:123"` prefix format (isolating private-chat sessions with the same numeric value); the bare key `"123"` is a compatible form matching all session types; configuration is read in real time and hot reload takes effect |
| memory_tracing | boolean | false | Memory tracing (tracemalloc): when enabled, `/metrics` and memory snapshots can output traced memory and top allocation sites, and growth thresholds no longer misuse RSS; roughly 2x CPU overhead on allocation paths — enable for troubleshooting, keep off normally; hot reload, takes effect on the next proactive GC round |

Session account binding example (prefix key format recommended):

```toml
[ErisPulse.framework.session_accounts.snowluma]
"group:643319481" = "1325859446"
```

### Proactive GC Configuration

After SDK initialization completes, a proactive GC background task starts, periodically performing Python GC and internal resource reclamation (offline Bot cleanup, etc.). All parameters support hot reload; changes restart the task immediately.

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| proactive_gc_interval | number | 300 | Reclamation interval (seconds), decimals supported. 0 disables proactive GC |
| proactive_gc_generation | integer | 0 | Generation collected in regular rounds (0/1/2, clamped to 0..2). Note that `gc.collect(2)` is equivalent to a full collection; the default 0 stays lightweight; deep reclamation is triggered periodically by `proactive_gc_full_every` |
| proactive_gc_full_every | integer | 20 | Perform a full collection every N rounds; 0 disables periodic full collection. Full collection is constrained by the `proactive_gc_memory_growth_mb` threshold |
| proactive_gc_memory_growth_mb | integer | 32 | Memory growth threshold (MB) for full collection: compares against the memory baseline after the last full collection (tracemalloc preferred, RSS fallback); full collection runs only when growth reaches this value. 0 means no threshold |
| proactive_gc_idle_only | boolean | false | When enabled, Python GC is skipped for that round during event floods (unfinished pending handlers exist), avoiding pauses competing with message processing; internal resource reclamation is unaffected |
| proactive_gc_gen0_min | integer | 500 | Minimum gen0 garbage count to trigger reclamation in regular rounds: if `gc.get_count()[0]` is below this value, the round is skipped directly (idle rounds cost nearly zero). 0 means always collect |

> **2.7.1 change**: the default `proactive_gc_generation` was adjusted from `2` to `0`, and the default `proactive_gc_full_every` from `0` to `20`. Previously, `generation=2` meant performing the heaviest full collection every round; the new defaults significantly reduce idle overhead while maintaining reclamation coverage. Explicitly configured old values still take effect per their literal semantics.

### Strict Mode

Strict mode controls the handling policy for non-compliant or failed modules/adapters at load time. Modern modules/adapters should inherit the corresponding base classes (`BaseModule`/`BaseAdapter`); components that do not inherit base classes affect the framework's context system and fallback cleanup, potentially causing resource leaks.

> **2.5.2 change**: the default level was adjusted from `1` (skip) to `0` (lenient) to reduce loading problems encountered by new users on first use. Components that do not inherit base classes trigger a WARNING and an attempt to load them, rather than being rejected outright. To restore the old behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (default) | Violations only warn; components not inheriting base classes are still loaded (compatible with legacy components) |
| 1 | Strict - Skip | Rejects and skips components not inheriting base classes; the rest start normally |
| 2 | Strict - Fatal | Collects all violations, reports them together, and aborts the entire startup |

At all levels, component self-crashes such as "errors during load/registration/initialization" are always skipped; the differences are:

- **0 → 1**: the only behavior change is that "not inheriting a base class" changes from "still loaded" to "skipped".
- **1 → 2**: all violations (not inheriting base classes, load failures, registration failures, initialization failures, etc.) escalate to fatal; after being collected at the startup checkpoint, the violation list is output at once and startup aborts.

#### Exemption List

If some components genuinely cannot be migrated for now (e.g., legacy modules they depend on), they can be added to the exemption list; listed components are treated under lenient mode even when non-compliant and continue to load:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log explicitly indicates how to restore loading (add to the exemption list or lower the level).

#### CLI Integration

`epsdk run`'s pre-start self-check (configuration file parseability, completeness of required component configuration) follows this configuration by default: when non-0, a failed check refuses startup; when 0, it only warns and continues. You can also switch temporarily without changing configuration: `epsdk run --strict` turns on both the self-check and the strict level for this run (the level can only go up, never down, and is propagated to the running process via the `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable); `--no-strict` temporarily presses it down to lenient for this run and only warns.

## Storage Configuration

Since 2.8.0, the storage engine supports three async backends with **identical APIs and one-key configuration switching**:

| Backend | Driver | Installation | Features |
|------|------|------|------|
| SQLite (default) | aiosqlite | Out of the box | Zero configuration, single file, WAL concurrency |
| MySQL / MariaDB | aiomysql | `pip install ErisPulse[mysql]` | Existing MySQL infrastructure, multi-instance sharing |
| PostgreSQL | asyncpg | `pip install ErisPulse[postgres]` | Strong transactional capability, high concurrency |

```toml
[ErisPulse.storage]
backend = "sqlite"        # "sqlite" (default) / "mysql" / "postgres"
use_global_db = false     # SQLite only: use the package-global database data/config.db

[ErisPulse.storage.sqlite]     # Only effective when backend = "sqlite"
busy_timeout = 5000       # Write-lock wait limit (milliseconds, PRAGMA busy_timeout)

[ErisPulse.storage.mysql]      # Effective when backend = "mysql"
host = "127.0.0.1"
port = 3306
user = "erispulse"
password = ""
database = "erispulse"
# charset = "utf8mb4"
# pool_min = 1
# pool_max = 10

[ErisPulse.storage.postgres]   # Effective when backend = "postgres"
host = "127.0.0.1"
port = 5432
user = "erispulse"
password = ""
database = "erispulse"
# pool_min = 1
# pool_max = 10
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| backend | string | sqlite | Storage backend: `sqlite` / `mysql` / `postgres`; switching requires zero code changes |
| use_global_db | boolean | false | SQLite only: whether to use the package-global database instead of a project-specific database |
| storage.sqlite.busy_timeout | int | 5000 | SQLite only: write-lock wait limit (milliseconds, PRAGMA busy_timeout); increasing it extends patience for write-lock queuing; changes require a restart to take effect |
| storage.mysql.* | table | see above | MySQL connection parameters (host / port / user / password / database / charset / pool) |
| storage.postgres.* | table | see above | PostgreSQL connection parameters (host / port / user / password / database / pool) |

Environment variable overrides are also supported (Docker / 12-factor): `ErisPulse.storage.postgres.host` → `ERISPULSE_STORAGE_POSTGRES_HOST`.

> [!TIP]
> - Connection parameter changes require a framework restart to take effect; transient connection pool creation failures are automatically retried with exponential backoff
> - Before switching backends, you can self-check with the verification script: `python tests/devs/test_storage_backend_verify.py --backend mysql`
> - For full details on transactions / dialect differences / custom backends, see [Storage Backends](../advanced/storage-backends.md)

## Web Service and Router Configuration

For the full set of configuration items for the web server and routing (`[ErisPulse.server]` / `[ErisPulse.router]`) — host / port / auto_start / ssl, CORS and security headers (`router.cors.*` / `router.security.*`, changes require a restart), and API rate limiting (`router.rate_limit.*`; `rate_limit_trust_proxy` determines whether rate limiting uses proxy headers or the peer address as the rate-limit key — verify carefully in reverse-proxy deployments) — see [Router System](../advanced/router.md) and [Deployment Guide](deployment.md).

## Interaction Session Configuration

For interaction wait / session mutual-exclusion lease parameters (`[ErisPulse.interaction]`, including the `checkpoint_ttl` conversation checkpoint expiry duration), see [Conversation Multi-Turn Dialogue](../advanced/conversation.md) and [Interaction Session System](../advanced/interaction.md).

## Event Configuration

### Command Configuration

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = true
allow_space_prefix = false
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| prefix | string | / | Command prefix |
| case_sensitive | boolean | true | Whether case is distinguished (whether `/Help` and `/help` are different commands) |
| allow_space_prefix | boolean | false | Whether spaces are allowed as prefix |
| must_at_bot | boolean | false | Whether the bot must be @-mentioned to trigger commands (private chats are unrestricted) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| ignore_self | boolean | true | Whether to ignore the bot's own messages |

> Event deduplication has three layers, each handling one type of duplication: `event_dedupe` (framework, duplicate deliveries with the same event id) → `ignore_self` (this section, the bot's own messages) → `cross_account_policy` (framework, content-level copies of the same group across multiple accounts). For layered responsibilities, see [Adapter Core Concepts](../developer-guide/adapters/core-concepts.md).

## Session Inbox Configuration (transcript)

```toml
[ErisPulse.transcript]
enabled = true
max_per_session = 50
ttl_hours = 168.0
self_echo = "bot"
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| enabled | boolean | true | Whether to automatically record inbound/outbound messages (stops writing when disabled; history remains queryable) |
| max_per_session | int | 50 | Number of entries retained per session (0 = disable trimming for that session) |
| ttl_hours | float | 168.0 | Global retention duration (hours; 0 = never cleaned) |
| self_echo | string | bot | Handling of inbound bot echoes (`self.user_id == user_id`, such as OneBot `report-self-message`): `bot` = record as bot and mark `meta.self_echo`; `skip` = do not record; `user` = record as user (legacy behavior) |

> For risks and auditing of the retention policy, see [Session Inbox](../advanced/transcript.md); attribution fields (`sender` / `meta`) and outbound attribution (`meta.module`) are also covered in that document.

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Configuration Item | Type | Default | Description |
|---------|------|---------|------|
| language | string | auto | Display language for framework built-in text. Set to `auto` to auto-detect the system language, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

## Module Configuration

Each module can define its own configuration in the configuration file:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

Reading and writing configuration in a module:

```python
from ErisPulse import sdk

# Read configuration
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# Write configuration at runtime (delayed save)
sdk.config.setConfig("MyModule.timeout", 60)

# Save to file immediately
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` uses delayed writes by default (batched saves to file roughly every 5 seconds); setting `immediate=True` persists immediately. Configuration changes trigger the `config.set` lifecycle event.

## Scope Configuration (scope)

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Scopes declare "**within what range they take effect**" — which modules are available in a given platform / Bot / session (① module dimension),
whether events from a given user / group / Bot / adapter are accepted (② identity dimension),
and which outbound calls a module can initiate (③ outbound dimension):

```toml
[ErisPulse.scope]
default_allow = true        # Global fallback (false = implicit-deny strict mode; does not affect the outbound dimension)
cache_size = 1024           # LRU cache size

# ① Module dimension (priority: session > Bot > platform; entries support exact / glob / re: regex)
[ErisPulse.scope.platforms.onebot11]
modules = ["Chat", "Tool*"]
blocked = ["re:^Danger"]

# When a child binding sets merge = true, it unions per-entry with lower priorities (default is wholesale override)
[ErisPulse.scope.bots.onebot11."123456"]
modules = ["Music"]
merge = true

# ② Identity dimension (priority: user > session > Bot > adapter; each level writes only allow or deny)
[ErisPulse.scope.identity.adapters.onebot11]
deny = true                 # All events from this platform are dropped at the entry
[ErisPulse.scope.identity.users.onebot11]
allow = ["u_admin"]         # User keys support glob / re: regex
deny = ["u_bad", "spam_*"]

# ③ Outbound dimension (all allowed by default; rules are inline tables; entries support exact / glob / re: regex)
[ErisPulse.scope.actions.MyModule]
send = { deny = true }                    # Forbid all sending
api = { allow = ["get_*"] }               # Only allow query-type standard APIs
request = { deny = true }                 # Forbid handling requests
```

| Configuration Item | Type | Description |
|---------|------|------|
| `scope.default_allow` | boolean | Global fallback: allow/deny (`true`) for modules/identities that do not match any rule |
| `scope.cache_size` | integer | LRU cache size (default 1024) |
| `scope.platforms / bots / sessions` | table | ① Three-level module binding: `{modules=[...], blocked=[...], merge=bool?}` |
| `scope.identity.adapters / bots / sessions / users` | table | ② Four-level identity binding: `{allow=true}` / `{deny=true}` |
| `scope.actions.<module>.<action>` | table | ③ Outbound rules: `{allow=[...], deny=true|[...]}` (actions are send / api / request) |

> For details and runtime APIs (dimension-specific `sdk.scope.set_module()` / `set_identity()` /
> `set_action()`, determination via `is_allowed()` / `is_identity_allowed()` / `is_action_allowed()`,
> and dictionary-style fallbacks `get()` / `set()` / `delete()`), see [Scope](../advanced/scope.md).

## Unified Event Override Configuration (event.overrides)

Unified override system: override the behavior of any module's handlers by **event type**, without changing module code.
OneBot12 standard types (meta / message / notice / request) and extension types (command)
each have their own dedicated overridable parameters:

```toml
[ErisPulse.event.overrides]

# message: text trigger conditions (ANDed with in-code conditions)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "chitchat*"

# notice / request / meta: detail_type whitelist (entries support exact / glob / re: regex)
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command (extension type): implementation parameter overrides (user priority; disabling uniformly goes through acl deny)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true               # Override to framework masters only (false relaxes the developer's master restriction)
hidden = true               # Hidden from the help list
aliases = ["rs"]            # Effective aliases

# acl (command-specific): command user allow/deny lists (command names support glob / re: regex; exact keys take priority)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]  # User identifier "platform:user_id"
deny = ["onebot11:u_bad"]

# ACL fallback: commands without a configured ACL are allowed (true) / strictly denied (false)
acl_default_allow = true
```

| Configuration Item | Type | Description |
|---------|------|------|
| `event.overrides.message.<module>` | table | Text conditions: `{pattern="...", regex="..."}` |
| `event.overrides.notice / request.<module>` | table | `{detail_types=[...], pattern, regex}` |
| `event.overrides.meta.<module>` | table | `{detail_types=[...]}` |
| `event.overrides.command.<module>` | table | Module-level parameter overrides (scalars such as `hidden = true`) |
| `event.overrides.command.<module>.<command>` | table | Command-level overrides (command level takes priority) |
| `event.overrides.acl.<command_name>` | table | User allow/deny lists: `{allow=[...], deny=[...]}` |
| `event.overrides.acl_default_allow` | boolean | ACL fallback: commands without a configured ACL are allowed (`true`) / strictly denied (`false`) |

> For runtime APIs (after `from ErisPulse.Core.Event import overrides`, call type-specific sub-namespaces such as
> `overrides.message.set()` / `overrides.command.set()` / `overrides.acl.set()`,
> or access via `sdk.Event.overrides`),
> see [Event Handling Basics · Event Overrides](../getting-started/event-handling.md#event-overrides-overriding-the-behavior-of-any-event-type-without-changing-module-code).

## Next Steps

- **Continue along the L1 path**: next up is [Exception Handling](../advanced/errors.md), learning to write error handling that won't drag down the framework
- **Don't want to hand-write TOML**: use the `epsdk config` interactive wizard to fill in declarative configuration items; see [CLI Command Reference · config](cli-reference.md#config)
- **Don't want to modify configuration files when deploying**: override configuration items with environment variables, combined with the Docker usage in the [Deployment Guide](deployment.md)