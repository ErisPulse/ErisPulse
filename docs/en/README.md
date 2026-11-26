# ErisPulse Documentation

ErisPulse is an event-driven, modular asynchronous bot framework — write your business code once, then deploy to QQ, Telegram, Kook, Yunhu, and many other platforms via adapters. The plugin system, hot reloading, and a complete developer toolchain work out of the box.

> **First time here?** Head straight to the [5-Minute Quick Start](quick-start.md) — from installation to running your first bot, all in one go.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is arranged from basic to advanced.

> [!IMPORTANT]
> **You don't need to read all documents.** Most developers can independently develop 90% of the features by reading the **L1 Core Five** in sequence (about 1–2 hours); the rest are on-demand reference materials for specific scenarios — consult them when you encounter the corresponding needs, and each document starts with a note indicating "when you need to read this."
>
> **L1 Core Five**: [Getting Started with Module Development](developer-guide/modules/getting-started.md) → [Basic Concepts](getting-started/basic-concepts.md) → [Event Wrapper](developer-guide/modules/event-wrapper.md) → [Configuration File Guide](user-guide/configuration.md) → [Exception Handling](advanced/errors.md)
>
> Adapter authors also need: [Getting Started with Adapter Development](developer-guide/adapters/getting-started.md) → [Event Converter](developer-guide/adapters/converter.md) → [SendDSL Explained](developer-guide/adapters/send-dsl.md)

### 1. I Want to Use the Bot

Get the bot running, install modules, and configure.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](quick-start.md) | Installation, initialization, and running — the only entry point |
| Direct App Installation | [ErisPulse-App Client](ecosystem/app.md) | Official multi-platform client: run and manage directly via mobile/desktop GUI, no terminal required |
| ② Deep Dive | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practical Use | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) · [Upgrade Migration Guide](user-guide/migration.md) · [FAQ](user-guide/faq.md) | Verify migration actions before upgrading; check FAQ for troubleshooting |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences among platforms (Yunhu/QQ/Telegram…) |
| Selection | [Selection Guide](showcase/README.md) | Comparison and migration from NoneBot2 / AstrBot / LangBot |

### 2. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|-----------------|----------|
| **Module Development** (Recommended) | [Getting Started with Module Development](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Getting Started with Adapter Development](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Explained](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Adapter development must follow [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) standards |
| **Testing & Debugging** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Debugging the decision chain for "why a command wasn't triggered" |
| **Publishing** | [Publishing & Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### 3. I Want to Deeply Understand the Principles

Understand how the framework works internally. Start with the architecture and API reference, then enter specific topics according to the table below.

**Architecture & API Reference**

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual chart: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and module hot-reload architecture (supports all module sources) |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |

**L2 Must-Read (Essential for Production-Level Modules)**

| Document | Description |
|----------|-------------|
| [Scopes (scope)](advanced/scope.md) | Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level fine-grained rules, binding inheritance merge) |
| [Ownership (owner) System](advanced/ownership.md) | Resource ownership and automatic cleanup: owner context, full view of owned resources, unload cleanup sequence, design boundaries, and module author guide |
| [Lifecycle Management](advanced/lifecycle.md) | Lifecycle event system: what to do when modules/adapters are loaded, unloaded, reloaded, or disabled |
| [Interactive Session System](advanced/interaction.md) | Full explanation of `wait_reply`, session timers (remind/escalate), multi-path waiting (select), session mutual exclusion leases, inbox, message transactions, and trace links |

**Grouped by Scenario (Read as Needed)**

| Group | Documents | Pitfalls if You Don't Understand the First Document |
|-------|-----------|-----------------------------------------------------|
| Startup & Operation | [Startup Process and Manual Control](advanced/startup.md) · [Lazy Loading](advanced/lazy-loading.md) | Without understanding the startup chain (Finder / Loader / Manager / Router), you can only stare at logs when module loading fails |
| Communication | [Inter-Module Communication](advanced/module-communication.md) · [Connection Pool & Broadcasting](advanced/connections.md) · [Routing System](advanced/router.md) | Without understanding service contracts (`meta.services` whitelist), cross-module `module.call` will be rejected by `ServiceNotProvidedError` without explanation |
| Data Storage | [Storage Backends](advanced/storage-backends.md) · [SQL Builder](advanced/sql-builder.md) · [Network Client](advanced/client.md) | Without understanding the semantics of connection failure cooling periods, database fluctuations will be misinterpreted as "framework failure" (actually, storage operations fail quickly and automatically reconnect after cooling) |
| Messaging | [Conversation Multi-turn Dialogue](advanced/conversation.md) · [Session Inbox](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [Internationalization](advanced/i18n.md) | Without understanding session mutual exclusion leases, two modules waiting for the same user's reply will interfere with each other |
| Performance Monitoring | [Performance Benchmarking & Tuning](advanced/performance.md) | Without checking benchmark numbers before deployment, capacity planning is guesswork; without regression comparisons after upgrades, performance degradation goes unnoticed |
| Shadow & Gradual Rollout | [Shadow Modules & Gradual Promotion](advanced/shadow.md) | Without understanding the five isolation gates, early promotion will cause shadow module outbound messages to leak into real users |

**Concept Relationship Table**

When you can't tell which subsystem manages what, use this table to match:

| Subsystem | Answers What Questions | One-Sentence Mnemonic |
|-----------|------------------------|-----------------------|
| [Communication](advanced/module-communication.md) (module-communication) | How do modules call each other and send events? | Cross-module calls use `module.call`; only whitelisted methods can be called if the other side declares `meta.services` |
| [Permissions](advanced/scope.md) (scope) | Who can use this module, trigger events, and execute actions? | Three gates — module binding, identity access, and outbound restrictions — all determined by user configuration |
| [Ownership](advanced/ownership.md) (ownership) | Where do connections, timers, and subscriptions go after a module is unloaded? | Whoever registers belongs, unloading means recycling, leaving no dangling resources |
| [Lazy Loading & Dormancy](advanced/lazy-loading.md) (lazy-loading) | When does a module load, and where does it go when idle? | Wakes up only when `activate_on` is used, goes dormant after `dormant_after` |
| [Interaction](advanced/interaction.md) (interaction) | How to wait for the user's next reply, and how to write multi-turn collection? | `wait_reply` waits for one message, `.got()` chains collect multiple turns, leases ensure no conflicts |
| [Shadow & Gradual Rollout](advanced/shadow.md) (shadow) | How can a new module run in trial without affecting production? | Shadows receive copies, outbound only logs, `promote` is confirmed by humans before going live |
| [Storage](advanced/storage-backends.md) (storage-backends) | Where is data stored, and how to switch backends? | Same storage API, switch between sqlite / mysql / postgres via configuration |

### 4. Ecosystem & Official Clients

Official clients + on-demand installed, plug-and-play ecosystem modules (none are built-in features of the framework).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, and why these are not built-in features |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | General-purpose intelligent agent module: tool loops / MCP / long-term memory / knowledge base; modules declaring services automatically become AI tools |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | Expose the bot as an MCP tool in reverse, allowing AI clients like Claude to directly control it |
| [ErisPulse-App](ecosystem/app.md) | Official multi-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **runs directly on mobile**, desktop tray always present |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + view registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-time / interval / Cron expressions, callback parameters, SQLite persistence, other modules can host scheduled callbacks |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### 5. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bugs / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

## Advanced Features Version Quick Reference

When making version compatibility checks, or when taking over a legacy project and wondering "which version introduced this capability," look it up in this table (based on the version entries in the repository root [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)).

| Version | Capabilities Introduced |
|------|-----------|
| **2.7** | Production-ready foundation: OneBot12 standardized base classes (`ApiDSL` / `BaseConverter`), systematized configuration hot-reload, graceful shutdown with SIGTERM/SIGHUP signal handling, environment variable configuration overrides, lifecycle callback hooks, lazy loading of the web stack; 2.7.1 adds configuration write reliability and GC generational tuning |
| **2.8** | Permission and communication skeleton: three-dimensional scoping system (scope), interactive session infrastructure (lease / checkpoint / message transaction / session inbox transcript), protocol-based inter-module RPC (`module.call` / `meta.services` service contracts / targeted events emit(to=)), multi-backend async storage (sqlite / mysql / postgres, connection failures do not block the framework), ownership cleanup, configuration comment preservation; subsequent 2.8.x releases polish CLI scaffolding, subcommands, and more |
| **2.9** | "Module development experience" mainline (EPRFC-2026-001): declarative command parameters (`args=` / `options=`) and command governance (`cooldown=` / `rate_limit=`), unified dependency injection (`Depends`), middleware event veto power, built-in ORM (auto migration + relational mapping), shadow module canary-to-official promotion, dispatch decision-chain tracing and troubleshooting diagnostics, official support for Python 3.14 |
| **2.10** | Connections as first-class resources (`connections` registry: broadcast / business grouping / cross-module passing and reuse / automatic reclamation on uninstall), root import contract (all commonly used APIs importable via `from ErisPulse import`), ownership system completion, runtime override of inbox retention policy; 2.10.2 adds adapter-local plugin directory (`plugins/`) + `epsdk create pack` + tomlclass lossless configuration writes |
| **2.11** (dev) | "Edit code → see results" development loop: hot-reload default full semantics (syntax pre-check + code identity verification + cascading re-export for dependents), lazy-load dormancy (`dormant_after`), adapter code-level hot reload (`sdk.adapter.reload`), `.got()` command-flow syntactic sugar, `epsdk stop` / `restart` runtime control |
| **2.12** (dev) | Lifecycle governance and operability: nested lifecycles (`ownership.nest()`), fine-grained hot reload (per-module/per-adapter determination, framework source changes trigger a process restart), background task pending queue, automatic account binding in the event dispatch chain (`send_context` / `api_context` / `request_context` with the same criteria, zero changes for multi-account modules), cross-account duplicate acceptance correlation (`framework.cross_account_policy`), shadow module whl ingestion and persistent-promotion closed loop, in-container `epsdk restart` in-process soft restart, `SendDSL.Location()` |

## Development Approaches

ErisPulse supports two development approaches:

- **Module development (recommended)**: create standalone module packages installed via a package manager, making distribution and management easy.
- **Embedded development**: write handlers directly in your project, suitable for rapid prototyping. See the [Quick Start](quick-start.md) for details.

## Other

- [Documentation Style Guide](styleguide/docstring.md) — writing conventions for contributing documentation
- [Contributing to ErisPulse](contributing/README.md) — the entry point for getting involved in the project
- [AI-Assisted Development](ai-support/README.md) — project prompts for use with AI coding assistants

## Getting Help

- GitHub repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Bug reports: submit an Issue
- Technical discussions: check Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)