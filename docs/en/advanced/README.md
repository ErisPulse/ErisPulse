# Advanced Topics

This directory contains advanced features and in-depth topics of the ErisPulse framework.

## Document List

- [Startup Process and Manual Control](startup.md) - Breakdown of the startup chain (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](lazy-loading.md) - Working principles, configuration, and event-driven lazy activation (activate_on) of the lazy loading module system
- [Module Scope System](scope.md) - Binding and isolation of modules and adapters (Bot/Platform)
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection
- [Lifecycle Management](lifecycle.md) - Usage methods of the lifecycle event system
- [Router Manager](router.md) - HTTP and WebSocket routing management
- [HTTP Client](http-client.md) - Unified HTTP request client
- [MessageBuilder Detailed Explanation](message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [SQL Query Builder](sql-builder.md) - General SQL chain query builder and storage backend abstraction
- [Session Type System](../standards/session-types.md) - Session type definition, mapping, and custom type registration
- [Conversation Multi-turn Dialogue](conversation.md) - Interaction methods for multi-turn dialogue context

> [!NOTE]
> Documentation for third-party ecosystem modules such as Dashboard window registration and Takumi image rendering has been moved to the [Ecosystem Modules](../ecosystem/README.md) directory.

## Target Audience

These documents are suitable for the following developers:

- Developers already familiar with ErisPulse basic features
- Developers needing a deep understanding of internal framework mechanisms
- Developers needing to optimize performance or implement complex features



## Prerequisites

Before reading the documents in this directory, it is recommended to understand:

- [Basic Concepts](../getting-started/basic-concepts.md)
- [Introduction to Event Handling](../getting-started/event-handling.md)
- [Module Development Guide](../developer-guide/modules/)