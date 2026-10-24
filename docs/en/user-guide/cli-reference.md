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

## Next Steps

- **After installing components, you need to fill in the configuration**: Use the `epsdk config` interactive wizard, or manually edit the configuration file as described in [Configuration File Description](configuration.md).
- **After writing code and wanting IDE auto-completion**: Run `epsdk types`, see [Type Stub Generation](../getting-started/ide-completion.md) for details.
- **If the robot fails to run**: First, use `epsdk doctor` to diagnose the environment (see [Environment Diagnosis](#environment-diagnosis)). For long-term deployment, refer to the [Deployment Guide](deployment.md).