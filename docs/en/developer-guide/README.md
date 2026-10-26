# Developer Guide

> [!TIP]
> **When to read this**: When you're ready to develop extensions for ErisPulse—adding features (modules) to the bot or integrating with new platforms (adapters). If you just want to use the bot, skip this and go directly to the [Quick Start](../quick-start.md).

Here you'll find your development path: **Module Development** allows you to extend the bot's functionality using commands and message processors; **Adapter Development** enables the bot to connect to new messaging platforms. Both paths cover the full workflow from project creation to testing and deployment.

## Table of Contents

### Module Development

1. [Getting Started with Module Development](modules/getting-started.md) - Create your first module
2. [Module Core Concepts](modules/core-concepts.md) - Core concepts and architecture of modules
3. [Event Wrapper Class in Detail](modules/event-wrapper.md) - A complete description of the Event object
4. [Module Best Practices](modules/best-practices.md) - Recommendations for developing high-quality modules
5. [Data Model Layer (ORM)](orm.md) - Advanced module development: declarative models, automatic table creation, and CRUD operations

### Adapter Development

1. [Getting Started with Adapter Development](adapters/getting-started.md) - Create your first adapter
2. [Adapter Core Concepts](adapters/core-concepts.md) - Core concepts of adapters (including two ways to write start() and the PollingAdapter / WebhookAdapter connection pattern base classes)
3. [SendDSL in Detail](adapters/send-dsl.md) - A complete description of the Send message DSL
4. [Event Converter](adapters/converter.md) - Implementing event converters
5. [Adapter Best Practices](adapters/best-practices.md) - Recommendations for developing high-quality adapters

### Testing and Troubleshooting

1. [Module Testing (ErisPulse-Testing)](testing.md) - TestBot, event factories, and the assertion interface

### Publishing Guide

- [Publishing and Module Store Guide](publishing.md) - Publish your work to PyPI and the ErisPulse module store

## Development Preparation

Before starting development, please ensure that you:

1. Read [Basic Concepts](../getting-started/basic-concepts.md)
2. Familiarized yourself with [Event Handling](../getting-started/event-handling.md)
3. Installed the development environment (Python >= 3.10)
4. Installed the ErisPulse SDK

## Development Type Selection

Choose the appropriate development type based on your needs:

| Development Type | Use Case | Getting Started |
|------------------|----------|-----------------|
| **Module Development** | Extend bot functionality, implement business logic, provide commands and message handling | [Getting Started with Module Development](modules/getting-started.md) |
| **Adapter Development** | Connect to new messaging platforms, enable cross-platform communication, provide platform-specific features | [Getting Started with Adapter Development](adapters/getting-started.md) |

> If you want to extend the bot's functionality (such as adding commands or handling messages), choose **module development**. If you need to connect the bot to a new platform, choose **adapter development**.

## Development Tools

### Project Templates

ErisPulse provides example projects as references:

- [Module Example](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - The complete project structure for a module
- [Adapter Example](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - The complete project structure for an adapter

### Development Mode

Use hot-reload mode for development, where code changes automatically trigger reloads:

```bash
epsdk run main.py --reload
```

### Debugging Tips

Enable DEBUG or TRACE level logging in `config/config.toml`:

```toml
[ErisPulse.logger]
# DEBUG: Outputs development and debugging information such as module loading and route registration
# TRACE: The lowest level, outputs detailed framework internal processes such as event dispatching, storage writes, and lazy loading
level = "DEBUG"
```

## Publish Your Module

For the complete publishing process, please refer to the [Publishing and Module Store Guide](publishing.md), which includes PyPI publishing steps and the ErisPulse module store submission process.

## Related Documentation

- [Standards](../standards/) - Technical standards to ensure compatibility
- [Platform Features Guide](../platform-guide/) - Learn about the features of each platform adapter