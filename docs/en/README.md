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

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)