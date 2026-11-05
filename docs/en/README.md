# ErisPulse Documentation

ErisPulse is an event-driven, modular asynchronous bot framework — write your business code once, then deploy to QQ, Telegram, Kook, Yunhu, and many other platforms via adapters. The plugin system, hot reloading, and a complete developer toolchain work out of the box.

> **First time here?** Head straight to the [5-Minute Quick Start](quick-start.md) — from installation to running your first bot, all in one go.

---

## Choose Your Path

Choose the learning path that matches your goal. Within each path, content is ordered from basic to advanced.

> [!IMPORTANT]
> **You don't need to read all the docs.** The vast majority of developers only need to read the **five L1 core docs**
> in order (about 1–2 hours) to independently develop 90% of features; all remaining docs are on-demand
> reference material for specific scenarios — consult them only when the corresponding need arises. Each doc states
> at the beginning "when you need to read this one".
>
> **The five L1 core docs**: [Module Development Getting Started](developer-guide/modules/getting-started.md)
> → [Basic Concepts](getting-started/basic-concepts.md)
> → [Event Wrapper](developer-guide/modules/event-wrapper.md)
> → [Configuration File Guide](user-guide/configuration.md)
> → [Exception Handling](advanced/errors.md)
>
> Adapter authors additionally need: [Adapter Development Getting Started](developer-guide/adapters/getting-started.md)
> → [Event Converter](developer-guide/adapters/converter.md)
> → [SendDSL in Depth](developer-guide/adapters/send-dsl.md)

### 1. I Want to Use a Bot

Get the bot running, install modules, and configure it.

| Stage | Document | Description |
|------|------|------|
| **① Get Started** | [5-Minute Quick Start](quick-start.md) | Install, initialize, run — the single starting point |
| Direct App Install | [ErisPulse-App Client](ecosystem/app.md) | Official all-platform client: run and manage via phone / desktop GUI, no terminal needed |
| ② Go Deeper | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters / modules / events |
| ④ Hands-On | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences across platforms (Yunhu/QQ/Telegram…) |
| Selection | [Selection Guide](showcase/README.md) | Comparison with NoneBot2 / AstrBot / LangBot and migration |

### 2. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|------|------|
| **Module Development** (recommended) | [Module Development Getting Started](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL in Depth](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | The [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Response](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) standards that adapter development must follow |
| **Testing & Troubleshooting** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Use the dispatch decision chain to troubleshoot "why didn't the command trigger" |
| **Publishing** | [Publishing & Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the module store |

### 3. I Want to Understand the Internals

Learn how the framework works under the hood. Start with the architecture and API references, then use the comparison table below to dive into specific topics.

**Architecture & API Reference**

| Document | Description |
|------|------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folders, and module hot-reload architecture (supporting all module sources) |
| [Event System](api-reference/event-system.md) | Complete API for the five major event categories |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, start/stop, API calls |
| [Core Modules](api-reference/core-modules.md) | Storage / Config / Logger / Router and other foundational capabilities |

**L2 Required Reading (Unavoidable for Production-Grade Modules)**

| Document | Description |
|------|------|
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event admission / outbound action restriction (including method-level fine-grained rules and binding inheritance merge) |
| [Ownership (Owner) System](advanced/ownership.md) | Resource ownership and automatic reclamation: owner context, panoramic view of owned resources, unload cleanup sequence, design boundaries, and guidance for module authors |
| [Lifecycle Management](advanced/lifecycle.md) | Lifecycle event system: what modules / adapters should do when loaded, unloaded, reloaded, or disabled |
| [Interaction Session System](advanced/interaction.md) | Complete guide to wait_reply, session timers (remind/escalate), multi-way waiting (select), session mutex leases, inbox, message transactions, and chain tracing |

**Grouped by Scenario (On-Demand Reference)**

| Group | Documents | Pitfall if You Skip the First Doc |
|------|------|------|
| Startup | [Startup Flow & Manual Control](advanced/startup.md) · [Lazy Loading](advanced/lazy-loading.md) | Without understanding the startup chain (Finder / Loader / Manager / Router), you'll be left staring helplessly at the logs when module loading fails |
| Communication & Connections | [Inter-Module Communication](advanced/module-communication.md) · [Connection Pool & Broadcasting](advanced/connections.md) · [Routing System](advanced/router.md) | Without understanding the service contract (`meta.services`) whitelist, cross-module `module.call` will be rejected with `ServiceNotProvidedError` and you won't know why |
| Data Storage | [Storage Backends](advanced/storage-backends.md) · [SQL Builder](advanced/sql-builder.md) · [Network Client](advanced/client.md) | Without understanding the cooldown semantics after connection failures, you may misjudge "the framework is broken" during database flapping (in fact, storage operations fail fast and automatically reconnect after the cooldown) |
| Messaging & Conversation | [Conversation Multi-Turn Dialogue](advanced/conversation.md) · [Session Transcript](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [Internationalization](advanced/i18n.md) | Without understanding session mutex leases, two modules waiting for the same user's reply will kick each other off |
| Shadow & Canary | [Shadow Modules & Canary Promotion](advanced/shadow.md) | Promoting early without understanding the five isolation gates will let the shadow's outbound messages leak to real users |

**Concept Relationship Master Table**

When you can't tell which subsystem handles what, use this table to find the right match:

| Subsystem | What Question It Answers | One-Line Rule of Thumb |
|--------|------------|-----------|
| [Communication](advanced/module-communication.md) (module-communication) | How do modules call each other and send targeted events? | Cross-module calls go through `module.call`; if the target declares `meta.services`, only whitelisted methods can be called |
| [Permissions](advanced/scope.md) (scope) | Who can use this module, who can trigger events, and which actions can be performed? | Three gates — module binding, identity admission, outbound restriction — all decided by user configuration |
| [Ownership](advanced/ownership.md) (ownership) | After a module is unloaded, where do its connections, timers, and subscriptions go? | Whoever registers it owns it; unloading reclaims everything, leaving no dangling resources |
| [Lazy Loading & Dormancy](advanced/lazy-loading.md) (lazy-loading) | When does a module actually load, and where does it go when idle? | `activate_on` wakes it only when needed; `dormant_after` puts it back to sleep when idle |
| [Interaction](advanced/interaction.md) (interaction) | How to wait for the user's next reply, and how to write multi-turn collection? | `wait_reply` waits for one message, `.got()` chains collect multiple turns, and leases guarantee no conflicts |
| [Shadow & Canary](advanced/shadow.md) (shadow) | How to trial-run a new module version without affecting production? | The shadow receives copies and outbound traffic is only recorded; `promote` requires human confirmation before going live |
| [Storage](advanced/storage-backends.md) (storage-backends) | Where is data stored, and how do you swap backends? | One storage API; switch between sqlite / mysql / postgres via configuration |

### 4. Ecosystem & Official Clients

Official clients plus ecosystem modules that are installed on demand and ready to use out of the box (none of them are built into the framework).

| Document | Description |
|------|------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, and why these are not built-in features |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | General-purpose agent module: tool loop / MCP / long-term memory / knowledge base; modules that declare services automatically become AI tools |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | Exposes the bot in reverse as an MCP tool, letting AI clients like Claude control it directly |
| [ErisPulse-App](ecosystem/app.md) | Official all-platform client (Android / Windows / Linux / macOS): manage multiple instances with a native interface, **runs directly on your phone**, and resides in the desktop tray |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + window registration API (modules can register custom pages in the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-shot / interval / Cron expressions, callback parameters, SQLite persistence; other modules can delegate scheduled callbacks to it |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node trees / SVG / animation, with built-in Chinese and English fonts) |

### 5. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|------|------|
| [Contributing to ErisPulse](contributing/README.md) | Overview of contribution channels: docs / i18n / bugs / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

## Advanced Features Version Quick Reference

When making version compatibility checks, or when taking over an old project and wondering "which version introduced this capability", look it up in this table (for authoritative details, see the version entries in the repository root [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md)).

| Version | Capabilities Introduced |
|------|-----------|
| **2.7** | Production-grade foundation: OneBot12 standardized base classes (`ApiDSL` / `BaseConverter`), systematic config hot-reloading, graceful shutdown and SIGTERM/SIGHUP signal handling, environment variable config overrides, lifecycle callback hooks, and lazy loading of the web stack; 2.7.1 added config write reliability and generational GC governance |
| **2.8** | Permission and communication skeleton: the three-dimensional scope system, interaction session infrastructure (leases / checkpoints / message transactions / session transcript inbox), protocol-based inter-module RPC (`module.call` / `meta.services` service contracts / targeted events via emit(to=)), multi-backend async storage (sqlite / mysql / postgres; connection failures don't block the framework), ownership cleanup, and config comment preservation; subsequent 2.8.x releases polished the CLI scaffolding, subcommands, and more |
| **2.9** | The "module development experience" mainline (EPRFC-2026-001): declarative command parameters (`args=` / `options=`) and command governance (`cooldown=` / `rate_limit=`), unified dependency injection (`Depends`), middleware event veto, built-in ORM (automatic migration + relational mapping), shadow module canary promotion, dispatch decision-chain tracing and troubleshooting diagnostics, and official support for Python 3.14 |
| **2.10** | Connections as first-class resources (`connections` registry: broadcasting / business grouping / cross-module passing and reuse / automatic reclamation on unload), root import contract (all common APIs importable via `from ErisPulse import`), completion of the ownership system, and runtime override of inbox retention policies; 2.10.2 added adapter local plugin directories (`plugins/`) + `epsdk create pack` + lossless config writing via tomlclass |
| **2.11** (dev) | The "edit code → see the effect" development loop: hot reload with full semantics by default (syntax pre-check + code identity verification + cascaded re-export for dependents), lazy-load dormancy (`dormant_after`), adapter code-level hot reload (`sdk.adapter.reload`), `.got()` command-flow syntax sugar, and `epsdk stop` / `restart` runtime control |

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