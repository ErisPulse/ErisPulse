---
name: erispulse-getting-started
description: "适用于：第一次接触 ErisPulse，想从零跑起一个机器人并理解核心概念。覆盖场景：ErisPulse is an event-driven, modular asynchronous bot framework — write your business logic once and deploy it via adapters to multiple platforms including QQ, Telegram, Kook, and Yunhu, with a plugin system, hot reload, and a complete developer toolchain that work out of the box.。**1. Install** (Python >= 3.10):。Your bot is already running, and you want to write your first `/hello` command handler and understand what `sdk.run` and command decorators do. If you haven't installed ErisPulse, initialized a project, or run the project yet, complete the "Install", "Initialize Project", and "Run Project" steps in [5-Minute Quick Start](../quick-start.md) first; otherwise, skip this section.。What components does a message pass through from the user's message to the bot's reply? What are the responsibilities of adapters and modules? After reading this, you will be able to answer design questions that arise when writing processors yourself, rather than just copying exampl..."
---

# ErisPulse 快速上手与核心概念

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 文档总入口与阅读路径: 82-92 行
- Choose Your Path: 94-209 行
- Advanced Features Version Quick Reference: 211-221 行
- Development Approaches: 223-228 行
- Other: 230-234 行
- Getting Help: 236-240 行
- 快速开始: 242-248 行
- 60-Second Demo: Let the Bot Reply to You First: 250-289 行
- Install ErisPulse: Three Ways: 291-356 行
- Initialize Project: 358-390 行
- Installing Modules: 392-412 行
- Running the Project: 414-422 行
- Enable IDE Completion (Optional): 424-441 行
- Project Structure: 443-453 行
- Configuration File: 455-492 行
- 第一个机器人: 494-503 行
- Step 1: Write Your First Command: 505-552 行
- Step 2: Run the Robot: 554-562 行
- Step 3: Test the Bot: 564-572 行
- Code Explanation: 574-606 行
- Extensions: Adding More Features: 608-614 行
- FAQ: 616-652 行
- What's Next: 654-658 行
- 基础概念: 660-669 行
- Event-Driven Architecture: 671-709 行
- Core Components: 711-833 行
- Event Types: 835-847 行
- Core Module Descriptions: 849-951 行
- SendDSL Message Sending: 953-998 行
- Lazy Loading System: 1000-1021 行
- 事件处理: 1023-1032 行
- Overview of Event Types: 1034-1044 行
- Message Event Handling: 1046-1117 行
- Command Event Handling: 1119-1472 行
- Middleware: Rewrite or Reject Before Distribution: 1474-1496 行
- Command Dispatch Decision Chain: Why a Command Didn't Trigger: 1498-1504 行
- Scope Filtering: Why My Module Didn't Receive the Message: 1506-1534 行
- Event Overwriting: Overwrite Any Event Type Behavior Without Modifying Module Code: 1536-1594 行
- Link Control: Claiming and Blocking: 1596-1645 行
- Notice Event Handling: 1647-1679 行
- Request Event Handling: 1681-1708 行
- Meta Event Handling: 1710-1757 行
- Interactive Handling: 1759-1980 行
- Event Data Access: 1982-2057 行
- Event Handling Best Practices: 2059-2110 行
- 常见任务: 2112-2119 行
- Content List: 2121-2131 行
- Data Persistence: 2133-2190 行
- Scheduled Tasks: 2192-2260 行
- Message Filtering: 2262-2301 行
- Multi-Platform Adaptation: 2303-2344 行
- Advanced Message Sending (Retry/Timeout/Batch): 2346-2399 行
- Permission Control: 2401-2451 行
- Message Statistics: 2453-2497 行
- Search Functionality: 2499-2553 行
- Image Processing: 2555-2618 行
- What's Next: 2620-2624 行
- IDE 补全: 2626-2636 行
- Core Design Principles: 2638-2644 行
- Basic Usage: 2646-2654 行
- Using in Code: 2656-2668 行
- How It Works: 2670-2694 行
- Command Options: 2696-2703 行
- When to Regenerate: 2705-2709 行
- Relationship with SendDSL Standard Methods: 2711-2715 行

## 文档总入口与阅读路径

> 来源: `docs/en/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/README.md）

# ErisPulse Documentation

ErisPulse is an event-driven, modular asynchronous bot framework — write your business logic once and deploy it via adapters to multiple platforms including QQ, Telegram, Kook, and Yunhu, with a plugin system, hot reload, and a complete developer toolchain that work out of the box.

> **First time here?** Head straight to the [5-Minute Quick Start](quick-start.md) — from installation to running your first bot, all in one go.

---

## Choose Your Path

Based on your goal, pick the corresponding learning path. Within each path, content is ordered from beginner to advanced.

> [!IMPORTANT]
> **You don't need to read all the docs.** The vast majority of developers can independently build 90% of their features just by reading the **L1 Core Five** in order
> (about 1–2 hours); all remaining docs are on-demand references for specific scenarios —
> consult them when the need arises. Each one opens with a note on "when you need to read this".
>
> **The L1 Core Five**: [Getting Started with Module Development](developer-guide/modules/getting-started.md)
> → [Basic Concepts](getting-started/basic-concepts.md)
> → [Event Wrapper](developer-guide/modules/event-wrapper.md)
> → [Configuration File Guide](user-guide/configuration.md)
> → [Exception Handling](advanced/errors.md)
>
> Adapter authors also need: [Getting Started with Adapter Development](developer-guide/adapters/getting-started.md)
> → [Event Converter](developer-guide/adapters/converter.md)
> → [SendDSL in Depth](developer-guide/adapters/send-dsl.md)

### 1. I Want to Use a Bot

Get the bot running, install modules, and configure it.

| Progress | Document | Description |
|------|------|------|
| **① Get Started** | [5-Minute Quick Start](quick-start.md) | Install, initialize, run — the single starting point |
| Direct App Install | [ErisPulse-App Client](ecosystem/app.md) | Official all-platform client: run and manage via a graphical interface on phone / desktop, no terminal required |
| ② Go Deeper | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Hands-On | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences across platforms (Yunhu/QQ/Telegram…) |
| Selection | [Selection Guide](showcase/README.md) | Comparison with and migration from NoneBot2 / AstrBot / LangBot |

### 2. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|------|------|
| **Module Development** (recommended) | [Getting Started with Module Development](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Getting Started with Adapter Development](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL in Depth](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Specifications that adapter development must follow: [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) |
| **Testing & Troubleshooting** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Trace the dispatch decision chain to troubleshoot "why didn't my command trigger" |
| **Publishing** | [Publishing & the Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the Module Store |

### 3. I Want to Deeply Understand the Internals

Learn how the framework works under the hood. Start with the architecture and API references, then use the lookup table below to dive into specific topics.

**Architecture & API References**

| Document | Description |
|------|------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle, module loading strategies (including `activate_on` event-driven lazy activation), local plugin folders, and the module hot-reload architecture (supports all module sources) |
| [Event System](api-reference/event-system.md) | Complete APIs for the five major event categories |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, start/stop, API invocation |
| [Core Modules](api-reference/core-modules.md) | Fundamental capabilities such as Storage / Config / Logger / Router |

**L2 Must-Read (Unavoidable for Production-Grade Modules)**

| Document | Description |
|------|------|
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event admission / outbound action restrictions (including method-level fine-grained rules and binding inheritance merge) |
| [Ownership (owner) System](advanced/ownership.md) | Resource ownership and automatic reclamation: the owner context, a panoramic view of owned resources, unload cleanup sequences, design boundaries, and a guide for module authors |
| [Lifecycle Management](advanced/lifecycle.md) | The lifecycle event system: what modules / adapters should do when loaded, unloaded, reloaded, or disabled |
| [Interaction Session System](advanced/interaction.md) | A complete guide to wait_reply, session timers (remind/escalate), multi-path waiting (select), session mutex leases, inbox, message transactions, and tracing |

**Grouped by Scenario (Consult as Needed)**

| Group | Documents | Pitfalls If You Skip the First Doc |
|------|------|------|
| Startup | [Startup Flow & Manual Control](advanced/startup.md) · [Lazy Loading](advanced/lazy-loading.md) | Without understanding the startup chain (Finder / Loader / Manager / Router), you'll be left staring helplessly at logs when module loading fails |
| Communication & Connections | [Inter-Module Communication](advanced/module-communication.md) · [Connection Pool & Broadcast](advanced/connections.md) · [Router System](advanced/router.md) | Without understanding the service contract (`meta.services`) whitelist, a cross-module `module.call` will be rejected with `ServiceNotProvidedError` and you won't know why |
| Data Storage | [Storage Backends](advanced/storage-backends.md) · [SQL Builder](advanced/sql-builder.md) · [HTTP Client](advanced/http-client.md) | Without understanding the connection-failure cooldown semantics, database flakiness will make you think "the framework crashed" (in reality, storage operations fail fast and automatically reconnect after the cooldown) |
| Messaging & Conversations | [Conversation Multi-Turn Dialogs](advanced/conversation.md) · [Session Inbox](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [Internationalization](advanced/i18n.md) | Without understanding session mutex leases, two modules waiting for the same user's reply will kick each other out |
| Shadow & Canary | [Shadow Modules & Canary Promotion](advanced/shadow.md) | Promote prematurely without understanding the five isolation gates, and the shadow's outbound messages will leak to real users |

**Concept Relationship Summary Table**

When you can't tell which subsystem handles what, use this table to find the right entry:

| Subsystem | What Question It Answers | One-Line Rule of Thumb |
|--------|------------|-----------|
| [Communication](advanced/module-communication.md) (module-communication) | How do modules call each other and send targeted events? | Cross-module calls go through `module.call`; if the target declares `meta.services`, only whitelisted methods can be called |
| [Permissions](advanced/scope.md) (scope) | Who can use this module, who can trigger events, and which actions can be performed? | Three gates — module binding, identity admission, outbound restrictions — all dictated by user configuration |
| [Ownership](advanced/ownership.md) (ownership) | After a module is unloaded, what happens to the connections, timers, and subscriptions it opened? | Whoever registers owns it; unloading reclaims everything, leaving no dangling resources |
| [Lazy Loading & Dormancy](advanced/lazy-loading.md) (lazy-loading) | When does a module actually load, and where does it go when idle? | `activate_on` wakes it only when needed; `dormant_after` puts it to sleep when idle |
| [Interaction](advanced/interaction.md) (interaction) | How to wait for the user's next reply, and how to collect multiple turns? | `wait_reply` waits for one, `.got()` chains collect multiple turns, and leases guarantee no conflicts |
| [Shadow Canary](advanced/shadow.md) (shadow) | How can a new module version be trialed without affecting production? | Shadows receive copies and outbound actions are merely recorded; `promote` only goes live after human confirmation |
| [Storage](advanced/storage-backends.md) (storage-backends) | Where is data stored, and how do I switch backends? | One storage API, switch between sqlite / mysql / postgres via configuration |

### 4. Ecosystem & Official Clients

Official clients plus ecosystem modules you install on demand and use right away (none of these are built into the framework).

| Document | Description |
|------|------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules and why these aren't built-in features |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | General-purpose agent module: tool loop / MCP / long-term memory / knowledge base; modules that declare services automatically become AI tools |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | Exposes your bot in reverse as an MCP tool, letting AI clients like Claude control it directly |
| [ErisPulse-App](ecosystem/app.md) | Official all-platform client (Android / Windows / Linux / macOS): manage multiple instances via a native UI, **run directly on your phone**, tray-resident on desktop |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + pane registration API (modules can register custom pages in the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-shot / interval / cron expressions, callback arguments, SQLite persistence; other modules can delegate scheduled callbacks to it |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node trees / SVG / animations, with built-in Chinese and English fonts) |

### 5. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|------|------|
| [Contributing to ErisPulse](contributing/README.md) | Overview of ways to contribute: docs / i18n / bugs / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

## Advanced Features Version Quick Reference

When making version-compatibility decisions, or taking over an older project and wondering "which version introduced this capability," look it up in this table (the per-version entries in the repository root [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) are authoritative).

| Version | Capabilities Introduced |
|------|-----------|
| **2.7** | Production-ready foundation: OneBot12 standardized base classes (`ApiDSL` / `BaseConverter`), systematized config hot-reload, graceful shutdown with SIGTERM/SIGHUP signal handling, environment-variable config overrides, lifecycle callback hooks, lazy loading of the web stack; 2.7.1 added config-write reliability and generational GC tuning |
| **2.8** | Permission and communication skeleton: the three-dimensional scope system (scope), interaction session infrastructure (leases / checkpoints / message transactions / session inbox transcript), protocol-based inter-module RPC (`module.call` / `meta.services` service contracts / targeted events via emit(to=)), multi-backend async storage (sqlite / mysql / postgres; connection failures don't block the framework), ownership cleanup, config comment preservation; later 2.8.x releases polished the CLI scaffolding, subcommands, and more |
| **2.9** | The "Module Development Experience" mainline (EPRFC-2026-001): declarative command parameters (`args=` / `options=`) and command governance (`cooldown=` / `rate_limit=`), unified dependency injection (`Depends`), middleware event veto, built-in ORM (auto migrations + relationship mapping), shadow module canary promotion, dispatch decision chain tracing and troubleshooting diagnostics, and official Python 3.14 support |
| **2.10** | Connections as first-class resources (the `connections` registry: broadcast / business grouping / cross-module transfer & reuse / automatic reclamation on unload), the root import contract (all commonly used APIs importable via `from ErisPulse import`), completion of the ownership system, runtime overrides for inbox retention policies; 2.10.2 added adapter-local plugin directories (`plugins/`) + `epsdk create pack` + lossless config writes via tomlclass |
| **2.11** (dev) | The "edit code → see results" development loop: hot reload with full semantics by default (syntax pre-check + code identity verification + cascaded re-export for dependents), lazy-loading dormancy (`dormant_after`), code-level adapter hot reload (`sdk.adapter.reload`), `.got()` command-flow syntactic sugar, `epsdk stop` / `restart` runtime control |

## Development Approaches

ErisPulse supports two development approaches:

- **Module development (recommended)**: create a standalone module package installed via a package manager, making it easy to distribute and manage.
- **Embedded development**: write handlers directly in your project, ideal for rapid prototyping. See [Quick Start](quick-start.md) for details.

## Other

- [Documentation Style Guide](styleguide/docstring.md) — writing conventions for contributing docs
- [Contributing to ErisPulse](contributing/README.md) — the entry point for getting involved in the project
- [AI-Assisted Development](ai-support/README.md) — get project prompts for use with AI coding assistants

## Getting Help

- GitHub repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue reports: submit an Issue
- Technical discussions: check out Discussions

## 快速开始

> 来源: `docs/en/quick-start.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/quick-start.md）

# Quick Start

> **This is your first step.** Run an ErisPulse robot from scratch in 5 minutes—see the result first, then expand each step.

## 60-Second Demo: Let the Bot Reply to You First

**1. Install** (Python >= 3.10):

```bash
pip install ErisPulse
```

**2. Initialize the project.** The wizard will prompt you to set the project name, select the platform adapter to connect, and complete the configuration, then generate `main.py` and `config/config.toml`:

```bash
epsdk init
```

**3. Open `main.py`, and replace it with these 9 lines of code:**

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    await event.reply("Pong! The bot is running normally.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(sdk.run(keep_running=True))
```

**4. Run**:

```bash
epsdk run main.py
```

The terminal will output framework startup logs and adapter connection information. At this point, send `/ping` to the bot in your connected platform; it will reply:

> Pong! The bot is running normally.

Seeing this reply confirms that the framework, adapter, and event handling chain are all working. If it doesn't work, go directly to the [Troubleshooting section](#troubleshooting) at the end of the document; if it works, continue reading to see what other options are available at each step.

## Install ErisPulse: Three Ways

The above uses the most direct pip method. Choose according to your environment:

### Install with pip

Ensure your Python version is >= 3.10, then install using pip:

```bash
pip install ErisPulse
```

If you have already installed [uv](https://github.com/astral-sh/uv), you can also use `uv pip install ErisPulse` for faster installation.

When you only want to install the `epsdk` command-line tool globally without polluting the project environment, it is recommended to use `uv tool install`:

```bash
uv tool install ErisPulse
```

After installation, `epsdk` will be globally available: when running within a project directory, it will automatically detect the project's `.venv` (installing `epsdk install` into the project environment, and running `epsdk run` using the project environment), while the framework itself is provided by the tool environment. See [Installation Reference](user-guide/installation.md) for details.

### One-Click Installation Script (Recommended for New Environments)

The installation script will automatically detect your environment (Docker, Python, uv), and guide you to select the most suitable installation method, supporting multiple languages (Chinese/English/Japanese/Russian/Traditional Chinese).

Windows (PowerShell):
```powershell
irm https://get.erisdev.com/install.ps1 -OutFile install.ps1; powershell -ExecutionPolicy Bypass -File install.ps1
```

macOS / Linux:
```bash
curl -fsSL https://get.erisdev.com/install.sh -o install.sh && chmod +x install.sh && ./install.sh
```

The script will guide you through:

- **Docker Installation** (recommended if Docker is detected): Choose image source (Docker Hub / GHCR), version channel (stable / pre-release), Dashboard management panel configuration, and port settings
- **Global CLI Installation (uv tool, recommended)**: Install `epsdk` as a global command, without virtual environments; uv automatically manages Python (even if the system version is too low); when running within a project directory, it automatically detects the project's `.venv`
- **Traditional Installation**: Automatically create a virtual environment, select the ErisPulse version, and optionally install the Dashboard management panel module

### Using Docker

The Docker image comes with the ErisPulse framework and the Dashboard management panel, supporting `linux/amd64` and `linux/arm64` architectures.

```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/ErisPulse/ErisPulse/main/docker-compose.yml

# Set the Dashboard token and start
ERISPULSE_DASHBOARD_TOKEN=your-token docker compose up -d
```

<details>
<summary>Is Docker Hub unavailable?</summary>

Use the GitHub Container Registry image, and modify the `image` in `docker-compose.yml`:

```yaml
image: ghcr.io/erispulse/erispulse:latest
```

</details>

After starting, access `http://<host>:8000/Dashboard` and log in using the set token.

## Initialize Project

### Interactive Initialization (Recommended)

```bash
epsdk init
```

This will start an interactive wizard that guides you through:
- Project name setting
- Log level configuration
- Server configuration (host and port)
- Adapter selection and configuration
- Project structure creation

### Quick Initialization

```bash
# Quick mode with a specified project name
epsdk init -q -n my_bot

# Or just specify the project name
epsdk init -n my_bot
```

### Manual Project Creation

If you prefer to create the project manually:

```bash
mkdir my_bot && cd my_bot
epsdk init
```

## Installing Modules

### Installing via CLI

```bash
epsdk install Yunhu AIChat
```

### Viewing Available Modules

```bash
epsdk list-remote
```

### Interactive Installation

Without specifying a package name, enter the interactive installation interface:

```bash
epsdk install
```

## Running the Project

```bash
# Run normally
epsdk run main.py

# Hot reload mode (recommended for development)
epsdk run main.py --reload
```

## Enable IDE Completion (Optional)

ErisPulse dynamically discovers modules/adapters, and IDEs cannot complete platform-specific methods by default.  
Run the following command to generate type stubs:

```bash
epsdk types
```

After generation, use the imported types as variable annotations to obtain precise completion (see [IDE Completion Guide](./getting-started/ide-completion.md)):

```python
from _ep_types import Yunhu
from ErisPulse import sdk

adapter: Yunhu = sdk.adapter.get("yunhu")
await adapter.Send.To("group", "123").Board(...)  # Completion for platform-specific methods
```

## Project Structure

After initialization, the project structure is as follows:

```
my_bot/
├── config/
│   └── config.toml          # Configuration file
└── main.py                  # Entry file

```

## Configuration File

Basic `config.toml` configuration:

```toml
[ErisPulse.server]
host = "0.0.0.0"
port = 8000

[ErisPulse.logger]
level = "INFO"

[Yunhu_Adapter]
# Adapter configuration
```

### Want to build a group bot (handle messages, group management, notifications)

- [Event Handling Introduction](getting-started/event-handling.md) — How to write message, notification, and request events
- [Common Tasks Examples](getting-started/common-tasks.md) — Storage, scheduled tasks, permission control

### Want to write your own module / adapter

- [Basic Concepts](getting-started/basic-concepts.md) — First understand the design of adapters / modules / events
- [Module Development Introduction](developer-guide/modules/getting-started.md)
- [Adapter Development Introduction](developer-guide/adapters/getting-started.md)
- [Architecture Overview](architecture.md) — Visual architecture diagram

### Want to keep the bot running long-term

- [Deployment Guide](user-guide/deployment.md)
- [Configuration File Explanation](user-guide/configuration.md)

### Encountered problems

- [Create Your First Bot](getting-started/first-bot.md) — Step-by-step guide to creating your first bot
- [Startup Process and Manual Control](advanced/startup.md) — Diagnosing module / adapter loading failures
- [CLI Command Reference](user-guide/cli-reference.md) — All `epsdk` subcommands

## 第一个机器人

> 来源: `docs/en/getting-started/first-bot.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/getting-started/first-bot.md）

# Create Your First Bot

> [!TIP]
> **When to read this**: Your bot is already running, and you want to write your first `/hello` command handler and understand what `sdk.run` and command decorators do. If you haven't installed ErisPulse, initialized a project, or run the project yet, complete the "Install", "Initialize Project", and "Run Project" steps in [5-Minute Quick Start](../quick-start.md) first; otherwise, skip this section.

Running through the quick start is just the first step—this guide walks you through writing your first command handler and explains what each line of code does within the framework.

## Step 1: Write Your First Command

Open `main.py` and write a simple command handler:

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("hello", help="Send a greeting message")
async def hello_handler(event):
    """Handle the hello command"""
    user_name = event.get_user_nickname() or "friend"
    await event.reply(f"Hello, {user_name}! I am the ErisPulse bot.")

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    """Handle the ping command"""
    await event.reply("Pong! The bot is running normally.")

async def main():
    """Main entry function"""
    print("Starting ErisPulse...")
    
    # keep_running=True (default): The framework blocks and stays running until a shutdown signal is received (e.g., Ctrl+C)
    await sdk.run(keep_running=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### `keep_running` Parameter

`sdk.run(keep_running)` controls whether the framework blocks and remains running:

- **`keep_running=True` (default)**: `run()` will block indefinitely until a shutdown signal (e.g., Ctrl+C) is received, suitable for pure bot applications.
- **`keep_running=False`**: `run()` returns immediately after initialization. **The framework is not unloaded**—active adapters/modules continue processing message events as background tasks. You can then proceed with your own logic until the event loop ends and the framework shuts down. For example:

```python
async def main():
    await sdk.run(keep_running=False)   # Returns immediately after initialization
    # The framework is running in the background, here you can continue doing other things
    while True:
        await asyncio.sleep(3600)
        print("Check every hour")
```

> Besides the two modes of `run()`, there are also more granular ways to manually control the lifecycle, such as `init()`/`uninit()` and individually starting/stopping adapters/routes. See [Startup Process and Manual Control](../advanced/startup.md).

## Step 2: Run the Robot

```bash
# Run normally
epsdk run main.py

# Development mode (supports hot reload)
epsdk run main.py --reload
```

## Step 3: Test the Bot

Send the following command in your chat platform:

```
/hello
```

You should receive a reply from the bot.

## Code Explanation

### Command Decorator

```python
@command("hello", help="Send a greeting message")
```

- `hello`: The command name, which users invoke via `/hello`
- `help`: The help description, displayed in the `/help` command

### Event Parameters

```python
async def hello_handler(event):
```

The `event` parameter is an Event object, containing:
- Message content: `event.get_text()`
- Sender information: `event.get_user_id()`, `event.get_user_nickname()`
- Platform information: `event.get_platform()`
- Group information: `event.get_group_id()`
- Raw data: `event.get_raw()`

> For a complete list of Event object methods, refer to [Event Wrapper Class Details](../developer-guide/modules/event-wrapper.md).

### Sending a Reply

```python
await event.reply("Reply content")
```

`event.reply()` is a convenient method for sending messages back to the sender.

## Extensions: Adding More Features

ErisPulse provides rich event handling and data processing capabilities:

- **Message Listening**: Use `@message.on_message()` to listen to various types of messages → [Event Handling Introduction](event-handling.md)
- **Notification Listening**: Use `@notice.on_friend_add()` and others to listen to system notifications → [Event Handling Introduction](event-handling.md)
- **Data Storage**: Use `sdk.storage.get/set` to persist data → [Common Tasks Examples](common-tasks.md)

## FAQ

### No response from command?

1. Check if the adapter is correctly configured, and confirm that the `status` of the adapter in `config/config.toml` is set to `true`.
2. Check the terminal log output to confirm if there are any error messages (especially those with `ERROR` level).
3. Confirm that the command prefix is correct (the default is `/`), and check the `[ErisPulse.event.command]` section in the configuration file.
4. Confirm that the command name is spelled correctly, and pay attention to case sensitivity settings.

### How to change the command prefix?

Add the following to `config.toml`:

```toml
[ErisPulse.event.command]
prefix = "!"
case_sensitive = false
```

### How to support multiple platforms?

ErisPulse uses the OneBot12 standard to unify the event formats of different platforms. Handlers registered with `@command` and `@message` will automatically receive events from all platforms. You can distinguish the source platform using `event.get_platform()`:

```python
@command("hello")
async def hello_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("你好！来自云湖")
    elif platform == "telegram":
        await event.reply("Hello! From Telegram")
    else:
        await event.reply("你好！")
```

> For more multi-platform adaptation techniques, please refer to [Common Tasks Examples](common-tasks.md#multi-platform-adaptation).

## What's Next

- **Continue along the learning path**: Read [Basic Concepts](basic-concepts.md) to understand what the framework behind command handlers does.
- **Want to handle more message types**: [Event Handling Introduction](event-handling.md), how to write handlers for messages / notifications / requests / meta-events.
- **Want to add practical features**: [Common Tasks Examples](common-tasks.md), ready-to-use code for persistence, scheduled tasks, and permission control.

## 基础概念

> 来源: `docs/en/getting-started/basic-concepts.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/getting-started/basic-concepts.md）

# Core Concepts

> [!NOTE]
> **L1 Core Must-Read** — The second article in the "L1 Core Five Articles" on the documentation homepage (Module Development Introduction → **Core Concepts** → Event Wrapper → Configuration File Explanation → Exception Handling).

What components does a message pass through from the user's message to the bot's reply? What are the responsibilities of adapters and modules? After reading this, you will be able to answer design questions that arise when writing processors yourself, rather than just copying examples.

## Event-Driven Architecture

ErisPulse adopts an event-driven architecture, where all interactions are passed and handled through events.

### Event Flow

```
User sends message
      │
      ▼
Platform receives
      │
      ▼
Adapter receives native platform event
      │
      ▼
Converts to OneBot12 standard event
      │
      ▼
Submits to event system
      │
      ▼
Distributes to registered handlers
      │
      ▼
Module processes event
      │
      ▼
Sends response via adapter
      │
      ▼
Platform displays to user
```

### OneBot12 Standard

ErisPulse uses OneBot12 as the core event standard. OneBot12 is a universal chatbot application interface standard that defines a unified event format.

All adapters convert platform-specific events into OneBot12 format, ensuring code consistency.

## Core Components

### 1. SDK Object

The SDK is the unified entry point for all features, providing access to core components.

```python
from ErisPulse import sdk

# Access core modules
sdk.storage    # Storage system
sdk.config     # Configuration system
sdk.logger     # Logging system
sdk.adapter    # Adapter system
sdk.module     # Module system
sdk.router     # Router system
sdk.client     # HTTP client
sdk.lifecycle  # Lifecycle system
```

> [!WARNING]
> **Import from root** — `from ErisPulse.Core import adapter` / `import ErisPulse.Core.adapter`
> This binds to the **manager instance** (`AdapterManager` singleton), not the sub-module — `ErisPulse.Core`
> package re-exports will mask the same-named sub-modules. When writing tests, patches, or needing the module object itself, always use
> `from ErisPulse import sdk` root import (where `sdk.adapter` is the manager instance).

### 2. Event Object

The Event object encapsulates event data and provides convenient access methods.

```python
@command("info")
async def info_handler(event):
    # Get event information
    event_id = event.get_id()
    user_id = event.get_user_id()
    platform = event.get_platform()
    text = event.get_text()
    
    # Send reply
    await event.reply(f"User: {user_id}, Platform: {platform}")
```

### 3. Adapters

Adapters serve as bridges between ErisPulse and external platforms.

**Responsibilities:**
- Receive native platform events
- Convert them into OneBot12 standard format
- Send standard-format events back to the platform

**Example Adapters:**
- Yunhu Adapter: Communicates with the Yunhu platform
- Telegram Adapter: Communicates with the Telegram Bot API
- OneBot11 Adapter: Communicates with OneBot11-compatible applications
- Email Adapter: Handles email sending and receiving

### 4. Modules

Modules are the basic units of functional extension and can:

- Register event handlers
- Implement business logic
- Call adapters to send messages
- Use services provided by core modules

#### Module Discovery Mechanism

ErisPulse discovers installed modules via Python's `importlib.metadata.entry_points`. Modules declare entry points in `pyproject.toml`:

```toml
[project.entry-points."erispulse.module"]
MyModule = "my_package:Main"
```

When the SDK initializes, it scans all entry points in the `erispulse.module` group, registers the module class with `ModuleManager`, then initializes them in topological order based on dependencies.

#### Minimal Viable Module

```python
from ErisPulse.Core.Bases import BaseModule
from ErisPulse import sdk

class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("MyModule")

    async def on_load(self, event):
        self.logger.info("Module loaded")

    async def on_unload(self, event):
        self.logger.info("Module unloaded")
```

#### Module Lifecycle

- **Registration**: The SDK discovers the module class and registers it with the manager
- **Loading**: The module instance is created, and `on_load(event)` is called (`event = {"module_name": "MyModule"}`)
- **Unloading**: `on_unload(event)` is called, and resources are cleaned up

#### Loading Strategy

Declare the module's loading behavior via `get_load_strategy()`:

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Whether to load lazily (default True)
            priority=0        # Loading priority, higher values initialize earlier
        )
```

- **`lazy_load=True` (default)**: The module initializes only when first accessed via `sdk.MyModule`, reducing startup time
- **`lazy_load=False`**: The module initializes immediately when the SDK starts, suitable for modules that need to listen to lifecycle events or execute scheduled tasks
- **`priority`**: Modules with the same priority load in registration order; higher values initialize earlier

> For detailed explanations of the lazy-loading mechanism, refer to [Lazy Loading System](../advanced/lazy-loading.md).

## Event Types

ErisPulse supports five types of events:

| Event Type | Decorator | Description |
|---------|--------|------|
| Message Event | `@message.on_message()` | Any message sent by the user (private chat, group chat) |
| Command Event | `@command("name")` | Messages starting with a command prefix (e.g., `/hello`) |
| Notice Event | `@notice.on_friend_add()` etc. | System notifications (friend added, group member changes, etc.) |
| Request Event | `@request.on_friend_request()` etc. | User requests (friend requests, group invitations) |
| Meta Event | `@meta.on_connect()` etc. | System-level events (connection, disconnection, heartbeat) |

> For detailed usage and code examples of each event type, refer to [Event Handling Introduction](event-handling.md).

## Core Module Descriptions

### Storage (Storage)

A key-value storage system based on SQLite, used for persistent data.

```python
# Set value
sdk.storage.set("key", "value")

# Get value
value = sdk.storage.get("key", "default_value")

# Bulk operations
sdk.storage.set_multi({
    "key1": "value1",
    "key2": "value2"
})

# Transactions
with sdk.storage.transaction():
    sdk.storage.set("key1", "value1")
    sdk.storage.set("key2", "value2")
```

### Config (Configuration)

TOML-based configuration file management.

```python
# Get configuration
config = sdk.config.getConfig("MyModule", {})

# Set configuration
sdk.config.setConfig("MyModule", {"key": "value"})

# Read nested configuration
value = sdk.config.getConfig("MyModule.subkey", "default")
```

### Logger (Logging)

A modular logging system.

```python
# Log messages
sdk.logger.info("This is an info message")
sdk.logger.warning("This is a warning message")
sdk.logger.error("This is an error message")

# Get child logger
child_logger = sdk.logger.get_child("submodule")
child_logger.info("Submodule log message")
```

**Attribute Access Syntactic Sugar**

In addition to using the `get_child()` method, you can also create child loggers using **attribute access**, which is a more concise **syntactic sugar**:

```python
# Create child logger using attribute access
sdk.logger.mymodule.info("Module message")

# Supports nested access
sdk.logger.mymodule.database.info("Database message")
```

### Router (Routing)

HTTP and WebSocket routing management, based on FastAPI + Uvicorn. Supports decorator routing, middleware, grouping, rate limiting, CORS.

```python
from ErisPulse.Core import HttpRequest

@sdk.router.get("MyModule", "/api")
async def handler(request: HttpRequest):
    data = await request.json()
    return {"status": "ok"}
```

> For the complete routing API (WebSocket, middleware, rate limiting, CORS, etc.), refer to [Router Manager](../advanced/router.md).

### Client (Network Client)

A unified network client that aggregates HTTP requests, WebSocket connections, connection pooling, automatic retries, timeout control, request statistics, and lifecycle event integration.

```python
from ErisPulse.Core import client

# HTTP request
resp = await client.get("https://api.example.com/users")
data = await resp.json()

# Request with retries and timeout
resp = await client.get(url, timeout=30, max_retries=3)

# WebSocket connection
ws = await client.ws_connect("wss://example.com/ws")
async for text in ws.iter_text():
    await ws.send_text(f"Echo: {text}")
```

> For the complete network client API, refer to [Network Client](../advanced/http-client.md).

## SendDSL Message Sending

Adapters provide a chainable message sending interface.

### Basic Sending

```python
# Get adapter instance
yunhu = sdk.adapter.get("yunhu")

# Send message
await yunhu.Send.To("user", "U1001").Text("Hello")

# Specify sender account
await yunhu.Send.Using("bot1").To("group", "G1001").Text("Group message")
```

### Chainable Modifiers

```python
# @user
await yunhu.Send.To("group", "G1001").At("U2001").Text("@message")

# Reply to message
await yunhu.Send.To("group", "G1001").Reply("msg123").Text("Reply")

# @all
await yunhu.Send.To("group", "G1001").AtAll().Text("Announcement")
```

### Event Reply Methods

The Event object provides convenient reply methods:

```python
@command("test")
async def test_handler(event):
    # Simple text reply
    await event.reply("Reply content")
    
    # Send image
    await event.reply("http://example.com/image.jpg", method="Image")
    
    # Send voice
    await event.reply("http://example.com/voice.mp3", method="Voice")
```

## Lazy Loading System

ErisPulse enables module lazy loading by default. Modules only initialize when first accessed (e.g., `sdk.MyModule`), significantly improving startup speed.

```python
from ErisPulse.loaders import ModuleLoadStrategy

class Main(BaseModule):
    @staticmethod
    def get_load_strategy():
        return ModuleLoadStrategy(
            lazy_load=True,   # Enable lazy loading (default)
            priority=0        # Loading priority, higher values initialize earlier
        )
```

**Scenarios where lazy loading should be disabled (`lazy_load=False`):**
- Modules that listen to lifecycle events (e.g., `core.init.complete`)
- Modules that start scheduled tasks or background services
- Modules that need to complete initialization before other modules are loaded

> For detailed explanations of the lazy loading mechanism and considerations, refer to [Lazy Loading System](../advanced/lazy-loading.md).

## 事件处理

> 来源: `docs/en/getting-started/event-handling.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/getting-started/event-handling.md）

# Getting Started with Event Handling

> [!TIP]
> **When to read this**: Read this if you want your bot to respond to messages, commands, notifications, or requests, or if you need to implement reply waiting / multi-turn conversations, or troubleshoot "why isn't my command triggering". If you only want to understand the framework design, [Basic Concepts](basic-concepts.md) is all you need; otherwise, feel free to skip this.

Event handlers are where the bot "understands" users and reacts to them. This guide provides copy-paste-ready code patterns for the five event types, covering practical scenarios such as argument parsing, permissions, throttling, and multi-turn interaction.

## Overview of Event Types

ErisPulse supports the following event types:

| Event Type | Description | Applicable Scenarios |
|---------|------|---------|
| Message Event | Any message sent by a user | Chatbot, content filtering |
| Command Event | Message starting with a command prefix | Command processing, function entry |
| Notice Event | System notifications (friend addition, group member changes, etc.) | Welcome messages, status notifications |
| Request Event | User requests (friend requests, group invitations) | Automatic request handling |
| Meta Event | System-level events (connection, heartbeat) | Connection monitoring, status checks |

## Message Event Handling

> **Tip**: It is recommended to use the `Event` type annotation in event handlers to get IDE auto-completion and type checking support.

```python
from ErisPulse.Core.Event import Event  # Import Event type for annotation
```

### Listening to All Messages

```python
from ErisPulse.Core.Event import message, Event

@message.on_message()
async def message_handler(event: Event):
    text = event.get_text()
    user_id = event.get_user_id()
    sdk.logger.info(f"Received message from {user_id}: {text}")
```

### Listening to Private Messages

```python
@message.on_private_message()
async def private_handler(event: Event):
    user_id = event.get_user_id()
    await event.reply(f"Hello, {user_id}! This is a private message.")
```

### Listening to Group Messages

```python
@message.on_group_message()
async def group_handler(event: Event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    sdk.logger.info(f"Message sent in group {group_id} by {user_id}")
```

### Listening to @ Messages

```python
@message.on_at_message()
async def at_handler(event: Event):
    # Get list of mentioned users
    mentions = event.get_mentions()
    await event.reply(f"You mentioned these users: {mentions}")
```

### Wildcard and Regex Listening

All four message decorators (`on_message` / `on_private_message` / `on_group_message` /
`on_at_message`) support `pattern` (glob wildcard) and `regex` (regex), and messages that do not match will **not trigger** the handler:

```python
# Glob wildcard: * any string, ? single character, [seq] character set
@message.on_message(pattern="签到*")
async def signin_handler(event: Event):
    await event.reply("Sign-in successful")

# Regex: match amount
@message.on_message(regex=r"\d+\s*元")
async def price_handler(event: Event):
    await event.reply(f"Received amount: {event.get_text()}")

# Both pattern and regex given → both must match
@message.on_message(pattern="*元", regex=r"\d+\s*元")
async def combined_handler(event: Event):
    pass
```

`wait_reply` also supports these two parameters (see [Wait Reply Functionality](../developer-guide/modules/event-wrapper.md#wait-reply-functionality)).

## Command Event Handling

### Basic Commands

```python
from ErisPulse.Core.Event import command

@command("help", help="Display help information")
async def help_handler(event):
    help_text = """
Available commands:
/help - Display help
/ping - Test connection
/info - View information
    """
    await event.reply(help_text)
```

### Command Aliases

```python
@command(["help", "h"], aliases=["帮助"], help="Display help information")
async def help_handler(event):
    await event.reply("Help information...")
```

Users can call using any of the following:
- `/help`
- `/h`
- `/帮助`

### Command Arguments

```python
@command("echo", help="Echo message")
async def echo_handler(event):
    # Get command arguments
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a message to echo")
    else:
        await event.reply(f"You said: {' '.join(args)}")
```

Arguments preserve the original case entered by the user (even if case-insensitive is configured, case normalization for command matching does not affect argument content).

### Declared Parameters and Options (args= / options=)

Manually parsing arguments requires handling type conversion and error messages yourself. After declaring `args=` / `options=`, the framework automatically parses command arguments and **injects them by name** after permission checks pass; when user input is incorrect, it automatically replies with localized error messages and usage (without throwing an exception crash); `/help <command>` will also automatically display usage:

```python
@command(
    "roll",
    args="<count:int> [sides:int=6]",
    options={"verbose": "-v/--verbose", "label": "--label"},
    help="Roll dice",
)
async def roll_handler(event, count: int, sides: int = 6, verbose: bool = False, label: str = ""):
    total = sum(random.randint(1, sides) for _ in range(count))
    await event.reply(f"Rolled {count} {sides}-sided dice, total points: {total}")
```

`args=` positional parameter syntax: `<count:int>` is required, `[sides:int=6]` is optional (with default value). Supported types:

| Type | Example Input | Description |
|------|---------|------|
| `str` | `hello` | Text (default type) |
| `int` / `float` | `3` / `0.5` | Number |
| `bool` | `是` / `yes` / `はい` / `да` / `true` / `no` / `取消` | Boolean, reuses confirmation words from `Event.confirm()` |
| `literal` | `<mode:literal=fast|slow>` | Enum, accepts only listed values; optional form defaults to first |
| `duration` | `90s`、`1h30m`、`1d` | Duration, converted to float in seconds |
| `rest` | `<text:rest>` | Remaining full text (must be at the end) |

`options=` is declared as a dictionary: key is the handler parameter name, value is the flag form (multiple aliases separated by `/`). Parameters annotated as `bool` are boolean flags (appear as `True`); others (default as `str`) are options with values, supporting `--label hello` and `--label=hello` value formats, with type following the handler annotation. Options are recognized and removed first, remaining tokens are parsed according to `args=` (the `rest` covers the remaining text after option removal).

**Behavior Points**:

- Permission checks precede parameter parsing—users without permission will not trigger parsing
- Parsing fails (type mismatch / missing parameter / too many parameters / unknown option) automatically replies with localized error + usage, command is still claimed
- Declared parameter names must exist in the handler signature, otherwise a `ValueError` is thrown during registration
- Commands without declaring `args=` / `options=` behave exactly the same (backward compatibility)

### Command Governance (cooldown= / rate_limit= / usage_limit= / deprecated=)

Handwritten cooldown timing, rate limiting window, usage quota, deprecation prompts can be replaced with declarations, all four can be combined.

**Cooldown**—duration syntax is consistent with the `duration` type in `args=` (e.g., `"30s"`, `"1h30m"`, `"1d"`):

```python
@command("daily", cooldown="1d", cooldown_key="user", cooldown_reply="Signed in today")
async def daily_handler(event):
    await event.reply("Sign-in successful!")
```

**Rate Limit**—sliding window declaration `"count/window"` (e.g., `"5/minute"`, `"10/s"`, `"3/2m"`):

```python
@command("search", rate_limit="5/minute", rate_limit_key="user")
async def search_handler(event):
    await event.reply("Search results")
```

**Usage Limit**—total usage limit within a period (e.g., `"100/day"`, `"10/hour"`, `"500/30d"`), exceeding the limit rejects execution:

```python
@command("translate", usage_limit="100/day", usage_limit_key="user",
         usage_limit_reply="Daily translation count exhausted")
async def translate_handler(event):
    ...
```

Unlike cooldown/limiting, usage counting is **persisted in storage** (KV key `erispulse.usage.<key>`, not lost on restart): if storage is unreachable, it automatically degrades to pure in-memory counting and logs a warning (count resets on restart in this case). Counting automatically resets with the usage period switch, and cleanup occurs when the module is unloaded.

**Deprecated**—automatically replies with deprecation text upon call; `deprecated_reject=True` rejects execution:

```python
@command("oldcmd", deprecated="Please use /newcmd", deprecated_reject=True)
async def old_handler(event): ...
```

Key granularity (`cooldown_key=` / `rate_limit_key=`): `"user"` (default, shared by the same user), `"session"` (shared by the same session, like the same group), `"global"` (shared by all users and sessions).

**Behavior Points**:

- Cooldown / rate limiting / usage limit hits default to **silent discard** (symmetrical to scope silence); if `cooldown_reply=` / `rate_limit_reply=` / `usage_limit_reply=` is declared, reply with the text when hit
- Command hits claim the command—governed commands won't leak to lower priority message handlers
- Governance checks occur after all permission checks and parameter parsing pass, before actual execution: users without permission don't trigger, parameter errors don't consume
- When cooldown and rate limiting are declared simultaneously, cooldown is checked first (cooldown hits don't occupy the rate limiting window); usage limits are checked after cooldown/limiting
- `deprecated=` defaults to replying with the text and **continues execution**; `deprecated_reject=True` rejects execution (`command.executed` hook records `success=False, error="deprecated"`)
- `/help` list and single command help automatically display deprecation markers and text
- Cooldown and rate limiting status are in-process memory, automatically cleaned up when the module is unloaded; cross-process sharing / persistence on restart is out of scope (**usage quota counting excepted**—persisted via storage, see above)
- Declaration is validated at registration (fail-fast): illegal syntax, key granularity not in whitelist, reply not paired with main declaration all throw `ValueError`

### Handler Throttling (throttle=) and Debouncing (debounce=)

Message handler anti-spam declaration—same key events are processed at most once within the interval, others are silently discarded:

```python
from ErisPulse import sdk

@sdk.message.on_message(throttle="2s", throttle_key="user")
async def handler(event): ...
```

Debounce and throttling are complementary: **only the last one within the window is executed**, previous pending tasks are automatically canceled (suitable for search suggestion scenarios where processing happens after the user stops typing):

```python
@sdk.message.on_message(debounce="2s", debounce_key="user")
async def search(event): ...
```

`on_message` / `on_private_message` / `on_group_message` / `on_at_message` all support it; `throttle_key=` / `debounce_key=` use the same key granularity as command governance (`user` / `session` / `global`), duration syntax is consistent with `duration`. Throttling and `pattern=` / `regex=` conditions are overlapped and effective (all must match to trigger); discarded within the interval only logs TRACE; declaration is validated at registration; `throttle=` and `debounce=` semantics are mutually exclusive (throw `ValueError` if both are declared).

> **Debounce does not interrupt midway**: Only pending tasks that have not crossed the waiting window are canceled; tasks already past the window and currently executing are not canceled by new events (avoid partial side effects if stopped at any await point).

### Dependency Injection (Depends)

Common dependencies (database sessions, configuration reading, etc.) can be extracted into dependency functions. Handlers declare them as `Depends(dependency function)` with a default value, and the framework automatically calls the dependency function with the context object before calling and injects it by name:

```python
from ErisPulse.Core import Depends

async def get_session(event):
    return await sdk.module.call("DB", "get_session")

@command("admin")
async def admin_handler(event, db=Depends(get_session)):
    ...
```

Request-level caching is enabled by default: within the same event distribution, the same dependency function is parsed only once, and all injection points share the result (e.g., `get_db` only creates a database session once per event); it is not reused across requests. Use `Depends(get_db, use_cache=False)` to disable caching for a single dependency.

Covers all framework injection points—command handlers, event handlers (`message.on_message()` etc.), lifecycle hooks (`sdk.lifecycle.on`), SSE route handlers. The first parameter of the dependency function is the context object of the injection point (event scenario is `Event`, lifecycle is event `data`, route is `HttpRequest` / `SseEmitter`); both synchronous and asynchronous dependency functions can be declared.

**Syntax sugar for declaring other module services**:

```python
@command("query")
async def query_handler(event, session=Depends.module("DB", "get_session")):
    ...
```

`Depends.module(module name, method name, *fixed arguments)` is equivalent to calling `sdk.module.call(...)` inside the dependency function. Module instantiation (`__init__`) is not covered—there is no context object during instantiation; for FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`.

**Behavior Points**:

- Declaration is validated at registration (fail-fast): throws `ValueError` if the dependency is not callable, or if it conflicts with `args=` / `options=` parameters
- Exceptions thrown by the dependency function are handled in the same way as the handler's own exceptions (command automatically replies with errors)
- Handlers without declaring `Depends` have zero overhead (no reflection during distribution)
- For FastAPI hosted HTTP routes, use FastAPI's native `fastapi.Depends`

### Command Groups

```python
@command("admin.reload", group="admin", help="Reload module")
async def reload_handler(event):
    await event.reply("Module reloaded")

@command("admin.stop", group="admin", help="Stop bot")
async def stop_handler(event):
    await event.reply("Bot stopped")
```

The `group` parameter is only used for help list categorization; the above example's `admin.reload` is a **single command name** (the dot is just a naming style, users need to input `/admin.reload`).

### Subcommands

Command names support **multi-token** forms separated by spaces, enabling subcommands like `/admin add`, `/admin user ban`:

```python
@command("admin", help="Admin commands")
async def admin_handler(event):
    await event.reply("Usage: /admin add | /admin remove")

@command("admin add", help="Add admin")
async def admin_add_handler(event):
    target = event.get_command_args()[0]
    await event.reply(f"Added {target}")

@command("admin remove", aliases=["a remove"], help="Remove admin")
async def admin_remove_handler(event):
    await event.reply("Removed")
```

Matching rules (**longest prefix match**):

- `/admin add x` prioritizes matching `admin add`, `event.get_command_args()` returns `["x"]` (arguments after the subcommand name)
- Only `admin` is registered, `/admin add x` matches `admin`, `get_command_args()` returns `["add", "x"]` (historical behavior unchanged)
- Aliases support multi-token forms (e.g., `a remove`), single-token aliases (e.g., `a`) can also point to subcommands
- When parent and child commands are registered simultaneously, unregistered subcommands (e.g., `/admin list x`) fall back to the parent command

**Permission Inheritance**: When subcommands do not declare `permission`, they automatically inherit the permission of the nearest ancestor command that declared it on the parent chain—protecting `/admin` automatically protects all its subcommands; the permission declared by the subcommand itself takes precedence:

```python
def is_admin(event):
    return event.get_user_id() in {"user123"}

@command("admin", permission=is_admin, help="Admin commands")
async def admin_handler(event):
    ...

# No need to repeat permission declaration, automatically inherits is_admin
@command("admin add", help="Add admin")
async def admin_add_handler(event):
    ...
```

Note: `master=True` and `hidden` **do not** inherit, they need to be declared separately on the subcommand; user ACL (whitelist/blacklist) matches by full command name, glob rules like `"admin*"` can cover entire subcommand groups.

In the `/help` command overview, subcommands are automatically indented under visible parent commands (e.g., `admin` → `admin add` indented one level, `admin user` → `admin user ban` indented two levels).

### Command Permissions and Access Control

Command permissions are divided into three layers, checked from top to bottom (if the upper layer rejects, the lower layer is not checked):

```python
# ① Command Permission ACL (user-side configuration): By user whitelist/blacklist of the command, rejects with "permission denied"
# ② master=True — Only the framework owner can execute (framework automatically checks, rejects with "permission denied")
@command("restart", master=True, help="Restart module")
async def restart_handler(event):
    await event.reply("Module restarted")

# ③ permission=call function — The command's own control logic (returns True to execute)
def is_admin(event):
    return event.get_user_id() in {"user123", "user456"}

@command("panel", permission=is_admin, help="Admin panel")
async def panel_handler(event):
    await event.reply("Welcome to the admin panel")
```

**Command User ACL** (`ErisPulse.event.command.acl`): Users can configure user whitelist/blacklist for any command, command names support exact and glob patterns (e.g., `"roll*"`), rejects with "permission denied":

```toml
# config.toml — Allow only 123456 to execute restart; 666 is always rejected
[ErisPulse.event.command.acl.restart]
allow = ["onebot11:123456"]
deny = ["onebot11:666"]
```

Order of judgment: `deny` hits → reject; `allow` is non-empty and does not hit → reject; if ACL is not configured, follow `event.command.default_allow` (false = strict mode, no ACL means reject; true means leave to developer default `master=True` / `permission`). Runtime API (command names support glob):

```python
from ErisPulse.Core.Event import command

command.allow_user("restart", "onebot11", "123456")   # Allow list
command.deny_user("restart", "onebot11", "666")       # Deny list
command.remove_acl("restart")                          # Clear whitelist/blacklist
command.get_acl("restart")                             # Query current list
```

> Command handlers are imported from event package: `from ErisPulse.Core.Event import command`; can also access via SDK event package: `sdk.Event.command` (both are the same singleton). In modules, they are usually imported with the command decorator (`from ErisPulse.Core.Event import command`).

Cross-command / cross-user **event-level** access control (whether to receive messages from a person / group / Bot) goes through the **identity dimension** of the scope ( `scope.identity` ); **module-level** availability (which modules can be used) goes through the **module dimension** of the scope ( `scope.platforms / bots / sessions` ).
See [Scope](../advanced/scope.md).

> Suggestion: Use `master=True` / `permission` for command internal logic that needs to be linked with business logic; use the identity dimension of the scope for access control based on users / groups; use the module dimension of the scope for controlling module availability.

### Command Priority

```python
# The higher the priority value, the earlier it executes
@message.on_message(priority=10)
async def high_priority_handler(event):
    await event.reply("High-priority handler")

@message.on_message(priority=1)
async def low_priority_handler(event):
    await event.reply("Low-priority handler")
```

### Parallel Event Handling

ErisPulse's event system uses a scheduling model where handlers of the same priority run in parallel, and handlers of different priorities run serially:

```
Event arrives
    ↓
priority=10 group: [handler C || handler D] parallel → merge results
    ↓ (if not interrupted)
priority=0 group: [handler A || handler B] parallel → merge results
    ↓
...
```

- **Parallel within the same priority**: Handlers of the same priority run simultaneously, improving throughput
- **Serial across different priorities**: Groups of different priorities run in order (the higher the value, the earlier it runs), ensuring that high-priority handlers run first
- **Copy-On-Write**: Handlers do not create a copy unless they make modifications, ensuring zero overhead
- **Conflict handling**: When multiple handlers of the same priority modify the same field, the last modification is used, and a warning log is recorded
- **Interruption mechanism**: After any handler calls `event.done()` (default) or `event.done(claim=False)`, subsequent lower-priority groups are skipped. The difference between claiming and blocking is explained in the next section [Link Control: Claiming and Blocking](#link-control-claiming-and-blocking)

```python
# Example: Parallel execution of handlers with the same priority
@message.on_message(priority=0)
async def handler_a(event):
    # Process task A
    event['result_a'] = process_a()

@message.on_message(priority=0)
async def handler_b(event):
    # Executes in parallel with handler_a
    event['result_b'] = process_b()

# Serial execution of different priorities
@message.on_message(priority=10)
async def handler_c(event):
    # Highest priority, executed first
    pass
```

> **Concurrency limit**: All matching handlers' tasks are created immediately, but a semaphore limits the number of concurrent executions, with a default upper limit of **64** (`ErisPulse.framework.handler_max_concurrency`, supports hot updates). Tasks exceeding the limit queue on the semaphore, waiting for previous tasks to complete before entering. This is your "pressure relief valve" during event peaks.
>
> **Slow logs**: If a single handler takes more than **1 second**, the framework logs a WARNING (`handler_slow`). The waiting time for `wait_reply` is excluded from the timing, so it won't misreport slow due to "waiting for a reply."

## Middleware: Rewrite or Reject Before Distribution

Middleware executes in order before event distribution, serving as the proper implementation point for scenarios such as firewalls, rate limiting, and event desensitization:

```python
from ErisPulse.Core import adapter

@adapter.middleware
async def firewall(data):
    if _is_banned(data.get("user_id")):
        return False          # Reject: Event is discarded, not entering any handler, no outbound side effects
    data["checked"] = True    # Return dict: Rewrite event payload (consistent with historical behavior)
    # Return None: Allow, payload unchanged (historical behavior)
    return data
```

| Return Value | Behavior |
|--------|------|
| `False` | **Reject**: Event is immediately discarded, not entering any handler |
| `dict` | Rewrite event payload and continue distribution |
| `None` | Allow, payload unchanged |

When rejected, the framework outputs a TRACE log and triggers the `adapter.event.blocked` lifecycle hook (carrying the middleware name and full event), providing audit for "why the event was not responded to."

## Command Dispatch Decision Chain: Why a Command Didn't Trigger

A command message sequentially passes through: **command text judgment → command name/alias match (suggests spelling if not matched) → match claims → scope → user ACL → owner → permission → cooldown/limit → usage limit (deprecated, notice/rejected) → parameter parsing → execution** (middleware can reject at the event level, see the previous section). If any step is not met, it terminates; governance hits are silently discarded by default (symmetrical to scope silence); permission rejections reply to the user, and deprecation replies or rejects according to the declaration.

In testing, `ErisPulse-Testing`'s `dispatch()` directly returns this decision chain (`DispatchTrace`, `trace.explain()` outputs step-by-step causality), and in production, `ErisPulse.Core.Event.start_dispatch_trace()` can collect the same record.

Additionally, `ErisPulse.runtime` provides two sets of diagnostic APIs: `explain_module(module name)` answers "why the module didn't load" (not registered / lazy loaded / disabled by configuration / missing dependencies / SDK version not satisfied, each item gives a reason), `explain_event(event)` answers "why the event didn't respond" (adapter not registered / identity blacklisted / module session blocked / command not matched); with `format_report()` renders human-readable conclusions.

## Scope Filtering: Why My Module Didn't Receive the Message

After an event arrives, there are two **silent** filters (neither reply nor error):

1. **Identity dimension** (`ErisPulse.scope.identity`): When the event enters the distribution entry point, it is judged by user > group > Bot > adapter whether to receive or not.
   Events rejected by this dimension are **completely discarded**, and no handler (including the command dispatcher) will be triggered.
2. **Module dimension** (`ErisPulse.scope`): When the event reaches a module's handler/command, it is judged by session > Bot > platform whether the module is available; if it does not pass, it is **silently skipped**.

```toml
# Example 1: All messages in a group are not propagated
[ErisPulse.scope.identity.sessions.onebot11."group_123"]
deny = true

# Example 2: Blocking MyModule in a certain Bot
[ErisPulse.scope.bots.onebot11."123456"]
blocked = ["MyModule"]
```

At this point, when a message from this group arrives, the commands and event handlers of `MyModule` **will not be scheduled**. This is not a bug, but a filtering mechanism—when troubleshooting "module response," first check the scope's identity and module binding.

- Filter logs are only visible at **TRACE** level ( `core.scope.identity_denied` / `core.scope.denied` ), and default INFO does not show any trace
- Framework-level handlers (such as the command dispatcher `scope_exempt=True`) are not affected by the **module dimension** but are affected by the **identity dimension** (the entire event has been discarded)
- There is a third filter before command execution: command user ACL (rejects with "permission denied," see above)
- The fourth filter is **event overwriting** (see next section)

> [!NOTE]
> **Relationship between scope filtering and event claiming (claim)**: Both silent filters occur before handler **scheduling**—handlers that are filtered out do not have the opportunity to execute, and naturally do not participate in the `event.done()` / `mark_processed()` claiming status. Whether an event has been claimed is determined only by **actual executed** handlers (command match claims, reply match claims, explicit calls); event rejection itself neither claims nor blocks (silently skips, the message continues through the remaining distribution chain).

> Scope configuration, matching syntax, and runtime API are described in [Scope](../advanced/scope.md).

## Event Overwriting: Overwrite Any Event Type Behavior Without Modifying Module Code

> [!NOTE]
> This feature requires ErisPulse **2.8.0+**.

Event handlers, when registered, declare parameters ( `pattern` / `regex` / `master` / `hidden` etc.) only as **developer defaults**.
A unified overwriting system allows users to overwrite any module's behavior by **event type**—OneBot12 standard types ( meta / message / notice / request ) and ErisPulse extended types ( command ) each have their own set of overwritable parameters:

| Event Type | Overwritable Parameters | Purpose |
|---------|-----------|------|
| `message` | `pattern` / `regex` / `detail_types` | Text trigger conditions + message subtype whitelist |
| `notice` | `detail_types` / `pattern` / `regex` | Notice subtype whitelist + text conditions |
| `request` | `detail_types` / `pattern` / `regex` | Request subtype whitelist + text conditions |
| `meta` | `detail_types` | Meta event subtype whitelist (connect / heartbeat etc.) |
| `command` | `master` / `hidden` / `aliases` / `prefix` / `help` / `usage` | Command implementation parameters (user priority) |
| `acl` (command-specific) | `allow` / `deny` | Command user whitelist/blacklist (by command name glob) |

```toml
# message: Overwrite text trigger condition (AND with code-level condition)
[ErisPulse.event.overrides.message.ChatModule]
pattern = "闲聊*"

# notice: Only respond to specific notice subtypes
[ErisPulse.event.overrides.notice.MyModule]
detail_types = ["group_increase"]

# command: Overwrite implementation parameters (user priority—can tighten or loosen developer default)
[ErisPulse.event.overrides.command.MyModule.restart]
master = true
hidden = true

# acl: Command user whitelist/blacklist (cross-command glob)
[ErisPulse.event.overrides.acl."roll*"]
allow = ["onebot11:u_vip"]

# ACL fallback (false = strict mode: no ACL means reject)
acl_default_allow = true
```

Runtime API (`from ErisPulse.Core.Event import overrides` or `sdk.Event.overrides`, **type sub-namespace**—each type has symmetric `set` / `get` / `delete` three-piece sets):

```python
from ErisPulse.Core.Event import overrides

overrides.message.set("ChatModule", pattern="闲聊*")   # message text condition
overrides.notice.set("MyModule", detail_types=["group_increase"])
overrides.command.set("MyModule", "restart", master=True)  # command parameter
overrides.acl.set("roll*", deny=["onebot11:u_bad"])    # command user blacklist

overrides.message.get("ChatModule")     # {"pattern": "闲聊*"}
overrides.message.delete("ChatModule")  # Restore developer default
```

- Overwrite conditions and handler code-level conditions **both take effect** (AND semantics); `command` parameter overwrite and developer declaration **deep merge** (overwrite priority)
- `detail_types`: Events without `detail_type` are allowed (not mistakenly kill unknown events)
- `pattern` / `regex`: Events without text (connect / heartbeat etc.) are not constrained, directly allowed
- `command` overwrite key `master` synchronously maps to storage key `must_master`; disabling commands uniformly goes through `acl` deny
- **Key name mapping explanation**: The parameter name `master` for `overrides.command.set("My", "restart", master=True)` is only a configuration alias; the actual storage key and the key name in the `get()` return value are unified as **`must_master`** ( `get()` returns `{"must_master": true}` )—runtime judgment reads the storage key, please do not read by the `master` key name
- Configuration changes take effect immediately (hot update), format validation warnings (unknown parameters / bad entries are ignored)

## Link Control: Claiming and Blocking

> [!NOTE]
> `event.done()` / `event.mark_processed()` `claim=` / `stop=` parameters for this feature require ErisPulse **2.7.1+**.

ErisPulse decouples the two orthogonal semantics of "claiming" and "blocking," unifying control through `event.done()`, which is convenient for stacking logging, auditing, permission, and other observation layers around command processing.

**Accurate definitions of the two concepts:**

- **Claiming (claim)**: Mark the event as processed by this handler (write to `_processed`). The command dispatcher sees claimed events and **skips duplicates**—preventing the same message from being processed by multiple command handlers. Typical scenario: After a command matches, claim it, preventing the command dispatcher from intervening again.
- **Blocking (stop)**: Prevent the event from propagating to **lower-priority** handlers (write to `_propagation_stopped`). Lower-priority handlers will no longer see the event. Typical scenario: A high-priority handler has fully processed the event and does not want lower-priority handlers to execute.

| `event.done(...)` | Claim | Block | Scenario |
|-------------------|------|------|------|
| `event.done()` | ✔ | ✔ | Standard practice for command / handler completion |
| `event.done(stop=False)` | ✔ | ✘ | Only claim: lower-priority observers (logging / statistics) still see it |
| `event.done(claim=False)` | ✘ | ✔ | Only block (e.g., firewall / rate limiting), but do not do command deduplication |

`event.done(claim=, stop=)` is an alias for `event.mark_processed(claim=, stop=)`, with identical parameters and behavior.

```python
@command("help")
async def help_cmd(event):
    event.done()            # Claim + Block (standard practice for command completion)

@message.on_message(priority=50)
async def observer(event):
    event.done(stop=False)  # Only claim: lower-priority still executes (logging / statistics)

@message.on_message(priority=100)
async def firewall(event):
    if denied(event):
        event.done(claim=False)  # Only block: lower-priority does not execute, but no deduplication
```

### Command and Reply Block Configuration

**Command match claims immediately**: Once a message matches a registered command name (including subcommands/aliases), regardless of subsequent scope or permission checks, it is claimed and defaults to blocking propagation—commands rejected by permissions will no longer leak to lower-priority message handlers (eliminating "double response" of commands being rejected and then responding again in `on_message`).

Blocking can be configured to allow lower-priority observers (logging / auditing / permissions) to still see these messages:

```toml
[ErisPulse.event.command]
block = false   # Command messages continue to flow to lower-priority handlers (claim is unaffected, will not be re-consumed)

[ErisPulse.event.wait_reply]
block = false   # Reply messages consumed by wait_reply continue to flow to lower-priority handlers
```

> Note: `block` only controls **blocking** (stop), not **claiming** (claim)—commands that match will never be re-consumed by message handlers; messages that do not match any command flow as usual to message handlers.

## Notice Event Handling

### Friend Addition

```python
from ErisPulse.Core.Event import notice

@notice.on_friend_add()
async def friend_add_handler(event):
    user_id = event.get_user_id()
    nickname = event.get_user_nickname() or "New friend"
    await event.reply(f"Welcome to add me as a friend, {nickname}!")
```

### Group Member Increase

```python
@notice.on_group_increase()
async def member_increase_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Welcome new member {user_id} to group {group_id}")
```

### Group Member Decrease

```python
@notice.on_group_decrease()
async def member_decrease_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    await event.reply(f"Member {user_id} left group {group_id}")
```

## Request Event Handling

### Friend Request

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def friend_request_handler(event):
    user_id = event.get_user_id()
    comment = event.get_comment()
    
    sdk.logger.info(f"Received friend request: {user_id}, comment: {comment}")
    
    # You can handle the request through the adapter API
    # Refer to each adapter's documentation for specific implementation
```

### Group Invitation Request

```python
@request.on_group_request()
async def group_request_handler(event):
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Received invitation to group {group_id} from {user_id}")
```

## Meta Event Handling

### Connection Event

```python
from ErisPulse.Core.Event import meta

@meta.on_connect()
async def connect_handler(event):
    platform = event.get_platform()
    sdk.logger.info(f"{platform} platform connected")

@meta.on_disconnect()
async def disconnect_handler(event):
    platform = event.get_platform()
    sdk.logger.warning(f"{platform} platform disconnected")
```

### Heartbeat Event

```python
@meta.on_heartbeat()
async def heartbeat_handler(event):
    platform = event.get_platform()
    sdk.logger.debug(f"{platform} heartbeat check")
```

### Bot Status Query

After the adapter sends a meta event, the framework automatically tracks the bot status, and you can query it at any time:

```python
from ErisPulse import sdk

# Check if a bot is online
if sdk.adapter.is_bot_online("telegram", "123456"):
    telegram = sdk.adapter.get("telegram")
    await telegram.Send.To("user", "123456").Text("Bot is online")

# List all online bots
bots = sdk.adapter.list_bots()
for platform, bot_list in bots.items():
    for bot_id, info in bot_list.items():
        print(f"{platform}/{bot_id}: {info['status']}")

# Get full status summary
summary = sdk.adapter.get_status_summary()
```

## Interactive Handling

### Using the reply method to send replies

The `event.reply()` method supports various modifier parameters, making it convenient to send messages with features like @, reply, etc.:

```python
# Simple reply
await event.reply("Hello")

# Send different types of messages
await event.reply("http://example.com/image.jpg", method="Image")  # Image
await event.reply("http://example.com/voice.mp3", method="Voice")  # Voice

# @ a single user
await event.reply("Hello", at_users=["user123"])

# @ multiple users
await event.reply("Hello everyone", at_users=["user1", "user2", "user3"])

# Reply to a message
await event.reply("Reply content", reply_to="msg_id")

# @ all members
await event.reply("Announcement", at_all=True)

# Combination usage: @ user + reply to message
await event.reply("Content", at_users=["user1"], reply_to="msg_id")
```

### Waiting for user reply

```python
@command("ask", help="Ask user")
async def ask_handler(event):
    await event.reply("Please enter your name:")
    
    # Wait for user reply, timeout 30 seconds
    reply = await event.wait_reply(timeout=30)
    
    if reply:
        name = reply.get_text()
        await event.reply(f"Hello, {name}!")
    else:
        await event.reply("Timeout, please re-enter.")
```

> [!TIP]
> **Commands remain available during waiting** (2.8.3+): Messages starting with a command prefix and matching a registered command (e.g., `/cancel`) will **execute the command** rather than serve as a reply, keeping the wait suspended—users can cancel/switch at any time, and the command executes while continuing the reply. For the old behavior of "waiting swallowing all text," configure `ErisPulse.event.wait_reply.cmdpass = true`, or use `wait_reply(cmdpass=True)` once.

### Waiting reply with validation

```python
@command("age", help="Ask age")
async def age_handler(event):
    def validate_age(event_data):
        """Validate age is valid"""
        try:
            age = int(event_data.get_text())
            return 0 <= age <= 150
        except ValueError:
            return False
    
    await event.reply("Please enter your age (0-150):")
    
    reply = await event.wait_reply(
        timeout=60,
        validator=validate_age
    )
    
    if reply:
        age = int(reply.get_text())
        await event.reply(f"Your age is {age} years old")
    else:
        await event.reply("Invalid input or timeout")
```

### Waiting reply with callback

```python
@command("confirm", help="Confirm action")
async def confirm_handler(event):
    async def handle_confirmation(reply_event):
        text = reply_event.get_text().lower()
        
        if text in ["是", "yes", "y"]:
            await event.reply("Action confirmed!")
        else:
            await event.reply("Action canceled.")
    
    await event.reply("Confirm to execute this action? (Yes/No)")
    
    await event.wait_reply(
        timeout=30,
        callback=handle_confirmation
    )
```

### Confirmation dialog (confirm)

Wait for user confirmation or negation, automatically recognize built-in Chinese and English confirmation words:

```python
@command("confirm", help="Confirm action")
async def confirm_handler(event):
    if await event.confirm("Are you sure to execute this action?"):
        await event.reply("Confirmed, executing...")
    else:
        await event.reply("Canceled")

# Custom confirmation words
if await event.confirm("Continue?", yes_words={"go", "continue"}, no_words={"stop", "stop"}):
    pass
```

### Selection menu (choose)

Users can reply with option number or option text:

```python
@command("choose", help="Choose")
async def choose_handler(event):
    choice = await event.choose(
        "Please select a color:",
        ["red", "green", "blue"]
    )
    
    if choice is not None:
        colors = ["red", "green", "blue"]
        await event.reply(f"You selected: {colors[choice]}")
    else:
        await event.reply("Timeout, no selection made")
```

**Merge mode**: `merge_prompt=True` combines options into the prompt message, sending in a single message using the specified `method`:

```python
# Send merged prompt + options using Markdown
choice = await event.choose(
    "## Please select a color\n{options}\nPlease reply with the number",
    ["red", "green", "blue"],
    method="Markdown",
    merge_prompt=True,
)
```

> The `{options}` placeholder controls the insertion position of options; if not written, it appends to the end of the prompt. You can customize the placeholder using the `placeholder` parameter (e.g., `placeholder="[choices]"`). `options_format="auto"` (default) automatically chooses the style based on method: unordered list for Markdown, ordered list for Html, plain text list for others. For text methods (Text/Markdown/Html, etc.), options are merged by default to the end; for non-text methods (Image, etc.), options are split by default into two messages.

### Form collection (collect)

Multi-step collection of user input:

```python
@command("register", help="Register")
async def register_handler(event):
    data = await event.collect([
        {"key": "name", "prompt": "Please enter your name:"},
        {"key": "age", "prompt": "Please enter your age:", 
         "validator": lambda e: e.get_text().isdigit()},
        {"key": "email", "prompt": "Please enter your email:"}
    ])
    
    if data:
        await event.reply(f"Registration successful!\nName: {data['name']}\nAge: {data['age']}\nEmail: {data['email']}")
    else:
        await event.reply("Registration timeout or invalid input")
```

### Wait for any event (wait_for)

Wait for an event that meets certain conditions, not limited to the same user:

```python
@command("wait_member", help="Wait for new member")
async def wait_member_handler(event):
    await event.reply("Waiting for group member join...")
    
    evt = await event.wait_for(
        event_type="notice",
        condition=lambda e: e.get_detail_type() == "group_member_increase",
        timeout=120
    )
    
    if evt:
        await event.reply(f"Welcome new member: {evt.get_user_id()}")
    else:
        await event.reply("Timeout")
```

### Multi-turn conversation (conversation)

Create an interactive multi-turn conversation context:

```python
@command("survey", help="Questionnaire survey")
async def survey_handler(event):
    conv = event.conversation(timeout=60)
    
    await conv.say("Welcome to the survey!")
    
    while conv.is_active:
        reply = await conv.wait()
        
        if reply is None:
            await conv.say("Conversation timeout, goodbye!")
            break
        
        text = reply.get_text()
        
        if text == "Exit":
            await conv.say("Goodbye!")
            break
        
        await conv.say(f"You said: {text}, continue entering or reply 'Exit' to end")
```

### Built-in confirmation words

ErisPulse includes built-in confirmation word sets:

- **Confirmation words** (`CONFIRM_YES_WORDS`): 是, yes, y, confirm, sure, ok, true, yes, agree, no problem, ...
- **Negation words** (`CONFIRM_NO_WORDS`): no, n, cancel, no, don't, no way, cancel, false, wrong, reject, not allowed, ...

## Event Data Access

### Common methods of Event object

```python
@command("info")
async def info_handler(event):
    # Basic information
    event_id = event.get_id()
    event_time = event.get_time()
    event_type = event.get_type()
    detail_type = event.get_detail_type()
    
    # Sender information
    user_id = event.get_user_id()
    nickname = event.get_user_nickname()
    
    # Message content
    message_segments = event.get_message()
    alt_message = event.get_alt_message()
    text = event.get_text()
    
    # Group information
    group_id = event.get_group_id()
    
    # Bot information
    self_id = event.get_self_user_id()
    self_platform = event.get_self_platform()
    
    # Raw data
    raw_data = event.get_raw()
    raw_type = event.get_raw_type()
    
    # Platform information
    platform = event.get_platform()
    
    # Message type judgment
    is_private = event.is_private_message()
    is_group = event.is_group_message()
    is_at = event.is_at_message()
    
    # Command information
    if event.is_command():
        cmd_name = event.get_command_name()
        cmd_args = event.get_command_args()
        cmd_raw = event.get_command_raw()
```

### Platform-specific methods

In addition to built-in methods, each platform adapter registers platform-specific methods, making it convenient to access platform-specific data.

```python
from ErisPulse.Core.Event import message

@message.on_message()
async def handle_message(event):
    platform = event.get_platform()

    # Call platform-specific methods based on the platform
    if platform == "telegram":
        chat_type = event.get_chat_type()      # Telegram-specific method
    elif platform == "email":
        subject = event.get_subject()           # Email-specific method
```

If you are unsure whether a platform has registered a particular method, you can query which methods are registered for a specific platform:

```python
from ErisPulse.Core.Event import get_platform_event_methods

methods = get_platform_event_methods("telegram")
# ["get_chat_type", "is_bot_message", ...]
```

> For platform-specific methods registered by each platform, please refer to the corresponding [platform documentation](../platform-guide/).

## Event Handling Best Practices

### 1. Exception Handling

```python
@command("process")
async def process_handler(event):
    try:
        # Business logic
        result = await do_some_work()
        await event.reply(f"Result: {result}")
    except ValueError as e:
        # Expected business error
        await event.reply(f"Parameter error: {e}")
    except Exception as e:
        # Unexpected error
        sdk.logger.error(f"Processing failed: {e}")
        await event.reply("Processing failed, please try again later")
```

### 2. Logging

```python
@message.on_message()
async def message_handler(event):
    user_id = event.get_user_id()
    text = event.get_text()
    
    sdk.logger.info(f"Processing message: {user_id} - {text}")
    
    # Use the module's own logger
    from ErisPulse import sdk
    logger = sdk.logger.get_child("MyHandler")
    logger.debug(f"Detailed debug information")
```

### 3. Conditional Handling

```python
@message.on_message(priority=0)
async def conditional_handler(event):
    """Conditional handling - judge within the handler"""
    # Only process messages from specific users
    if event.get_user_id() in ["bot1", "bot2"]:
        return
    
    # Only process messages containing specific keywords
    if "keyword" not in event.get_text():
        return
    
    await event.reply("Condition met, processing message")
```

## 常见任务

> 来源: `docs/en/getting-started/common-tasks.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/getting-started/common-tasks.md）

# Common Task Examples

> [!TIP]
> **When to read this**: When you want to add a specific feature to your bot, refer to each section—persistence, scheduled tasks, message filtering, permission control, batch sending. Each section is a complete example you can copy directly. If you want to learn event handling patterns systematically, start with [Introduction to Event Handling](event-handling.md); otherwise, skip it.

## Content List

1. Data Persistence  
2. Scheduled Tasks  
3. Message Filtering  
4. Multi-Platform Adaptation  
5. Advanced Message Sending (Retry/Timeout/Batch)  
6. Permission Control  
7. Message Statistics  
8. Search Functionality  
9. Image Processing

## Data Persistence

### Simple Counter

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command

@command("count", help="View command invocation count")
async def count_handler(event):
    # Get the count
    count = sdk.storage.get("command_count", 0)
    
    # Increment the count
    count += 1
    sdk.storage.set("command_count", count)
    
    await event.reply(f"This is the {count}th invocation of this command")
```

### User Data Storage

```python
@command("profile", help="View profile")
async def profile_handler(event):
    user_id = event.get_user_id()
    
    # Get user data
    user_data = sdk.storage.get(f"user:{user_id}", {
        "nickname": "",
        "join_date": None,
        "message_count": 0
    })
    
    profile_text = f"""
Nickname: {user_data['nickname']}
Join Date: {user_data['join_date']}
Message Count: {user_data['message_count']}
    """
    
    await event.reply(profile_text.strip())

@command("setnick", help="Set nickname")
async def setnick_handler(event):
    user_id = event.get_user_id()
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a nickname")
        return
    
    # Update user data
    user_data = sdk.storage.get(f"user:{user_id}", {})
    user_data["nickname"] = " ".join(args)
    sdk.storage.set(f"user:{user_id}", user_data)
    
    await event.reply(f"Nickname has been set to: {' '.join(args)}")
```

## Scheduled Tasks

### Simple Timer

```python
from ErisPulse import sdk
from ErisPulse.Core.Event import command
import asyncio

class TimerModule:
    def __init__(self):
        self.sdk = sdk
        self._tasks = []
    
    async def on_load(self, event):
        """Start scheduled tasks when the module is loaded"""
        self._start_timers()
        
        @command("timer", help="Timer management")
        async def timer_handler(event):
            await event.reply("The timer is running...")
    
    def _start_timers(self):
        """Start scheduled tasks"""
        # Execute every 60 seconds
        task = asyncio.create_task(self._every_minute())
        self._tasks.append(task)
        
        # Execute daily at midnight
        task = asyncio.create_task(self._daily_task())
        self._tasks.append(task)
    
    async def _every_minute(self):
        """Task executed every minute"""
        self.sdk.logger.info("Executing every minute task")
        # Your logic...
    
    async def _daily_task(self):
        """Task executed daily at midnight (Note: based on UTC time calculation, adjust for local time if needed)"""
        import time
        
        while True:
            # Calculate time until midnight
            now = time.time()
            midnight = now + (86400 - now % 86400)
            
            await asyncio.sleep(midnight - now)
            
            # Execute task
            self.sdk.logger.info("Executing daily task")
            # Your logic...
```

### Using Lifecycle Events

```python
@sdk.lifecycle.on("core.init.complete")
async def init_complete_handler(event_data):
    """Start scheduled tasks after SDK initialization completes"""
    import asyncio
    
    async def daily_reminder():
        """Daily reminder"""
        await asyncio.sleep(86400)  # 24 hours
        sdk.logger.info("Executing daily task")
    
    # Start background task
    asyncio.create_task(daily_reminder())
```

## Message Filtering

### Keyword Filtering

```python
from ErisPulse.Core.Event import message

blocked_words = ["垃圾", "广告", "钓鱼"]

@message.on_message()
async def filter_handler(event):
    text = event.get_text()
    
    # Check if the message contains any blocked words
    for word in blocked_words:
        if word in text:
            sdk.logger.warning(f"Blocked sensitive message: {word}")
            return  # Do not process this message
    
    # Process the message normally
    await event.reply(f"Received: {text}")
```

### Blacklist Filtering

```python
# Load blacklist from configuration or storage
blacklist = sdk.storage.get("user_blacklist", [])

@message.on_message()
async def blacklist_handler(event):
    user_id = event.get_user_id()
    
    if user_id in blacklist:
        sdk.logger.info(f"User on blacklist: {user_id}")
        return  # Do not process
    
    # Process normally
    await event.reply(f"Hello, {user_id}")
```

## Multi-Platform Adaptation

### Platform-Specific Responses

```python
@command("help", help="Show help")
async def help_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        await event.reply("Yunhu platform help...")
    elif platform == "telegram":
        await event.reply("Telegram platform help...")
    elif platform == "onebot11":
        await event.reply("OneBot11 help...")
    else:
        await event.reply("General help information")
```

### Platform Feature Detection

```python
@command("rich", help="Send rich text message")
async def rich_handler(event):
    platform = event.get_platform()
    
    if platform == "yunhu":
        # Yunhu supports HTML
        yunhu = sdk.adapter.get("yunhu")
        await yunhu.Send.To("user", event.get_user_id()).Html(
            "<b>Bold text</b><i>Italic text</i>"
        )
    elif platform == "telegram":
        # Telegram supports Markdown
        telegram = sdk.adapter.get("telegram")
        await telegram.Send.To("user", event.get_user_id()).Markdown(
            "**Bold text** *Italic text*"
        )
    else:
        # Other platforms use plain text
        await event.reply("Bold text Italic text")
```

## Advanced Message Sending (Retry/Timeout/Batch)

In addition to the simple `event.reply()`, you can use the adapter's Send DSL to implement more complex sending scenarios: automatic retry on failure, timeout cancellation, executing logic after success, and batch sending of multiple messages.

> The following examples use `event.get_detail_type()` and `event.get_target_id()` to retrieve the target type and ID from the event (automatically getting `group_id` for group chats and `user_id` for private chats), avoiding hardcoding.

### Execute Logic After Successful Sending

```python
@command("pay", help="Simulate payment")
async def pay_handler(event):
    yunhu = sdk.adapter.get(event.get_platform())
    user_id = event.get_user_id()
    # Deduct points only after successful sending
    await (yunhu.Send.To(event.get_detail_type(), event.get_target_id())
           .Hook(lambda r: sdk.storage.set(f"points:{user_id}", -10))
           .Text("Payment successful, 10 points deducted"))
```

### Retry on Failure + Timeout Cancellation

```python
@command("notice", help="Send important notification")
async def notice_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Retry up to 3 times, with each attempt timed out after 10 seconds
    task = (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
            .Retry(3)
            .Timeout(10)
            .OnError(lambda ctx: sdk.logger.error(f"Notification sending failed: {ctx.error}"))
            .Text("This is an important notification"))
    # Send in the background without waiting
```

### Batch Send Multiple Messages

Send multiple messages in a single chain, with unified execution:

```python
@command("announce", help="Send announcement")
async def announce_handler(event):
    adapter_inst = sdk.adapter.get(event.get_platform())
    # Build multiple messages and send them together (default is parallel)
    results = await (adapter_inst.Send.To(event.get_detail_type(), event.get_target_id())
                    .Build()
                    .Text("📋 Today's announcement")
                    .Image("https://example.com/banner.jpg")
                    .Text("See the image above for details")
                    .Retry(2)            # Each failed item retries individually
                    .send_all())
    sdk.logger.info(f"Batch sending completed, {len(results)} messages in total")
```

> For a more complete explanation of rules and batch operations, see the [Platform Features Guide](../platform-guide/README.md#sending-rules-decorators).

## Permission Control

### Administrator Check

```python
# Configure the list of owners
MASTERS = ["user123", "user456"]

def is_master(user_id):
    """Check if the user is the framework owner"""
    return user_id in MASTERS

@command("master", help="Framework owner command")
async def master_handler(event):
    user_id = event.get_user_id()
    
    if not is_master(user_id):
        await event.reply("Insufficient permissions, this command is only available to the framework owner")
        return
    
    await event.reply("Framework owner command executed successfully")

@command("addmaster", help="Add framework owner")
async def addmaster_handler(event):
    if not is_master(event.get_user_id()):
        return
    
    args = event.get("text", "").split()
    if len(args) < 2:
        await event.reply("Usage: /addmaster <user ID>")
        return
    
    new_master = args[0]
    MASTERS.append(new_master)
    await event.reply(f"Framework owner added: {new_master}")
```

### Group Permissions

```python
@command("groupinfo", help="View group information")
async def groupinfo_handler(event):
    if not event.is_group_message():
        await event.reply("This command is only available in group chats")
        return
    
    group_id = event.get_group_id()
    user_id = event.get_user_id()
    
    await event.reply(f"Group ID: {group_id}, Your ID: {user_id}")
```

## Message Statistics

### Message Counting

> **Note**: The following example uses `sdk.storage.get/set` for simple counting. In high-concurrency scenarios, it is recommended to use `sdk.storage.transaction()` to ensure atomicity.

```python
@message.on_message()
async def count_handler(event):
    # Get statistics
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    # Update statistics
    stats["total"] += 1
    
    user_id = event.get_user_id()
    stats["by_user"][user_id] = stats["by_user"].get(user_id, 0) + 1
    
    # Save
    sdk.storage.set("message_stats", stats)

@command("stats", help="View message statistics")
async def stats_handler(event):
    stats = sdk.storage.get("message_stats", {
        "total": 0,
        "by_user": {},
        "by_day": {}
    })
    
    top_users = sorted(
        stats["by_user"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_text = "\n".join(
        f"{uid}: {count} messages" for uid, count in top_users
    )
    
    await event.reply(f"Total messages: {stats['total']}\n\nActive users:\n{top_text}")
```

## Search Functionality

### Simple Search

> **Note**: The following example uses an in-memory list to store message history; **data will be lost after program restart**. For production environments, it is recommended to use `sdk.storage` or SQLite tables for persistent storage.

```python
from ErisPulse.Core.Event import command, message

# Store message history
message_history = []

@message.on_message()
async def store_handler(event):
    """Store messages for searching"""
    user_id = event.get_user_id()
    text = event.get_text()
    
    message_history.append({
        "user_id": user_id,
        "text": text,
        "time": event.get_time()
    })
    
    # Limit the number of history records
    if len(message_history) > 1000:
        message_history.pop(0)

@command("search", help="Search messages")
async def search_handler(event):
    args = event.get_command_args()
    
    if not args:
        await event.reply("Please enter a search keyword")
        return
    
    keyword = " ".join(args)
    results = []
    
    # Search through history
    for msg in message_history:
        if keyword in msg["text"]:
            results.append(msg)
    
    if not results:
        await event.reply("No matching messages found")
        return
    
    # Display results
    result_text = f"Found {len(results)} matching messages:\n\n"
    for i, msg in enumerate(results[:10], 1):  # Show at most 10 results
        result_text += f"{i}. {msg['text']}\n"
    
    await event.reply(result_text)
```

## Image Processing

### Image Download and Storage

```python
from ErisPulse.Core import client

@message.on_message()
async def image_handler(event):
    """Handle image messages"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            if file_url:
                # Recommended to use the SDK built-in client to download images
                resp = await client.get(file_url)
                if resp.status == 200:
                    image_data = await resp.read()
                    
                    # Save to file
                    filename = f"images/{event.get_time()}.jpg"
                    with open(filename, "wb") as f:
                        f.write(image_data)
                    
                    sdk.logger.info(f"Image saved: {filename}")
                    await event.reply("Image saved")
```

### Image Recognition Example

> **Note**: The following example uses a placeholder API address. Please replace it with your own image recognition service when using it.

```python
from ErisPulse.Core import client

@command("identify", help="Identify image")
async def identify_handler(event):
    """Identify images in the message"""
    message_segments = event.get_message()
    
    for segment in message_segments:
        if segment.get("type") == "image":
            file_url = segment.get("data", {}).get("file")
            
            # Call the image recognition API
            result = await _identify_image(file_url)
            
            await event.reply(f"Recognition result: {result}")
            return
    
    await event.reply("No image found")

async def _identify_image(url):
    """Call the image recognition API (example) - Use the SDK built-in client"""
    resp = await client.post(
        "https://api.example.com/identify",
        json={"url": url}
    )
    data = await resp.json()
    return data.get("description", "Recognition failed")
```

## What's Next

- **Function is ready, want to run it long-term**: See [Deployment Guide](../user-guide/deployment.md), Docker / systemd daemon and backup & upgrade
- **Want to distribute your own function to others**: Start from [Module Development Introduction](../developer-guide/modules/getting-started.md), upgrade your script to an installable module
- **Need to adjust configuration or troubleshoot "module not responding"**: Check [Configuration File Description](../user-guide/configuration.md) and [Scope](../advanced/scope.md)

## IDE 补全

> 来源: `docs/en/getting-started/ide-completion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/getting-started/ide-completion.md）

# Type Stub Generation (IDE Completion)

> [!TIP]
> **When to read this**: If IDE completion doesn't surface an adapter's platform-specific methods (such as Yunhu's `Board`) or a module's custom methods, simply run the `epsdk types` command to generate type stubs; otherwise, skip this.

ErisPulse dynamically discovers modules/adapters via entry-points, so the concrete types of user classes cannot be known statically from entry points.
The `epsdk types` command scans installed modules/adapters and generates a type stub file, allowing users to use these types as variable annotations and thereby get IDE completion.

## Core Design Principles

Stub files **export only types** and provide no runtime instances:

- All imports are under ``TYPE_CHECKING``, **zero runtime overhead, no behavior changes**
- Type names use PascalCase form of entry-point names (e.g., ``yunhu`` → ``Yunhu``), matching the names passed to ``sdk.adapter.get()`` / ``sdk.module.get()``
- Users use ``sdk.module.get(...)`` / ``sdk.adapter.get(...)`` as usual to get instances in their code, only using imported types for **variable annotations**

## Basic Usage

Run the following command in the project root directory:

```bash
epsdk types
```

This will generate `_ep_types.py` in the current directory, containing types for all installed modules/adapters.

## Using in Code

```python
from _ep_types import MyModule, Yunhu
from ErisPulse import sdk

# By using the imported types as variable annotations, IDE will provide completion for the class's methods
my_mod: MyModule = sdk.module.get("MyModule")
my_mod.hello()                  # ← IDE completes hello

my_adapter: Yunhu = sdk.adapter.get("yunhu")
await my_adapter.Send.To("group", "123").Board(...)   # ← Completes platform-specific methods
```

## How It Works

1. Scan `erispulse.adapter` / `erispulse.module` entry-points
2. Inspect each adapter/module's actual class information (including module path and qualified name) within the target Python environment via a subprocess
3. Generate a `.py` file, where:
   - All `from xxx import Yyy as Zzz` statements are included under `TYPE_CHECKING`
   - `Zzz` is the PascalCase form of the entry-point name
4. The IDE reads the `TYPE_CHECKING` section to provide code completion; no code is executed at runtime

Example of generated stubs:

```python
# _ep_types.py (auto-generated)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Adapters
    from MyAdapter.Core import MyAdapter as MyAdapter
    from YunhuAdapter.Core import YunhuAdapter as Yunhu

    # Modules
    from MyModule.Core import Main as MyModule

    __all__ = ['MyAdapter', 'Yunhu', 'MyModule']
```

## Command Options

| Option | Description |
|--------|-------------|
| `-o, --output PATH` | Specify the output file path (default: `./_ep_types.py`) |
| `--force` | Overwrite existing stub files |
| `--adapters-only` | Scan only adapters |
| `--modules-only` | Scan only modules |

## When to Regenerate

- After installing/uninstalling new modules or adapters
- After modules/adapters update their public APIs
- When IDE auto-completion fails or types are outdated

## Relationship with SendDSL Standard Methods

The `SendDSL` base class already has built-in standard sending methods (Text/Image/Voice/Video/File), and any instance of `SendDSL` obtained through any method can complete these methods.  
The `types` command is mainly used to complete **platform-specific methods** (such as `Board` for Yunhu, `Dice` for Sandbox) and **module-specific methods**.
