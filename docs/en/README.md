# ErisPulse Documentation

ErisPulse is a scalable, multi-platform message processing framework that supports interaction with different platforms through adapters and provides a flexible module system for feature extension.

> **First time using?** Go straight to [5-minute quick start](docs/en/quick-start.md) —— from installation to running your first bot, one-stop guide.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is arranged from basic to advanced.

### I. I Want to Use a Bot

Get the bot running, install modules, and configure settings.

| Progress | Document | Description |
|------|------|------|
| **① Getting Started** | [5-minute quick start](docs/en/quick-start.md) | Installation, initialization, and running — the only starting point |
| ② In-depth | [Create Your First Bot](getting-started/first-bot.md) | Writing your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understanding the design of adapters/modules/events |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences among platforms (Yunhu/Telegram/…)|

### II. I Want to Develop Modules / Adapters

Develop distributable extensions for ErisPulse.

| Type | Beginner | Advanced |
|------|------|------|
| **Module Development** (Recommended) | [Module Development Guide](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Guide](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Detailed Explanation](developer-guide/adapters/send-dsl.md) · [Event Converters](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Standards that adapter development must follow: [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Response](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) |
| **Publishing** | [Publishing and Module Store](developer-guide/publishing.md) | Publishing your work to PyPI and the module store |

### III. I Want to Deeply Understand the Principles

Understand how the framework works internally.

| Document | Description |
|------|------|
| [Architecture Overview](architecture.md) | Visual chart: core architecture, initialization flow, event handling, lifecycle |
| [Startup Process and Manual Control](advanced/startup.md) | Breakdown of the startup chain, manual control of each step, diagnosis of loading failures |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](advanced/lifecycle.md) · [Lazy Loading](advanced/lazy-loading.md) · [Routing System](advanced/router.md) | Internal subsystems |
| [Conversation Multi-turn Dialogue](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL Builder](advanced/sql-builder.md) · [HTTP Client](advanced/http-client.md) · [Internationalization](advanced/i18n.md) | Advanced tools |

### IV. Recommended Ecosystem Modules

Third-party community modules (not built-in features of the framework) that can be installed on demand.

| Document | Description |
|------|------|
| [Ecosystem Modules Overview](ecosystem/README.md) | Learn how to install ecosystem modules and why these are not built-in features |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### V. I Want to Contribute to ErisPulse

Make the framework better.

| Document | Description |
|------|------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bug / module / adapter |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

## Development Approaches

ErisPulse supports two development approaches:

- **Module Development (Recommended)**: Create independent module packages, install via package managers, and manage them easily.
- **Embedded Development**: Write handlers directly within your project, suitable for rapid prototyping. See [Quick Start](docs/en/quick-start.md).

## Others

- [Documentation Style Guide](styleguide/docstring.md) — Writing guidelines for contributing documentation
- [Contribute to ErisPulse](contributing/README.md) — Entry point for participating in project development
- [AI-Assisted Development](ai-support/README.md) — Access project prompts for AI programming assistants

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Reporting: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)