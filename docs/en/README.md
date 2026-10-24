# ErisPulse Documentation

ErisPulse is an event-driven, modular, and asynchronous robot framework—write your business logic once, deploy it across multiple platforms (such as QQ, Telegram, Kook, Yunhu) via adapters, and benefit from a plugin system, hot reload, and a fully featured developer toolchain out of the box.

> **New to ErisPulse?** Start with the [5-Minute Quick Start](quick-start.md) — a step-by-step guide from installation to running your first robot.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is ordered from basic to advanced.

> [!IMPORTANT]
> **You don't need to read all the documentation.** Most developers only need to read the **L1 Core Five** (about 1–2 hours) to independently develop 90% of features; the rest are optional references for specific scenarios—consult them when needed, as each section begins with "When to read this."

**L1 Core Five**: [Module Development Introduction](developer-guide/modules/getting-started.md) → [Basic Concepts](getting-started/basic-concepts.md) → [Event Wrapper Class](developer-guide/modules/event-wrapper.md) → [Configuration File Guide](user-guide/configuration.md) → [Exception Handling](advanced/errors.md)

For adapter authors: [Adapter Development Introduction](developer-guide/adapters/getting-started.md) → [Event Converter](developer-guide/adapters/converter.md) → [SendDSL Explained](developer-guide/adapters/send-dsl.md)

### I. I Want to Use a Robot

Get a robot running, install modules, and configure it.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](quick-start.md) | Installation, initialization, and running — the only starting point |
| Direct App Installation | [ErisPulse-App Client](ecosystem/app.md) | Official cross-platform client: run and manage directly via graphical interface on mobile / desktop, no terminal required |
| ② Deep Dive | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand adapter/module/event design |
| ④ Practical | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences between platforms (Yunhu / QQ / Telegram…) |

### II. I Want to Develop Modules / Adapters

Develop extensions for ErisPulse that can be distributed.

| Type | Getting Started | Advanced |
|------|-----------------|----------|
| **Module Development** (Recommended) | [Module Development Introduction](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper Class](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Introduction](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Explained](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Adapter development must follow [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Method Spec](standards/send-method-spec.md) · [API Response](standards/api-response.md) · [Request Action Spec](standards/request-action-spec.md) standards |
| **Testing & Debugging** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Debugging the decision chain for "why a command didn't trigger" |
| **Publishing** | [Publishing & Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### III. I Want to Understand the Core Architecture

Understand how the framework works internally. Start with the architecture and API reference, then consult the following table for specialized topics.

**Architecture & API Reference**

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagram: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and hot reload architecture (supports all module sources) |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |

**L2 Must-Read (Essential for Production-Level Modules)**

| Document | Description |
|----------|-------------|
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event access / outbound action restrictions (including method-level fine-grained rules, binding inheritance merge) |
| [Ownership System](advanced/ownership.md) | Resource ownership and automatic cleanup: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Lifecycle Management](advanced/lifecycle.md) | Lifecycle event system: what to do when modules / adapters are loaded, unloaded, reloaded, or disabled |
| [Interaction Session System](advanced/interaction.md) | Full explanation of wait_reply, session timers (remind/escalate), multi-path waiting (select), session mutual exclusion leases, inbox, message transactions, and trace links |

**By Scenario (Consult as Needed)**

| Group | Document | Pitfall if You Don't Understand the First Document |
|-------|----------|--------------------------------------------------|
| Startup & Execution | [Startup Process & Manual Control](advanced/startup.md) · [Lazy Loading](advanced/lazy-loading.md) | Without understanding the startup chain (Finder / Loader / Manager / Router), you'll be clueless when module loading fails |
| Communication | [Inter-Module Communication](advanced/module-communication.md) · [Connection Pool & Broadcast](advanced/connections.md) · [Routing System](advanced/router.md) | Without understanding service contracts (`meta.services` whitelist), cross-module `module.call` will be rejected by `ServiceNotProvidedError` without explanation |
| Data Storage | [Storage Backends](advanced/storage-backends.md) · [SQL Builder](advanced/sql-builder.md) · [HTTP Client](advanced/http-client.md) | Without understanding the semantics of connection failure cooldown, you'll mistakenly think the framework crashed when the database is unstable (in reality, storage operations fail quickly and reconnect automatically after cooldown) |
| Message Conversation | [Conversation Multi-Turn Dialogue](advanced/conversation.md) · [Session Inbox](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [Internationalization](advanced/i18n.md) | Without understanding session mutual exclusion leases, two modules waiting for the same user's reply will interfere with each other |
| Shadow Gray Release | [Shadow Modules & Gray Promotion](advanced/shadow.md) | Without understanding the five isolation gates, premature promotion will cause shadow module outbound messages to leak to real users |

**Conceptual Relationship Table**

When unsure which subsystem manages what, refer to this table:

| Subsystem | Answers What Question | One-Sentence Mnemonic |
|-----------|----------------------|-----------------------|
| [Communication](advanced/module-communication.md) (module-communication) | How do modules call each other and send events to specific targets? | Use `module.call` for cross-module calls; only methods declared in `meta.services` can be called |
| [Scope](advanced/scope.md) (scope) | Who can use this module, trigger events, and execute actions? | Three gates—module binding, identity access, and outbound restrictions—all determined by user configuration |
| [Ownership](advanced/ownership.md) (ownership) | Where do connections, timers, and subscriptions go after a module is unloaded? | Whoever registers, owns; unload means cleanup, no dangling resources |
| [Lazy Loading & Dormancy](advanced/lazy-loading.md) (lazy-loading) | When does a module load, and where does it go when idle? | Wakes up only when `activate_on` is used; goes dormant after `dormant_after` |
| [Interaction](advanced/interaction.md) (interaction) | How to wait for the user's next reply and write multi-turn collection? | `wait_reply` waits for one message; `.got()` chains collect multiple, leases ensure no conflicts |
| [Shadow Gray Release](advanced/shadow.md) (shadow) | How can a new module run in parallel without affecting the live environment? | Shadow receives copies, outbound messages are recorded only; `promote` is confirmed by humans before promotion |
| [Storage](advanced/storage-backends.md) (storage-backends) | Where is data stored, and how to switch backends? | Same storage API, sqlite / mysql / postgres can be configured and switched |

### IV. Ecosystem & Official Clients

Official clients and optional, ready-to-use ecosystem modules (none of these are built-in features).

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules and why these are not built-in features |
| [ErisPulse-App](ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray icon |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages to the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-time / interval / Cron expressions, callback parameters, SQLite persistence, other modules can host scheduled callbacks |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### V. I Want to Contribute to ErisPulse

Help improve the framework.

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / bug reports / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

## Advanced Features Version Quick Reference

When determining version compatibility or inheriting an old project and wanting to know "which version introduced this feature," refer to this table (based on the [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) in the repository root).

| Version | Introduced Features |
|---------|---------------------|
| **2.7** | Production-ready base: standardized OneBot12 base class (`ApiDSL` / `BaseConverter`), systematic configuration hot update, graceful shutdown and SIGTERM/SIGHUP signal handling, environment variable configuration override, lifecycle callback hooks, lazy-loaded web stack; 2.7.1 fixes reliability of configuration writes and GC generational governance |
| **2.8** | Permission and communication infrastructure: three-dimensional scope system (`scope`), interaction session infrastructure (leases / checkpoints / message transactions / session inbox `transcript`), inter-module RPC protocol (`module.call` / `meta.services` service contract / targeted event `emit(to=)`), multi-backend asynchronous storage (sqlite / mysql / postgres, connection failures don't block the framework), ownership cleanup, configuration comment retention; subsequent 2.8.x versions refine CLI scaffolding, subcommands, etc. |
| **2.9** | "Module Development Experience" mainline (EPRFC-2026-001): declarative command parameters (`args=` / `options=`) and command governance (`cooldown=` / `rate_limit=`), unified dependency injection (`Depends`), middleware event veto power, built-in ORM (automatic migration + relationship mapping), shadow module gray promotion, distribution decision chain tracing and diagnostic troubleshooting, official support for Python 3.14 |
| **2.10** | "Connection as a first-class resource" (`connections` registry: broadcast / business groups / cross-module reusable transfer / automatic cleanup on unload), root import contract (all common APIs can be `from ErisPulse import`), completion of ownership system, runtime overridable inbox retention policies; 2.10.2 adds local adapter plugin directory (`plugins/`) + `epsdk create pack` + tomlclass lossless configuration writes |
| **2.11** (dev) | "Code changes → see effects" development loop: default full hot reload semantics (syntax pre-check + code identity verification + cascaded re-import of dependents), lazy loading and dormancy (`dormant_after`), code-level hot reload for adapters (`sdk.adapter.reload`), `.got()` command flow syntax sugar, `epsdk stop` / `restart` runtime control |

## Development Approaches

ErisPulse supports two development approaches:

- **Module Development (Recommended)**: Create independent module packages, install via package manager, suitable for distribution and management.
- **Embedded Development**: Write handlers directly within the project, suitable for rapid prototyping. See [Quick Start](quick-start.md).

## Other

- [Documentation Style Guide](styleguide/docstring.md) — Writing guidelines for contributing documentation
- [Contribute to ErisPulse](contributing/README.md) — Entry point for contributing to the project
- [AI-Assisted Development](ai-support/README.md) — Project prompts for AI programming assistants

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Report Issues: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

**English** | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)