# Migration Guide: From AstrBot to ErisPulse

> [!TIP]
> **When to read this**: Read this when you already have an AstrBot robot and want to migrate it to ErisPulse. For new setups, see [Quick Start](../quick-start.md) directly.

First, the conclusion: **Platform integration, models, personality, and knowledge bases can be transferred; AstrBot plugins cannot be transferred**—the plugin APIs are completely different between the two platforms, and plugins need to be rewritten according to the ErisPulse module specifications. Data will not be automatically migrated.

## Concept Comparison

| In AstrBot | In ErisPulse | Explanation |
|---|---|---|
| Platform Adapters (QQ/WeChat/Telegram…) | [Platform Adapters](../platform-guide/README.md) | The concept is consistent; install the corresponding adapter for ErisPulse. |
| LLM Provider (API Key, Model) | [QvQChat](../ecosystem/qvqchat.md) Model Pool | Both support OpenAI-compatible integration; QvQChat supports model pool self-healing and difficulty routing. |
| Persona | QvQChat Persona System | System prompt + opening remarks + tool whitelists, manually migrated. |
| Knowledge Base | QvQChat Knowledge Base | Worldbook-style keyword triggers + vector retrieval, requires re-importing. |
| WebUI | [Dashboard](../ecosystem/dashboard.md) | Module start/stop, configuration, logs, event monitoring; QvQChat also has a separate control panel. |
| Plugin | Module | Different APIs, requires rewriting (see below). |
| Admin/Whitelist | Three-dimensional [Scope](../advanced/scope.md) + module-specific permissions (e.g., QvQChat `admins`) | More granular permission model, configured per module. |

## Migration Steps

1. **Set up the framework**: Initialize the project according to [Quick Start](../quick-start.md) (either Docker or pip is fine), and install the Dashboard.
2. **Connect to the platform**: `epsdk install` the platform adapter you previously used (install the OneBot adapter for QQ ecosystem, the Telegram adapter for Telegram...), and the login method and protocol implementation selection are the same as in the AstrBot era.
3. **Install the agent**: `epsdk install ErisPulse-QvQChat`, and fill in the original Base URL / API Key / model name in the model pool.
4. **Migrate personality and knowledge base**: Create new personality entries one by one on the QvQChat personality page; re-import the knowledge base documents.
5. **Rewrite plugins**: Follow the comparison in the next section to translate the original plugin's "command → processing logic" into an ErisPulse module.

## Plugin Rewrite Comparison

The same plugin that responds "pong" to a received `/ping` command, with code written on both sides:

**AstrBot Plugin** (example, refer to the official AstrBot documentation):

```python
from astrbot.api.event import filter, AstrMessageEvent

@filter.command("ping")
async def ping(self, event: AstrMessageEvent):
    yield event.plain_result("pong")
```

**ErisPulse Module** (complete and runnable, see [Module Development Introduction](../developer-guide/modules/getting-started.md)):

```python
from ErisPulse.Core.Event import command

@command("ping", help="Test if the bot is online")
async def ping_handler(event):
    await event.reply("pong")
```

Key differences:

- **Event Model**: AstrBot uses platform-specific event objects; ErisPulse uses the unified OneBot12 event model, where `event.reply` / SendDSL behave consistently across all platforms.
- **Package Structure**: ErisPulse modules are standard Python packages, generated using the `epsdk create module` scaffolding tool, and published to PyPI and the module marketplace.
- **Scheduled Tasks / Storage**: Use the [Cron](../ecosystem/cron.md) module or directly use the framework's built-in storage API, without introducing third-party dependencies.

## Recommended Migration Strategy

**Parallel Dual Operation**: The ErisPulse bot first runs in a test group to verify all functionalities. Once confirmed to be complete, it switches to the main group. The account systems of both platforms are independent (each with its own protocol implementation/Token), so they do not interfere with each other, and the rollback cost is low.

> [!NOTE]
> The plugin API and feature list of AstrBot are continuously evolving. This page focuses on general concepts; to determine if a specific plugin has an equivalent in ErisPulse, first search the [Module Market](https://www.erisdev.com/#market). If not found, refer to the previous section for rewriting—most business plugins are actually shorter to implement in ErisPulse.

## Next Steps

- **Learn module development systematically**: [Getting Started with Module Development](../developer-guide/modules/getting-started.md) → [Core Concepts](../developer-guide/modules/core-concepts.md)
- **Want more detailed configuration for the AI part**: [QvQChat General Agent](../ecosystem/qvqchat.md)
- **Still hesitant about migrating**: [Comparison: AstrBot vs. LangBot](comparison-agent-platforms.md)