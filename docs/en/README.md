# ErisPulse Documentation

ErisPulse is an extensible, multi-platform message processing framework that supports interaction with various platforms through adapters, providing a flexible module system for functional extension.

> **First time using?** Just check out the [5-Minute Quick Start](docs/en/quick-start.md) —— from installation to running your first bot, all in one go.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is arranged from basic to advanced.

### I. I Want to Use a Bot

Get your bot up and running, install modules, and configure settings.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](quick-start.md) | Install, initialize, and run — the only entry point to get started |
| App Direct Install | [ErisPulse-App Client](ecosystem/app.md) | Official cross-platform client: run and manage directly via mobile/PC graphical interface, no terminal required |
| ② In-Depth | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Feature Guide](platform-guide/README.md) | Differences across platforms (Yunhu/QQ/Telegram…) |

### II. I Want to Develop Modules / Adapters

Develop distributable extensions for ErisPulse.

| Type | Beginner | Advanced |
|------|----------|----------|
| **Module Development** (Recommended) | [Module Development Getting Started](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Explained](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Adapter development must follow these standards: [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Method Spec](standards/send-method-spec.md) · [API Response](standards/api-response.md) · [Request Action Spec](standards/request-action-spec.md) |
| **Publishing** | [Publishing and Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### III. I Want to Deeply Understand the Principles

Understand how the framework operates internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and module hot-reload architecture (supports all module sources) |
| [Startup Process and Manual Control](advanced/startup.md) | Breakdown of startup chain, manual control of each step, diagnosis of loading failures |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](advanced/lifecycle.md) · [Lazy Loading](advanced/lazy-loading.md) · [Routing System](advanced/router.md) | Internal subsystems |
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level granular rules, binding inheritance merge) |
| [Ownership (owner) System](advanced/ownership.md) | Resource ownership and automatic recycling: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Interactive Session System](advanced/interaction.md) | Full explanation of wait_reply, session timers (remind/escalate), multi-path waiting (select), session mutual exclusive leases, inbox, message transactions, link tracing |
| [Inter-Module Communication](advanced/module-communication.md) | RPC protocol (module.call), meta.services service contracts and directory, targeted event emit(to=), cold start replay, event idempotency deduplication |
| [Conversation Multi-turn Dialogue](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL Builder](advanced/sql-builder.md) · [Storage Backends](advanced/storage-backends.md) · [HTTP Client](advanced/http-client.md) · [Internationalization](advanced/i18n.md) | Advanced tools |

### IV. Ecosystem and Official Clients

Official clients + ecosystem modules that can be installed on demand (not built-in features of the framework).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, and why these are not built-in features |
| [ErisPulse-App](ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray icon |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages in the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-time / interval / Cron expressions, callback parameters, SQLite persistence, other modules can host scheduled callbacks |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### V. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bug fixes / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a pull request |

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