# Configuration File Documentation
> This document will introduce the framework's configuration file. If third-party modules require configuration, please refer to the module's documentation.

ErisPulse uses a TOML-formatted configuration file `config/config.toml` to manage project configurations.

Please directly return the complete translated Markdown content without including any other text.

Once again, please note: If the document contains language switch lines (lines with language names separated by `` | ``), be sure to strictly follow the format requirements above in item 8, and do not write incorrect formats such as ``[**Label**](file)``.

## Configuration File Location

The configuration file is located in the `config/` folder at the root of the project:

```
project/
├── config/
│   └── config.toml
├── main.py
```

Please directly return the complete translated Markdown content, without including any other text.

Once again, if the document contains language switch lines (lines with language names separated by `` | ``), be sure to strictly follow the format requirements in item 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## Configuration Loading Error Handling

The framework distinguishes three error states when loading `config.toml`, providing **actionable diagnostic information** instead of silently falling back to default configurations:

| Error State | Trigger Condition | Framework Behavior |
|-------------|-------------------|--------------------|
| File Missing | `config.toml` does not exist | On normal first startup, silently use an empty configuration (no warning issued) |
| TOML Syntax Error | File exists but has invalid format (e.g., missing quotes, unclosed parentheses) | Output **line/column number and reason for error**, and indicate that default configuration has been reverted |
| Permission/Other Errors | No read permission, IO errors, etc. | Output **clear reason**, and indicate that default configuration has been reverted |

For example, if you accidentally write the configuration as `port = 8000` (missing quotes around the string), the log will output something similar to:

```
[ERROR] [Config] Syntax error in configuration file config/config.toml (line 3, column 1): ...
[WARNING] [Config] Failed to read configuration file. Continuing with last valid configuration; changes in this file were not applied—please fix and reload or restart
```

This allows you to immediately identify the issue at the **default INFO level**, rather than being confused about why your configuration changes did not take effect.

> **What if you accidentally corrupt the configuration file while the bot is running?** If you manually edit `config.toml` during runtime and introduce a syntax error, the framework will output "Configuration file is corrupted (syntax error, line X), unable to merge and write—please fix the configuration file and restart" on the next write (merge configuration), instead of the confusing "write failed". The configuration items awaiting write will be preserved and will not be lost.

Please directly return the complete translated Markdown content without any additional text.

## Environment Variable Override

The framework supports **overriding** `ErisPulse.*` configuration items using environment variables (suitable for Docker / containerization / CI deployment, without modifying `config.toml`).

Naming convention: Convert the dot-separated path `ErisPulse.<section>.<key>` to all uppercase, replace `.` with `_`, and add the `ERISPULSE_` prefix:

| Configuration Item | Environment Variable | Example Value |
|--------------------|----------------------|---------------|
| `ErisPulse.server.port` | `ERISPULSE_SERVER_PORT` | `9000` |
| `ErisPulse.server.host` | `ERISPULSE_SERVER_HOST` | `0.0.0.0` |
| `ErisPulse.logger.level` | `ERISPULSE_LOGGER_LEVEL` | `DEBUG` |
| `ErisPulse.framework.strict_mode` | `ERISPULSE_FRAMEWORK_STRICT_MODE` | `false` |

Behavior description:
- **Highest priority**: Environment variables override "configuration file" and "default values", automatically converting to the original value type (`bool` / `int` / `float` / comma-separated `list` / string)
- **Non-persistent**: The override only takes effect during runtime and is not written back to `config.toml`
- **Supports hot reload**: After modifying environment variables during runtime, the changes take effect when combined with configuration monitoring reload

```bash
# Docker deployment example: Do not modify config.toml, directly override the port
ERISPULSE_SERVER_PORT=9000 docker compose up -d
```

> Note: Framework configurations such as `ErisPulse.server.port` that are read via APIs like `get_server_config()` are all affected by environment variable overrides.

Please directly return the complete translated Markdown content, without any additional text.

Once again, if the document contains language switch lines (with each language name separated by `` | ``), strictly follow the format requirement above in point 8, and do not write incorrect formats such as ``[**Label**](file)``.

## Configuration Hot Reload

Starting from version 2.7.0, the framework provides **systematic support** for configuration hot reload. After external modification of `config.toml` (background watcher checks every 5 seconds), or after code calls `setConfig()`, components automatically respond:

| Component | Configurations Supporting Hot Reload | Behavior |
|-----------|--------------------------------------|----------|
| **Logger** | `logger.level` / `log_files` / `memory_limit` / `format` | Automatically re-applied (with change detection) |
| **Command System CommandHandler** | `event.command.prefix` / `case_sensitive` / `allow_space_prefix` / `must_at_bot` | Takes effect on the next message |
| **Adapter Concurrency** | `framework.handler_max_concurrency` | Invalidates cached semaphore, rebuilds with new value |
| **Proactive GC** | `framework.proactive_gc_interval` | Re-reads each round, supports runtime adjustment/disable |
| **Master System Master** | `master.users` | Each `is_master()` check reads real-time, no restart required |
| **Module/Adapter Configurations** | Their respective configuration items | Triggers `on_config_update(old, new)` callback |

**Configurations Requiring Restart** (cannot be safely hot-swapped; warning "Process needs to be restarted for changes to take effect" is output when changed):

| Configuration | Reason |
|---------------|--------|
| `router.cors.*` / `router.security.*` | Middleware is written into FastAPI at service startup, cannot be safely hot-swapped at runtime |
| `storage.use_global_db` | SQLite file handle is already open at runtime, switching path is unsafe |

> **Error occurred during editing and saving?** If a transient syntax error occurs while editing `config.toml`, the framework will **retain the last valid configuration** and output diagnostic logs, and will not broadcast an empty configuration to components (to avoid `on_config_update` receiving empty values and mistakenly reverting to default).

7. **Path Replacement Rule**
   - Replace `docs/en/` in document links with `docs/en/`
   - Example: `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`
   - For links pointing to non-current language version files (e.g., `README.xx.md`), keep them unchanged
   - This ensures links point to the correct language version of the document

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

## Server Configuration

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000
ssl_certfile = "/path/to/cert.pem"
ssl_keyfile = "/path/to/key.pem"
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| host | string | 0.0.0.0 | Listening address, 0.0.0.0 means all interfaces |
| port | integer | 8000 | Listening port number |
| ssl_certfile | string | empty | Path to SSL certificate file |
| ssl_keyfile | string | empty | Path to SSL private key file |

Please directly return the translated complete Markdown content, without including any other text.

Once again, if the document contains language switching lines (lines with language names separated by `` | ``), be sure to strictly follow the format requirement in the above item 8, and do not write the incorrect format of ``[**Label**](file)``.

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| level | string | INFO | Logging level: TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL (TRACE is the lowest level, outputs detailed internal debugging information) |
| format | string | rich | Logging output format: `rich` (colored, default), `plain` (plain text without color, suitable for log collection/pipeline redirection), `json` (JSON structured, suitable for ELK, etc.) |
| log_files | array | empty | List of log output files |
| memory_limit | integer | 1000 | Number of log entries saved in memory |

Please directly return the complete translated Markdown content, without including any other text.

Once again, if the document contains language switch lines (lines with language names separated by `` | ``), strictly follow the above rule #8 and do not write incorrect formats such as ``[**Label**](file)``.

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
| uninit_timeout | integer | 30 | Total timeout (in seconds) for graceful shutdown, after which the process is forcibly terminated. 0 means no timeout is set |
| strict_mode | integer | 0 | Strict mode level, see the "Strict Mode" section below |

### Strict Mode

The strict mode controls the handling strategy for modules/adapters that are non-compliant or fail during the loading phase. Modern modules/adapters should inherit their corresponding base classes (`BaseModule`/`BaseAdapter`). Components that do not inherit from the base class may affect the framework's context system and fallback cleanup, potentially leading to resource leaks.

> **2.5.2 Change**: The default level has been adjusted from `1` (skip) to `0` (lenient) to reduce loading issues for new users during their first use. Components that do not inherit from the base class will be warned and attempted to load, rather than being directly rejected. If you wish to restore the previous behavior, explicitly set `strict_mode = 1`.

| Level | Name | Behavior |
|------|------|------|
| 0 | Lenient (default) | Non-compliant components are only warned, and components that do not inherit from the base class will still be attempted to load (compatible with old components) |
| 1 | Strict-Skip | Reject components that do not inherit from the base class and skip them, while starting the rest normally |
| 2 | Strict-Fatal | Collect all non-compliant components and report them together, then terminate the entire startup process |

Under each level, component crashes such as errors during "loading/registration/initialization" will always be skipped; the difference lies in:

- **0 → 1**: The only behavioral change is that "not inheriting from the base class" changes from "still loading" to "skipping".
- **1 → 2**: All violations (not inheriting from the base class, loading failure, registration failure, initialization failure, etc.) are upgraded to fatal, and after collecting them at the startup checkpoint, the violation list is output once and the process is terminated.

#### Exemption List

If certain components cannot be migrated temporarily (for example, due to dependencies on old modules), they can be added to the exemption list. Components listed in the exemption list will be treated as lenient mode even if they are non-compliant, and will continue to be loaded:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly indicate how to restore loading (add to the exemption list or lower the level).

Please directly return the complete translated Markdown content, without including any other text.

## Storage Configuration

```toml
[ErisPulse.storage]
use_global_db = false
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| use_global_db | boolean | false | Whether to use the global database (within the package) instead of the project database. When set to `true`, all projects share the SQLite database within the ErisPulse package; when set to `false` (default), each project uses an independent database in the `config/` directory |

Please directly return the fully translated Markdown content, without any additional text.

Once again, please note: if the document contains language switching lines (with each language name separated by `` | ``), strictly follow the formatting requirements in the above point 8 and do not write incorrect formats such as ``[**Label**](file)``.

## Event Configuration

### Command Configuration

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| prefix | string | / | Command prefix |
| case_sensitive | boolean | true | Whether to distinguish case (whether `/Help` and `/help` are different commands) |
| allow_space_prefix | boolean | false | Whether to allow space as prefix |
| must_at_bot | boolean | false | Whether the command must be triggered by mentioning the bot (not restricted in private chats) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| ignore_self | boolean | true | Whether to ignore messages sent by the bot itself |

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Configuration Item | Type | Default Value | Description |
|---------|------|---------|------|
| language | string | auto | The display language for framework built-in text. Set to `auto` to automatically detect the system language, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

## Module Configuration

Each module can define its own configuration in the configuration file:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

Reading and writing configuration within the module:

```python
from ErisPulse import sdk

# Reading configuration
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# Writing configuration at runtime (delayed save)
sdk.config.setConfig("MyModule.timeout", 60)

# Saving immediately to file
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> By default, `setConfig` uses delayed writing (approximately batch saving to file every 5 seconds). Setting `immediate=True` will persist immediately. Configuration changes will trigger the `config.set` lifecycle event.

Please replace paths in document links by replacing `docs/en/` with `docs/en/`. For example, `docs/en/quick-start.md` should be changed to `docs/en/quick-start.md`. For links pointing to files of non-current language versions (such as `README.xx.md`), keep them unchanged to ensure links point to the correct language version of the document.

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn about all command-line commands
- [Developer Guide](../developer-guide/) - Learn how to develop custom modules

Please directly return the complete translated Markdown content, without including any other text.

Once again, please note: If the document contains a language switch line (with language names separated by `` | ``), be sure to strictly follow the format requirements in the above rule 8, and do not write the incorrect format ``[**Label**](file)``.