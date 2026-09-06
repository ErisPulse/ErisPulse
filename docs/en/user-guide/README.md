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
|---------|-------------|
| `epsdk init` | Initialize project (`-q` for quick mode, `-n` to specify name) |
| `epsdk install <package-name>` | Install module/adapter (without parameters, enter interactive mode) |
| `epsdk config <name>` | Interactively configure declarative configuration items for adapter/module |
| `epsdk run main.py` | Run project (`--reload` for hot reload mode) |
| `epsdk list` | List installed modules/ adapters |
| `epsdk upgrade <package-name>` | Upgrade module/adapter |
| `epsdk doctor` | Diagnose environment (Python/backend/configuration/PyPI connectivity) |

> For a complete list of commands and parameter descriptions, see [CLI Command Reference](cli-reference.md).

### Common Configuration Locations

| Configuration Item | Description | See Also |
|--------------------|-------------|----------|
| `[ErisPulse.server]` | Server configuration (host, port) | [Configuration File Description](configuration.md#server-configuration) |
| `[ErisPulse.logger]` | Logging configuration (level, output file) | [Configuration File Description](configuration.md#logging-configuration) |
| `[ErisPulse.framework]` | Framework configuration (lazy loading) | [Configuration File Description](configuration.md#framework-configuration) |
| `[ErisPulse.event.command]` | Command event configuration (prefix) | [Configuration File Description](configuration.md#event-configuration) |
| `[Adapter Name]` | Adapter-specific configuration | [Platform Features Guide](../platform-guide/) |

## Related Documentation

- [Quick Start](../quick-start.md) - Quick start guide
- [Getting Started](../getting-started/) - Getting started tutorial
- [Developer Guide](../developer-guide/) - Developing custom modules and adapters
- [API Reference](../api-reference/) - API documentation