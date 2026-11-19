# CLI Command Reference

> [!TIP]
> **When to read this**: Consult this page when you forget the arguments of an `epsdk` command, want to put component management into scripts, or need to control run / stop / restart behavior. If you only use `init` / `install` / `run` day to day, remembering one rule is enough: `epsdk <command> --help` always shows the argument descriptions — no need to read this entire page.

`epsdk` is the command-line tool of ErisPulse: initialize projects, install / upgrade modules and adapters, configure components interactively, run and stop the bot, and diagnose the environment — all under this single command.

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
| `doctor` | `diag` | `[--verbose] [--fix]` | Diagnose the environment and output a health report; `--fix` attempts automatic repairs |

### install

Install ErisPulse module or adapter packages. If no package name is specified, an interactive installation interface is launched.

**Aliases:** `i`, `add`

> **uv project integration** (2.11.1+): Inside a uv-managed project (where `uv.lock` or `[tool.uv]` exists),
> `install` / `upgrade` / `uninstall` automatically switch to `uv add` / `uv remove` — dependencies are written
> to both `pyproject.toml` and `uv.lock`, so `uv sync` no longer wipes out components installed by epsdk; on failure it
> automatically falls back to the uv pip / pip channel. Arguments not supported by uv, such as `--user`, go directly through pip. Target environment resolution order:
> `ERISPULSE_PYTHON` → `UV_PROJECT_ENVIRONMENT` → project `.venv` → `UV_PYTHON` →
> `VIRTUAL_ENV` → current interpreter (`epsdk doctor` shows the full decision chain).

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to install; multiple allowed |
| `--upgrade` | `-U` | Upgrade to the latest version during installation |
| `--pre` | | Allow installing pre-release versions |
| `--editable` | `-e` | Install in editable mode (requires a path) |
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
| `--no-binary` | | Restrict to not use binary packages (format such as `:all:`) |
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

# Install and upgrade from a mirror source
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install in editable mode (development mode)
epsdk install -e ./my-adapter
```

### uninstall

Uninstall installed ErisPulse module or adapter packages. If no package name is specified, an interactive uninstallation interface is launched.

**Aliases:** `rm`, `remove`

**Arguments:**

| Argument | Description |
|------|------|
| `<package>...` | Package names to uninstall; multiple allowed |
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
| `[package]...` | | Package names to upgrade; multiple allowed |
| `--force` | `-f` | Force upgrade, skip confirmation |
| `--pre` | | Allow upgrading to pre-release versions |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Upgrade all packages
epsdk upgrade

# Upgrade specified packages
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

# Update to a specified version
epsdk self-update 1.2.3

# Allow pre-release versions
epsdk self-update --pre

# Force update
epsdk self-update -f
```

> [!NOTE]
> When installed via `uv tool install ErisPulse`, this command automatically switches to `uv tool upgrade ErisPulse` (or `uv tool install ErisPulse==<version> --force` when a version is specified), because upgrading the tool environment directly with pip would be wiped out by uv's manifest restoration.
> On Windows, updates run in a new console window: the current CLI must exit first to release the file locks on the tool environment; once the window reports completion, simply reopen the terminal.

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
| `--refresh` | `-r` | Force a refresh of the remote package list cache |

**Examples:**

```bash
# List all remotely available components
epsdk list-remote

# List remote modules only
epsdk list-remote -t modules

# Force a cache refresh and then list
epsdk list-remote -r
```

---

## Configuration Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `config` | `cfg`, `conf` | `[name] [--list/-l] [--json]` | Interactively configure declarative configuration items of adapters/modules |

### config

Interactively fill in the declarative configuration items of adapters/modules. The wizard is driven by the configuration classes (`ConfigClass` / `AccountConfigClass`) declared by the adapter/module, automatically generating and validating forms — no need to hand-write config.toml.

Adapters additionally support multi-account (bot account) management: add/edit/delete accounts, plus enable/disable toggles.

**Aliases:** `cfg`, `conf`

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[name]` | | Target name (adapter platform name or module name); leave empty for interactive selection |
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

# Configure the specified adapter directly
epsdk config yunhu

# Configure the specified module directly
epsdk config MyModule
```

**Notes:**

- Configuration status has four tiers: `Ready` (validation passed), `Incomplete` (required fields missing or validation failed), `Not Configured` (never generated), `No Configuration` (target declares no configuration class)
- Field values carry source annotations: existing configuration shows `(current: value)`, and when unconfigured the schema default is shown as `(default: value)`; pressing Enter keeps the value
- Secret-type fields (declared with `secret`) are not echoed during input; pressing Enter keeps the already-set value
- In interactive selection mode, after a single wizard finishes you return to the selection menu (with refreshed status), so you can configure multiple targets consecutively; leave empty to exit
- When global form validation fails and you give up on re-filling, the wizard aborts and writes no configuration (avoiding a half-finished state of "enabled but incompletely configured")
- After saving, changes are written to `config/config.toml` immediately, visible to both the Dashboard and the running SDK; for a running adapter to apply new account configuration, simply restart the process
- After `epsdk install` (interactive installation) and `epsdk init` successfully install an adapter, the wizard is automatically launched if configuration declarations are detected; when installing by specifying a package name directly on the command line, only a configuration hint is printed

---

## Run Control Commands

> [!TIP]
> `epsdk run` automatically detects and uses the `.venv` virtual environment in the project directory to run the bot
> (you can also explicitly specify the interpreter via the `ERISPULSE_PYTHON` environment variable). `epsdk install` /
> `uninstall` / `upgrade` / `list` likewise operate on the project virtual environment.

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `run` | `r` | `[script] [--reload] [--strict/--no-strict]` | Run the specified script or the SDK |
| `stop` | — | `[--force] [--pid PID]` | Stop a running instance (started by `epsdk run`) |
| `restart` | — | `[--force] [--pid PID]` | Restart a running instance (stops it, then restarts with the original arguments) |

### run

Run an ErisPulse project script or start the SDK directly. Hot-reload mode is supported.

**Aliases:** `r`

**Arguments:**

| Argument | Description |
|------|------|
| `[script]` | The script file to run; if not specified, the SDK runs |
| `--reload` | Enable hot-reload mode: monitor file changes and automatically trigger component-level code hot reloading (no full process restart needed); `.venv`/`.git` and similar directories are ignored by default (configurable via `ErisPulse.framework.watch_ignore_dirs`), while the plugin directory is handled precisely by the plugin hot-reload watcher |
| `--strict` / `--no-strict` | Temporarily enable / disable strict mode (effective for this run only, not written to configuration); defaults follow `ErisPulse.framework.strict_mode` |

**Examples:**

```bash
# Run the SDK directly
epsdk run

# Run the specified script file
epsdk run main.py

# Run in hot-reload mode (file changes automatically trigger code-level hot reloading)
epsdk run main.py --reload

# SDK hot-reload mode
epsdk run --reload

# Temporary strict mode: exit if the pre-start self-check fails; the framework strictness level is raised to at least 1 for this run
epsdk run main.py --strict

# Temporary lenient mode (strict_mode is enabled in configuration but you want to get running this time)
epsdk run main.py --no-strict
```

**Pre-start self-check:** before starting, `run` quickly checks the parseability of `config/config.toml` and the completeness of required configuration of installed components; strictness defaults to `ErisPulse.framework.strict_mode` (when non-zero, the process exits on check failure; when 0, it only warns and continues). A missing configuration file is treated as a normal first startup — a notice only, not a failure. `--strict` temporarily enables it: exit on pre-check failure, and the framework strictness level is raised to at least 1 for this run (non-compliant components are skipped, conveyed to the running process via the `ERISPULSE_FRAMEWORK_STRICT_MODE` environment variable, not written to the configuration file); `--no-strict` conversely temporarily lowers it to lenient. If the self-check itself errors, it is skipped automatically; no network probing is involved, so startup is never blocked.

> **The supervision structure of `--reload`** (since 2.11.1): `epsdk run --reload` runs as a "supervisor process + reload worker subprocess". Hot reloads triggered by saving `.py` files all complete inside the worker (mutually exclusive, serialized, storm-coalesced); module-side syntax errors are rejected by an overall pre-check and the old instance keeps serving. On `sdk.hard_restart()`, the worker exits with code 42, and after the supervisor displays the reason it automatically pulls up a brand-new worker — after upgrading the framework itself, new code takes effect immediately.

### stop

Stop a running ErisPulse instance (started by `epsdk run` and executed in the same project directory).
When `run` starts, it writes the supervisor PID, the current framework subprocess PID, and the original startup command into
`.erispulse/runtime.json`; `stop` locates the instance based on this.

**Stop sequence:** On POSIX, SIGINT is first sent to the supervisor process (the same graceful shutdown path as Ctrl+C —
the finally chain automatically terminates the framework subprocess), escalating to SIGTERM / SIGKILL stepwise on timeout; Windows has no
process signal semantics, so the framework subprocess is terminated first, then the supervisor process (to prevent the supervisor from misinterpreting the force kill as a crash and relaunching).

**Arguments:**

| Argument | Description |
|------|------|
| `--force` | Skip graceful stop and terminate forcibly |
| `--pid PID` | Directly specify the target process PID (overrides the runtime status file, for non-standard startup methods) |

**Examples:**

```bash
# Stop the running instance of the current project
epsdk stop

# Terminate forcibly
epsdk stop --force
```

### restart

Restart a running ErisPulse instance: after stopping per the `stop` semantics, restart with the
**original startup command** recorded in the status file (taking over the current terminal in the foreground; the new instance writes a new runtime status file).

**In-container instances (PID 1)**: when the instance recorded in the status file is the container's main process (`pid == 1`, e.g. the official
image's `CMD ["epsdk", "run"]`), terminate-and-relaunch is unavailable — PID 1 exiting means the container exits. In that case,
`SIGUSR1` is sent to the framework process instead, triggering an **in-process hot restart** (`sdk.restart()`):
code-level hot reloading of modules and adapters; adapters newly installed via `ep i` take effect immediately, and the container stays online. For a full process restart
(updating the framework itself, structural configuration changes), restart the container (`docker restart <container>`). See
[Deployment → In-Container Restart](deployment.md#in-container-restart-pid-1-instance).

**Arguments:** Same as `stop` (`--force` / `--pid PID`).

**Examples:**

```bash
# Graceful restart (make code effective after pip-upgrading adapters/modules; running modules can also use
# sdk.reload_module / sdk.adapter.reload for code-level hot reloading without restarting)
epsdk restart
```

> [!NOTE]
> Startup methods that bypass `epsdk run`, such as `python main.py`, do not write the runtime status file — manage such
> processes with system tools, or specify the PID with `epsdk stop --pid <PID>`.

---

## Project Management Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--adapter/-a <name>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | Initialize an ErisPulse project |
| `create` | — | `{module,adapter,pack} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f] [--local]` | Create module/adapter scaffolding; `pack` converts local plugins into publishable projects |

### init

Initialize a new ErisPulse project. Interactive and quick modes are supported; since 2.8.4 it generates `pyproject.toml` (dependency manifest), optionally creates a project `.venv` virtual environment and installs the framework and adapters, and supports **specifying any directory**.

**Arguments:**

| Argument | Short | Description |
|------|--------|------|
| `[path]` | | Target path (may include parent directories, e.g. `../apps/mybot`; a bare name is equivalent to `--project-name`) |
| `--project-name` | `-n` | Project name |
| `--path` | | Project parent directory (combined with `-n` to specify the creation location) |
| `--adapter` | `-a` | Pre-select adapters to install (can be passed multiple times or comma-separated); when provided, skips adapter prompting and selection |
| `--quick` | `-q` | Quick mode, skip the interactive wizard (creates `.venv` and installs dependencies by default) |
| `--force` | `-f` | Force overwrite of existing configuration files |
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

# Force overwrite of existing configuration
epsdk init -f

# Initialize in the current directory
epsdk init --here -n my_bot

# Generate only the project structure, without creating a virtual environment
epsdk init --no-venv -n my_bot
```

init artifacts: `main.py`, `pyproject.toml` (dependency manifest), `config/config.toml` + `config.full.example`, `config/ssl/`, `logs/`, `.gitignore`, `README.md`; when virtual environment creation is chosen, a `.venv` is additionally generated with `erispulse` and the selected adapters installed into it.

> [!NOTE]
> `.gitignore` is a grouped template: Python bytecode and build artifacts, virtual environments and `.env`, tool caches, editor and system files, and **excludes the `config/` and `logs/` runtime directories entirely** — `config.toml` contains sensitive information such as adapter tokens and is not recommended for version control; use `config.full.example` to share the configuration skeleton.

> [!WARNING]
> **Do not use `uv run epsdk run` to run the bot**. When executed in a directory without `pyproject.toml`, `uv run` creates a **one-off isolated environment** — adapters installed there via `epsdk install` are not persisted. Use `epsdk run` inside the project directory (which automatically uses the project `.venv`), or activate the virtual environment first before running.

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
| `--output` | `-o` | Output directory (defaults to the current directory) |
| `--force` | `-f` | Force overwrite of existing directories |
| `--local` | | Create a local plugin (available for `module` / `adapter`): generates a `plugins/<name>/` package structure, no packaging needed for installation |

**Examples:**

```bash
# Interactive creation (guided type selection and information entry)
epsdk create

# Create a Module project directly
epsdk create module -n MyModule

# Create a local plugin (placed in the project plugins/ directory, auto-discovered at startup)
epsdk create module -n MyModule --local

# Create a local adapter plugin (same as above, packaging-free development)
epsdk create adapter -n MyAdapter --local

# Create an Adapter project directly
epsdk create adapter -n MyAdapter

# Convert a local plugin into a publishable project (interactively select plugin → complete metadata → generate standard project)
epsdk create pack

# Full arguments
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Specify the output directory
epsdk create module -n MyModule -o ./projects

# Force overwrite of an existing directory
epsdk create module -n MyModule -f
```

---

## Language Commands

| Command | Alias | Arguments | Description |
|------|------|------|------|
| `i18n` | `language`, `lang` | `[lang] [--list/-l]` | View or switch the CLI display language |

### i18n

View the current CLI language, list supported languages, switch the display language. If no arguments are specified, an interactive selection interface is launched.

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

Scan installed ErisPulse modules and adapters and generate `.pyi` type stub files for them, so that you get accurate code completion and type-checking support in the IDE.

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

# Output to the specified directory
epsdk types -o ./typings

# Force overwrite of existing files
epsdk types --force
```

---

## Global Arguments

The following arguments apply to all commands:

| Argument | Short | Description |
|------|--------|------|
| `--help` | `-h` | Show help information |
| `--version` | `-V` | Show version information |
| `--verbose` | `-v` | Show verbose output (can be stacked as `-vv`/`-vvv`) |
| `--no-color` | | Disable colored output (suitable for CI / log collection) |
| `--no-banner` | | Skip the startup Banner (for scripted calls / CI; automatically silenced on non-interactive terminals and when `ERISPULSE_NO_BANNER=1`) |
| `--yes` | `-y` | Auto-confirm all interactive prompts (non-interactive run) |

---

## Environment Diagnostics

### doctor

> [!NOTE]
> This command requires ErisPulse **2.7.0+**.

Diagnose the current CLI runtime environment and output a health report. Used to troubleshoot issues like "why can't it install / connect".

| Argument | Description |
|------|------|
| `--verbose` | Show detailed diagnostic information |
| `--fix` | After diagnosis, attempt to automatically repair fixable issues |

**Checks**:
- **Python**: interpreter version and path
- **Install backend**: whether `uv` or `pip` is used
- **Target interpreter**: the target Python environment where packages are actually installed
- **Configuration file**: whether `config/config.toml` exists
- **Component configuration**: completeness of the declarative configuration of installed components ("installed but won't run" is often due to missing required fields)
- **Configuration pollution** (2.11.1+): scans for residual keys left behind by historical upgrades (shadow status keys bound by older runtime versions, orphaned configuration sections), reporting any that are found
- **PyPI connectivity**: whether PyPI is reachable (and shows the number of components discovered)
- **System proxy**: whether a proxy is detected

**Automatic repairs (`--fix`)**:
- Missing `config.toml` → generates the initial configuration file in the current language (same source as `init` project creation)
- Component configuration "Incomplete" → launches the interactive configuration wizard one by one to fill in required fields (in non-interactive environments, suggests using `epsdk config <name>` instead)
- Configuration pollution residual keys → lists their sources and deletes them after confirmation (lossless tomlclass path, preserving comments and ordering)
- Issues requiring manual intervention, such as too-low Python versions or unreachable PyPI → only action suggestions are output

```bash
# Run environment diagnostics
epsdk doctor

# Use the alias
epsdk diag

# Diagnose and attempt automatic repairs
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

# Configure the specified adapter
epsdk config yunhu
```

### Upgrading Components

```bash
# Upgrade all components
epsdk upgrade

# Upgrade specified components
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Running Projects

```bash
# Normal run
epsdk run main.py

# Hot-reload mode
epsdk run main.py --reload
```

### Switching Languages

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

### Initializing Projects

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot
```

### Creating Scaffolding

```bash
# Interactive creation (guided type selection and information entry)
epsdk create

# Create a Module project directly
epsdk create module -n MyModule

# Create an Adapter project directly
epsdk create adapter -n MyAdapter

# Full arguments
epsdk create module -n MyModule -d "Module description" -a "Author" -e "mail@example.com"

# Force overwrite of an existing directory
epsdk create module -n MyModule -f
```

## Next Steps

- **Components installed and need configuration**: use the `epsdk config` interactive wizard, or see the [Configuration File Guide](configuration.md) to edit manually
- **Finished coding and want IDE completion**: run `epsdk types`; see [Type Stub Generation](../getting-started/ide-completion.md) for details
- **Bot won't run**: first run `epsdk doctor` to diagnose the environment (see [Environment Diagnostics](#environment-diagnostics)); for long-term deployment, see the [Deployment Guide](deployment.md)