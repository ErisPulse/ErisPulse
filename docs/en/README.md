# ErisPulse Documentation

ErisPulse is an extensible, multi-platform messaging processing framework that supports interaction with different platforms through adapters and provides a flexible module system for feature expansion.

> Confused by some terms? Check out the [Glossary](terminology.md) for accessible explanations.

## Documentation Navigation

### Quick Start

- [Quick Start Guide](quick-start.md) - An introductory guide for installing and running ErisPulse

### Getting Started

If this is your first time using ErisPulse, we recommend reading the following in order:

1. [Getting Started Overview](getting-started/README.md)
2. [Create Your First Bot](getting-started/first-bot.md)
3. [Basic Concepts](getting-started/basic-concepts.md)
4. [Introduction to Event Handling](getting-started/event-handling.md)
5. [Common Task Examples](getting-started/common-tasks.md)

### User Guide

- [Installation and Configuration](user-guide/installation.md)
- [CLI Command Reference](user-guide/cli-reference.md)
- [Configuration File Guide](user-guide/configuration.md)

### Developer Guide

#### Module Development

- [Module Development Introduction](developer-guide/modules/getting-started.md)
- [Module Core Concepts](developer-guide/modules/core-concepts.md)
- [Event Wrapper Class Detailed Explanation](developer-guide/modules/event-wrapper.md)
- [Module Development Best Practices](developer-guide/modules/best-practices.md)

#### Adapter Development

- [Adapter Development Introduction](developer-guide/adapters/getting-started.md)
- [Adapter Core Concepts](developer-guide/adapters/core-concepts.md)
- [SendDSL Detailed Explanation](developer-guide/adapters/send-dsl.md)
- [Adapter Development Best Practices](developer-guide/adapters/best-practices.md)

#### Extension Development

- [CLI Extension Development](developer-guide/extensions/cli-extensions.md)

### Platform Features Guide

- [Platform Features Overview](platform-guide/README.md)
- [Yunhu Platform Features](platform-guide/yunhu.md)
- [Telegram Platform Features](platform-guide/telegram.md)
- [OneBot11 Platform Features](platform-guide/onebot11.md)
- [OneBot12 Platform Features](platform-guide/onebot12.md)
- [Email Platform Features](platform-guide/email.md)

### API Reference

- [Core Modules API](api-reference/core-modules.md)
- [Event System API](api-reference/event-system.md)
- [Adapter System API](api-reference/adapter-system.md)

### Technical Standards

- [Event Conversion Standard](standards/event-conversion.md)
- [API Response Standard](standards/api-response.md)
- [Send Method Specification](standards/send-method-spec.md)

### Advanced Topics

- [Lazy Loading System](advanced/lazy-loading.md)
- [Lifecycle Management](advanced/lifecycle.md)
- [Router System](advanced/router.md)

### AI-Assisted Development

- [AI-Assisted Development](ai-support/README.md)

### Style Guide

- [Documentation Style Guide](styleguide/docstring.md)

## Development Methods

ErisPulse supports two development methods:

### 1. Module Development (Recommended)

Create independent module packages, install and use them via a package manager. This method facilitates distribution and management, suitable for publicly released features.

### 2. Embedded Development

Embed ErisPulse code directly into your project without creating a separate module. This method is suitable for rapid prototyping or internal project-specific features.

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

# Run SDK and maintain running | Must run in async environment
asyncio.run(sdk.run(keep_running=True))
```

## Getting Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Reporting: Submit an Issue
- Technical Discussions: Check Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)