# User Guide

This guide helps you install, configure, and manage the ErisPulse project.

## Table of Contents

| Document | Description |
|----------|-------------|
| [Installation and Configuration](installation.md) | System requirements, installation methods (pip/uv/Docker), verification of installation |
| [CLI Command Reference](cli-reference.md) | Complete usage instructions for the command-line tool `epsdk` |
| [Configuration File Guide](configuration.md) | Detailed explanation of configuration items in `config/config.toml` |
| [Deployment Guide](deployment.md) | Docker deployment, systemd service, SSL configuration |

## Quick Reference

### Common Commands

| Command | Description |
|---------|-------------|
| `epsdk init` | Initialize project (`-q` quick mode, `-n` specify name) |
| `epsdk install <package name>` | Install module/adapter (enter interactive mode without parameters) |
| `epsdk run main.py` | Run project (`--reload` hot reload mode) |
| `epsdk list` | List installed modules/adapters |
| `epsdk upgrade <package name>` | Upgrade module/adapter |

> For a complete list of commands and parameter descriptions, see [CLI Command Reference](cli-reference.md).

### Common Configuration Locations

| Configuration Item | Description | See Also |
|--------------------|-------------|----------|
| `[ErisPulse.server]` | Server configuration (host, port) | [Configuration File Guide](configuration.md#server-configuration) |
| `[ErisPulse.logger]` | Logging configuration (level, output file) | [Configuration File Guide](configuration.md#logging-configuration) |
| `[ErisPulse.framework]` | Framework configuration (lazy loading) | [Configuration File Guide](configuration.md#framework-configuration) |
| `[ErisPulse.event.command]` | Command event configuration (prefix) | [Configuration File Guide](configuration.md#event-configuration) |
| `[Adapter Name]` | Specific configuration for each adapter | [Platform Features Guide](../platform-guide/) |

## Related Documentation

- [Quick Start](../quick-start.md) - Quick start guide
- [Getting Started](../getting-started/) - Getting started tutorials
- [Developer Guide](../developer-guide/) - Develop custom modules and adapters
- [API Reference](../api-reference/) - API documentation