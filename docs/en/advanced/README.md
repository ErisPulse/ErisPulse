# Advanced Topics

This directory contains advanced features and in-depth topics of the ErisPulse framework.

## Documentation List

- [Startup Process & Manual Control](startup.md) - Startup flow breakdown (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](lazy-loading.md) - Working principles, configuration, and event-driven lazy activation (activate_on) of the lazy loading module system
- [Scope](scope.md) - Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level granular rules and binding inheritance merge)
- [Ownership System](ownership.md) - Resource ownership and automatic cleanup: owner context mechanism, ownership resource overview, unload cleanup sequence, and design boundaries
- [Interaction Session System](interaction.md) - wait_reply / session timer / multipath waiting / session mutual exclusion lease / inbox / message transaction / link tracing
- [Inter-Module Communication](module-communication.md) - RPC protocol (module.call), service contracts and directory, directed events, cold start replay, event idempotent deduplication
- [Internationalization (i18n)](i18n.md) - Multi-language support, translation registration, and language detection
- [Lifecycle Management](lifecycle.md) - Usage methods of the lifecycle event system
- [Router Manager](router.md) - HTTP and WebSocket routing management
- [HTTP Client](http-client.md) - Unified HTTP request client
- [MessageBuilder Detailed Explanation](message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [SQL Query Builder](sql-builder.md) - General SQL chained query builder and storage backend abstraction
- [Storage Backends](storage-backends.md) - Selection, configuration, and switching of asynchronous native storage backends: sqlite / mysql / postgres
- [Session Type System](../standards/session-types.md) - Session type definition, mapping, and custom type registration
- [Conversation Multi-turn Dialogue](conversation.md) - Interaction methods of multi-turn dialogue context

> [!NOTE]
> Documentation for **third-party ecosystem modules** such as Dashboard window registration and Takumi image rendering has been moved to the [Ecosystem Modules](../ecosystem/README.md) directory.

## Intended Audience

These documents are suitable for the following developers:

- Developers who are already familiar with the basic features of ErisPulse
- Developers who need to deeply understand the internal mechanisms of the framework
- Developers who need to optimize performance or implement complex features

## Prerequisites

Before reading the documents in this directory, it is recommended to first understand:

- [Basic Concepts](../getting-started/basic-concepts.md)
- [Event Handling Introduction](../getting-started/event-handling.md)
- [Module Development Guide](../developer-guide/modules/)