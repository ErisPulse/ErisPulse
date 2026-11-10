# ErisPulse Documentation

ErisPulse is an event-driven, modular asynchronous bot framework — write your business code once, then deploy to QQ, Telegram, Kook, Yunhu, and many other platforms via adapters. The plugin system, hot reloading, and a complete developer toolchain work out of the box.

> **First time here?** Head straight to the [5-Minute Quick Start](quick-start.md) — from installation to running your first bot, all in one go.

---

## Choose Your Path

Depending on your goal, choose the corresponding learning path. Within each path, content is ordered from basic to advanced.

> [!IMPORTANT]
> **You do not need to read all the documentation.** The vast majority of developers can
> independently develop 90% of features just by reading the **five L1 core articles** in order
> (about 1–2 hours); all remaining documentation is on-demand reference material for specific
> scenarios—consult it only when you encounter the corresponding need. Each article states
> at its beginning "when you need to read this article".
>
> **Five L1 core articles**: [Module Development Getting Started](developer-guide/modules/getting-started.md)
> → [Basic Concepts](getting-started/basic-concepts.md)
> → [Event Wrapper Classes](developer-guide/modules/event-wrapper.md)
> → [Configuration File Reference](user-guide/configuration.md)
> → [Exception Handling](advanced/errors.md)
>
> Adapter authors additionally need: [Adapter Development Getting Started](developer-guide/adapters/getting-started.md)
> → [Event Converters](developer-guide/adapters/converter.md)
> → [SendDSL in Detail](developer-guide/adapters/send-dsl.md)

### 1. I Want to Use a Bot

Get the bot running, install modules, and make configurations.

| Progress | Document | Description |
|------|------|------|
| **① Get Started** | [5-Minute Quick Start](quick-start.md) | Installation, initialization, running — the single entry point |
| App Direct Install | [ErisPulse-App Client](ecosystem/app.md) | Official all-platform client: run and manage directly via graphical interface on mobile / desktop, no terminal needed |
| ② Go Deeper | [Create Your First Bot](getting-started/first-bot.md) | Write your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understand the design of adapters/modules/events |
| ④ Practice | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Reference](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) | Consult as needed |
| Reference | [Platform Features Guide](platform-guide/README.md) | Differences across platforms (Yunhu/QQ/Telegram…) |
| Selection | [Selection Guide](showcase/README.md) | Comparison with and migration from NoneBot2 / AstrBot / LangBot |

### 2. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|------|------|
| **Module Development** (recommended) | [Module Development Getting Started](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper Classes](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Getting Started](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL in Detail](developer-guide/adapters/send-dsl.md) · [Event Converters](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Standards that adapter development must follow: [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) |
| **Testing & Troubleshooting** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Trace the dispatch decision chain to find out "why a command didn't trigger" |
| **Publishing** | [Publishing & Module Store](developer-guide/publishing.md) | Publish your work to PyPI and the Module Store |

### 3. I Want to Deeply Understand the Internals

Understand how the framework works internally. Start with the architecture and API reference, then dive into specific topics using the tables below.

**Architecture & API Reference**

| Document | Description |
|------|------|
| [Architecture Overview](architecture.md) | Visual diagrams: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folders, and module hot-reload architecture (supports all module sources) |
| [Event System](api-reference/event-system.md) | Complete API for the five major event categories |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, start/stop, API calls |
| [Core Modules](api-reference/core-modules.md) | Storage / Config / Logger / Router and other foundational capabilities |

**L2 Must-Read (Unavoidable for Production-Grade Modules)**

| Document | Description |
|------|------|
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event admission / outbound action restrictions (including method-level fine-grained rules and binding inheritance merge) |
| [Ownership (owner) System](advanced/ownership.md) | Resource ownership and automatic reclamation: owner context, full picture of owned resources, unload cleanup sequence, design boundaries, and module author guide |
| [Lifecycle Management](advanced/lifecycle.md) | Lifecycle event system: what modules / adapters should do when loaded, unloaded, reloaded, or disabled |
| [Interactive Session System](advanced/interaction.md) | Complete guide to wait_reply, session timers (remind/escalate), multi-way waiting (select), session mutex leases, inbox, message transactions, and traceability |

**Grouped by Scenario (Consult as Needed)**

| Group | Documents | Pitfalls if You Skip the First Article |
|------|------|------|
| Startup & Boot | [Startup Flow & Manual Control](advanced/startup.md) · [Lazy Loading](advanced/lazy-loading.md) | Without understanding the startup chain (Finder / Loader / Manager / Router), you'll be left staring blankly at logs when module loading fails |
| Communication & Connections | [Inter-Module Communication](advanced/module-communication.md) · [Connection Pools & Broadcasting](advanced/connections.md) · [Routing System](advanced/router.md) | Without understanding the service contract (`meta.services`) whitelist, cross-module `module.call` will be rejected with `ServiceNotProvidedError` and you won't know why |
| Data Storage | [Storage Backends](advanced/storage-backends.md) · [SQL Builder](advanced/sql-builder.md) · [Network Client](advanced/client.md) | Without understanding the cooldown semantics for connection failures, database instability may lead you to wrongly conclude "the framework crashed" (in fact, storage operations fail fast and automatically reconnect after cooldown) |
| Messaging & Conversation | [Conversation Multi-Turn Dialogues](advanced/conversation.md) · [Session Inbox](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [Internationalization](advanced/i18n.md) | Without understanding session mutex leases, two modules waiting for the same user's reply simultaneously will kick each other out |
| Performance & Observability | [Performance Benchmarks & Tuning](advanced/performance.md) | Skip the benchmark numbers before deployment and capacity planning is pure guesswork; skip regression comparison after upgrades and performance degradation goes unnoticed |
| Shadow & Canary | [Shadow Modules & Canary Promotion](advanced/shadow.md) | Promote a shadow module early without understanding the five isolation gates, and its outbound messages will leak to real users |

**Concept Relationship Master Table**

When you can't tell which subsystem handles what, use this table to find your way:

| Subsystem | What Question It Answers | One-Line Mnemonic |
|--------|------------|-----------|
| [Communication](advanced/module-communication.md) (module-communication) | How do modules call each other and send targeted events? | Cross-module calls go through `module.call`; if the target declares `meta.services`, only whitelisted methods can be called |
| [Permissions](advanced/scope.md) (scope) | Who can use a module, who can trigger events, and which actions can be performed? | Three gates—module binding, identity admission, and outbound restrictions—all dictated by user configuration |
| [Ownership](advanced/ownership.md) (ownership) | After a module unloads, where do its connections, timers, and subscriptions go? | Whoever registers owns it; unloading reclaims everything, leaving no dangling resources |
| [Lazy Loading & Dormancy](advanced/lazy-loading.md) (lazy-loading) | When does a module actually load, and where does it go when idle? | `activate_on` wakes it only when needed; `dormant_after` puts it back to sleep when idle |
| [Interaction](advanced/interaction.md) (interaction) | How to wait for the user's next reply, and how to write multi-turn collection? | `wait_reply` waits for one; `.got()` chains collect multiple turns; leases guarantee no conflicts |
| [Shadow & Canary](advanced/shadow.md) (shadow) | How to trial-run a new module version without affecting production? | The shadow receives copies and outbound actions are only logged; `promote` requires human confirmation before going official |
| [Storage](advanced/storage-backends.md) (storage-backends) | Where is data stored, and how do you switch backends? | One storage API; switch between sqlite / mysql / postgres via configuration |

### 4. Ecosystem & Official Client

Official client plus ecosystem modules that are installed on demand and work out of the box (none of them are built-in framework features).

| Document | Description |
|------|------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules, and why these aren't built-in features |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | General-purpose agent module: tool loop / MCP / long-term memory / knowledge base; modules declaring services automatically become AI tools |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | Exposes the bot in reverse as MCP tools, letting AI clients like Claude control it directly |
| [ErisPulse-App](ecosystem/app.md) | Official all-platform client (Android / Windows / Linux / macOS): manage multiple instances via native UI, **runs directly on mobile**, resides in the desktop tray |
| [ErisPulse-Dashboard](ecosystem/dashboard.md) | Web management panel + view registration API (modules can register custom pages in the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-time / interval / cron expressions, callback parameters, SQLite persistence; other modules can delegate scheduled callbacks to it |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, with built-in Chinese and English fonts) |

### 5. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|------|------|
| [Contributing to ErisPulse](contributing/README.md) | Overview of ways to contribute: documentation / i18n / bugs / modules / adapters |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

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