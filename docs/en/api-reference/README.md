# API Reference

This directory contains the API reference documentation for the ErisPulse framework.

## Documentation List

| Document | Description |
|------|------|
| [Core Modules API](core-modules.md) | Quick reference for Storage, Config, Logger, Adapter, Module, Lifecycle, Router, and HTTP Client APIs |
| [Event System API](event-system.md) | API reference for Command, Message, Notice, Request, and Meta event modules |
| [Adapter System API](adapter-system.md) | API reference for Adapter Manager, SendDSL, Middleware, and Bot State Management |
| [Auto-generated API](auto_api/README.md) | Complete API documentation automatically generated from source code docstrings |

> Manually written API documentation focuses on usage examples and quick lookup; auto-generated API documentation includes complete class/method signatures. They complement each other.

## Module Overview

### Core Modules

| Module | Path | Description |
|------|------|------|
| `sdk.storage` | `sdk.storage` | SQLite-based Key-Value Storage + SQL Chained Query |
| `sdk.config` | `sdk.config` | TOML format Configuration Management |
| `sdk.logger` | `sdk.logger` | Modular Logging System with support for sub-loggers |
| `sdk.adapter` | `sdk.adapter` | Multi-platform Adapter Management |
| `sdk.module` | `sdk.module` | Module Registration, Loading, and Unloading Management |
| `sdk.lifecycle` | `sdk.lifecycle` | Lifecycle Event Management |
| `sdk.router` | `sdk.router` | HTTP/WebSocket Routing Management |
| `sdk.client` | `sdk.client` | Unified HTTP/WS Client |

### Event System

| Module | Import Path | Description |
|------|------|------|
| `command` | `ErisPulse.Core.Event.command` | Command Handling (Prefix parsing, Aliases) |
| `message` | `ErisPulse.Core.Event.message` | Message Events (Private, Group, @ mention) |
| `notice` | `ErisPulse.Core.Event.notice` | Notice Events (Friend, Group member changes) |
| `request` | `ErisPulse.Core.Event.request` | Request Events (Friend request, Group invite) |
| `meta` | `ErisPulse.Core.Event.meta` | Meta Events (Connect, Disconnect, Heartbeat) |

### Base Classes

| Base Class | Import Path | Description |
|------|------|------|
| `BaseModule` | `ErisPulse.Core.Bases.module.BaseModule` | Module Base Class (on_load/on_unload) |
| `BaseAdapter` | `ErisPulse.Core.Bases.adapter.BaseAdapter` | Adapter Base Class (start/shutdown/call_api) |

## Related Documentation

- [Core Concepts](../getting-started/basic-concepts.md) - Understand framework core concepts
- [Module Development Guide](../developer-guide/modules/) - Develop custom modules
- [Adapter Development Guide](../developer-guide/adapters/) - Develop platform adapters
- [Advanced Topics](../advanced/) - Deep dive into Routing, HTTP Client, SQL Builder, etc.