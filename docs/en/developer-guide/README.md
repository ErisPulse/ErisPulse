# Developer Guide

This guide helps you develop custom modules and adapters to extend the functionality of ErisPulse.

## Table of Contents

### Module Development

1. [Getting Started with Module Development](modules/getting-started.md) - Create your first module
2. [Core Concepts of Modules](modules/core-concepts.md) - Core concepts and architecture of modules
3. [Event Wrapper Class Detailed Explanation](modules/event-wrapper.md) - Complete explanation of the Event object
4. [Best Practices for Module Development](modules/best-practices.md) - Recommendations for developing high-quality modules

### Adapter Development

1. [Getting Started with Adapter Development](adapters/getting-started.md) - Create your first adapter
2. [Core Concepts of Adapters](adapters/core-concepts.md) - Core concepts of adapters
3. [Detailed Explanation of SendDSL](adapters/send-dsl.md) - Complete explanation of the Send message sending DSL
4. [Event Converters](adapters/converter.md) - Implement event converters
5. [Best Practices for Adapter Development](adapters/best-practices.md) - Recommendations for developing high-quality adapters

### Publishing Guide

- [Publishing and Module Store Guide](publishing.md) - Publish your work to PyPI and the ErisPulse module store

## Development Preparation

Before starting development, ensure that you:

1. Read the [Basic Concepts](../getting-started/basic-concepts.md)
2. Familiarize yourself with [Event Handling](../getting-started/event-handling.md)
3. Install the development environment (Python >= 3.10)
4. Install the ErisPulse SDK

## Choosing a Development Type

Choose the appropriate development type based on your needs:

| Development Type | Use Case | Getting Started Guide |
|------------------|----------|-----------------------|
| **Module Development** | Extend robot functionality, implement business logic, provide commands and message handling | [Getting Started with Module Development](modules/getting-started.md) |
| **Adapter Development** | Connect to new messaging platforms, implement cross-platform communication, provide platform-specific features | [Getting Started with Adapter Development](adapters/getting-started.md) |

> If you want to extend the robot's functionality (such as adding commands or handling messages), choose **Module Development**. If you need to connect the robot to a new platform, choose **Adapter Development**.

## Development Tools

### Project Templates

ErisPulse provides example projects as references:

- [Module Example](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-module) - Complete project structure for modules
- [Adapter Example](https://github.com/ErisPulse/ErisPulse/tree/main/examples/example-adapter) - Complete project structure for adapters

### Development Mode

Use the hot-reload mode for development, where code changes automatically reload:

```bash
epsdk run main.py --reload
```

### Debugging Tips

Enable DEBUG or TRACE level logging in `config/config.toml`:

```toml
[ErisPulse.logger]
# DEBUG: Outputs development and debugging information such as module loading and route registration
# TRACE: The lowest level, outputs detailed internal framework processes such as event dispatching, storage writing, and lazy loading
level = "DEBUG"
```

## Publishing Your Module

For the complete publishing process, refer to the [Publishing and Module Store Guide](publishing.md), which includes PyPI publishing steps and the ErisPulse module store submission process.

## Related Documentation

- [Standards](../standards/) - Technical standards to ensure compatibility
- [Platform Features Guide](../platform-guide/) - Learn about the features of each platform adapter