# ErisPulse Documentation

ErisPulse is an event-driven, modular, and asynchronous robot framework—write your business logic once and deploy it across multiple platforms such as QQ, Telegram, Kook, and Yunhu via adapters. The plugin system, hot-reloading, and a full suite of developer tools are available out of the box.

> **First time using?** Go straight to [5-Minute Quick Start](quick-start.md) — a step-by-step guide from installation to running your first robot.

---

## Choose Your Path

Based on your goals, select the corresponding learning path. Each path is arranged from basic to advanced.

> [!IMPORTANT]
> **You don't need to read all the documentation.** Most developers only need to read the **L1 Core Five** (about 1–2 hours) to independently develop 90% of features; the rest are on-demand reference materials for specific scenarios—refer to them when you encounter the corresponding needs. Each section clearly indicates "When you need to read this."
>
> **L1 Core Five**: [Module Development Introduction](developer-guide/modules/getting-started.md) → [Basic Concepts](getting-started/basic-concepts.md) → [Event Wrapper](developer-guide/modules/event-wrapper.md) → [Configuration File Guide](user-guide/configuration.md) → [Exception Handling](advanced/errors.md)
>
> Adapter authors also need: [Adapter Development Introduction](developer-guide/adapters/getting-started.md) → [Event Converter](developer-guide/adapters/converter.md) → [SendDSL Guide](developer-guide/adapters/send-dsl.md)

### 1. I Want to Use a Robot

Get your robot up and running, install modules, and configure settings.

| Progress | Document | Description |
|----------|----------|-------------|
| **① Getting Started** | [5-Minute Quick Start](quick-start.md) | Installation, initialization, and running — the only starting point |
| Direct App Installation | [ErisPulse-App Client](ecosystem/app.md) | Official cross-platform client: graphical interface on mobile/PC for direct operation and management, no terminal required |
| ② Going Deeper | [Create Your First Bot](getting-started/first-bot.md) | Writing your first command handler |
| ③ Concepts | [Basic Concepts](getting-started/basic-concepts.md) | Understanding the design of adapters/modules/events |
| ④ Practical Application | [Common Task Examples](getting-started/common-tasks.md) | Storage, scheduled tasks, permission control |
| Reference | [Configuration File Guide](user-guide/configuration.md) · [CLI Commands](user-guide/cli-reference.md) · [Deployment Guide](user-guide/deployment.md) · [Upgrade and Migration Guide](user-guide/migration.md) · [FAQ](user-guide/faq.md) | Check migration actions before upgrading; consult FAQ for troubleshooting |
| Reference | [Platform-Specific Guides](platform-guide/README.md) | Differences between platforms (Yunhu/QQ/Telegram…) |
| Selection | [Selection Guide](showcase/README.md) | Comparison and migration with NoneBot2 / AstrBot / LangBot |

### 2. I Want to Develop Modules / Adapters

Write distributable extensions for ErisPulse.

| Type | Getting Started | Advanced |
|------|-----------------|----------|
| **Module Development** (Recommended) | [Module Development Introduction](developer-guide/modules/getting-started.md) | [Core Concepts](developer-guide/modules/core-concepts.md) · [Event Wrapper](developer-guide/modules/event-wrapper.md) · [Best Practices](developer-guide/modules/best-practices.md) |
| **Adapter Development** | [Adapter Development Introduction](developer-guide/adapters/getting-started.md) | [Core Concepts](developer-guide/adapters/core-concepts.md) · [SendDSL Guide](developer-guide/adapters/send-dsl.md) · [Event Converter](developer-guide/adapters/converter.md) · [Best Practices](developer-guide/adapters/best-practices.md) |
| **Technical Standards** | [Standards Overview](standards/README.md) | Adapter development must follow the [Session Types](standards/session-types.md) · [Event Conversion](standards/event-conversion.md) · [Send Methods](standards/send-method-spec.md) · [API Responses](standards/api-response.md) · [Request Actions](standards/request-action-spec.md) standards |
| **Testing and Debugging** | [Module Testing (ErisPulse-Testing)](developer-guide/testing.md) | Debugging the decision chain for "why a command didn't trigger" |
| **Publishing** | [Publishing and Module Store](developer-guide/publishing.md) | Publishing your work to PyPI and the module store |

### 3. I Want to Deeply Understand the Principles

Understand how the framework works internally. First, read the architecture and API reference, then refer to the table below to enter specialized topics.

**Architecture and API Reference**

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture.md) | Visual diagram: core architecture, initialization flow, event handling, lifecycle, module loading strategy (including `activate_on` event-driven lazy activation), local plugin folder and hot-reload architecture (supports all module sources) |
| [Event System](api-reference/event-system.md) | Complete API for five major event types |
| [Adapter System](api-reference/adapter-system.md) | Adapter registration, startup/shutdown, API calls |
| [Core Modules](api-reference/core-modules.md) | Basic capabilities such as Storage / Config / Logger / Router |

**L2 Must-Read (Essential for production-level modules)**

| Document | Description |
|----------|-------------|
| [Scope](advanced/scope.md) | Three-dimensional scope control: module availability / event access / outbound action restrictions (including fine-grained method-level rules, binding inheritance merge) |
| [Ownership System](advanced/ownership.md) | Resource ownership and automatic cleanup: owner context, resource ownership overview, unload cleanup sequence, design boundaries, and module author guide |
| [Lifecycle Management](advanced/lifecycle.md) | Lifecycle event system: what to do when modules/adapters are loaded, unloaded, reloaded, or disabled |
| [Interaction Session System](advanced/interaction.md) | Full explanation of wait_reply, session timers (remind/escalate), multi-path waiting (select), session mutual exclusion leases, inbox, message transactions, and traceability |

**By Scenario Group (Read as Needed)**

| Group | Document | Pitfalls if you don't understand the first document |
|-------|----------|--------------------------------------------------|
| Startup and Operation | [Startup Process and Manual Control](advanced/startup.md) · [Lazy Loading](advanced/lazy-loading.md) | Without understanding the startup chain (Finder / Loader / Manager / Router), you can only stare at the log when a module fails to load |
| Communication and Connection | [Module Communication](advanced/module-communication.md) · [Connection Pool and Broadcast](advanced/connections.md) · [Routing System](advanced/router.md) | Without understanding service contracts (`meta.services` whitelist), cross-module `module.call` will be rejected by `ServiceNotProvidedError` without knowing the reason |
| Data Storage | [Storage Backends](advanced/storage-backends.md) · [SQL Builder](advanced/sql-builder.md) · [Network Client](advanced/client.md) | Without understanding the semantics of connection failure cooling periods, database jitter may be mistaken for "the framework is down" (actual reason: storage operations fail quickly, then automatically reconnect after cooling) |
| Message and Conversation | [Conversation Multi-turn Dialogue](advanced/conversation.md) · [Session Inbox](advanced/transcript.md) · [MessageBuilder](advanced/message-builder.md) · [Internationalization](advanced/i18n.md) | Without understanding session mutual exclusion leases, two modules waiting for the same user's reply will kick each other out |
| Performance Monitoring | [Performance Benchmarking and Optimization](advanced/performance.md) | Without checking benchmark numbers before deployment, capacity planning relies on guesswork; without doing regression comparisons after upgrades, performance degradation won't be noticed |
| Shadow and Gray Release | [Shadow Modules and Gray Promotion](advanced/shadow.md) | Without understanding five isolation gates, prematurely promoting a shadow module will leak its outbound messages to real users |

**Concept Relationship Table**

When confused about which subsystem manages what, refer to this table:

| Subsystem | Answers What Question | One-Sentence Mnemonic |
|-----------|-----------------------|-----------------------|
| [Communication](advanced/module-communication.md) (module-communication) | How do modules call each other and send events? | Cross-module calls use `module.call`; only whitelisted methods can be called if the other party declares `meta.services` |
| [Scope](advanced/scope.md) (scope) | Who can use this module, trigger events, or execute actions? | Three gates—module binding, identity access, and outbound restrictions—all determined by user configuration |
| [Ownership](advanced/ownership.md) (ownership) | What happens to connections, timers, and subscriptions when a module unloads? | Whoever registers is the owner; unloading means automatic cleanup, leaving no dangling resources |
| [Lazy Loading and Dormancy](advanced/lazy-loading.md) (lazy-loading) | When does a module actually load, and where does it go when idle? | `activate_on` wakes up when needed; `dormant_after` goes dormant when idle |
| [Interaction](advanced/interaction.md) (interaction) | How to wait for the user's next reply and write multi-turn collection? | `wait_reply` waits for one reply; `.got()` chains collect multiple replies, leases ensure no conflicts |
| [Shadow Gray Release](advanced/shadow.md) (shadow) | How can a new module test run without affecting production? | Shadow receives copies, outbound messages are only recorded; `promote` is confirmed by a person before promotion |
| [Storage](advanced/storage-backends.md) (storage-backends) | Where is data stored, and how do backends switch? | Same storage API, sqlite / mysql / postgres configuration switching |

### 4. Ecosystem and Official Client

Official client + ecosystem modules (not built-in features) that can be installed as needed and are ready to use.

| Document | Description |
|----------|-------------|
| [Ecosystem Overview](ecosystem/README.md) | How to install ecosystem modules and why these are not built-in features |
| [ErisPulse-QvQChat](ecosystem/qvqchat.md) | General-purpose intelligent agent module: tool loops / MCP / long-term memory / knowledge base; modules declaring services automatically become AI tools |
| [ErisPulse-ApiMCP](ecosystem/apimcp.md) | Expose the robot as an MCP tool in reverse, allowing AI clients like Claude to directly control it |
| [ErisPulse-App](ecosystem/app.md) | Official cross-platform client (Android / Windows / Linux / macOS): native interface to manage multiple instances, **run directly on mobile**, desktop tray always on |
| [ErisPulse Workbench](ecosystem/workbench.md) | Unified account center: module catalog and authentication, `plugin-xxx.erisdev.com` hosting domain, access tokens and OAuth login integration (online service, no installation required) |
| [ErisPulse Dashboard](ecosystem/dashboard.md) | Web management panel + view registration API (modules can register custom pages in the sidebar) |
| [ErisPulse-Cron](ecosystem/cron.md) | Scheduled task module: one-time / interval / Cron expressions, callback parameters, SQLite persistence, other modules can host scheduled callbacks |
| [ErisPulse-Takumi](ecosystem/takumi.md) | Image rendering (HTML / node tree / SVG / animation, built-in Chinese and English fonts) |

### 5. I Want to Contribute to ErisPulse

Make the framework better

| Document | Description |
|----------|-------------|
| [Contribute to ErisPulse](contributing/README.md) | Overview of contribution methods: documentation / i18n / Bug / module / adapter |
| [First Contribution](contributing/first-contribution.md) | From fork to submitting a PR |

---

## Advanced Features Version Quick Reference

When making version compatibility judgments or taking over an old project and wanting to know "which version introduced this capability," refer to this table (based on the [CHANGELOG.md](https://github.com/ErisPulse/ErisPulse/blob/main/CHANGELOG.md) in the repository root).

| Version | Introduced Capability |
|---------|-----------------------|
| **2.7** | Production-ready foundation: standardized OneBot12 base class (`ApiDSL` / `BaseConverter`), systematic configuration hot-update, graceful shutdown and SIGTERM/SIGHUP signal handling, environment variable configuration override, lifecycle callback hooks, lazy-loaded web stack; 2.7.1 fixes reliability of configuration writes and GC generational governance |
| **2.8** | Permission and communication framework: three-dimensional scope system (scope), infrastructure for interactive sessions (leases/checkpoints/message transactions/session inbox transcript), protocolized module-to-module RPC (`module.call` / `meta.services` service contract / directed event emit(to=)), multi-backend asynchronous storage (sqlite / mysql / postgres, connection failures don't block the framework), ownership cleanup, preserved configuration comments; subsequent 2.8.x versions refine CLI scaffolding, subcommands, etc. |
| **2.9** | "Module Development Experience" mainline (EPRFC-2026-001): declarative command parameters (`args=` / `options=`) and command governance (`cooldown=` / `rate_limit=`), unified dependency injection (`Depends`), middleware event veto power, built-in ORM (automatic migration + relationship mapping), shadow module gray promotion, distribution decision chain tracing and diagnostic troubleshooting, official support for Python 3.14 |
| **2.10** | "Connections as First-Class Resources" (`connections` registry: broadcast / business groups / cross-module transfer/reuse / automatic cleanup on unload), root import contract (all common APIs can be `from ErisPulse import`), complete ownership system, runtime-overridable inbox retention policies; 2.10.2 adapter local plugin directory (`plugins/`) + `epsdk create pack` + tomlclass lossless configuration writes |
| **2.11** (dev) | "Edit code → See effect" development loop: default full hot-reload semantics (syntax pre-check + code identity verification + cascading re-import of dependents), lazy loading and dormancy (`dormant_after`), adapter code-level hot-reload (`sdk.adapter.reload`), `.got()` command flow syntax sugar, `epsdk stop` / `restart` runtime control |
| **2.12** (dev) | Lifecycle governance and operability: nested lifecycle (`ownership.nest()`), fine-grained hot-reload (single module/single adapter determination, framework source code changes trigger process restart), background task pending queue, event distribution chain account auto-binding (`send_context` / `api_context` / `request_context` same口径, multi-account modules require zero changes), cross-account duplicate handling linkage (`framework.cross_account_policy`), shadow module whl ingestion and persistent promotion closure, container `epsdk restart` soft restart within process, `SendDSL.Location()` |

## Development Methods

ErisPulse supports two development methods:

- **Module Development (Recommended)**: Create a separate module package and install it via a package manager, which is convenient for distribution and management.
- **Embedded Development**: Write handlers directly in the project, suitable for rapid prototyping. See [Quick Start](quick-start.md).

## Other

- [Documentation Style Guide](styleguide/docstring.md) — Writing guidelines for contributing documentation
- [Contribute to ErisPulse](contributing/README.md) — Entry point for project collaboration
- [AI-Assisted Development](ai-support/README.md) — Project prompts for AI programming assistants

## Get Help

- GitHub Repository: [https://github.com/ErisPulse/ErisPulse](https://github.com/ErisPulse/ErisPulse)
- Issue Reporting: Submit an Issue
- Technical Discussion: View Discussions

## Related Links

- [OneBot12 Standard](https://12.onebot.dev/)
- [Yunhu Official Documentation](https://www.yhchat.com/document/)
- [Telegram Bot API](https://core.telegram.org/bots/api)