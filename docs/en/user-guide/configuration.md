# Configuration File Guide
> This document introduces the framework's configuration files. If third-party modules require configuration, please refer to the module's documentation.

ErisPulse uses TOML format configuration files `config/config.toml` to manage project configuration.

## Configuration File Location

The configuration file is located in the `config/` folder of the project root directory:

```
project/
├── config/
│   └── config.toml
├── main.py
```

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
strict_mode = 1

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

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| host | string | 0.0.0.0 | Listening address; 0.0.0.0 means all interfaces |
| port | integer | 8000 | Listening port number |
| ssl_certfile | string | empty | SSL certificate file path |
| ssl_keyfile | string | empty | SSL private key file path |

## Logging Configuration

```toml
[ErisPulse.logger]
level = "INFO"
log_files = ["app.log", "debug.log"]
memory_limit = 1000
```

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| level | string | INFO | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| format | string | rich | Log output format; defaults to rich colored output |
| log_files | array | empty | List of log output files |
| memory_limit | integer | 1000 | Number of log entries saved in memory |

## Framework Configuration

```toml
[ErisPulse.framework]
enable_lazy_loading = true
uninit_timeout = 30
strict_mode = 1

[ErisPulse.framework.strict_mode_exceptions]
modules = []
adapters = []
```

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| enable_lazy_loading | boolean | true | Whether to enable module lazy loading |
| uninit_timeout | integer | 30 | Graceful shutdown timeout in seconds; if exceeded, forcefully terminate. 0 means no timeout |
| strict_mode | integer | 1 | Strict mode level; see below for "Strict Mode" explanation |

### Strict Mode

Strict mode controls the handling strategy for modules/adapters that are non-compliant or fail during the loading phase. Modern modules/adapters should inherit the corresponding base classes (`BaseModule`/`BaseAdapter`). Components that do not inherit these base classes may affect the framework's context system and cleanup, potentially causing resource leaks. Strict mode is enabled by default to block such components.

| Level | Name | Behavior |
|------|------|------|
| 0 | Permissive | Non-compliance only triggers warnings; components not inheriting base classes will still be attempted to load (for compatibility with old components) |
| 1 | Strict-Skip (Default) | Rejects components not inheriting base classes and skips them; other components start normally |
| 2 | Strict-Fatal | Collects all non-compliant components and reports them collectively, then terminates the entire startup process |

Under each level, component crashes during the "loading/registration/initialization" phases are always skipped; the difference lies in:

- **0 → 1**: The only behavioral change is that components "not inheriting base classes" change from "still loaded" to "skipped".
- **1 → 2**: All non-compliance (not inheriting base classes, loading failure, registration failure, initialization failure, etc.) is upgraded to fatal, and a list of non-compliant components is output at the startup checkpoint and the process is terminated.

#### Exception List

If certain components cannot be migrated temporarily (e.g., due to dependencies on old modules), they can be added to the exception list. Components listed in the exception list will be treated as permissive mode even if they are non-compliant, and will continue to be loaded:

```toml
[ErisPulse.framework.strict_mode_exceptions]
modules = ["SeTu", "SomeLegacyModule"]
adapters = ["OldAdapter"]
```

> When a component is rejected by strict mode, the log will clearly indicate how to restore loading (add to the exception list or lower the level).

## Storage Configuration

```toml
[ErisPulse.storage]
use_global_db = false
```

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| use_global_db | boolean | false | Whether to use the global database (within package) instead of the project database. When `true`, all projects share the ErisPulse package's internal SQLite database; when `false` (default), each project uses a separate database in the `config/` directory |

## Event Configuration

### Command Configuration

```toml
[ErisPulse.event.command]
prefix = "/"
case_sensitive = false
allow_space_prefix = false
must_at_bot = false
```

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| prefix | string | / | Command prefix |
| case_sensitive | boolean | true | Whether to be case sensitive (i.e., whether `/Help` and `/help` are different commands) |
| allow_space_prefix | boolean | false | Whether to allow spaces as prefix |
| must_at_bot | boolean | false | Whether the bot must be mentioned (@bot) to trigger the command (DMs are not restricted) |

### Message Configuration

```toml
[ErisPulse.event.message]
ignore_self = true
```

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| ignore_self | boolean | true | Whether to ignore messages sent by the bot itself |

## Internationalization Configuration

```toml
[ErisPulse.i18n]
language = "auto"
```

| Config Item | Type | Default | Description |
|---------|------|---------|------|
| language | string | auto | Language for displaying framework built-in text. Set to `auto` to automatically detect system language, or set to a specific code: `zh-CN`, `zh-TW`, `en`, `ja`, `ru` |

## Module Configuration

Each module can define its own configuration in the configuration file:

```toml
[MyModule]
api_url = "https://api.example.com"
timeout = 30
enabled = true
```

Reading and writing configuration in modules:

```python
from ErisPulse import sdk

# Read config
config = sdk.config.getConfig("MyModule", {})
api_url = config.get("api_url", "https://default.api.com")

# Runtime write config (delayed save)
sdk.config.setConfig("MyModule.timeout", 60)

# Save to file immediately
sdk.config.setConfig("MyModule.timeout", 60, immediate=True)
```

> `setConfig` defaults to delayed writing (batch saving to file every ~5 seconds). Setting `immediate=True` will persist immediately. Configuration changes trigger the `config.set` lifecycle event.

## Next Steps

- [CLI Command Reference](cli-reference.md) - Learn about all command line commands
- [Developer Guide](../developer-guide/) - Learn how to develop custom modules