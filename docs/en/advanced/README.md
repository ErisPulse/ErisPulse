# Advanced Topics

This directory contains advanced topics of the ErisPulse framework—deep capabilities such as permission control, canary release, multi-round interaction, and storage backends—each addressing a specific category of problems.

> [!NOTE]
> All topics in this directory are **on-demand reference documents**—please first read the five core L1 articles in the homepage, and then refer to this directory when encountering corresponding needs. Each article begins with a note indicating "When you need to read this article."

## Four Essential L2 Articles

The following four articles are essential for writing production-grade modules. It is recommended to read them thoroughly before working on complex modules (consistent with the guidance on the documentation homepage):

- [Scope](scope.md) - Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level granular rules and binding inheritance merge)
- [Ownership (owner) System](ownership.md) - Resource ownership and automatic cleanup: owner context mechanism, full view of owned resources, unload cleanup sequence, hot reload boundaries, and design boundaries
- [Lifecycle Management](lifecycle.md) - Lifecycle event system: what each module / adapter should do when loading, unloading, reloading, or disabling
- [Interaction Session System](interaction.md) - wait_reply / session timers / multi-path waiting / session mutual exclusion leases / inbox / message transactions / link tracing

## Grouped by Scenario

The grouping follows the same criteria as the "Deep Understanding of Principles" section on the documentation homepage; the first article in each group notes "what pitfalls you'll hit without understanding it."

**Running & Startup** —— Without understanding the startup chain (Finder / Loader / Manager / Router), you can only stare helplessly at the logs when module loading fails.

- [Startup Process and Manual Control](startup.md) - Breakdown of the startup chain (Finder/Loader/Manager/Router) and a full manual startup
- [Lazy Loading System](lazy-loading.md) - How the lazy-loading module system works, its configuration, and event-driven lazy activation (activate_on)

**Communication & Connection** —— Without understanding the service contract (`meta.services`) whitelist, cross-module `module.call` calls will be rejected by `ServiceNotProvidedError` and you won't know why.

- [Inter-Module Communication](module-communication.md) - RPC protocolization (module.call), service contracts and directory, directed events, cold-start replay, and event idempotent deduplication
- [Connection Pools and Broadcasting](connections.md) - Connection registry: broadcasting, group subscription, cross-module passing and reuse, connection pool inspection
- [Router Manager](router.md) - HTTP and WebSocket route management (including single-parameter registration and tuple response conventions)

**Data Storage** —— Without understanding the semantics of the connection-failure cooldown period, database instability will lead you to misjudge that "the framework is down" (in fact it fails fast and automatically reconnects after the cooldown).

- [Storage Backends](storage-backends.md) - Selection, configuration, and switching of the sqlite / mysql / postgres async native storage backends
- [SQL Query Builder](sql-builder.md) - A general-purpose SQL chained query builder and storage backend abstraction
- [Network Client](client.md) - Unified HTTP request client

**Messaging & Conversation** —— Without understanding the conversation mutual-exclusion lease, two modules waiting for the same user's reply at the same time will kick each other off.

- [Conversation Multi-Turn Dialogue](conversation.md) - Interaction methods for multi-turn conversation context
- [Conversation Inbox](transcript.md) - Automatic message recording: retention policy knobs, runtime override APIs, and risk/audit considerations
- [MessageBuilder in Detail](message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection

**Shadow & Canary** —— Promoting early without understanding the five isolation gates will let the shadow's outbound messages spill over to real users.

- [Shadow Modules and Canary Promotion](shadow.md) - Independent-owner parallel trial runs of new module versions: outbound interception accounting, behavior diff comparison, promote-to-production, and rollback on failure

**Performance & Observability** —— If your only response to problems is restarting without looking at metrics, you're flying blind.

- [Performance Benchmarks and Tuning](performance.md) - Measured benchmark figures (including NoneBot2 comparisons), how to run benchmarks yourself and compare regressions, tuning essentials, and memory diagnostics
- [runtime Toolkit](runtime.md) - Quick reference for the `ErisPulse.runtime` aggregated export layer: ownership, background tasks, event context, memory snapshots, dict parsing, and troubleshooting diagnostics

**Exceptions & Standards Reference**

- [Exception System and Catching Guide](errors.md) - All framework exception types, where they occur, and recommendations for catching them
- [Session Type System](../standards/session-types.md) - Session type definitions, mappings, and custom type registration

> [!NOTE]
> Documentation for **third-party ecosystem modules** such as Dashboard window registration and Takumi image rendering has been migrated to the [Ecosystem Modules](../ecosystem/README.md) directory.

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