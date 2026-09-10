# ErisPulse Documentation

ErisPulse is an extensible, multi-platform message processing framework that supports interaction with various platforms through adapters, providing a flexible module system for functional extension.

> **First time using?** Just check out the [5-Minute Quick Start](docs/en/quick-start.md) —— from installation to running your first bot, all in one go.

---

## Choose Your Path

Based on your goals, select the learning path that best suits you. Each path is arranged in order from beginner to advanced.

### 1. I Want to Use a Robot

Get a robot up and running, install modules, and configure settings.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [Quick Start in 5 Minutes](docs/en/quick-start.md) | Installation, initialization, and execution — the only entry point to get started |
| Direct App Installation | [ErisPulse-App Client](ecosystem/app.md) | Official cross-platform client: run and manage directly via mobile or desktop GUI, no terminal required |
| ② In-Depth | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences among platforms (Yunhu/QQ/Telegram…) |

### 2. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Beginner | Advanced |
|------|----------|----------|
| **Module Development** (Recommended) | [Module Development Getting Started](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper Classes](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Explained](developer-guide/adapters/send-dsl.md) · [Event Transformers](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Adapter development must follow [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) specifications |
| **Publishing** | [Publishing and Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### 3. I Want to Deeply Understand the Principles

Understand how the framework works internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle, module loading strategies (including `activate_on` event-driven lazy activation), local plugin folder and module hot-reload architecture (supports all module sources) |
| [Startup Process and Manual Control](advanced/startup.md) | Breakdown of the startup chain, manual control of each step, diagnosis of loading failures |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](advanced/lifecycle.md) · [Lazy Loading](advanced/lazy-loading.md) · [Routing System](advanced/router.md) | Internal subsystems |
| [Scope (作用域)](advanced/scope.md) | Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level granular rules, binding inheritance merge) |
| [Ownership (归属权) System](advanced/ownership.md) | Resource ownership and automatic recycling: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Interactive Session System](advanced/interaction.md) | Full explanation of wait_reply, session timers (remind/escalate), multi-path waiting (select), session mutual exclusivity leases, inbox, message transactions, and trace links |
| [Inter-Module Communication](advanced/module-communication.md) | RPC protocol (module.call), meta.services service contracts and directories, targeted event emit(to=), cold start replay, event idempotency deduplication |
| [Conversation Multi-turn Dialogue](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL Builder](advanced/sql-builder.md) · [Storage Backends](advanced/storage-backends.md) · [HTTP Client](advanced/http-client.md) · [Internationalization](advanced/i18n.md) | Advanced tools |

### 4. Ecosystem and Official Clients

Official clients + ecosystem modules that can be installed on-demand and used immediately (none of these are built-in features of the framework).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, why these are not built-in features |
| [ErisPulse-App](ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray icon |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### 5. I Want to Contribute to ErisPulse

Make the framework better.

| Document | Description |
|----------|-------------|
| [Contributing to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bugs / modules / adapters |
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