# API Reference

This directory contains the API reference documentation for the ErisPulse framework.

## Documentation List

| Documentation | Description |
|---------------|-------------|
| [Core Module API](core-modules.md) | Quick reference for Storage, Config, Logger, Adapter, Module, Lifecycle, Router, and HTTP Client APIs |
| [Event System API](event-system.md) | API reference for Command, Message, Notice, Request, and Meta event modules |
| [Adapter System API](adapter-system.md) | API reference for Adapter Manager, SendDSL, Middleware, and Bot state management |
| [Auto-generated API](auto_api/README.md) | Complete API documentation automatically generated from source code docstrings |

> Manually written API documentation focuses on usage examples and quick reference; auto-generated API documentation includes complete class/method signatures. The two complement each other.

## Module Overview

### Core Modules

| Module | Access Path | Description |
|--------|-------------|-------------|
| `sdk.storage` | `sdk.storage` | Key-value storage based on SQLite + SQL chain query |
| `sdk.config` | `sdk.config` | Configuration management in TOML format |
| `sdk.logger` | `sdk.logger` | Modular logging system, supports sub-loggers |
| `sdk.adapter` | `sdk.adapter` | Multi-platform adapter management |
| `sdk.module` | `sdk.module` | Module registration, loading, and unloading management |
| `sdk.lifecycle` | `sdk.lifecycle` | Lifecycle event management |
| `sdk.router` | `sdk.router` | HTTP/WebSocket routing management |
| `sdk.client` | `sdk.client` | Unified HTTP/WS client |

### Event System

| Module | Import Path | Description |
|--------|-------------|-------------|
| `command` | `ErisPulse.Core.Event.command` | Command handling (prefix parsing, aliases) |
| `message` | `ErisPulse.Core.Event.message` | Message events (private chat, group chat, @ messages) |
| `notice` | `ErisPulse.Core.Event.notice` | Notice events (friend, group member changes) |
| `request` | `ErisPulse.Core.Event.request` | Request events (friend requests, group invitations) |
| `meta` | `ErisPulse.Core.Event.meta` | Meta events (connection, disconnection, heartbeat) |

### Base Classes

| Base Class | Import Path | Description |
|------------|-------------|-------------|
| `BaseModule` | `ErisPulse.Core.Bases.module.BaseModule` | Module base class (on_load/on_unload) |
| `BaseAdapter` | `ErisPulse.Core.Bases.adapter.BaseAdapter` | Adapter base class (start/shutdown/call_api) |

## Related Documentation

- [Core Concepts](../getting-started/basic-concepts.md) - Understand the framework's core concepts
- [Module Development Guide](../developer-guide/modules/) - Develop custom modules
- [Adapter Development Guide](../developer-guide/adapters/) - Develop platform adapters
- [Advanced Topics](../advanced/) - In-depth documentation on routing, HTTP clients, SQL builders, and more