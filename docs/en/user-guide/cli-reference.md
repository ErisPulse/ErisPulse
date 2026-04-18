# CLI Command Reference

The ErisPulse command-line tool provides project management and package management capabilities.

## Package Management Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `install` | `[package]... [--upgrade/-U] [--pre]` | Install modules/adapters | `epsdk install Yunhu` |
| `uninstall` | `<package>...` | Uninstall modules/adapters | `epsdk uninstall old-module` |
| `upgrade` | `[package]... [--force/-f] [--pre]` | Upgrade specified modules or all | `epsdk upgrade --force` |
| `self-update` | `[version] [--pre] [--force/-f]` | Update SDK itself | `epsdk self-update` |

## Information Query Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `list` | `[--type/-t <type>]` | List installed modules/adapters | `epsdk list -t modules` |
| | `[--outdated/-o]` | Only show upgradable packages | `epsdk list -o` |
| `list-remote` | `[--type/-t <type>]` | List remote available packages | `epsdk list-remote` |
| | `[--refresh/-r]` | Force refresh package list | `epsdk list-remote -r` |

## Execution Control Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `run` | `<script> [--reload]` | Run specified script | `epsdk run main.py --reload` |

## Project Management Commands

| Command | Arguments | Description | Example |
|-------|------|------|------|
| `init` | `[--project-name/-n <name>]` | Interactive project initialization | `epsdk init -n my_bot` |
| | `[--quick/-q]` | Quick mode, skip interaction | `epsdk init -q -n bot` |
| | `[--force/-f]` | Force override existing configuration | `epsdk init -f` |

## Parameter Reference

### Common Parameters

| Parameter | Short Option | Description |
|------|---------|------|
| `--help` | `-h` | Display help information |
| `--verbose` | `-v` | Display verbose output |

### install Parameters

| Parameter | Description |
|------|------|
| `[package]` | Package name to install, multiple can be specified |
| `--upgrade` | `-U` | Upgrade to latest version during install |
| `--pre` | Allow installing pre-release versions |

### list Parameters

| Parameter | Description |
|------|------|
| `--type` | `-t` | Specify type: `modules`, `adapters`, `all` |
| `--outdated` | `-o` | Only show upgradable packages |

### run Parameters

| Parameter | Description |
|------|------|
| `--reload` | Enable hot reload mode to monitor file changes |
| `--no-reload` | Disable hot reload mode |

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

### Installing Modules

```bash
# Install a single module
epsdk install Weather

# Install multiple modules
epsdk install Yunhu Weather

# Upgrade module
epsdk install Weather -U
```

### Listing Modules

```bash
# List all modules
epsdk list

# List only adapters
epsdk list -t adapters

# List only upgradable modules
epsdk list -o
```

### Uninstalling Modules

```bash
# Uninstall a single module
epsdk uninstall Weather

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

### Upgrading Modules

```bash
# Upgrade all modules
epsdk upgrade

# Upgrade specified module
epsdk upgrade Weather

# Force upgrade
epsdk upgrade -f
```

### Running Projects

```bash
# Normal run
epsdk run main.py

# Hot reload mode
epsdk run main.py --reload
```

### Initializing Projects

```bash
# Interactive initialization
epsdk init

# Quick initialization
epsdk init -q -n my_bot