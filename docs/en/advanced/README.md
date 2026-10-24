# Advanced Topics

This directory contains advanced topics of the ErisPulse framework—deep capabilities such as permission control, canary release, multi-round interaction, and storage backends—each addressing a specific category of problems.

> [!NOTE]
> All topics in this directory are **on-demand reference documents**—please first read the five core L1 articles in the homepage, and then refer to this directory when encountering corresponding needs. Each article begins with a note indicating "When you need to read this article."

## Four Must-Reads for L2

These four articles are essential when writing production-level modules. It is recommended to read them thoroughly before working on complex modules (consistent with the guidelines in the documentation homepage):

- [Scope](scope.md) - Three-dimensional scope control: module availability / event entry / outbound action restrictions (including method-level granular rules and binding inheritance merge)
- [Ownership (owner) System](ownership.md) - Resource ownership and automatic cleanup: owner context mechanism, ownership resource overview, unload cleanup sequence, and design boundaries
- [Lifecycle Management](lifecycle.md) - Lifecycle event system: what each module / adapter should do during loading, unloading, reloading, and disabling
- [Interaction Session System](interaction.md) - wait_reply / session timer / multi-path waiting / session mutual exclusion lease / inbox / message transaction / link tracing

## Group by Scenario

Grouped in the same way as the "Deep Understanding of Principles" section on the documentation homepage. The first article in each group is marked with "What pitfalls will you encounter if you don't understand this?"

**Startup** —— If you don't understand the startup chain (Finder / Loader / Manager / Router), you'll be left staring helplessly at the logs when module loading fails.

- [Startup Flow and Manual Control](startup.md) - Breakdown of the startup chain (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](lazy-loading.md) - Working principle, configuration, and event-driven lazy activation (activate_on) of the lazy loading module system

**Communication & Connection** —— If you don't understand service contracts (`meta.services`) whitelists, cross-module `module.call` will be rejected by `ServiceNotProvidedError` without knowing the reason.

- [Module Communication](module-communication.md) - RPC protocol (module.call), service contracts and directories, directed events, cold-start replay, event idempotency deduplication
- [Connection Pool & Broadcasting](connections.md) - Connection registry: broadcasting, group subscriptions, cross-module passing and reuse, and viewing connection pools
- [Router Manager](router.md) - HTTP and WebSocket routing management (including single-argument registration and tuple response conventions)

**Data Storage** —— If you don't understand the semantics of connection failure cooldown periods, you may mistakenly conclude that the framework has crashed during database fluctuations (when in fact it is a rapid failure followed by automatic reconnection after cooldown).

- [Storage Backends](storage-backends.md) - Selecting, configuring, and switching asynchronous native storage backends such as sqlite / mysql / postgres
- [SQL Query Builder](sql-builder.md) - A generic SQL chainable query builder and storage backend abstraction
- [HTTP Client](http-client.md) - Unified HTTP request client

**Messaging & Conversation** —— If you don't understand session mutual exclusion leases, two modules simultaneously waiting for the same user's reply will kick each other off.

- [Conversation Multi-turn Dialogue](conversation.md) - Interaction methods for multi-turn dialogue context
- [Session Inbox](transcript.md) - Automatic message recording: retention policy controls, runtime override APIs, and risk/audit considerations
- [MessageBuilder Detailed Explanation](message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection

**Gray Shadow** —— If you don't understand the five isolation gates before promoting to production, shadow outbound messages will leak to real users.

- [Shadow Modules and Gray Promotion](shadow.md) - Independent parallel testing of new module versions with separate owners: outbound interception and accounting, behavior diff comparison, promote to production, and rollback on failure

**Exceptions & Standards Reference**

- [Exception System and Capture Guide](errors.md) - All framework exception types, occurrence locations, and capture recommendations
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