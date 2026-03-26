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

### Extension Development

1. [CLI Extension Development](extensions/cli-extensions.md) - Developing custom CLI commands

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

### CLI Extension Development

**Use Cases:**
- Extending command-line tools
- Providing custom management commands
- Automating deployment processes

**Examples:**
- Deployment scripts
- Data migration tools
- Configuration management tools

**Getting Started Guide:** [CLI Extension Development](extensions/cli-extensions.md)

## Development Tools

### Project Templates

ErisPulse provides example projects for reference:

- `examples/example-module/` - Module example
- `examples/example-adapter/` - Adapter example
- `examples/example-cli-module/` - CLI extension example

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

### Packaging

Ensure the project contains the following files:

```
MyModule/
├── pyproject.toml
├── README.md
├── LICENSE
└── MyModule/
    ├── __init__.py
    └── Core.py
```

### pyproject.toml Configuration

```toml
[project]
name = "ErisPulse-MyModule"
version = "1.0.0"
description = "Description of module functionality"
readme = "README.md"
requires-python = ">=3.9"
license = { file = "LICENSE" }
authors = [ { name = "yourname", email = "your@mail.com" } ]

[project.urls]
"homepage" = "https://github.com/yourname/MyModule"

[project.entry-points."erispulse.module"]
"MyModule" = "MyModule:Main"
```

### Publishing to PyPI

```bash
# Build distribution packages
python -m build

# Publish to PyPI
python -m twine upload dist/*
```

## Related Documentation

- [Standards](../standards/) - Technical standards to ensure compatibility
- [Platform Guide](../platform-guide/) - Learn about the features of various platform adapters