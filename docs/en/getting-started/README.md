# Getting Started

Welcome to the ErisPulse Getting Started Guide. If you are new to ErisPulse, this guide will take you from zero, step by step, through the core concepts and basic usage of the framework.

## Learning Path

This guide is organized in the following order. It is recommended to read them sequentially:

| Step | Topic | Description |
|------|-------|-------------|
| 1 | [Create Your First Bot](first-bot.md) | From project initialization to running your first command |
| 2 | [Basic Concepts](basic-concepts.md) | Understand the core architecture and module design of ErisPulse |
| 3 | [Introduction to Event Handling](event-handling.md) | Learn how to handle various events such as messages, commands, notifications, etc. |
| 4 | [Common Task Examples](common-tasks.md) | Master commonly used features such as data persistence, scheduled tasks, and permission control |
| 5 | [IDE Completion Guide](ide-completion.md) | Generate type stubs to enable IDE auto-completion for platform-specific methods |

## Development Approaches

ErisPulse supports two development approaches:

| Approach | Applicable Scenarios | Description |
|----------|----------------------|-------------|
| **Embedded Development** | Rapid prototyping, internal project features | Write handlers directly in `main.py`, without creating a separate module |
| **Module Development** (Recommended) | Production environments, feature distribution | Create a separate Python package and install it using `epsdk install` |

> For a detailed comparison and examples of both approaches, please refer to [Create Your First Bot](first-bot.md) and [Introduction to Module Development](../developer-guide/modules/getting-started.md).

## Architecture Overview

ErisPulse adopts an event-driven architecture, primarily composed of the following systems:

- **Adapter System** — Communicates with various platforms, converting platform events into a unified OneBot12 standard format
- **Event System** — Handles five major types of events: messages, commands, notifications, requests, and meta-events
- **Module System** — Extends functionality through independent modules, supporting dependency management and lazy loading
- **Core Modules** — Provides basic capabilities such as Storage (storage), Config (configuration), Logger (logging), and Router (routing)

> For a detailed architecture diagram and initialization flow, please refer to [Architecture Overview](../architecture.md).

## Start Learning

Are you ready to begin?

- [Create Your First Bot](first-bot.md) — Get started in 5 minutes