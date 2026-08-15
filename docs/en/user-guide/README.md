# User Guide

This guide helps you install, configure, and manage the ErisPulse project.

## Table of Contents

| Document | Description |
|------|------|
| [Installation and Configuration](docs/en/installation.md) | System requirements, installation methods (pip/uv/Docker), verification of installation |
| [ErisPulse-App Mobile/Desktop Client](../ecosystem/app.md) | Official client: Mobile / Desktop direct execution, native interface to manage ErisPulse instances |
| [CLI Command Reference](docs/en/cli-reference.md) | Complete usage instructions for the `epsdk` command line tool |
| [Configuration File Guide](docs/en/configuration.md) | Detailed description of various configuration items in `config/config.toml` |
| [Deployment Guide](docs/en/deployment.md) | Docker deployment, systemd service, SSL configuration |

## Quick Reference

### Common Commands

| Command | Description |
|------|------|
| `epsdk init` | Initialize project (`-q` quick mode, `-n` specify name) |
| `epsdk install <package_name>` | Install module/adapter (enter interactive mode without parameters) |
| `epsdk run main.py` | Run project (`--reload` hot reload mode) |
| `epsdk list` | List installed modules/adapter |
| `epsdk upgrade <package_name>` | Upgrade module/adapter |
| `epsdk doctor` | Diagnose environment (Python/Backend/Configuration/PyPI connectivity) |

> For a complete list of commands and parameter descriptions, please refer to [CLI Command Reference](cli-reference.md).

### Common Configuration Locations

| Configuration Item | Description | See Also |
|--------|------|------|
| `[ErisPulse.server]` | Server configuration (host, port) | [Configuration File Description](configuration.md#server-configuration) |
| `[ErisPulse.logger]` | Logging configuration (level, output file) | [Configuration File Description](configuration.md#logging-configuration) |
| `[ErisPulse.framework]` | Framework configuration (lazy loading) | [Configuration File Description](configuration.md#framework-configuration) |
| `[ErisPulse.event.command]` | Command event configuration (prefix) | [Configuration File Description](configuration.md#event-configuration) |
| `[AdapterName]` | Adapter-specific configuration | [Platform Features Guide](../platform-guide/) |

## Related Documentation

- [Quick Start](../quick-start.md) - Quick start guide
- [Getting Started](../getting-started/) - Getting started tutorial
- [Developer Guide](../developer-guide/) - Developing custom modules and adapters
- [API Reference](../api-reference/) - API documentation