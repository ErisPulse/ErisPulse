# User Guide

This guide helps you install, configure, and manage the ErisPulse project.

## Table of Contents

| Document | Description |
|------|------|
| [Installation and Configuration](installation.md) | System requirements, installation methods (pip/uv/Docker), verification |
| [CLI Command Reference](cli-reference.md) | Complete usage instructions for the `epsdk` command-line tool |
| [Configuration File Guide](configuration.md) | Detailed description of each item in `config/config.toml` |
| [Deployment Guide](deployment.md) | Docker deployment, systemd service, SSL configuration |

## Quick Reference

### Common Commands

| Command | Description |
|------|------|
| `epsdk init` | Initialize project (`-q` quick mode, `-n` specify name) |
| `epsdk install <package_name>` | Install module/adapter (enter interactive mode without arguments) |
| `epsdk run main.py` | Run project (`--reload` hot-reload mode) |
| `epsdk list` | List installed modules/adapter |
| `epsdk upgrade <package_name>` | Upgrade module/adapter |
| `epsdk doctor` | Diagnose environment (Python/Backend/Config/PyPI connectivity) |

> For the complete list of commands and parameter descriptions, please refer to [CLI Command Reference](cli-reference.md).

### Common Configuration Locations

| Config Item | Description | See Details |
|--------|------|------|
| `[ErisPulse.server]` | Server configuration (host, port) | [Configuration File Guide](configuration.md#server-config) |
| `[ErisPulse.logger]` | Logger configuration (level, output file) | [Configuration File Guide](configuration.md#logger-config) |
| `[ErisPulse.framework]` | Framework configuration (lazy loading) | [Configuration File Guide](configuration.md#framework-config) |
| `[ErisPulse.event.command]` | Command event configuration (prefix) | [Configuration File Guide](configuration.md#event-config) |
| `[Adapter_Name]` | Specific configuration for each adapter | [Platform Guide](../platform-guide/) |

## Related Documentation

- [Quick Start](../quick-start.md) - Quick start guide
- [Getting Started](../getting-started/) - Tutorials for beginners
- [Developer Guide](../developer-guide/) - Guide to developing custom modules and adapters
- [API Reference](../api-reference/) - API documentation