# ErisPulse Documentation

ErisPulse is a scalable, multi-platform message processing framework that supports interaction with various platforms through adapters, providing a flexible module system for feature extension.

> Encounter unfamiliar terms? Check the [Glossary](terminology.md) for clear explanations.

## Document Navigation

### Quick Start

- [Quick Start Guide](docs/en/quick-start.md) - A beginner's guide to installing and running ErisPulse

### Architecture Overview

- [Architecture Overview](docs/en/architecture.md) - Understand the SDK's core architecture, initialization process, event handling, and lifecycle through visual diagrams

### Getting Started

If you're new to ErisPulse, we recommend reading the following in order:

1. [Getting Started Overview](getting-started/README.md)
2. [Create Your First Bot](getting-started/first-bot.md)
3. [Basic Concepts](getting-started/basic-concepts.md)
4. [Event Handling Introduction](getting-started/event-handling.md)
5. [Common Task Examples](getting-started/common-tasks.md)

### User Guide

- [Installation and Configuration](user-guide/installation.md)
- [CLI Command Reference](user-guide/cli-reference.md)
- [Configuration File Guide](user-guide/configuration.md)
- [Deployment Guide](user-guide/deployment.md)

### Developer Guide

#### Module Development

- [Module Development Introduction](developer-guide/modules/getting-started.md)
- [Core Module Concepts](developer-guide/modules/core-concepts.md)
- [Event Wrapper Class Guide](developer-guide/modules/event-wrapper.md)
- [Module Development Best Practices](developer-guide/modules/best-practices.md)

#### Adapter Development

- [Adapter Development Introduction](developer-guide/adapters/getting-started.md)
- [Core Adapter Concepts](developer-guide/adapters/core-concepts.md)
- [SendDSL Guide](developer-guide/adapters/send-dsl.md)
- [Adapter Development Best Practices](developer-guide/adapters/best-practices.md)

#### Publishing

- [Publishing and Module Store Guide](developer-guide/publishing.md) - Publish modules and adapters to the ErisPulse Module Store

### Platform Feature Guides

- [Platform Feature Guide](platform-guide/README.md)
- [Yunhu Platform Features](platform-guide/yunhu.md)
- [Telegram Platform Features](platform-guide/telegram.md)
- [OneBot11 Platform Features](platform-guide/onebot11.md)
- [OneBot12 Platform Features](platform-guide/onebot12.md)
- [Email Platform Features](platform-guide/email.md)

### API Reference

- [Core Module API](api-reference/core-modules.md)
- [Event System API](api-reference/event-system.md)
- [Adapter System API](api-reference/adapter-system.md)

### Technical Standards

- [Event Conversion Standard](standards/event-conversion.md)
- [API Response Standard](standards/api-response.md)
- [Send Method Specification](standards/send-method-spec.md)

### Advanced Topics

- [Startup Process and Manual Control](advanced/startup.md) - Breakdown of startup chain and manual full startup
- [Lazy Loading System](advanced/lazy-loading.md)
- [Lifecycle Management](advanced/lifecycle.md)
- [Routing System](advanced/router.md)
- [MessageBuilder Guide](advanced/message-builder.md)
- [Session Type System](advanced/session-types.md)
- [Conversation Multi-turn Dialogue](advanced/conversation.md)

### AI-Assisted Development

- [AI-Assisted Development](ai-support/README.md)

### Style Guide

- [Documentation Style Guide](styleguide/docstring.md)

## Development Methods

ErisPulse supports two development approaches:

### 1. Module Development (Recommended)

Create a standalone module package and install it using a package manager. This approach is suitable for distributing and managing features, especially for publicly released functionalities.

### 2. Embedded Development

Directly embed ErisPulse code into your project without creating a separate module. This approach is suitable for rapid prototyping or internal project-specific features.

Example:

```python
# Direct embedding usage
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

# Register command handler
@command("hello")
async def hello_handler(event):
    await event.reply("Hello!")

# Run SDK and keep it running | Must be executed in an asynchronous environment
asyncio.run(sdk.run(keep_running=True))
```

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Reporting: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)