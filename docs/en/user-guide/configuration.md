# Configuration File Documentation
> This document will introduce the framework's configuration file. If third-party modules require configuration, please refer to their respective documentation.

ErisPulse uses a TOML-formatted configuration file `config/config.toml` to manage project configurations.

## Configuration File Location

The configuration file is located in the `config/` folder at the root of the project:

```
project/
├── config/
│   └── config.toml
├── main.py
```

## Configuration Loading Error Handling

The framework distinguishes three error states when loading `config.toml` and provides **actionable diagnostic information**, rather than silently falling back to default configurations:

| Error State | Trigger Condition | Framework Behavior |
|-------------|-------------------|--------------------|
| File Missing | `config.toml` does not exist | Normal first-time startup, silently uses empty configuration (no warning) |
| TOML Syntax Error | File exists but format is invalid (e.g., missing quotes, unclosed parentheses) | Outputs **line/column number and reason** of error, and indicates fallback to default configuration |
| Permission/Other Error | No read permission, IO error, etc. | Outputs **clear reason**, and indicates fallback to default configuration |

For example, if you accidentally write a configuration as `port = 8000` (missing quotes for a string), the log will output something like:

```
[ERROR] [Config] Syntax error in configuration file config/config.toml (line 3, column 1): ...
[WARNING] [Config] Fallback to default configuration, your custom settings did not take effect — please fix and restart
```

This allows you to immediately locate issues at the **default INFO level**, without confusion about why your modified configuration did not take effect.

> **Editing the configuration file during runtime?** If you manually edit `config.toml` during robot operation and introduce a syntax error, the framework will output "Configuration file is corrupted (syntax error, line X), unable to merge and write — please fix the configuration file and restart" during the next write (merge configuration), instead of a confusing "write failed". The configuration items to be written will be retained, and nothing will be lost.

## Environment Variable Override

The framework supports using environment variables to **override** `ErisPulse.*` configuration items (suitable for Docker / containerization / CI deployment, without modifying `config.toml`).

Naming rule: Convert the dot-separated path `ErisPulse.<section>.<key>` to all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|----------------------|----------------------|---------------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

Behavior description:
- **Highest priority**: Environment variables override "configuration file" and "default values", automatically converting to the original value type (`bool` / `int` / `float` / comma-separated `list` / string)
- **Non-persistent**: Overriding only takes effect during runtime, and will not be written back to `config.toml`
- **Supports hot updates**: After modifying environment variables during runtime, combined with configuration monitoring reload, changes will take effect

```bash
# Docker deployment example: Do not modify config.toml, directly override port
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: Framework configuration such as `ErisPulse.server.port` is read through APIs like `get_server_config()`, and is affected by environment variable overrides.

## Configuration Hot Update

Starting from version 2.7.0, the framework provides **systematic support** for configuration hot updates. After external modification of `config.toml` (background watcher checks every 5 seconds), or after code calls `setConfig()`, each component automatically responds:

| Component | Hot-updatable Configuration | Behavior |
|-----------|-----------------------------|----------|
| **Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | Automatically reapply (with change detection) |
| **Command System CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter Concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphores, rebuilds with new value |
| **Proactive GC** | `framework.proactive_gc_interval` | Reads each round, supports runtime adjustment/disable |
| **Module/Adapter Configuration** | Their own configuration items | Triggers `on_config_update(old, new)` callback |

**Configuration items requiring restart** (cannot be safely switched at runtime, warning is output when changed "requires process restart to take effect"):

| Configuration | Reason |
|---------------|--------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely switched at runtime |
| `storage.use_global_db` | SQLite file handle is already open at runtime, switching path is unsafe |

> **Error during editing and saving?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, and will not broadcast an empty configuration to each component (to avoid `on_config_update` receiving empty values and mistakenly reverting to default).

## Complete Configuration Example

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = ""
ssl_keyfile = ""

[ErisPulse.logger]
level = "INFO"
format = "rich"
log_files = []
memory_limit = 1000

[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 0

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []

[ErisPulse.storage]
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
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| Configuration Item | Type | Default Value | Description |
|----------------------|------|---------------|-------------|
| host | string | 0.0.0.0 | Listening address; 0.0.0.0 means all interfaces |
| port | integer | 8000 | Listening port number |
| ssl_certfile | string | empty | Path to SSL certificate file |
| ssl_keyfile | string | empty | Path to SSL private key file |

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| Configuration Item | Type | Default Value | Description |
|----------------------|------|---------------|-------------|
| level | string | INFO | Log level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed internal debugging information) |
| format | string | rich | Log output format; defaults to rich colored output |
| log_files | array | empty | List of log output files |
| memory_limit | integer | 1000 | Number of log entries saved in memory |

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
|----------------------|------|---------------|-------------|
| enable_lazy_loading | boolean | true | Whether to enable lazy loading of modules |
| uninit_timeout | integer | 30 | Total timeout for graceful shutdown (seconds); if exceeded, forcibly terminate. 0 means no timeout is set |
| strict_mode | integer | 0 | Strict mode level; see "Strict Mode" description below |

### Strict Mode

Strict mode controls the handling strategy for modules/adapters that are non-compliant or fail during the loading phase. Modern modules/adapters should inherit corresponding base classes (`BaseModule`/`BaseAdapter`). Components that do not inherit base classes affect the framework's context system and fallback cleanup, potentially causing resource leaks.

> **Change in 2.5.2**: The default level is adjusted from `1` (skip) to `0` (lenient) to reduce loading issues for new users. Components that do not inherit base classes will be warned and still attempted to load, rather than directly rejected. To restore the old behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|-------|------|----------|
| 0 | Lenient (default) | Non-compliance only warns; components that do not inherit base classes will still be attempted to load (compatible with old components) |
| 1 | Strict-Skip | Rejects components that do not inherit base classes and skips them; other components start normally |
| 2 | Strict-Fatal | Collects all non-compliance and reports them together, then terminates the entire startup |

Under all levels, component crashes during the "loading/registration/initialization phase" are always skipped; the difference is:

- **0 → 1**: The only behavioral change is that "not inheriting base class" changes from "still loading" to "skipping".
- **1 → 2**: All non-compliance (not inheriting base class, loading failure, registration failure, initialization failure, etc.) is upgraded to fatal, and a list of non-compliant components is output at the startup checkpoint before termination.

#### Exemption List

If certain components cannot be migrated temporarily (e.g., depending on old modules), they can be added to the exemption list. Components listed will be treated leniently even if non-compliant, and continue loading:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly indicate how to restore loading (add to exemption list or lower the level).

## Storage Configuration

```toml
[ErisPulse.storage]
use_global_db = false
```

| Configuration Item | Type | Default Value | Description |
|----------------------|------|---------------|-------------|
| use_global_db | boolean | false | Whether to use a global database (within package) instead of the project database. When `true`, all projects share the SQLite database within the ErisPulse package; `false` (default) means each project uses an independent database in the `config/` directory |

## Event Configuration

### Command Configuration

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| Configuration Item | Type | Default Value | Description |
|----------------------|------|---------------|-------------|
| prefix | string | / | Command prefix |
| case_sensitive | boolean | true | Whether to distinguish case (`/Help` and `/help` as different commands) |
| allow_space_prefix | boolean | false | Whether to allow spaces as prefix |
| must_at_bot | boolean | false | Whether to require mentioning the bot to trigger commands (private chat is unrestricted) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Configuration Item | Type | Default Value | Description |
|----------------------|------|---------------|-------------|
| ignore_self | boolean | true | Whether to ignore the robot's own messages |

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Configuration Item | Type | Default Value | Description |
|----------------------|------|---------------|-------------|
| language | string | auto | Display language for framework built-in text. Set to `auto` to automatically detect system language, or set to specific codes: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

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

> `setConfig` defaults to delayed writing (batch saved to file approximately every 5 seconds). Setting `immediate=True` will persist immediately. Configuration changes will trigger the `config.set` lifecycle event.

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn all command-line commands
- [Developer Guide](../developer-guide/) - Learn how to develop custom modules