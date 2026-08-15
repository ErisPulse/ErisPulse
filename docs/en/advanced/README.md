# Advanced Topics

This directory contains advanced features and in-depth topics of the ErisPulse framework.

## Documentation List

- [Startup Process and Manual Control](docs/en/startup.md) - Deconstruction of the startup pipeline (Finder/Loader/Manager/Router) and manual full startup
- [Lazy Loading System](docs/en/lazy-loading.md) - How the lazy loading module system works and configuration
- [Module Scope System](docs/en/scope.md) - Binding and isolation of modules and adapters Bot/Platform
- [Internationalization (i18n)](docs/en/i18n.md) - Multi-language support, translation registration, and language detection
- [Lifecycle Management](docs/en/lifecycle.md) - Usage of the lifecycle event system
- [Router Manager](docs/en/router.md) - HTTP and WebSocket routing management
- [HTTP Client](docs/en/http-client.md) - Unified HTTP request client
- [MessageBuilder Deep Dive](docs/en/message-builder.md) - Dual-mode usage of the OneBot12 message segment builder
- [SQL Query Builder](docs/en/sql-builder.md) - Generic SQL chain query builder and storage backend abstraction
- [Session Type System](docs/en/session-types.md) - Session type definition, mapping, and custom type registration
- [Conversation Multi-turn Dialogue](docs/en/conversation.md) - Interaction methods for multi-turn dialogue context

> [!NOTE]
> Documentation for **Third-party Ecosystem Modules** such as Dashboard window registration and Takumi image rendering has been migrated to the [Ecosystem Modules](../ecosystem/README.md) directory.

Please return the complete translated Markdown content directly, without including any other text.

## Target Audience

These documents are suitable for the following developers:

- Developers already familiar with ErisPulse basic features
- Developers needing a deep understanding of internal framework mechanisms
- Developers needing to optimize performance or implement complex features

Please return the complete translated Markdown content directly, without including any other text.

Reminder: If the document contains language switching lines (lines separated by ` | `), strictly follow the formatting requirement in item 8 above; do not write incorrect formats like ``[**Label**](file)``.

## Prerequisites

Before reading the documents in this directory, it is recommended to understand:

- [Basic Concepts](../getting-started/basic-concepts.md)
- [Introduction to Event Handling](../getting-started/event-handling.md)
- [Module Development Guide](../developer-guide/modules/)