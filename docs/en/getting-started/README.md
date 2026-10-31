# Getting Started

> [!TIP]
> **When to read this**: The robot has already been started using [5-Minute Quick Start](../quick-start.md), and you want to systematically understand the framework's core concepts and learn all the commonly used capabilities. If you haven't started yet, complete the quick start first; if you just want to look up a specific issue, go directly to the corresponding article.

After the robot is up and running, here we will guide you to systematically understand the framework's core concepts and commonly used capabilities.

## Learning Path

The following is the **L1 Core Five** defined on the documentation homepage — reading them in order (about 1–2 hours) will allow you to independently develop 90% of the features:

| Step | Topic | Description |
|------|-------|-------------|
| 1 | [Getting Started with Module Development](../developer-guide/modules/getting-started.md) | Create a standalone module package, understand module structure and registration mechanism |
| 2 | [Basic Concepts](basic-concepts.md) | Understand the core architecture of ErisPulse and module design |
| 3 | [Event Wrapper Class](../developer-guide/modules/event-wrapper.md) | Master reply, request, and field access of event objects |
| 4 | [Configuration File Guide](../user-guide/configuration.md) | Learn to fill in configurations, understand hot updates, and environment variable overrides |
| 5 | [Exception Handling](../advanced/errors.md) | Recognize the exception hierarchy of the framework and write robust handling chains |

There are also several **optional reference documents** in this directory:

| Document | When to Read |
|----------|--------------|
| [Create Your First Bot](first-bot.md) | If you want to start by writing an embedded processor before learning modular development |
| [Event Handling Guide](event-handling.md) | If you need to quickly check how to handle different event types (message / command / notification / request) |
| [Common Task Examples](common-tasks.md) | If you want to copy ready-to-use complete code for tasks such as storage, scheduled tasks, and permission control |
| [IDE Completion Guide](ide-completion.md) | If you want IDE auto-completion support for platform-specific methods |

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

## Next Steps

Follow the learning path above (L1 Core Five) in order. You can also jump directly based on your objectives:

- **Want to get started hands-on**: Begin with [Create Your First Bot](first-bot.md) to write your first `/hello` command handler, then proceed to [Module Development Introduction](../developer-guide/modules/getting-started.md).
- **Want to understand the principles first**: Read [Basic Concepts](basic-concepts.md) to understand how adapters / modules / events collaborate.
- **Want to solve specific problems**: Check [Common Task Examples](common-tasks.md), which include complete, copy-paste-ready code for storage, scheduled tasks, and permission control.
- **After completing the L1 Core Five articles**: For advanced topics, consult [Advanced Topics](../advanced/README.md) as needed. When developing complex modules, start with the four essential L2 articles there.