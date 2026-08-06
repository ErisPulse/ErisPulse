# ErisPulse Documentation

ErisPulse is a scalable, multi-platform message processing framework that supports interaction with different platforms through adapters and provides a flexible module system for feature extension.

> **First time using?** Go straight to [Quick Start in 5 Minutes](docs/en/quick-start.md) —— From installation to running your first bot, it's all covered in one go.

---

Please directly return the complete translated Markdown content, without including any other text.

Once again, please note: If the document contains a language switch line (with language names separated by `` | ``), strictly follow the formatting requirement in point 8 above, and do not write incorrect formats such as ``[**Label**](file)``.

## Choose Your Path

Based on your goals, choose the corresponding learning path. Each path is arranged from basic to advanced.

### I. I Want to Use Robots

Get the robot running, install modules, and make configurations.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](docs/en/quick-start.md) | Installation, initialization, and running — the only entry point to get started |
| ② In-depth | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Refer as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences among platforms (Yunhu/QQ/Telegram…) |

### II. I Want to Develop Modules / Adapters

Develop distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|-----------------|----------|
| **Module Development** (Recommended) | [Module Development Getting Started](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Detailed Explanation](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standard Overview](standards/README.md) | Adapters must follow standards for [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Sending Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) |
| **Publishing** | [Publishing and Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### III. I Want to Deeply Understand the Principles

Understand how the framework operates internally.

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization process, event handling, lifecycle |
| [Startup Process and Manual Control](advanced/startup.md) | Breakdown of startup flow, manual control of each step, diagnosis of loading failures |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, start/stop, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |
| [Lifecycle Management](advanced/lifecycle.md) · [Lazy Loading](advanced/lazy-loading.md) · [Routing System](advanced/router.md) | Internal subsystems |
| [Conversation Multi-turn Dialogue](advanced/conversation.md) · [MessageBuilder](advanced/message-builder.md) · [SQL Builder](advanced/sql-builder.md) · [HTTP Client](advanced/http-client.md) · [Internationalization](advanced/i18n.md) | Advanced tools |

### IV. Recommended Ecosystem Modules

Third-party community modules (not built-in features of the framework) that can be installed on demand and used immediately.

| Document | Description |
|----------|-------------|
| [Ecosystem Modules Overview](ecosystem/README.md) | Learn how to install ecosystem modules and why these are not built-in features |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, with built-in Chinese and English fonts) |

### V. I Want to Contribute to ErisPulse

Make the framework better.

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bugs / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

## Development Methods

ErisPulse supports two development methods:

- **Module Development (Recommended)**: Create independent module packages and install them through a package manager, which facilitates distribution and management.
- **Embedded Development**: Write processors directly within the project, suitable for rapid prototyping. See [Quick Start](docs/en/quick-start.md).

Please directly return the complete translated Markdown content without any additional text.

Once again, please note: If the document contains a language switch line (with each language name separated by `` | ``), strictly adhere to the above rule #8 and do not write incorrect formats such as ``[**Label**](file)``.

## Others

- [Documentation Style Guide](styleguide/docstring.md) — Writing guidelines for contributing documentation
- [Contribute to ErisPulse](contributing/README.md) — Entry point to participate in project development
- [AI-Assisted Development](ai-support/README.md) — Project prompts for AI programming assistants

Please directly return the translated complete Markdown content, without any other text.

Once again, if the document contains language switching lines (with language names separated by `` | ``), strictly follow the above rule #8 for formatting, and do not write incorrect formats such as ``[**Label**](file)``.

## Getting Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Reporting: Submit Issue
- Technical Discussion: View Discussions

Please directly return the translated complete Markdown content, without including any other text.

## Related Links

- [OneBot12 Specification](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)