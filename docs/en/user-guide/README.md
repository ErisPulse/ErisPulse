# User Guide

This guide helps you install, configure, and manage the ErisPulse project.

## Content List

| Document | Description |
|----------|-------------|
| [Installation and Setup](installation.md) | System requirements, installation methods (pip/uv/Docker), and installation verification |
| [ErisPulse-App Mobile/Desktop Client](../ecosystem/app.md) | Official client: Run directly on mobile/desktop with native interface to manage ErisPulse instances |
| [CLI Command Reference](cli-reference.md) | Complete usage instructions for the `epsdk` command-line tool |
| [Configuration File Reference](configuration.md) | Detailed explanation of each configuration item in `config/config.toml` |
| [Deployment Guide](deployment.md) | Docker deployment, systemd service setup, and SSL configuration |

## Quick Reference

### Common Commands

| Command | Description |
|---------|-------------|
| `epsdk init` | Initialize project (`-q` for quick mode, `-n` to specify name) |
| `epsdk install <package-name>` | Install module/adapter (enters interactive mode without parameters) |
| `epsdk config <name>` | Interactive configuration of declarative configuration items for adapter/module |
| `epsdk run main.py` | Run project (`--reload` for hot-reload mode) |
| `epsdk list` | List installed modules/adapters |
| `epsdk upgrade <package-name>` | Upgrade module/adapter |
| `epsdk doctor` | Diagnose environment (Python/backend/configuration/PyPI connectivity) |

> For the complete list of commands and parameter descriptions, see [CLI Command Reference](cli-reference.md).

### Common Configuration Locations

| Configuration | Description | See Also |
|---------------|-------------|----------|
| `[ErisPulse.server]` | Server configuration (host, port) | [Configuration File Guide](configuration.md#server-configuration) |
| `[ErisPulse.logger]` | Logging configuration (level, output file) | [Configuration File Guide](configuration.md#logging-configuration) |
| `[ErisPulse.framework]` | Framework configuration (lazy loading) | [Configuration File Guide](configuration.md#framework-configuration) |
| `[ErisPulse.event.command]` | Command event configuration (prefix) | [Configuration File Guide](configuration.md#event-configuration) |
| `[Adapter Name]` | Adapter-specific configuration | [Platform Features Guide](../platform-guide/) |

## Related Documentation

- [Quick Start](../quick-start.md) - Quick start guide
- [Getting Started](../getting-started/) - Getting started tutorial
- [Developer Guide](../developer-guide/) - Guide to developing custom modules and adapters
- [API Reference](../api-reference/) - API documentation