# Advanced Topics

This directory contains advanced features and in-depth topics of the ErisPulse framework.

## Document List

- [Startup Process and Manual Control](startup.md) - Breakdown of the startup chain (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](lazy-loading.md) - Working principles, configuration, and event-driven lazy activation (activate_on) of the lazy loading module system
- [Scope](scope.md) - Three-dimensional scope control: module availability / event access / outbound action restriction (including method-level granular rules and binding inheritance merge)
- [Ownership System](ownership.md) - Resource ownership and automatic recycling: owner context mechanism, full view of owned resources, unload cleanup sequence, and design boundaries
- [Shadow Modules and Gray Promotion](shadow.md) - Independent owner parallel testing of new module versions: outbound interception and accounting, behavior diff comparison, promote promotion, and rollback on failure
- [Interaction Session System](interaction.md) - wait_reply / session timer / multi-path waiting / session mutual exclusion lease / inbox / message transaction / chain tracing
- [Inter-Module Communication](module-communication.md) - RPC protocol (module.call), service contracts and directory, directed events, cold-start replay, event idempotency deduplication
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection
- [Lifecycle Management](lifecycle.md) - Usage methods of the lifecycle event system
- [Router Manager](router.md) - HTTP and WebSocket routing management (including single-argument registration, tuple response conventions)
- [Connection Pool and Broadcasting](connections.md) - Connection registry: broadcasting, group subscriptions, cross-module passing and reuse, connection pool viewing
- [HTTP Client](http-client.md) - Unified HTTP request client
- [Session Inbox](transcript.md) - Automatic message recording: retention policy knobs, runtime override APIs, and risk/audit
- [MessageBuilder Detailed Explanation](message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [SQL Query Builder](sql-builder.md) - General SQL chain query builder and storage backend abstraction
- [Storage Backends](storage-backends.md) - Asynchronous native storage backends selection, configuration, and switching (sqlite / mysql / postgres)
- [Exception System and Capture Guide](errors.md) - Framework-wide exception types, occurrence locations, and capture recommendations
- [Session Type System](../standards/session-types.md) - Session type definition, mapping, and custom type registration
- [Conversation Multi-turn Dialogue](conversation.md) - Interaction methods for multi-turn dialogue context

> [!NOTE]
> Documentation for **third-party ecosystem modules** such as Dashboard view registration and Takumi image rendering has been moved to the [Ecosystem Modules](../ecosystem/README.md) directory.

## Intended Audience

These documents are suitable for the following types of developers:

- Developers who are already familiar with the basic features of ErisPulse
- Developers who need to deeply understand the internal mechanisms of the framework
- Developers who need to optimize performance or implement complex features

## Prerequisites

Before reading the documents in this directory, it is recommended to first understand:

- [Basic Concepts](../getting-started/basic-concepts.md)
- [Event Handling Introduction](../getting-started/event-handling.md)
- [Module Development Guide](../developer-guide/modules/)