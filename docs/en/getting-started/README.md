# Getting Started Guide

> This guide is a **detailed supplement** to the [5-Minute Quick Start](../quick-start.md). If you haven't yet started your first robot, please complete the quick start first.

After your robot is up and running, this guide will help you systematically understand the core concepts and common capabilities of the framework.

## Learning Path

We recommend reading in the following order:

| Step | Topic | Description |
|------|-------|-------------|
| 1 | [Create Your First Bot](first-bot.md) | Write command handlers and understand the execution mechanism |
| 2 | [Basic Concepts](basic-concepts.md) | Understand the core architecture and module design of ErisPulse |
| 3 | [Event Handling Introduction](event-handling.md) | Learn how to handle various types of events such as messages, commands, notifications, etc. |
| 4 | [Common Task Examples](common-tasks.md) | Master commonly used features like data persistence, scheduled tasks, and permission control |
| 5 | [IDE Completion Guide](ide-completion.md) | Generate type stubs to enable IDE auto-completion for platform-specific methods |

## Development Approach Selection

ErisPulse supports two development approaches:

| Approach | Use Case | Description |
|----------|----------|-------------|
| **Embedded Development** | Rapid prototyping, internal project features | Write handlers directly in `main.py`, no need to create a separate module |
| **Module Development** (Recommended) | Production environments, feature distribution | Create a separate Python package and install it using `epsdk install` |

> For a detailed comparison and examples of both approaches, refer to [Create Your First Bot](first-bot.md) and [Module Development Introduction](../developer-guide/modules/getting-started.md).

## Architecture Overview

ErisPulse adopts an event-driven architecture, with the core composed of the following systems:

- **Adapter System** — Communicates with various platforms, converting platform events into a unified OneBot12 standard format
- **Event System** — Handles five major types of events: messages, commands, notifications, requests, and meta-events
- **Module System** — Extends functionality through independent modules, supporting dependency management and lazy loading
- **Core Modules** — Provide foundational capabilities such as Storage (storage), Config (configuration), Logger (logging), and Router (routing)

> For a detailed architecture diagram and initialization process, see [Architecture Overview](../architecture.md).

## Start Learning

Ready to begin?

- [Create Your First Bot](first-bot.md) — Get started in 5 minutes