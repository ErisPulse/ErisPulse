# Getting Started Guide

Welcome to the ErisPulse Getting Started Guide. If you are using ErisPulse for the first time, this guide will take you from scratch to gradually understand the core concepts and basic usage of the framework.

## Learning Path

This guide is organized in the following order, and is recommended to be read sequentially:

1. **Create Your First Bot** - Understand the complete project initialization workflow
2. **Core Concepts** - Understand the core architecture of ErisPulse
3. **Introduction to Event Handling** - Learn how to handle various types of events
4. **Common Task Examples** - Master the implementation of common features

## Choosing a Development Approach

ErisPulse supports two development approaches; you can choose based on your needs:

### Embedded Development (Suitable for Fast Prototyping)

Use ErisPulse directly within a project without creating separate modules.

```python
# main.py
import asyncio
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello")
async def hello(event):
    await event.reply("你好！")

# Run the SDK and keep it running | Needs to run in an async environment
asyncio.run(sdk.run(keep_running=True))
```

**Pros:**
- Quick to get started, no extra configuration needed
- Suitable for internal project-specific features
- Convenient for debugging and testing

**Cons:**
- Not convenient for code reuse and distribution
- Difficult to manage dependencies independently

### Modular Development (Recommended for Production)

Create independent module packages and install and use them via package managers.

**Pros:**
- Easy to distribute and share
- Independent dependency management
- Clear version control

**Cons:**
- Requires additional project structure
- Initial configuration is relatively complex

## ErisPulse Core Concepts

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                ErisPulse 框架                 │
├─────────────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌──────────────┐    │
│  │  Adapter Sys │◄────►│  Event Sys   │    │
│  │             │      │              │    │
│  │  Yunhu      │      │  Message     │    │
│  │  Telegram   │      │  Command     │    │
│  │  OneBot11   │      │  Notice      │    │
│  │  Email      │      │  Request     │    │
│  └──────────────┘      │  Meta        │    │
│         │              └──────────────┘    │
│         ▼                   │              │
│  ┌──────────────┐           ▼              │
│  │  Module Sys  │◄──────────────┐       │
│  │             │               │       │
│  │  Module A   │               │       │
│  │  Module B   │               │       │
│  │  ...        │               │       │
│  └──────────────┘               │       │
│                               │       │
│  ┌──────────────┐              │       │
│  │  Core Modules│◄─────────────┘       │
│  │  Storage    │                      │
│  │  Config     │                      │
│  │  Logger     │                      │
│  │  Router     │                      │
│  └──────────────┘                      │
└─────────────────────────────────────────────┘
             │                    │
             ▼                    ▼
        ┌────────┐          ┌────────┐
        │  Plat  │          │  User  │
        │  API   │          │  Code  │
        └────────┘          └────────┘
```

### Core Components Explanation

#### 1. Adapter System

The adapter is responsible for communicating with specific platforms, converting platform-specific events into a unified OneBot12 standard format.

**Examples:**
- Yunhu Adapter: Communicating with the Yunhu platform
- Telegram Adapter: Communicating with the Telegram Bot API
- OneBot11 Adapter: Communicating with OneBot11-compatible applications

#### 2. Event System

The event system is responsible for handling various types of events, including:
- **Message Event**: Messages sent by the user
- **Command Event**: Commands entered by the user (e.g., `/hello`)
- **Notice Event**: System notifications (e.g., friend added, group member changes)
- **Request Event**: User requests (e.g., friend requests, group invitations)
- **Meta Event**: System-level events (e.g., connection, heartbeat)

#### 3. Module System

Modules are the primary way to extend functionality and are used to:
- Register event handlers
- Implement business logic
- Provide command interfaces
- Call adapters to send messages

#### 4. Core Modules

Modules providing basic functions:
- **Storage**: SQLite-based key-value storage
- **Config**: Configuration management in TOML format
- **Logger**: Modular logging system
- **Router**: HTTP and WebSocket routing management

## Start Learning

Are you ready? Let's start creating your first bot.

- [Create Your First Bot](first-bot.md)