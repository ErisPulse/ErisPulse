# CLI Command Reference

The ErisPulse command-line tool (`epsdk`) provides project management and package management features.

> **Tip:** You can view detailed parameter descriptions for all commands using `epsdk <command> --help`.

---

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
| `doctor` | `diag` | `[--verbose]` | Diagnose environment and output health report |

### install

Installs ErisPulse modules or adapter packages. If no package name is specified, it enters interactive installation mode.

**Aliases:** `i`, `add`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to install, multiple can be specified |
| `--upgrade` | `-U` | Upgrade to the latest version during installation |
| `--pre` | | Allow installation of pre-release versions |
| `--editable` | `-e` | Install in editable mode (requires path) |
| `--user` | | Install to user site-packages directory |
| `--no-deps` | | Do not install dependencies |
| `--target` | `-t` | Install to a specified directory |
| `--index-url` | | Specify PyPI mirror source URL |
| `--extra-index-url` | | Additional PyPI mirror source URL (can be specified multiple times) |
| `--no-cache-dir` | | Disable cache |
| `--requirement` | `-r` | Install from a requirements file |
| `--constraint` | `-c` | Install from a constraint file |
| `--force-reinstall` | | Force reinstallation |
| `--ignore-installed` | | Ignore already installed packages |
| `--compile` | | Compile .pyc files after installation |
| `--no-compile` | | Do not compile .pyc files after installation |
| `--prefix` | | Install to a specified prefix directory |
| `--src` | | Source code directory used for editable installation |
| `--config-settings` | | Pass configuration to the build backend (can be specified multiple times) |
| `--no-binary` | | Restrict not to use binary packages (format like `:all:`) |
| `--only-binary` | | Restrict to use only binary packages (format like `:all:`) |
| `--prefer-binary` | | Prefer binary packages |
| `--build-isolation` | | Enable build isolation |
| `--no-build-isolation` | | Disable build isolation |
| `--upgrade-strategy` | | Upgrade strategy: `eager`, `only-if-needed`, `to-satisfy-only` |
| `--break-system-packages` | | Allow modification of Python packages managed by the system package manager |
| `--no-uv` | | Use pip instead of uv |

**Examples:**

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Install from mirror source and upgrade
epsdk install Weather -U --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# Install in editable mode (development mode)
epsdk install -e ./my-adapter
```

### uninstall

Uninstalls installed ErisPulse modules or adapter packages. If no package name is specified, it enters interactive uninstallation mode.

**Aliases:** `rm`, `remove`

**Parameters:**

| Parameter | Description |
|------|------|
| `<package>...` | Package names to uninstall, multiple can be specified |
| `--no-uv` | Use pip instead of uv |

**Examples:**

```bash
# Uninstall a single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### upgrade

Upgrades installed ErisPulse components. If no package name is specified, it enters interactive upgrade mode for all.

**Aliases:** `up`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[package]...` | | Package names to upgrade, multiple can be specified |
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

Updates the ErisPulse SDK itself to the latest version.

**Aliases:** `su`, `update`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[version]` | | Specify the target version to update to |
| `--pre` | | Allow update to pre-release versions |
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
> When installing with `uv tool install ErisPulse`, this command automatically switches to `uv tool upgrade ErisPulse` (with specified version as `uv tool install ErisPulse==<version> --force`). Direct pip upgrades will have the tool environment overwritten by uv's manifest. On Windows, updates are performed in a new console window: the current CLI must exit first to release file locks on the tool environment, and the terminal should be reopened after the prompt completes.

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
| `--outdated` | `-o` | Only display upgradable packages |

**Examples:**

```bash
# List all installed components
epsdk list

# Only list modules
epsdk list -t modules

# Only list adapters
epsdk list -t adapters

# Only display upgradable packages
epsdk list -o
```

### list-remote

Lists available ErisPulse modules and adapters in the remote repository.

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
| `config` | `cfg`, `conf` | `[name] [--list/-l]` | Interactive configuration of declarative configuration items for adapters/modules |

### config

Interactive configuration of declarative configuration items for adapters/modules. The wizard is driven by the adapter/module's declared configuration class (`ConfigClass` / `AccountConfigClass`), generating forms and performing validation automatically, eliminating the need to manually write `config.toml`.

Adapters additionally support multi-account (bot account) management: adding/editing/deleting accounts, and enabling/disabling switches.

**Aliases:** `cfg`, `conf`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[name]` | | Target name (adapter platform name or module name), leave empty to enter interactive selection |
| `--list` | `-l` | Only list the configuration status of all targets, do not enter the wizard |

**Examples:**

```bash
# View configuration status of all adapters/modules
epsdk config --list

# Interactive selection of target for configuration
epsdk config

# Directly configure a specified adapter
epsdk config yunhu

# Directly configure a specified module
epsdk config MyModule
```

**Explanation:**

- Configuration status is divided into four levels: `Ready` (validation passed), `Incomplete` (missing or validation failed required fields), `Not Configured` (never generated), `No Configuration` (target did not declare a configuration class)
- Field values are annotated with source: existing configuration displays ` (current: value)`, unconfigured fields display schema default values ` (default: value)`; pressing Enter retains the value
- Secret-type fields (declared `secret`) do not echo input, pressing Enter retains the set value
- In interactive selection mode, after completing a single wizard, it returns to the selection menu (status refreshed), allowing continuous configuration of multiple targets, leaving empty to exit
- If global form validation fails and the user chooses not to re-enter, the current wizard is terminated and no configuration is written (to avoid creating a half-finished state with "enabled but incomplete configuration")
- After saving, it is immediately written to `config/config.toml`, visible in the Dashboard and running SDK; running adapters need to restart the process to apply new account configurations
- After `epsdk install` (interactive installation) or `epsdk init` successfully installs an adapter, if configuration declaration is detected, it automatically guides into this wizard; when installing directly via command line, only a configuration prompt is printed

---

## Runtime Control Commands

> [!TIP]
> `epsdk run` will automatically detect and use the `.venv` virtual environment in the project directory to run the robot
> (you can also explicitly specify the interpreter via the `ERISPULSE_PYTHON` environment variable). `epsdk install` /
> `uninstall` / `upgrade` / `list` also operate on the project virtual environment.

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `run` | `r` | `[script] [--reload]` | Run a specified script or SDK |

### run

Run an ErisPulse project script or directly start the SDK. Supports hot-reload mode.

**Aliases:** `r`

**Parameters:**

| Parameter | Description |
|------|------|
| `[script]` | Script file to run, if not specified, run the SDK |
| `--reload` | Enable hot-reload mode, monitor file changes and automatically restart |

**Examples:**

```bash
# Directly run SDK
epsdk run

# Run a specified script file
epsdk run main.py

# Hot-reload mode (automatically restart on file change)
epsdk run main.py --reload

# SDK hot-reload mode
epsdk run --reload
```

---

## Project Management Commands

| Command | Alias | Parameters | Description |
|------|------|------|------|
| `init` | — | `[path] [--project-name/-n <name>] [--path <dir>] [--quick/-q] [--force/-f] [--here] [--no-uv] [--no-venv]` | Initialize an ErisPulse project |
| `create` | — | `{module,adapter} [--name/-n <name>] [--description/-d <desc>] [--author/-a <name>] [--email/-e <mail>] [--homepage <url>] [--output/-o <dir>] [--force/-f]` | Create module/adapter scaffold |

### init

Initialize a new ErisPulse project. Supports interactive and quick modes, since version 2.8.4 generates `pyproject.toml` (dependency manifest), optionally creates a project `.venv` virtual environment and installs framework and adapters, and supports **specifying any directory**.

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `[path]` | | Target path (can include parent directory, e.g., `../apps/mybot`; pure name is equivalent to `--project-name`) |
| `--project-name` | `-n` | Project name |
| `--path` | | Project parent directory (combined with `-n` to specify creation location) |
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

# Initialize in any specified directory (../apps/mybot)
epsdk init ../apps/mybot

# Combine parent directory and project name
epsdk init -n my_bot --path ../apps

# Force overwrite existing configuration
epsdk init -f

# Initialize in current directory
epsdk init --here -n my_bot

# Only generate project structure, skip virtual environment
epsdk init --no-venv -n my_bot
```

init output: `main.py`, `pyproject.toml` (dependency manifest), `config/config.toml` + `config.full.example`, `config/ssl/`, `logs/`, `.gitignore`, `README.md`; if virtual environment creation is selected, `.venv` is additionally generated and `erispulse` and selected adapters are installed within it.

> [!NOTE]
> `.gitignore` is a grouped template: Python bytecode and build artifacts, virtual environment and `.env`, tool cache, editor and system files, and **excludes `config/` and `logs/` runtime directories** as a whole—`config.toml` contains sensitive information such as adapter tokens and should not be committed to the repository; for sharing configuration skeletons, use `config.full.example`.

> [!WARNING]
> **Do not use `uv run epsdk run` to run the robot**. `uv run` creates a **one-time isolated environment** when executed in a directory without `pyproject.toml`—packages installed via `epsdk install` in it will not persist. Use `epsdk run` within the project directory (which automatically uses the project's `.venv`), or activate the virtual environment first before running.

### create

Creates a scaffold project for an ErisPulse module or adapter.

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `{module,adapter}` | | Type to create: `module` or `adapter` |
| `--name` | `-n` | Project name (PascalCase) |
| `--description` | `-d` | Project description |
| `--author` | `-a` | Author name |
| `--email` | `-e` | Author email |
| `--homepage` | | Project homepage URL |
| `--output` | `-o` | Output directory (default is current directory) |
| `--force` | `-f` | Force overwrite existing directory |
| `--local` | | Create a local plugin (only available for `module`): generates `plugins/<name>/` package structure, allowing installation without packaging |

**Examples:**

```bash
# Interactive creation (guides selection of type and fills in information)
epsdk create

# Directly create Module project
epsdk create module -n MyModule

# Create local plugin (placed in project's plugins/ directory, automatically discovered on startup, supports hot-reload)
epsdk create module -n MyModule --local

# Directly create Adapter project
epsdk create adapter -n MyAdapter

# Full parameters
epsdk create module -n MyModule -d "module description" -a "author" -e "mail@example.com"

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

View the current CLI language, list supported languages, and switch display language. If no parameter is specified, it enters interactive selection mode.

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

Scans installed ErisPulse modules and adapters, generating `.pyi` type stub files for accurate code completion and type checking support in IDEs.

**Aliases:** `t`, `stub`

**Parameters:**

| Parameter | Short | Description |
|------|--------|------|
| `--output` | `-o` | Output path (default is `ep-stubs/` in current directory) |
| `--force` | | Force overwrite existing stub files |
| `--adapters-only` | | Generate type stubs only for adapters |
| `--modules-only` | | Generate type stubs only for modules |

> **Note:** `--adapters-only` and `--modules-only` are mutually exclusive; if both are specified, the latter takes effect.

**Examples:**

```bash
# Generate type stubs for all installed modules and adapters
epsdk types

# Generate stubs only for adapters
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
| `--no-banner` | | Skip startup banner (scripted calls / CI scenarios; non-interactive terminals and `ERISPULSE_NO_BANNER=1` automatically silence) |
| `--yes` | `-y` | Automatically confirm all interactive prompts (non-interactive runs) |

---

## Environment Diagnosis

### doctor

> [!NOTE]
> This command requires ErisPulse **2.7.0+**.

Diagnose the current CLI runtime environment and output a health report. Used to troubleshoot issues like "why can't install / connect".

| Parameter | Description |
|------|------|
| `--verbose` | Display detailed diagnostic information |

**Check items:**
- **Python:** Interpreter version and path
- **Installation backend:** Whether `uv` or `pip` is used
- **Target interpreter:** The actual Python environment where packages are installed
- **Configuration file:** Whether `config/config.toml` exists
- **PyPI connectivity:** Whether PyPI can be accessed (and displays the number of discovered components)
- **System proxy:** Whether a proxy is detected

```bash
# Run environment diagnosis
epsdk doctor

# Use alias
epsdk diag
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

# Interactive selection of target for configuration
epsdk config

# Configure a specified adapter
epsdk config yunhu
```

### Upgrade Components

```bash
# Upgrade all components
epsdk upgrade

# Upgrade a specified component
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

### Create Scaffold

```bash
# Interactive creation (guides selection of type and fills in information)
epsdk create

# Directly create Module project
epsdk create module -n MyModule

# Directly create Adapter project
epsdk create adapter -n MyAdapter

# Full parameters
epsdk create module -n MyModule -d "module description" -a "author" -e "mail@example.com"

# Force overwrite existing directory
epsdk create module -n MyModule -f
```