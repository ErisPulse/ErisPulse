# Comparison: ErisPulse vs NoneBot2

> [!TIP]
> **When to read this**: Read this when you'll be writing code in Python bot frameworks and are choosing between NoneBot2 and ErisPulse. Skip it if you won't be coding.

Positioning differences in one sentence:

- **NoneBot2**: The async bot framework with the deepest plugin ecosystem, a mature event-handling model, and over a decade of community accumulation
- **ErisPulse**: A bot SDK built around the OneBot12 unified event model; a single handler naturally works across platforms, with module-level hot reloading and ecosystem service contracts as native design

Both are frameworks where "developers write code", not install-and-go products.

## Design Differences Comparison

| Dimension | ErisPulse | NoneBot2 |
|---|---|---|
| Cross-platform approach | OneBot12 unified event model is built into the core; handlers need not be aware of platform differences | Each adapter has its own event model; cross-platform support relies on unified message abstraction plugins (e.g., alconna) |
| Plugin system | Modules = PyPI packages + `epsdk` CLI installation + [Module Market](https://www.erisdev.com/#market) indexing | Plugins = PyPI packages (`nonebot-plugin-*`), discovered via the store website, installed with pip |
| Send API | SendDSL chained sending: mentions, replies, retries, timeouts, and batching all done in one line | Matcher-side `send` / per-adapter APIs; unified message abstraction provided by plugins |
| Hot reload | Module/adapter-level hot reload; changes take effect on save without restarting the process | Full process reload in dev mode (file changes restart the process) |
| AI integration | Zero AI dependencies in the framework; modules that declare service contracts automatically become tools for the [QvQChat](../ecosystem/qvqchat.md) agent; [ApiMCP](../ecosystem/apimcp.md) can expose the bot in reverse to MCP clients such as Claude | Assembled on demand via community plugins |
| Management tools | Official [Dashboard](../ecosystem/dashboard.md) web panel, `epsdk` CLI, ErisPulse-App mobile client | Community WebUI plugins, nb-cli |
| Production features | Three-dimensional scoping, automatic ownership reclamation, shadow-module gray release, inter-module RPC service contracts | Dependency injection, hook system, community solutions |
| Storage | Unified KV + SQL API (switch between sqlite/mysql/postgres via configuration) | Each plugin chooses its own solution |

## When to Choose Which

**Choose NoneBot2**: You need a specific plugin that already exists in its ecosystem; or your team is deeply familiar with its event model. The existing plugin inventory is a hard advantage — other differences can be compensated for with code, but the ecosystem cannot.

**Choose ErisPulse**: Cross-platform consistency is your core requirement (unified event model + 16 platform adapters); you want a "modify code without restarting" development rhythm; you want module capabilities to go directly into the AI toolbox instead of wiring up the LLM separately.

> [!NOTE]
> This comparison is compiled from the public documentation of both projects. It is an objective fact that NoneBot2's plugin ecosystem and community are significantly larger; for decision-making purposes, please refer to [their official documentation](https://nonebot.dev/).

---

## Next Steps

- **Want to see what it's like to write with ErisPulse**: [5-Minute Quick Start](../quick-start.md)
- **Want to understand the details of the unified event model**: [Basic Concepts](../getting-started/basic-concepts.md)
- **Comparing all-in-one platforms like "group AI assistants"**: [Comparison: AstrBot vs LangBot](comparison-agent-platforms.md)