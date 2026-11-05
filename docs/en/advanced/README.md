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

Consistent with the grouping criteria on the documentation homepage "Deep Understanding of Principles," the first entry in each group is marked with "What pitfalls will you encounter if you don't understand."

**Startup** —— Not understanding the startup chain (Finder / Loader / Manager / Router) leaves you staring helplessly at logs when module loading fails.

- [Startup Process and Manual Control](startup.md) - Breakdown of the startup chain (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](lazy-loading.md) - Working principles, configuration, and event-driven lazy activation (activate_on) of the lazy loading module system

**Communication & Connection** —— Not understanding service contracts (`meta.services`) whitelists causes cross-module `module.call` to be rejected by `ServiceNotProvidedError` without knowing the reason.

- [Module Communication](module-communication.md) - RPC protocol (module.call), service contracts and directories, directed events, cold start replay, event idempotency deduplication
- [Connection Pool & Broadcasting](connections.md) - Connection registry: broadcasting, grouped subscriptions, cross-module passing and reuse, connection pool inspection
- [Router Manager](router.md) - HTTP and WebSocket routing management (including single-argument registration, tuple response conventions)

**Data Storage** —— Not understanding the semantics of connection failure cooldown periods leads to mistakenly concluding the framework is down during database jitter (actually it's fast failure followed by automatic reconnection after cooldown).

- [Storage Backends](storage-backends.md) - Selecting, configuring, and switching between asynchronous native storage backends (sqlite / mysql / postgres)
- [SQL Query Builder](sql-builder.md) - General SQL chainable query builder and storage backend abstraction
- [Network Client](client.md) - Unified HTTP request client

**Messaging & Conversation** —— Not understanding session mutual exclusion leases causes two modules waiting for the same user's reply to kick each other out.

- [Conversation Multi-turn Dialogue](conversation.md) - Interaction methods for multi-turn dialogue context
- [Session Inbox](transcript.md) - Automatic message recording: retention policy controls, runtime override APIs, risk/audit
- [MessageBuilder Detailed Explanation](message-builder.md) - Dual-mode usage of OneBot12 message segment builder
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection

**Shadow & Grey-scale** —— Not understanding five isolation gates before promotion causes shadow outbound messages to leak into real users.

- [Shadow Modules & Grey-scale Promotion](shadow.md) - New module versions run in parallel with independent owners: outbound interception and accounting, behavior diff comparison, promote promotion and rollback on failure

**Exceptions & Standards Reference**

- [Exception System and Capture Guide](errors.md) - All framework exception types, occurrence locations, and capture recommendations
- [Session Type System](../standards/session-types.md) - Session type definitions, mappings, and custom type registration

> [!NOTE]
> Documentation for **third-party ecosystem modules** such as Dashboard view registration and Takumi image rendering has been moved to the [ecosystem](../ecosystem/README.md) directory.

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