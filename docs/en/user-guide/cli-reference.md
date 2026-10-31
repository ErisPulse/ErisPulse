# CLI Command Reference

> [!TIP]
> **When to read this**: Consult it when you forget the arguments of an `epsdk` command, want to script component management, or need to control run / stop / restart behavior. If your daily usage is limited to `init` / `install` / `run`, remembering one thing is enough: `epsdk <command> --help` shows argument descriptions anytime—no need to read this document end to end.

`epsdk` is the command-line tool for ErisPulse: initializing projects, installing / upgrading modules and adapters, interactively configuring components, running and stopping bots, and diagnosing the environment—all under this single command.

> **Tip**: The main help of `epsdk` (without a command) is grouped by category: **Project** (init / create / run), **Component Management** (install / uninstall / upgrade / list / list-remote / types), **Configuration & Diagnostics** (config / doctor / i18n), **Other** (self-update / version).

---

## Package Management Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `install` | `i`, `add` | `[package]... [--upgrade/-U] [--pre] [-e PATH] [--user] [--no-deps] [-t DIR] [--index-url URL] [--extra-index-url URL] [--no-cache-dir] [-r FILE] [-c FILE] [--force-reinstall] [--ignore-installed] [--compile/--no-compile] [--prefix DIR] [--src DIR] [--config-settings SETTINGS] [--no-binary FORMAT] [--only-binary FORMAT] [--prefer-binary] [--build-isolation/--no-build-isolation] [--upgrade-strategy {eager,only-if-needed,to-satisfy-only}] [--break-system-packages] [--no-uv]` | Install modules/adapters |
| `uninstall` | `rm`, `remove` | `<package>... [--no-uv]` | Uninstall modules/adapters |
| `upgrade` | `up` | `[package]... [--force/-f] [--pre] [--no-uv]` | Upgrade specified modules or all |
| `self-update` | `su`, `update` | `[version] [--pre] [--force/-f] [--no-uv]` | Update the SDK itself |

## Diagnostic Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `doctor` | `diag` | `[--verbose] [--fix]` | Diagnose the environment and output a health report; `--fix` attempts automatic repair |

### install

Install ErisPulse module or adapter packages. If no package name is specified, an interactive installation interface is launched.

**Aliases:** `i`, `add`

> **uv project integration** (2.11.1+): Inside a uv-managed project (where `uv.lock` or `[tool.uv]` exists),
> `install` / `upgrade` / `uninstall` automatically switch to `uv add` / `uv remove`—dependencies are written to both
> `pyproject.toml` and `uv.lock`, so `uv sync` no longer wipes out components installed by epsdk; on failure it automatically
> falls back to the uv pip / pip channel. Arguments unsupported by uv, such as `--user`, go directly through pip. Target environment resolution order:
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → project `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → current interpreter (`epsdk doctor` shows the full decision chain).

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to install; multiple can be specified |
| `--upgrade` | `-U` | Upgrade to the latest version during installation |
| `--pre` | | Allow installing pre-release versions |
| `--editable` | `-e` | Install in editable mode (path required) |
| `--user` | | Install to the user site-packages directory |
| `--no-deps` | | Do not install dependencies |
| `--target` | `-t` | Install to the specified directory |
| `--index-url` | | Specify the PyPI mirror URL |
| `--extra-index-url` | | Additional PyPI mirror URLs (can be specified multiple times) |
| `--no-cache-dir` | | Disable the cache |
| `--requirement` | `-r` | Install from a requirements file |
| `--constraint` | `-c` | Install from a constraints file |
| `--force-reinstall` | | Force reinstall |
| `--ignore-installed` | | Ignore installed packages |
| `--compile` | | Compile .pyc files after installation |
| `--no-compile` | | Do not compile .pyc files after installation |
| `--prefix` | | Install to the specified prefix directory |
| `--src` | | Source directory used for editable installs |
| `--config-settings` | | Configuration passed to the build backend (can be specified multiple times) |
| `--no-binary` | | Restrict use of binary packages (format such as `:all:`) |
| `--only-binary` | | Restrict to binary packages only (format such as `:all:`) |
| `--prefer-binary` | | Prefer binary packages |
| `--build-isolation` | | Enable build isolation |
| `--no-build-isolation` | | Disable build isolation |
| `--upgrade-strategy` | | Upgrade strategy: `eager`, `only-if-needed`, `to-satisfy-only` |
| `--break-system-packages` | | Allow modifying Python packages managed by the system package manager |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Install and upgrade from a mirror
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install in editable mode (development mode)
epsdk install -e ./my-adapter
```

### uninstall

Uninstall installed ErisPulse module or adapter packages. If no package name is specified, an interactive uninstall interface is launched.

**Aliases:** `rm`, `remove`

**Arguments:**

| Argument | Description |
|------|------|
| `<package>...` | Package names to uninstall; multiple can be specified |
| `--no-uv` | Use pip instead of uv |

**Examples:**

```bash
# Uninstall a single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### upgrade

Upgrade installed ErisPulse components. If no package name is specified, upgrade all interactively.

**Aliases:** `up`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to upgrade; multiple can be specified |
| `--force` | `-f` | Force upgrade, skip confirmation |
| `--pre` | | Allow upgrading to pre-release versions |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Upgrade all packages
epsdk upgrade

# Upgrade a specific package
epsdk upgrade Weather

# Force upgrade (skip confirmation)
epsdk upgrade -f
```

### self-update

Update the ErisPulse SDK itself to the latest version.

**Aliases:** `su`, `update`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[version]` | | Specify the target version to update to |
| `--pre` | | Allow updating to pre-release versions |
| `--force` | `-f` | Force update, skip confirmation |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Update to the latest stable version
epsdk self-update

# Update to a specific version
epsdk self-update 1.2.3

# Allow pre-release versions
epsdk self-update --pre

# Force update
epsdk self-update -f
```

> [!NOTE]
> When installed via `uv tool install ErisPulse`, this command automatically switches to `uv tool upgrade ErisPulse` (or `uv tool install ErisPulse==<version> --force` when a version is specified), since a direct pip upgrade of the tool environment would be wiped out by uv's manifest restoration.
> On Windows, the update runs in a new console window: the current CLI must exit first to release the tool environment files; after the window indicates completion, simply reopen the terminal.

---

## Information Query Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `list` | `l`, `ls` | `[--type/-t {modules,adapters,all}] [--outdated/-o]` | List installed components |
| `list-remote` | `lsr` | `[--type/-t {modules,adapters,all}] [--refresh/-r]` | List remotely available components |
| `version` | `ver` | | Show SDK and Python version information (equivalent to `-V`) |

### list

List installed ErisPulse modules and adapters.

**Aliases:** `l`, `ls`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--outdated` | `-o` | Show only upgradable packages |

**Examples:**

```bash
# List all installed components
epsdk list

# List modules only
epsdk list -t modules

# List adapters only
epsdk list -t adapters

# Show only upgradable packages
epsdk list -o
```

### list-remote

List ErisPulse modules and adapters available in remote repositories.

**Aliases:** `lsr`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` (default) |
| `--refresh` | `-r` | Force refresh of the remote package list cache |

**Examples:**

```bash
# List all remotely available components
epsdk list-remote

# List remote modules only
epsdk list-remote -t modules

# Force refresh the cache before listing
epsdk list-remote -r
```

---

## Configuration Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | Interactively configure declarative config entries of adapters/modules |

### config

Interactively fill in the declarative config entries of adapters/modules. The wizard is driven by the config classes declared by the adapter/module (`ConfigClass` / `AccountConfigClass`), automatically generating and validating forms—no need to hand-write config.toml.

Adapters additionally support multi-account (bot account) management: adding/editing/deleting accounts, and enable/disable switches.

**Aliases:** `cfg`, `conf`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[name]` | | Target name (adapter platform name or module name); leave empty to enter interactive selection |
| `--list` | `-l` | Only list the configuration status of all targets without entering the wizard |
| `--json` | | Output all targets and their configuration status as JSON (for CI / script consumption) without entering the wizard |

**Examples:**

```bash
# View the configuration status of all adapters/modules
epsdk config --list

# Output configuration status as JSON (for CI / script consumption)
epsdk config --json

# Interactively select a target to configure
epsdk config

# Directly configure a specific adapter
epsdk config yunhu

# Directly configure a specific module
epsdk config MyModule
```

**Notes:**

- Configuration status has four levels: `Ready` (validation passed), `Incomplete` (required fields missing or validation failed), `Not Configured` (never generated), `No Configuration` (target declares no config class)
- Field values carry a source annotation: existing configuration shows `(current: value)`, and when unconfigured the schema default is shown as `(default: value)`; pressing Enter directly keeps that value
- Secret-type fields (declared with `secret`) are not echoed during input; pressing Enter keeps the already-set value
- In interactive selection mode, after a single wizard finishes it returns to the selection menu (with refreshed status), allowing you to configure multiple targets consecutively; leave empty to exit
- If global form validation fails and you abandon re-filling, the wizard aborts without writing any configuration (avoiding a half-finished state of "enabled but incomplete configuration")
- After saving, it is immediately written to `config/config.toml`, visible to both the Dashboard and the running SDK; running adapters that need to apply new account configuration can pick it up by restarting the process
- After `epsdk install` (interactive installation) and `epsdk init` successfully install an adapter, if a configuration declaration is detected, this wizard is automatically invoked; when installing by directly specifying package names on the command line, only a configuration hint is printed

---

## Run Control Commands

> [!TIP]
> `epsdk run` automatically detects and uses the `.venv` virtual environment in the project directory to run the bot
> (you can also explicitly specify an interpreter via the `ERISPULSE_PYTHON` environment variable). `epsdk install` /
> `uninstall` / `upgrade` / `list` likewise operate on the project virtual environment.

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | Run the specified script or the SDK |
| `stop` | — | `[--force] [--pid PID]` | Stop the running instance (started by `epsdk run`) |
| `restart` | — | `[--force] [--pid PID]` | Restart the running instance (stop, then relaunch with the original arguments) |

### run

Run an ErisPulse project script or start the SDK directly. Hot reload mode is supported.

**Aliases:** `r`

**Arguments:**

| Argument | Description |
|------|------|
| `[script]` | Script file to run; if not specified, runs the SDK |
| `--reload` | Enable hot reload mode: monitoring file changes automatically triggers component-level code hot reload (no full process restart needed); by default directories like `.venv`/`.git` are ignored (configurable via `ErisPulse.framework.watch_ignore_dirs`), and the plugins directory is handled precisely by the plugin hot-reload watcher |
| `--strict` / `--no-strict` | Temporarily enable / disable strict mode (effective for this run only, not written to config); by default follows `ErisPulse.framework.strict_mode` |

**Examples:**

```bash
# Run the SDK directly
epsdk run

# Run a specific script file
epsdk run main.py

# Run in hot reload mode (file changes automatically trigger code-level hot reload)
epsdk run main.py --reload

# SDK hot reload mode
epsdk run --reload

# Temporary strict mode: exit if the pre-start self-check fails, framework strictness raised to at least 1 for this run
epsdk run main.py --strict

# Temporary relaxed mode (strict_mode is on in config but you just want to get running this time)
epsdk run main.py --no-strict
```

**Pre-start self-check:** Before starting, `run` quickly checks the parseability of `config/config.toml` and the completeness of required configuration for installed components; strictness defaults to `ErisPulse.framework.strict_mode` (when non-zero, a failed check exits immediately; when 0, it only warns and continues). A missing config file is treated as a normal first launch—only a hint is shown, not judged as a failure. `--strict` temporarily enables it: exit immediately if the pre-check fails, and raise the framework strictness level to at least 1 for this run (non-compliant components are skipped, propagated to the running process via the `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable, not written to the config file); `--no-strict` conversely temporarily relaxes it. The self-check skips itself automatically when it encounters its own errors, involves no network probing, and never blocks startup.

> **Supervision structure of `--reload`** (since 2.11.1): `epsdk run --reload` runs as a "supervisor process + reload worker subprocess". Hot reloads triggered by saving `.py` files all happen inside the worker (mutually exclusive serialization, burst coalescing); syntax errors on the module side are rejected by an upfront pre-check, and the old instance keeps serving. When `sdk.hard_restart()` is called, the worker exits with code 42, and after the supervisor displays the reason it automatically pulls up a brand-new worker—after upgrading the framework itself, the new code takes effect immediately.

### stop

Stop a running ErisPulse instance (started by `epsdk run` and executed in the same project directory).
When `run` starts, it writes the supervisor process PID, the current framework subprocess PID, and the original launch command into
`.erispulse/runtime.json`, which `stop` uses to locate the instance.

**Stop sequence:** On POSIX, SIGINT is first sent to the supervisor process (the same graceful shutdown path as Ctrl+C—the
finally chain automatically terminates the framework subprocess), escalating step by step to SIGTERM / SIGKILL on timeout; Windows has no
process signal semantics, so the framework subprocess is terminated first and then the supervisor process (to prevent the supervisor from misjudging the force kill as a crash
and respawning).

**Arguments:**

| Argument | Description |
|------|------|
| `--force` | Skip graceful stop, terminate forcibly |
| `--pid PID` | Directly specify the target process PID (overrides the runtime state file, for non-standard launch methods) |

**Examples:**

```bash
# Stop the running instance of the current project
epsdk stop

# Force terminate
epsdk stop --force
```

### restart

Restart the running ErisPulse instance: after stopping with `stop` semantics, relaunch with the
**original launch command** recorded in the state file (taking over the current terminal in the foreground; the new instance writes a new runtime state file).

**Arguments:** Same as `stop` (`--force` / `--pid PID`).

**Examples:**

```bash
# Graceful restart (make pip-upgraded adapters/modules take effect; running modules can also use
# sdk.reload_module / sdk.adapter.reload code-level hot reload, no restart needed)
epsdk restart
```

> [!NOTE]
> Launch methods such as `python main.py` that bypass `epsdk run` do not write the runtime state file—manage such
> processes with system tools, or specify the PID with `epsdk stop --pid <PID>`.

---

## Project Management Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | Initialize an ErisPulse project |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | Create module/adapter scaffolding; `pack` converts a local plugin into a publishable project |

### init

Initialize a new ErisPulse project. Supports interactive and quick modes; since 2.8.4 it generates `pyproject.toml` (dependency manifest), optionally creates a project `.venv` virtual environment and installs the framework and adapters, and supports **specifying any directory**.

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[path]` | | Target path (may include a parent directory, e.g. `../apps/mybot`; a bare name is equivalent to `--project-name`) |
| `--project-name` | `-n` | Project name |
| `--path` | | Project parent directory (combined with `-n` to specify the creation location) |
| `--adapter` | `-a` | Preselect adapters to install (repeatable or comma-separated); when provided, skips adapter prompting and selection |
| `--quick` | `-q` | Quick mode, skip the interactive wizard (creates `.venv` and installs dependencies by default) |
| `--force` | `-f` | Force overwrite of existing config files |
| `--here` | | Initialize in the current directory without creating a subdirectory |
| `--no-uv` | | Use pip instead of uv |
| `--no-venv` | | Skip virtual environment creation and dependency installation |

**Examples:**

```bash
# Interactive initialization
epsdk init

# Quick initialization (creates my_bot/ in the current directory, with pyproject.toml + .venv)
epsdk init -q -n my_bot

# Quick initialization with pre-installed adapters (non-interactive, for scripts / CI)
epsdk init -q -n my_bot --adapter yunhu,telegram

# Initialize in any specified directory (../apps/mybot)
epsdk init ../apps/mybot

# Combine parent directory and project name
epsdk init -n my_bot --path ../apps

# Force overwrite existing configuration
epsdk init -f

# Initialize in the current directory
epsdk init --here -n my_bot

# Generate project structure only, without creating a virtual environment
epsdk init --no-venv -n my_bot
```

init artifacts: `main.py`, `pyproject.toml` (dependency manifest), `config/config.toml` + `config.full.example`, `config/ssl/`, `logs/`, `.gitignore`, `README.md`; when creating a virtual environment is chosen, a `.venv` is additionally generated with `erispulse` and the selected adapters installed into it.

> [!NOTE]
> The `.gitignore` is a grouped template: Python bytecode and build artifacts, virtual environments and `.env`, tool caches, editor and system files, and it **excludes the `config/` and `logs/` runtime directories entirely**—`config.toml` contains sensitive information such as adapter tokens and is not recommended for version control; use `config.full.example` to share the configuration skeleton.

> [!WARNING]
> **Do not use `uv run epsdk run` to run the bot**. When executed in a directory without `pyproject.toml`, `uv run` creates a **disposable isolated environment**—adapters installed via `epsdk install` inside it will not persist. Use `epsdk run` inside the project directory (which automatically uses the project `.venv`), or activate the virtual environment first and then run.

### create

Create scaffolding projects for ErisPulse modules or adapters; the `pack` subcommand converts local plugins (the `plugins/` directory) into publishable standard projects.

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `{module,adapter,pack}` | | Type to create: `module` / `adapter` / `pack` (plugin to project) |
| `--name` | `-n` | Project name (PascalCase) |
| `--description` | `-d` | Project description |
| `--author` | `-a` | Author name |
| `--email` | `-e` | Author email |
| `--homepage` | | Project homepage URL |
| `--output` | `-o` | Output directory (defaults to current directory) |
| `--force` | `-f` | Force overwrite of an existing directory |
| `--local` | | Create a local plugin (available for `module` / `adapter`): generates a `plugins/<name>/` package structure, installable without packaging |

**Examples:**

```bash
# Interactive creation (guided type selection and info filling)
epsdk create

# Create a Module project directly
epsdk create module -n MyModule

# Create a local plugin (placed in the project's plugins/ directory, auto-discovered at startup)
epsdk create module -n MyModule --local

# Create a local adapter plugin (same as above, package-free development)
epsdk create adapter -n MyAdapter --local

# Create an Adapter project directly
epsdk create adapter -n MyAdapter

# Convert a local plugin into a publishable project (interactively select plugin → complete metadata → generate standard project)
epsdk create pack

# Full arguments
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Specify output directory
epsdk create module -n MyModule -o ./projects

# Force overwrite existing directory
epsdk create module -n MyModule -f
```

---

## Language Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | View or switch the CLI display language |

### i18n

View the current CLI language, list supported languages, or switch the display language. If no argument is specified, an interactive selection interface is launched.

**Aliases:** `language`, `lang`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[lang]` | | Language code to switch to (e.g. `zh-CN`, `en`, `ja`, `ru`) |
| `--list` | `-l` | List all supported languages |

**Examples:**

```bash
# Interactively select a language
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

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `types` | `t`, `stub` | `[--output/-o <path>] [--force] [--adapters-only] [--modules-only]` | Generate type stub files to enable IDE completion |

### types

Scan installed ErisPulse modules and adapters and generate `.pyi` type stub files for them, enabling accurate code completion and type checking support in your IDE.

**Aliases:** `t`, `stub`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `--output` | `-o` | Output path (defaults to `ep-stubs/` in the current directory) |
| `--force` | | Force overwrite of existing stub files |
| `--adapters-only` | | Generate type stubs for adapters only |
| `--modules-only` | | Generate type stubs for modules only |

> **Note:** `--adapters-only` and `--modules-only` are mutually exclusive; when both are specified, the latter takes effect.

**Examples:**

```bash
# Generate type stubs for all installed modules and adapters
epsdk types

# Generate adapter stubs only
epsdk types --adapters-only

# Output to a specified directory
epsdk types -o ./typings

# Force overwrite existing files
epsdk types --force
```

---

## Global Parameters

The following parameters apply to all commands:

| Argument | Short | Description |
|------|--------|------|
| `--help` | `-h` | Show help information |
| `--version` | `-V` | Show version information |
| `--verbose` | `-v` | Show verbose output (stackable `-vv`/`-vvv`) |
| `--no-color` | | Disable colored output (suitable for CI / log collection) |
| `--no-banner` | | Skip the startup banner (for scripted calls / CI scenarios; automatically silent on non-interactive terminals and when `ERISPULSE_NO_BANNER=1`) |
| `--yes` | `-y` | Automatically confirm all interactive prompts (non-interactive run) |

---

## Environment Diagnostics

### doctor

> [!NOTE]
> This command requires ErisPulse **2.7.0+**.

Diagnose the current CLI runtime environment and output a health report. Used to troubleshoot "why won't it install / connect" type issues.

| Argument | Description |
|------|------|
| `--verbose` | Show detailed diagnostic information |
| `--fix` | After diagnosis, attempt automatic repair of fixable issues |

**Check items**:
- **Python**: interpreter version and path
- **Install backend**: whether `uv` or `pip` is used
- **Target interpreter**: the target Python environment where packages are actually installed
- **Config file**: whether `config/config.toml` exists
- **Component configuration**: declarative configuration completeness of installed components ("installed but won't run" is often due to missing required fields)
- **Configuration pollution** (2.11.1+): scans for residual keys left over from historical upgrades (shadow state keys bound by older runtime versions, orphaned config sections) and reports upon detection
- **PyPI connectivity**: whether PyPI is reachable (and shows the number of components discovered)
- **System proxy**: whether a proxy is detected

**Automatic repair (`--fix`)**:
- Missing `config.toml` → generates an initial config file in the current language (same source as `init` project creation)
- Component configuration "Incomplete" → launches the interactive configuration wizard one by one to complete required fields (in non-interactive environments, prompts to use `epsdk config <name>` instead)
- Configuration pollution residual keys → lists their sources and deletes them after confirmation (tomlclass lossless path, comments and order preserved)
- Issues requiring manual intervention such as a too-low Python version or unreachable PyPI → outputs action recommendations only

```bash
# Run environment diagnostics
epsdk doctor

# Use the alias
epsdk diag

# Diagnose and attempt automatic repair
epsdk doctor --fix
```

---

## Interactive Installation

Running `epsdk install` without a package name enters interactive installation:

```bash
epsdk install
```

The interactive interface provides:
1. Adapter selection
2. Module selection
3. Custom installation

## Common Usage

### Installing Modules

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Upgrade a module
epsdk install Weather -U
```

### Listing Components

```bash
# List all components
epsdk list

# List adapters only
epsdk list -t adapters

# List upgradable components only
epsdk list -o

# View remotely available components
epsdk list-remote
```

### Uninstalling Components

```bash
# Uninstall a single component
epsdk uninstall Weather

# Uninstall multiple components
epsdk uninstall Yunhu Weather
```

### Configuring Components

```bash
# View configuration status
epsdk config --list

# Interactively select a target to configure
epsdk config

# Configure a specific adapter
epsdk config yunhu
```

### Upgrading Components

```bash
# Upgrade all components
epsdk upgrade

# Upgrade a specific component
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Running the Project

```bash
# Normal run
epsdk run main.py

# Hot reload mode
epsdk run main.py --reload
```

### Switching Language

```bash
# Interactively select a language
epsdk i18n

# Switch directly to English
epsdk i18n en

# List supported languages
epsdk i18n --list
```

### Generating Type Stubs

```bash
# Generate all type stubs
epsdk types

# Generate module type stubs only
epsdk types --modules-only
```

### Initializing a Project

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot
```

### Creating Scaffolding

```bash
# Interactive creation (guided type selection and info filling)
epsdk create

# Create a Module project directly
epsdk create module -n MyModule

# Create an Adapter project directly
epsdk create adapter -n MyAdapter

# Full arguments
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Force overwrite existing directory
epsdk create module -n MyModule -f
```

## Next Steps

- **Components installed and need configuration**: use the `epsdk config` interactive wizard, or see [Configuration File Guide](configuration.md) for manual editing
- **Want IDE completion after writing code**: run `epsdk types`; see [Type Stub Generation](../getting-started/ide-completion.md) for details
- **Bot won't run**: first run `epsdk doctor` to diagnose the environment (see [Environment Diagnostics](#environment-diagnostics)); for long-term deployment, see the [Deployment Guide](deployment.md)