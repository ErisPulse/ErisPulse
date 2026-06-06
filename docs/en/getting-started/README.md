# Getting Started Guide

Welcome to the ErisPulse Getting Started Guide. If you are using ErisPulse for the first time, this guide will take you from scratch to gradually understand the core concepts and basic usage of the framework.

## Learning Path

This guide is organized in the following order, and is recommended to be read sequentially:

| Step | Topic | Description |
|------|-------|-------------|
| 1 | [Create Your First Bot](first-bot.md) | From project initialization to running your first command |
| 2 | [Basic Concepts](basic-concepts.md) | Understanding ErisPulse's core architecture and module design |
| 3 | [Introduction to Event Handling](event-handling.md) | Learn how to handle various event types, such as messages, commands, and notices |
| 4 | [Common Task Examples](common-tasks.md) | Master common features such as data persistence, scheduled tasks, and permission control |

## Choosing a Development Approach

ErisPulse supports two development approaches:

| Approach | Suitable Scenarios | Description |
|----------|-------------------|-------------|
| **Embedded Development** | Fast prototyping, internal project features | Write handlers directly in `main.py` without creating separate modules |
| **Module Development** (Recommended) | Production environment, feature distribution | Create independent Python packages and install and use them via `epsdk install` |

> For a detailed comparison and examples of both approaches, please refer to [Create Your First Bot](first-bot.md) and [Getting Started with Module Development](../developer-guide/modules/getting-started.md).

## Architecture Overview

ErisPulse adopts an event-driven architecture and consists of the following core systems:

- **Adapter System** — Communicating with various platforms, converting platform events into a unified OneBot12 standard format
- **Event System** — Handling five major types of events: messages, commands, notices, requests, and meta events
- **Module System** — Extending functionality through independent modules, supporting dependency management and lazy loading
- **Core Modules** — Providing basic capabilities such as Storage (storage), Config (configuration), Logger (logging), and Router (routing)

> For detailed architecture diagrams and initialization flows, please refer to [Architecture Overview](../architecture.md).

## Start Learning

Are you ready to get started?

- [Create Your First Bot](first-bot.md) — Get up and running in 5 minutes