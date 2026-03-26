# User Guide

This guide helps you install, configure, and manage the ErisPulse project.

## Table of Contents

1. [Installation and Configuration](installation.md) - Install ErisPulse and configure the project
2. [CLI Command Reference](cli-reference.md) - Complete usage instructions for the command-line tool
3. [Configuration File Guide](configuration.md) - Detailed explanation of configuration files

## Quick Reference

### Common Commands

| Command | Description | Example |
|---------|-------------|---------|
| `epsdk init` | Initialize project | `epsdk init -q -n my_bot` |
| `epsdk install` | Install module/adapter | `epsdk install Yunhu` |
| `epsdk run` | Run project | `epsdk run main.py --reload` |
| `epsdk list` | List installed modules | `epsdk list -t modules` |
| `epsdk upgrade` | Upgrade module | `epsdk upgrade Yunhu` |

### Common Configuration Locations

| Configuration Item | Description |
|--------------------|-------------|
| `[ErisPulse.server]` | Server configuration (host, port) |
| `[ErisPulse.logger]` | Logging configuration (level, output file) |
| `[ErisPulse.framework]` | Framework configuration (lazy loading) |
| `[ErisPulse.event.command]` | Command event configuration (prefix) |
| `[Adapter Name]` | Specific configuration for each adapter |

### Project Directory Structure

```
project/
├── config/
│   └── config.toml          # Project configuration file
├── main.py                  # Project entry point file
└── requirements.txt          # List of dependencies
```

## Development Mode

### Hot Reload Mode

Use hot reload mode during development to automatically reload after code changes:

```bash
epsdk run main.py --reload
```

### Standard Run Mode

Use standard run mode for production environments:

```bash
epsdk run main.py
```

## Common Tasks

### Install New Modules

```bash
# Install from remote repository
epsdk install Yunhu Weather

# Install from local directory
epsdk install ./my-module

# Interactive install
epsdk install
```

### View Available Modules

```bash
# List all modules
epsdk list

# List only adapters
epsdk list -t adapters

# List only modules
epsdk list -t modules

# List remotely available modules
epsdk list-remote
```

### Upgrade Modules

```bash
# Upgrade specific module
epsdk upgrade Yunhu

# Upgrade all modules
epsdk upgrade
```

### Uninstall Modules

```bash
# Uninstall specific module
epsdk uninstall Yunhu

# Uninstall multiple modules
epsdk uninstall Yunhu Weather
```

## Related Documentation

- [Quick Start](../quick-start.md) - Quick start guide
- [Getting Started](../getting-started/) - Getting started tutorials
- [Developer Guide](../developer-guide/) - Develop custom modules and adapters
- [API Reference](../api-reference/) - API documentation