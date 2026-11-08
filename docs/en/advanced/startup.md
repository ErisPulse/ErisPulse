# Startup Flow and Manual Control

> [!TIP]
> **When to read this**: When you need to manually drive the startup chain, customize the startup sequence, or troubleshoot startup failures. Skip if not needed, as it does not affect the use of other features.

The `await sdk.run()` / `await sdk.init()` in ErisPulse encapsulates the entire startup chain into a "one-line" code. However, when you need to fully customize the startup process (e.g., partial loading, dynamic registration, hot-plugging, injecting custom loading strategies), you need to understand what happens inside this chain and how to manually drive each step.

This article breaks down the startup chain into independent components, explains their respective responsibilities, calling order, and provides an example of manual full startup.

> This article assumes you have already run [the first bot](../getting-started/first-bot.md) and understand the two `keep_running` modes of `sdk.run()`. This article focuses on the internal breakdown of the `init()` chain, as well as lower-level entry points such as `init()` / `init_task()` / `init_sync()`.

## Overview of SDK Top-Level Entry Points

In addition to the two `keep_running` modes of `run()`, the SDK provides several lower-level initialization entry points, which differ in **asynchronicity, return value, and whether exceptions are wrapped**:

| Entry Point | Asynchronicity | Return Value | Exception Handling | Use Cases |
|-------------|----------------|--------------|--------------------|-----------|
| `await sdk.run(True)` | async, blocks to maintain | `None` (automatically `uninit` on shutdown) | Module/adapter errors are intercepted, not crashing the process | Pure bot applications |
| `await sdk.run(False)` | async, does not block | `None` (does not automatically unload) | Same as above | Initialize then execute custom logic |
| `await sdk.init()` | async, requires await | `bool` | Internal capture of component exceptions, returns `False` on failure | Manual control of lifecycle (paired with `uninit()`) |
| `sdk.init_task()` | async, returns Task without blocking | `asyncio.Task` | Same as `init()` | Concurrently execute other initializations or when event loop is not running |
| `sdk.init_sync()` | **Synchronous**, blocks current thread | `bool` | Same as `init()` | Command-line scripts, synchronous entry points without event loop |

> **Common misconception**: `await sdk.init()` **is not equivalent** to `await sdk.run(keep_running=False)`. Two differences: ① `init()` returns `bool` (returns `False` on failure), `run()` returns `None`; ② `init()` only performs initialization, **does not automatically unload**, while `run()` automatically `uninit()` when the event loop ends. Therefore, when you need to manually pair unloading or customize the lifecycle, use `init()` + `uninit()`.

## Overview of the Startup Chain

`sdk.init()` (specifically its internal `Initializer.init()`) launches the entire framework in the following order:

```mermaid
flowchart TD
    A[0. Prepare environment<br/>Configuration loading / Exception handling] --> B
    B[1. Parallel discovery and loading<br/>AdapterLoader.load / ModuleLoader.load<br/>Internal call to Finder.find_all] --> C
    C[2. Register adapters<br/>AdapterLoader.register_to_manager] --> D
    D[3. Start adapters<br/>adapter.startup] --> E
    E[4. Register modules<br/>ModuleLoader.register_to_manager] --> F
    F[5. Initialize modules<br/>ModuleLoader.initialize_modules<br/>Instantiation and mounting to sdk] --> G
    G[6. Start routing server<br/>router.start]
```

Corresponding core components:

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| Discovery | `AdapterFinder` / `ModuleFinder` | **Discover** adapters/modules from entry-points of installed packages |
| Loading | `AdapterLoader` / `ModuleLoader` | Discovery + Import + Read metadata + Determine enable/disable, return object lists |
| Registration | `*Loader.register_to_manager` | Register objects to corresponding managers |
| Management | `sdk.adapter` / `sdk.module` | Maintain adapter/module instances, provide start/stop interfaces |
| Initialization | `ModuleLoader.initialize_modules` | Create module instances and mount to `sdk` (handle dependency topological sorting) |
| Routing | `sdk.router` | HTTP / WebSocket server |

> **Important**: `Finder` and `Loader` are two layers. The `Loader` internally **already holds** a `Finder` (e.g., `AdapterLoader` has its own `AdapterFinder`, `ModuleLoader` has its own `ModuleFinder`). In most scenarios, you only need to use `Loader`; only when you need "list only without importing" would you use `Finder` alone.

## Detailed Breakdown of Each Step

### 1. Discovery Layer: Finder

The Finder only finds out which packages provide adapters/modules, without importing or instantiating.

```python
from ErisPulse.finders import AdapterFinder, ModuleFinder

adapter_finder = AdapterFinder()
module_finder = ModuleFinder()

# Find all installed adapters/modules entry-points
adapter_entries = adapter_finder.find_all()    # list[EntryPoint]
module_entries = module_finder.find_all()      # list[EntryPoint]

# Find a single by name
entry = module_finder.find_by_name("MyModule")  # EntryPoint | None
```

Each `EntryPoint` can be loaded via `.load()` to get the corresponding class, but you usually don't need to call it manually—`Loader` handles this.

### 2. Loading Layer: Loader

The Loader does "import + read metadata + determine enable/disable" on top of the Finder.

```python
from ErisPulse.loaders import AdapterLoader, ModuleLoader
from ErisPulse import sdk

adapter_loader = AdapterLoader()
module_loader = ModuleLoader()

# load() internally: calls finder.find_all() → processes each entry-point → returns a triple
adapter_objs, enabled_adapters, disabled_adapters = await adapter_loader.load(sdk.adapter)
module_objs, enabled_modules, disabled_modules = await module_loader.load(sdk.module)
```

The triple returned by `load()`:

| Return Value | Meaning |
|--------------|---------|
| `objs` (`dict`) | Name → Object (adapter class / module wrapper object) |
| `enabled` (`list[str]`) | Enabled names (not disabled in configuration) |
| `disabled` (`list[str]`) | Disabled names |

#### Diagnostic Information on Loading Failures

When a module/adapter throws an exception during loading or initialization, the framework skips that component and continues loading other components, while outputting a **summary of user code frames** so you can locate the error position at the default INFO level without manually turning on DEBUG:

```
[ERROR] [ModuleLoader] Failed to load module MyModule from entry-point, skipped: 'NoneType' object has no attribute 'platform'
  → MyModule/Core.py:42 in on_load
      adapter = sdk.platform
  → AttributeError: 'NoneType' object has no attribute 'platform'
  → Hint: Increase log level to DEBUG to view full stack trace; check implementation code of module MyModule
```

The diagnostic information is generated by the `ErisPulse.runtime.diagnostics` module, automatically filtering out framework internal frames and retaining only your code frames. If you need to reuse it in custom loading logic:

```python
from ErisPulse.runtime import log_diagnostic

try:
    risky_init()
except Exception as e:
    log_diagnostic(e)  # Automatically extract user code frames and write to ERROR log
```

This module also provides two low-level functions: `extract_user_frame()` (returns structured frame information) and `format_diagnostic_block()` (returns multi-line text).

### 3. Registration Layer: register_to_manager

Registers the objects produced by the Loader into the manager so that `sdk.adapter` / `sdk.module` can recognize them.

```python
# Register adapters (returns bool, indicating whether all succeeded)
await adapter_loader.register_to_manager(enabled_adapters, adapter_objs, sdk.adapter)

# Register modules
await module_loader.register_to_manager(enabled_modules, module_objs, sdk.module)
```

After registration, adapters are registered to the adapter manager and modules to the module manager, but they are **not yet started/instantiated**.

### 4. Start Adapters

```python
# Start all registered adapters
await sdk.adapter.startup()
# Or specify a platform
await sdk.adapter.startup("yunhu")
await sdk.adapter.startup(["yunhu", "telegram"])
```

> Registration ≠ Startup. `register_to_manager` only registers; `startup` calls the adapter's `start()`, establishing a connection with the platform.

### 5. Initialize Modules

Modules have an extra step—they need to be **instantiated** and mounted to `sdk` (so you can call `sdk.MyModule.xxx`). This step also handles module dependencies and topological sorting.

```python
success = await module_loader.initialize_modules(
    enabled_modules, module_objs, sdk.module, sdk
)
```

After successful instantiation, modules will appear on `sdk.<ModuleName>`.

### 6. Start Routing Server

```python
await sdk.router.start(
    host="0.0.0.0",
    port=8000,
    ssl_certfile=None,
    ssl_keyfile=None,
)
```

The routing server is responsible for receiving webhook / WebSocket callbacks from adapters. Without starting it, server-mode adapters cannot receive messages.

## Complete Manual Startup Example

The following code is **equivalent** to the core process of `await sdk.init()`, but each step is exposed to you, allowing you to insert custom logic at any step:

```python
import asyncio
from ErisPulse import sdk
from ErisPulse.loaders import AdapterLoader, ModuleLoader

async def manual_startup():
    # 0. Prepare environment (load configuration, register global exception handler)
    #    _prepare_environment is a pre-step inside init(); the manual process must call it first,
    #    otherwise Loader cannot read the configuration and will misjudge all adapters/modules as disabled.
    if not await sdk._prepare_environment():
        print("Environment preparation failed")
        return False

    # 1. Create loaders (each internally holds a Finder)
    adapter_loader = AdapterLoader()
    module_loader = ModuleLoader()

    # 2. Parallel discovery and loading (consistent with internal use of gather in init())
    (adapter_objs, enabled_adapters, disabled_adapters), \
    (module_objs, enabled_modules, disabled_modules) = await asyncio.gather(
        adapter_loader.load(sdk.adapter),
        module_loader.load(sdk.module),
    )

    # 3. Register adapters
    await adapter_loader.register_to_manager(
        enabled_adapters, adapter_objs, sdk.adapter
    )

    # 4. Start adapters
    if enabled_adapters:
        await sdk.adapter.startup()

    # 5. Register modules
    await module_loader.register_to_manager(
        enabled_modules, module_objs, sdk.module
    )

    # 6. Initialize modules (instantiation + mounting to sdk)
    if enabled_modules:
        await module_loader.initialize_modules(
            enabled_modules, module_objs, sdk.module, sdk
        )

    # 7. Start routing server
    await sdk.router.start(host="0.0.0.0", port=8000)

    print("Manual startup completed")
    return True

async def main():
    ok = await manual_startup()
    if ok:
        # Block to maintain (manual process does not automatically block)
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### When to Use Manual Startup?

In most cases, manual startup is **not needed**—`await sdk.run()` has already handled all the above steps. Manual startup is only valuable in these scenarios:

- **Partial loading**: Load only specific adapters/modules, skipping others
- **Dynamic registration**: Register new adapters/modules at runtime based on conditions
- **Custom order**: Need to disrupt the default loading order (e.g., start a module before an adapter)
- **Inject strategies**: Inject custom strict-mode managers, loading strategies, etc., into the Loader
- **Debugging/diagnosis**: Manually drive at a certain step when failure occurs to locate the issue

## Fine-Grained Runtime Control

Even after using `sdk.run()` to complete the startup, you can still individually control subsystems at runtime without restarting the entire SDK:

### Hot Restart/Stop of Adapters

```python
# Hot restart an adapter (fix connection, does not affect other platforms)
await sdk.adapter.shutdown("yunhu")
await sdk.adapter.startup("yunhu")

# Start a new platform at runtime
await sdk.adapter.startup("telegram")

# Temporarily take a platform offline
await sdk.adapter.shutdown("telegram")
```

> `adapter.startup()` requires the adapter to be **registered** to the manager. Registration occurs during `init()`/`run()` internally, so this is fine-grained control after startup.

### Routing Server

```python
# Temporarily take down the webhook server
await sdk.router.stop()

# Restart (e.g., after changing port)
await sdk.router.start(host="0.0.0.0", port=9000)
```

### Modules on Demand

```python
# Manually load a (possibly lazy-loaded) module
await sdk.load_module("MyModule")
```

## Graceful Shutdown

Since version 2.7.0, `sdk.shutdown()` provides **programmatic graceful shutdown**: set a shutdown event to let the main loop suspended by `await sdk.run(keep_running=True)` return, triggering `uninit()` to complete resource cleanup.

```python
# Call from any coroutine to trigger graceful exit (run() suspended returns and automatically uninit)
sdk.shutdown()
```

Typical use cases:

```python
async def shutdown_after_idle():
    await asyncio.sleep(3600)
    sdk.shutdown()  # Gracefully exit after 1 hour of idle
```

**Signal Handling**: `run()` internally registers `SIGTERM` / `SIGHUP` handlers, converting system signals to graceful shutdown—when container orchestration (Docker `docker stop`) or `systemd` stops the service, the process completes `uninit()` cleanup instead of being forcefully killed.

- Windows does not support `loop.add_signal_handler`, so the signal handler is automatically skipped (still use `sdk.shutdown()` or Ctrl+C to trigger shutdown)
- Repeatedly calling `sdk.shutdown()` is safe (no operation after the event is set)

## Unload Process

The reverse operation of startup is `await sdk.uninit()`, which cleans up in the opposite order:

1. Shut down all adapters (`adapter.shutdown()`)
2. Unload all modules
3. Clean up all event handlers
4. Clean up managers and module attributes on SDK

In manual startup scenarios, remember to call `uninit()` before exiting to ensure a graceful shutdown:

```python
try:
    await asyncio.Event().wait()   # Maintain operation
finally:
    await sdk.uninit()
```

## Restart

The SDK provides two restart methods, both of which do not require you to manually unload first— the framework handles it automatically:

| Method | Call | Behavior | Use Cases |
|--------|------|----------|-----------|
| Hot Restart | `await sdk.restart()` | **Code-level hot reload at the component layer** within the same process: all modules follow a unified reload pipeline (global syntax pre-check / snapshot rollback / identity verification), adapters first **re-discover entry-points** (newly installed/uninstalled adapters during runtime take effect immediately) then code-level reload one by one | Pip upgrade or installation of components to make code effective, hot update of modules |
| Hard Restart | `await sdk.hard_restart()` | `uninit()` followed by exiting the process with **exit code 42**, restarted by an external supervisor | Framework self-upgrade (new framework code only takes effect in a new process), C extension side effects, suspected resource leaks |

```python
# Hot restart: component-level code hot reload (most commonly used; newly installed adapters during runtime are also pulled in)
await sdk.restart()

# Hard restart: exit process, handed over to external supervisor (see "Supervisor Guide" below)
await sdk.hard_restart("sdk self-update")  # Optional reason for supervisor display
```

> **Two points to note**:
> 1. These two methods run the restart in the background task and **immediately return `True` indicating "restart task scheduled"**, not "restart completed". The actual restart happens in the background, avoiding interruption of the current event chain.
> 2. The principle of `hard_restart()` is: after unloading and flushing configuration, exit the process with **exit code 42** (`HARD_RESTART_EXIT_CODE`)—**it does not launch a new process itself**. It must be restarted by an external supervisor detecting exit code 42. If you directly run `python main.py` without any supervisor, the process exits with code 42 and **does not automatically restart** (the framework will issue a warning).

> **Hot Restart Mutual Exclusion and Merging** (since 2.11.1): All hot reload operations (single module reload / full reload / adapter reload / hibernation / new plugin hot loading) are mutually exclusive throughout—the save storm does not trigger concurrently when multiple requests are received in quick succession. During an ongoing restart, new requests are automatically merged (requests received during normal reload locking are also merged and queued), and at most one round is completed after the process finishes. When saving a file with syntax errors, the entire reload will be **rejected by a pre-check** before unloading (all error files and line numbers are listed at once), adapter layer skips this round of reload, `restart` fails, and all old instances continue serving; after fixing, `restart` again.

### When to Use Hard Restart?

Hot restart covers most scenarios (pip upgrade/install components, hot update module code, **including newly installed adapters during runtime**). The following scenarios require hard restart:

- **Framework self-upgrade**: After upgrading ErisPulse itself, the new framework code only takes effect in a new process (Python does not re-import loaded framework code).
- **Binary library (C extension) side effects**: Hot restart occurs in the same process and cannot release C extensions, open file descriptors, threads, and other process-level resources; hard restart switches to a new process, completely clearing these side effects.
- **Resource leak diagnosis**: When suspected memory or handle leaks exist, hard restart provides a clean environment.

> The "Framework Restart" feature in the Dashboard management panel internally calls `hard_restart()`.

### Exit Code 42 Contract

Hard restart is cross-process collaboration: **SDK is responsible for exiting (code 42), supervisor is responsible for restarting**.

| Role | Behavior |
|------|----------|
| SDK (during hard restart) | `uninit()` → Flush configuration → Write hard restart marker (reason / PID, for supervisor display) → `os._exit(42)` |
| Supervisor | Detect child process exit code 42 → Display hard restart reason → Restart the same command |

> `sdk.is_supervised()` can query whether the current process was started by a supervisor (detects environment variable `ERISPULSE_SUPERVISED`). The CLI `run` command injects this marker when starting a subprocess; external supervisors like systemd / Docker do not inject it, so `is_supervised()` returns `False`, and the framework will issue a "Supervisor not detected" warning after a hard restart.

### Supervisor Guide

Choose a supervisor suitable for your needs to make hard restart truly effective:

#### 1. CLI run command (development/simple deployment, recommended)

`epsdk run main.py` includes a built-in supervision loop: detects sub-process exit codes, restarts immediately when 42 is detected (and displays the hard restart reason); other abnormal exit codes retry automatically with exponential backoff; `Ctrl+C` first gracefully terminates the sub-process (code 0 is considered normal exit, no restart).

```bash
epsdk run main.py
```

`epsdk run --reload` (development hot-reload mode, since 2.11.1) also follows the "supervisor process + reload worker sub-process" structure: worker internal saves `.py` files to trigger **component-level hot reload** (not full framework restart); hard restart is handled by the supervisor process restarting a new worker, making new code effective after framework upgrade.

#### Fine-Grained Reload Determination (2.12+)

After saving a `.py` file, the smallest reload unit is selected based on runtime source code ownership, not path string guessing:

| Changed File | Handling |
|--------------|----------|
| Plugin directory (within `ErisPulse.framework.plugins_dir`) | Handled by plugin hot-reload watcher, dev watcher does not trigger repeatedly |
| Source code of loaded module (including `pip install -e` and site-packages) | `sdk.reload_module(module name)` |
| Source code of registered adapter | `sdk.reload_adapter(platform name)` |
| Entry script | Process-level restart (exit code 42, restarted by supervisor) |
| Framework source code (within `ErisPulse` package) | Process-level restart |
| Matches multiple owners / cannot be assigned | Conservative process-level restart |

Script mode (`epsdk run main.py --reload`) does not workerize the script: the script sub-process mounts a dev watcher and writes `component_reload_pid` to `.erispulse/runtime.json`; the parent process sees this marker and delegates module/adapter/plugin changes to the sub-process, only restarting the script process when the entry script or framework source code changes.

#### 2. systemd (Linux server)

`RestartForceExitStatus=42` makes exit code 42 trigger a restart (default `on-failure` only works for non-zero codes):

```ini
[Service]
ExecStart=/usr/bin/python3 /opt/mybot/main.py
Restart=on-failure
RestartForceExitStatus=42
RestartSec=2
User=mybot
```

#### 3. Docker / docker-compose

Inside the container, PID 1 is the application process; after exit code 42, the container exits—use `restart` policy to automatically restart it:

```yaml
services:
  bot:
    build: .
    restart: unless-stopped   # Restart on any exit (including 42)
```

#### 4. PM2 (Node ecosystem operations)

```bash
pm2 start main.py --name mybot --interpreter python3
# 42 is treated as an exit code, PM2 defaults to restart; set restart_delay to debounce
pm2 set mybot.restart_delay 2000
```

#### 5. supervisord

```ini
[program:mybot]
command=python3 /opt/mybot/main.py
autorestart=true
exitcodes=0,2,42    # 42 is also considered "normal exit requiring restart"
```

#### 6. Pure Python Custom Supervisor

```python
import subprocess, sys, time

while True:
    p = subprocess.Popen([sys.executable, "main.py"])
    code = p.wait()
    if code == 42:          # Hard restart request
        time.sleep(0.5)
        continue
    if code == 0:           # Normal exit
        break
    time.sleep(3)           # Abnormal exit, backoff retry
```

> **Behavior without supervisor**: Directly running `python main.py`, calling `hard_restart()` exits the process with code 42 and does not restart. In this case, you should integrate with any of the supervisors above.

## Related Documentation

- [Create the First Bot](../getting-started/first-bot.md) - Introduction to the two basic modes of `keep_running`
- [Lifecycle Management](lifecycle.md) - Listen to startup events such as `core.init.start` / `core.init.complete`
- [Lazy Loading System](lazy-loading.md) - Module lazy loading mechanism and `load_module`