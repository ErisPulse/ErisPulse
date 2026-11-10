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

Consistent with the grouping logic in the documentation homepage's "Deep Dive into Principles," the first article in each group is marked with "What pitfalls you'll encounter if you don't understand this."

**Startup** —— Without understanding the startup chain (Finder / Loader / Manager / Router), you can only stare helplessly at the logs when module loading fails.

- [Startup Process and Manual Control](startup.md) - Breakdown of the startup chain (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](lazy-loading.md) - Working principle, configuration, and event-driven lazy activation (activate_on) of the lazy loading module system

**Communication & Connection** —— Without understanding service contracts (`meta.services`) whitelists, cross-module `module.call` will be rejected by `ServiceNotProvidedError` and you won't know why.

- [Module Communication](module-communication.md) - RPC protocolization (`module.call`), service contracts and directories, directed events, cold-start replay, event idempotency deduplication
- [Connection Pool & Broadcasting](connections.md) - Connection registry: broadcasting, group subscriptions, cross-module passing and reuse, connection pool inspection
- [Router Manager](router.md) - HTTP and WebSocket route management (including single-parameter registration, tuple response conventions)

**Data Storage** —— Without understanding the semantics of connection failure cooldown periods, you might mistakenly conclude that the framework has crashed during database fluctuations (it is actually a rapid failure followed by automatic reconnection after cooldown).

- [Storage Backends](storage-backends.md) - Selection, configuration, and switching of asynchronous native storage backends (sqlite / mysql / postgres)
- [SQL Query Builder](sql-builder.md) - General SQL fluent query builder and storage backend abstraction
- [Network Client](client.md) - Unified HTTP request client

**Messaging & Conversations** —— Without understanding session mutual exclusion leases, two modules waiting for the same user's reply will kick each other off.

- [Conversation Multi-turn Dialogue](conversation.md) - Interaction methods for multi-turn conversation context
- [Conversation Inbox](transcript.md) - Automatic message recording: retention policy controls, runtime override APIs, and risk/audit considerations
- [MessageBuilder Detailed Explanation](message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection

**Shadow Gray Release** —— Without understanding the five isolation gates, shadow outbound messages will leak into real users prematurely.

- [Shadow Modules & Gray Release Promotion](shadow.md) - Independent owner parallel testing of new module versions: outbound interception and accounting, behavior diff comparison, promote promotion and rollback on failure

**Performance & Observability** —— If you only restart when problems occur without checking metrics, it's like flying blind.

- [Performance Benchmarking & Tuning](performance.md) - Measured baseline numbers (including NoneBot2 comparison), self-running benchmarks and regression comparison methods, tuning key points

**Exceptions & Standards Reference**

- [Exception System & Handling Guide](errors.md) - All framework exception types, occurrence locations, and handling suggestions
- [Session Type System](../standards/session-types.md) - Session type definitions, mappings, and custom type registration

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