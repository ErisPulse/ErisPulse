# ErisPulse Documentation

ErisPulse is an extensible, multi-platform message processing framework that supports interaction with various platforms through adapters, providing a flexible module system for functional extension.

> **First time using?** Just check out the [5-Minute Quick Start](docs/en/quick-start.md) —— from installation to running your first bot, all in one go.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is arranged from basic to advanced.

### 1. I want to use a bot

Get the bot running, install modules, and configure settings.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](quick-start.md) | Installation, initialization, and running — the only entry point for beginners |
| App Direct Install | [ErisPulse-App Client](ecosystem/app.md) | Official cross-platform client: run and manage directly via graphical interface on mobile / computer, no terminal required |
| ② In-depth | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences among platforms (Yunhu/QQ/Telegram…) |

### 2. I want to develop modules / adapters

Develop distributable extensions for ErisPulse.

| Type | Beginner | Advanced |
|------|----------|----------|
| **Module Development** (Recommended) | [Module Development Getting Started](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Explained](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standard Overview](standards/README.md) | Adapters must follow the [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Method](standards/send-method-spec.md) · [API Response](standards/api-response.md) · [Request Action](standards/request-action-spec.md) specifications |
| **Publishing** | [Publishing and Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### 3. I want to deeply understand the principles

Understand how the framework operates internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagram: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and module hot-reload architecture (supports all module sources) |
| [Startup Process and Manual Control](advanced/startup.md) | Breakdown of startup chain, manual control of each step, diagnosis of loading failures |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](advanced/lifecycle.md) · [Lazy Loading](advanced/lazy-loading.md) · [Routing System](advanced/router.md) | Internal subsystems |
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event admission / outbound action restrictions (including method-level fine-grained rules, binding inheritance merge) |
| [Ownership (owner) System](advanced/ownership.md) | Resource ownership and automatic cleanup: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Conversation Multi-turn Dialogue](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL Builder](advanced/sql-builder.md) · [HTTP Client](advanced/http-client.md) · [Internationalization](advanced/i18n.md) | Advanced tools |

### 4. Ecosystem & Official Clients

Official clients + ecosystem modules that can be installed as needed (not built-in features of the framework).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, and why these are not built-in features |
| [ErisPulse-App](ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray icon |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### 5. I want to contribute to ErisPulse

Make the framework better.

| Document | Description |
|----------|-------------|
| [Contributing to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bug fixes / modules / adapters |
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