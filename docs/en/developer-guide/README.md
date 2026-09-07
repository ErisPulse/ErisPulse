# Developer Guide

This guide helps you develop custom modules and adapters to extend the functionality of ErisPulse.

## Content List

### Module Development

1. [Getting Started with Module Development](modules/getting-started.md) - Create your first module
2. [Core Concepts of Modules](modules/core-concepts.md) - Core concepts and architecture of modules
3. [Event Wrapper Class Detailed Explanation](modules/event-wrapper.md) - Complete documentation of the Event object
4. [Best Practices for Module Development](modules/best-practices.md) - Recommendations for developing high-quality modules

### Adapter Development

1. [Getting Started with Adapter Development](adapters/getting-started.md) - Create your first adapter
2. [Core Concepts of Adapters](adapters/core-concepts.md) - Core concepts of adapters
3. [SendDSL Detailed Explanation](adapters/send-dsl.md) - Complete documentation of the Send message sending DSL
4. [Event Converters](adapters/converter.md) - Implementing event converters
5. [Best Practices for Adapter Development](adapters/best-practices.md) - Recommendations for developing high-quality adapters

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