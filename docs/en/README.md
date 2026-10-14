# ErisPulse Documentation

ErisPulse is an extensible, multi-platform message processing framework that supports interaction with various platforms through adapters, providing a flexible module system for functional extension.

> **First time using?** Just check out the [5-Minute Quick Start](docs/en/quick-start.md) —— from installation to running your first bot, all in one go.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is ordered from basic to advanced.

> [!IMPORTANT]
> **You don't need to read all the documentation.** Most developers only need to read the **L1 Core Five** (about 1–2 hours) to independently develop 90% of features; the rest are on-demand reference materials for specific scenarios—refer to them when you encounter corresponding needs. Each document starts with "When you need to read this."
>
> **L1 Core Five**: [Getting Started with Module Development](developer-guide/modules/getting-started.md) → [Basic Concepts](getting-started/basic-concepts.md) → [Event Wrapper](developer-guide/modules/event-wrapper.md) → [Configuration File Guide](user-guide/configuration.md) → [Error Handling](advanced/errors.md)
>
> Adapter authors also need: [Getting Started with Adapter Development](developer-guide/adapters/getting-started.md) → [Event Converters](developer-guide/adapters/converter.md) → [SendDSL Explained](developer-guide/adapters/send-dsl.md)

### I. I Want to Use a Bot

Get the bot up and running, install modules, and configure it.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](quick-start.md) | Installation, initialization, and running — the only starting point |
| Direct App Installation | [ErisPulse-App Client](ecosystem/app.md) | Official cross-platform client: run and manage directly via mobile/PC GUI, no terminal required |
| ② In-depth | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Read as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences between platforms (Yunhu/QQ/Telegram…) |

### II. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|-----------------|----------|
| **Module Development** (Recommended) | [Getting Started with Module Development](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Getting Started with Adapter Development](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Explained](developer-guide/adapters/send-dsl.md) · [Event Converters](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Adapter development must follow the [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) standards |
| **Testing & Debugging** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Troubleshoot why a command wasn't triggered |
| **Publishing** | [Publishing & Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### III. I Want to Deeply Understand the Principles

Understand how the framework works internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and module hot-reload architecture (supports all module sources) |
| [Startup Process & Manual Control](advanced/startup.md) | Breakdown of the startup chain, manual control of each step, diagnosis of loading failures |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, start/stop, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](advanced/lifecycle.md) · [Lazy Loading](advanced/lazy-loading.md) · [Routing System](advanced/router.md) | Internal subsystems |
| [Connection Pool & Broadcasting](advanced/connections.md) · [Session Inbox](advanced/transcript.md) | First-class resources: broadcast/group/cross-module passing and reuse, connection pool viewing; message retention policies and runtime overrides |
| [Scopes (scope)](advanced/scope.md) | Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level fine-grained rules, binding inheritance merge) |
| [Ownership (owner) System](advanced/ownership.md) | Resource ownership and automatic cleanup: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Shadow Modules & Gray Promotion](advanced/shadow.md) | New module versions run in parallel with independent owners: five isolation gates, behavior diff alignment, promote to official and rollback on failure |
| [Interactive Session System](advanced/interaction.md) | Full explanation of wait_reply, session timers (remind/escalate), multi-path waiting (select), session mutual exclusion leases, inbox, message transactions, and traceability |
| [Inter-Module Communication](advanced/module-communication.md) | RPC protocol (module.call), meta.services service contracts and directories, targeted event emit(to=), cold start replay, event idempotency deduplication |
| [Conversation Multi-turn Dialogue](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL Builder](advanced/sql-builder.md) · [Storage Backends](advanced/storage-backends.md) · [HTTP Client](advanced/http-client.md) · [Internationalization](advanced/i18n.md) | Advanced tools |

### IV. Ecosystem & Official Clients

Official clients + on-demand installable, plug-and-play ecosystem modules (none are built-in features).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, why these are not built-in features |
| [ErisPulse-App](ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray icon |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-time / interval / Cron expressions, callback parameters, SQLite persistence, other modules can host scheduled callbacks |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### V. I Want to Contribute to ErisPulse

Make the framework better.

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / Bug / module / adapter |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

## Development Methods

ErisPulse supports two development methods:

- **Module Development (Recommended)**: Create independent module packages and install them via the package manager, which facilitates distribution and management.
- **Embedded Development**: Write processors directly within the project, suitable for rapid prototyping. See [Quick Start](quick-start.md).

## Others

- [Documentation Style Guide](styleguide/docstring.md) — Writing guidelines for contributing documentation
- [Contribute to ErisPulse](contributing/README.md) — Entry point for participating in project development
- [AI-Assisted Development](ai-support/README.md) — Project prompts for AI programming assistants

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Report Issues: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Specification](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)