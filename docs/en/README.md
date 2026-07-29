# ErisPulse Documentation

ErisPulse is a scalable, multi-platform message processing framework that supports interaction with different platforms through adapters, providing a flexible module system for feature extension.

> **First time here?** Go straight to [Quick Start in 5 Minutes](docs/en/quick-start.md) —— From installation to running your first bot, everything in one go.
>
> Encounter unfamiliar terms? Check out the [Glossary](docs/en/terminology.md).

---

## Choose Your Path

Based on your goals, choose the corresponding learning path. Each path is arranged from beginner to advanced.

### I. I Want to Use a Bot

Get a bot running, install modules, and configure settings.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [Quick Start in 5 Minutes](docs/en/quick-start.md) | Installation, initialization, and running — the only starting point |
| ② In-depth | [Create Your First Bot](docs/en/getting-started/first-bot.md) | Writing your first command handler |
| ③ Concepts | [Basic Concepts](docs/en/getting-started/basic-concepts.md) | Understanding the design of adapters/modules/events |
| ④ Practical Examples | [Common Task Examples](docs/en/getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](docs/en/user-guide/configuration.md) · [CLI Commands](docs/en/user-guide/cli-reference.md) · [Deployment Guide](docs/en/user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](docs/en/platform-guide/README.md) | Differences across platforms (Yunhu/QQ/Telegram…) |

### II. I Want to Develop Modules / Adapters

Develop distributable extensions for ErisPulse.

| Type | Beginner | Advanced |
|------|----------|----------|
| **Module Development** (Recommended) | [Module Development Getting Started](docs/en/developer-guide/modules/getting-started.md) | [Core Concepts](docs/en/developer-guide/modules/core-concepts.md) · [Event Wrapper](docs/en/developer-guide/modules/event-wrapper.md) · [Best Practices](docs/en/developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](docs/en/developer-guide/adapters/getting-started.md) | [Core Concepts](docs/en/developer-guide/adapters/core-concepts.md) · [SendDSL Detailed Explanation](docs/en/developer-guide/adapters/send-dsl.md) · [Event Converters](docs/en/developer-guide/adapters/converter.md) · [Best Practices](docs/en/developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](docs/en/standards/README.md) | Standards that adapter development must follow: [Session Types](docs/en/standards/session-types.md) · [Event Conversion](docs/en/standards/event-conversion.md) · [Send Method](docs/en/standards/send-method-spec.md) · [API Response](docs/en/standards/api-response.md) · [Request Action](docs/en/standards/request-action-spec.md) |
| **Publishing** | [Publishing and Module Store](docs/en/developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### III. I Want to Deeply Understand the Principles

Understand how the framework works internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](docs/en/architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle |
| [Startup Process and Manual Control](docs/en/advanced/startup.md) | Breakdown of startup chain, manual control of each step, failure diagnosis |
| [Event System](docs/en/api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](docs/en/api-reference/adapter-system.md) | Adapter registration, start/stop, API calls |
| [Core Modules](docs/en/api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](docs/en/advanced/lifecycle.md) · [Lazy Loading](docs/en/advanced/lazy-loading.md) · [Routing System](docs/en/advanced/router.md) | Internal subsystems |
| [Conversation Multi-turn Dialogue](docs/en/advanced/conversation.md) · [MessageBuilder](docs/en/advanced/message-builder.md) · [SQL Builder](docs/en/advanced/sql-builder.md) · [HTTP Client](docs/en/advanced/http-client.md) · [Internationalization](docs/en/advanced/i18n.md) | Advanced tools |
| [Dashboard Management Panel](docs/en/advanced/dashboard-view.md) | Web management interface integration |

---

## Development Approaches

ErisPulse supports two development approaches:

- **Module Development (Recommended)**: Create independent module packages, install them via package managers, making distribution and management easier.
- **Embedded Development**: Write handlers directly in your project, suitable for rapid prototyping. See [Quick Start](docs/en/quick-start.md).

## Other

- [Documentation Style Guide](docs/en/styleguide/docstring.md) — Writing guidelines for contributing documentation
- [AI-Assisted Development](docs/en/ai-support/README.md) — Get project prompts for use with AI programming assistants

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Reporting: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)