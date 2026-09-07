# Getting Started

> This guide is a **detailed supplement** to the [5-Minute Quick Start](../quick-start.md). If you haven't yet run your first robot, please complete the quick start first.

After your robot is up and running, this guide will help you systematically understand the framework's core concepts and common capabilities.

## Learning Path

It is recommended to read in the following order:

| Step | Topic | Description |
|------|-------|-------------|
| 1 | [Create Your First Bot](first-bot.md) | Write a command handler and understand the runtime mechanism |
| 2 | [Basic Concepts](basic-concepts.md) | Understand the core architecture and module design of ErisPulse |
| 3 | [Event Handling Introduction](event-handling.md) | Learn how to handle various events such as messages, commands, and notifications |
| 4 | [Common Task Examples](common-tasks.md) | Master commonly used features such as data persistence, scheduled tasks, and permission control |
| 5 | [IDE Completion Guide](ide-completion.md) | Generate type stubs to enable IDE auto-completion for platform-specific methods |

## Development Approach Selection

ErisPulse supports two development approaches:

| Approach | Use Case | Description |
|----------|----------|-------------|
| **Embedded Development** | Rapid prototyping, internal project features | Write processors directly in `main.py` without creating a separate module |
| **Module Development** (Recommended) | Production environment, feature distribution | Create a standalone Python package and install it using `epsdk install` for use |

> For a detailed comparison and examples of both approaches, please refer to [Create Your First Bot](first-bot.md) and [Getting Started with Module Development](../developer-guide/modules/getting-started.md).

## Architecture Overview

ErisPulse adopts an event-driven architecture, and its core consists of the following systems:

- **Adapter System** — Communicates with various platforms, converting platform events into the unified OneBot12 standard format
- **Event System** — Handles five types of events: messages, commands, notifications, requests, and meta-events
- **Module System** — Extends functionality through independent modules, supporting dependency management and lazy loading
- **Core Modules** — Provide foundational capabilities such as Storage (storage), Config (configuration), Logger (logging), and Router (routing)

> For a detailed architecture diagram and initialization flow, please refer to [Architecture Overview](../architecture.md).

## Getting Started

Ready to get started?

- [Create Your First Bot](first-bot.md) — 5 minutes to get started