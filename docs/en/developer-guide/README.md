# Developer Guide

This guide helps you develop custom modules and adapters to extend the functionality of ErisPulse.

## Table of Contents

### Module Development

1. [Getting Started with Modules](modules/getting-started.md) - Create your first module
2. [Module Core Concepts](modules/core-concepts.md) - Core concepts and architecture of modules
3. [Event Wrapper Details](modules/event-wrapper.md) - Full description of the Event object
4. [Module Best Practices](modules/best-practices.md) - Recommendations for developing high-quality modules

### Adapter Development

1. [Getting Started with Adapters](adapters/getting-started.md) - Create your first adapter
2. [Adapter Core Concepts](adapters/core-concepts.md) - Core concepts of adapters
3. [SendDSL Details](adapters/send-dsl.md) - Full description of the Send message sending DSL
4. [Event Converter](adapters/converter.md) - Implementing event converters
5. [Adapter Best Practices](adapters/best-practices.md) - Recommendations for developing high-quality adapters

### Publishing Guide

- [Publishing and Module Store Guide](publishing.md) - Publish your work to PyPI and the ErisPulse Module Store

## Prerequisites

Before starting development, ensure that you:

1. Have read [Basic Concepts](../getting-started/basic-concepts.md)
2. Are familiar with [Event Handling](../getting-started/event-handling.md)
3. Installed the development environment (Python >= 3.10)
4. Installed the ErisPulse SDK

## Choosing a Development Type

Choose the appropriate development type based on your needs:

### Module Development

**Use Cases:**
- Extending bot functionality
- Implementing specific business logic
- Providing commands and message handling

**Examples:**
- Weather query bot
- Music player
- Data collection tool

**Getting Started Guide:** [Getting Started with Modules](modules/getting-started.md)

### Adapter Development

**Use Cases:**
- Connecting to new messaging platforms
- Implementing cross-platform communication
- Providing platform-specific features

**Examples:**
- Discord adapter
- Slack adapter
- Custom platform adapter

**Getting Started Guide:** [Getting Started with Adapters](adapters/getting-started.md)

## Development Tools

### Project Templates

ErisPulse provides example projects for reference:

- `examples/example-module/` - Module example
- `examples/example-adapter/` - Adapter example

### Development Mode

Use hot reload mode for development:

```bash
epsdk run main.py --reload
```

### Debugging Tips

Enable DEBUG level logging:

```toml
[ErisPulse.logger]
level = "DEBUG"
```

Use the module's own logger:

```python
from ErisPulse import sdk

logger = sdk.logger.get_child("MyModule")
logger.debug("Debug info")
```

## Publishing Your Module

For the complete publishing process, refer to [Publishing and Module Store Guide](publishing.md), including:

- PyPI publishing steps
- ErisPulse Module Store submission process
- Publishing adapters

### Quick Reference

```bash
# Build and publish to PyPI
python -m build
python -m twine upload dist/*
```

Then go to [ErisPulse-ModuleRepo](https://github.com/ErisPulse/ErisPulse-ModuleRepo/issues/new?template=module_submission.md) to submit to the module store.

## Related Documentation

- [Standards](../standards/) - Technical standards to ensure compatibility
- [Platform Guide](../platform-guide/) - Learn about the features of various platform adapters