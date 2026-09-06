# ErisPulse Documentation

ErisPulse is an extensible, multi-platform message processing framework that supports interaction with various platforms through adapters, and provides a flexible module system for functional extension.

> **New to ErisPulse?** Start with the [5-Minute Quick Start](docs/en/quick-start.md) — a step-by-step guide from installation to running your first bot.

---

## Choose Your Path

Based on your goals, select the appropriate learning path. Each path is arranged from basic to advanced.

### I. I Want to Use a Bot

Get a bot running, install modules, and configure it.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](docs/en/quick-start.md) | Installation, initialization, and running — the only entry point to begin |
| App Direct Installation | [ErisPulse-App Client](docs/en/ecosystem/app.md) | Official cross-platform client: run and manage directly via mobile or desktop GUI, no terminal required |
| ② In-Depth | [Create Your First Bot](docs/en/getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](docs/en/getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical Use | [Common Task Examples](docs/en/getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](docs/en/user-guide/configuration.md) · [CLI Commands](docs/en/user-guide/cli-reference.md) · [Deployment Guide](docs/en/user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](docs/en/platform-guide/README.md) | Differences among platforms (Yunhu/Telegram/Cloud Lake/...) |

### II. I Want to Develop Modules / Adapters

Develop distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|-----------------|----------|
| **Module Development** (Recommended) | [Module Development Getting Started](docs/en/developer-guide/modules/getting-started.md) | [Core Concepts](docs/en/developer-guide/modules/core-concepts.md) · [Event Wrapper](docs/en/developer-guide/modules/event-wrapper.md) · [Best Practices](docs/en/developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](docs/en/developer-guide/adapters/getting-started.md) | [Core Concepts](docs/en/developer-guide/adapters/core-concepts.md) · [SendDSL Explained](docs/en/developer-guide/adapters/send-dsl.md) · [Event Converter](docs/en/developer-guide/adapters/converter.md) · [Best Practices](docs/en/developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](docs/en/standards/README.md) | Adapter development must follow the [Session Types](docs/en/standards/session-types.md) · [Event Conversion](docs/en/standards/event-conversion.md) · [Send Method Spec](docs/en/standards/send-method-spec.md) · [API Response](docs/en/standards/api-response.md) · [Request Action Spec](docs/en/standards/request-action-spec.md) standards |
| **Publishing** | [Publishing and Module Store](docs/en/developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### III. I Want to Deeply Understand the Principles

Understand how the framework works internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/en/architecture.md) | Visual chart: core architecture, initialization process, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and module hot-reload architecture (supports all module sources) |
| [Startup Process and Manual Control](docs/en/advanced/startup.md) | Startup chain dissection, manual control of each step, diagnosis of loading failures |
| [Event System](docs/en/api-reference/event-system.md) | Complete API for the five major event types |
| [Adapter System](docs/en/api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](docs/en/api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](docs/en/advanced/lifecycle.md) · [Lazy Loading](docs/en/advanced/lazy-loading.md) · [Routing System](docs/en/advanced/router.md) | Internal subsystems |
| [Scope](docs/en/advanced/scope.md) | Three-dimensional scope control: module availability / event admission / outbound action restrictions (including method-level granular rules, binding inheritance merge) |
| [Ownership System](docs/en/advanced/ownership.md) | Resource ownership and automatic cleanup: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Conversation Multi-turn Dialogue](docs/en/advanced/conversation.md) · [MessageBuilder](docs/en/advanced/message-builder.md) · [SQL Builder](docs/en/advanced/sql-builder.md) · [HTTP Client](docs/en/advanced/http-client.md) · [Internationalization](docs/en/advanced/i18n.md) | Advanced tools |

### IV. Ecosystem and Official Clients

Official clients + on-demand installable, plug-and-play ecosystem modules (none of which are built-in features).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](docs/en/ecosystem/README.md) | How to install ecosystem modules, why these are not built-in features |
| [ErisPulse-App](docs/en/ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray icon |
| [ErisPulse-Dashboard](docs/en/ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Takumi](docs/en/ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### V. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](docs/en/contributing/README.md) | Overview of contribution methods: documentation / i18n / bug reports / modules / adapters |
| [First Contribution](docs/en/contributing/first-contribution.md) | From fork to submitting a PR |

---

## Development Methods

ErisPulse supports two development methods:

- **Module Development (Recommended)**: Create a separate module package, install it via package manager, convenient for distribution and management.
- **Embedded Development**: Write handlers directly in the project, suitable for rapid prototyping. See [Quick Start](docs/en/quick-start.md).

## Others

- [Documentation Style Guide](docs/en/styleguide/docstring.md) — Writing guidelines for contributing documentation
- [Contribute to ErisPulse](docs/en/contributing/README.md) — Entry point for participating in project development
- [AI-Assisted Development](docs/en/ai-support/README.md) — Project prompts for AI programming assistants

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Feedback: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)