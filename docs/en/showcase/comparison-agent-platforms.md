# Comparison: ErisPulse vs. AstrBot / LangBot

> [!TIP]
> **When to read this**: When you're looking for an "AI assistant in a group chat" and are choosing between integrated platforms like AstrBot / LangBot and ErisPulse, read this. For writing non-AI business code, see [Comparison: NoneBot2](comparison-nonebot.md).

A one-sentence summary of the differences:

- **AstrBot / LangBot**: An integrated AI chatbot platform—install, configure your Key, start chatting, with LLM conversations at the core of the product.
- **ErisPulse**: A bot framework/SDK—AI is just one of the pluggable modules ([QvQChat](../ecosystem/qvqchat.md)), and the framework itself can also handle non-AI business logic.

All three can ultimately deliver an "AI that works in a group chat," but their paths and ceilings differ.

## Comparison

| Dimension | ErisPulse + QvQChat | AstrBot / LangBot |
|---|---|---|
| Getting Started Experience | Initialize project + install adapter + install QvQChat + configure model pool, about 10 minutes | Install + configure Key and ready to use, faster |
| Platform Coverage | 16 platform adapters (including Yunhu, email, terminal, Webhook bridge) | Mainstream IM platforms |
| LLM Support | OpenAI-compatible model pool (self-healing, failover, difficulty routing), MCP client | Built-in access to multiple providers |
| AI Depth | Tool loops + sub-agents + long-term memory/user profiles + knowledge base + computer operation sandbox + scheduled "plan-execute-review" | Conversations, personality, knowledge base, plugin tools |
| Ecosystem Integration | Any ErisPulse module declaring a service automatically becomes an AI tool; adding/removing modules increases/decreases AI capabilities | Install corresponding plugins to extend AI capabilities |
| Reverse Openness | [ApiMCP](../ecosystem/apimcp.md) exposes the bot as an MCP tool, allowing AI clients like Claude to directly control it | — |
| Hot Reload | Module/adapter level, changes take effect on save | Plugin updates usually require a restart |
| Non-AI Business | Framework-native: command system, multi-turn conversations, ORM, scheduled tasks, message statistics, each module is independent | Platform is AI conversation-centric; non-AI capabilities depend on plugins |
| Management Panel | Dashboard (modules/config/logs/events + third-party window registration), mobile App, AI Builder | Built-in WebUI |
| Community Size | Relatively young, ecosystem growing | Larger user base, more third-party plugins |

## When to Choose Which

**Choose AstrBot / LangBot**: You just want to quickly use AI chat, don't plan to write business code, and don't need integration with niche platforms (such as Yunhu). They are mature, all-in-one solutions.

**Choose ErisPulse**: The bot needs to do more than just AI (such as scheduled push, group management, message statistics, bridging...), and you want AI to be just one of the modular components; or you care about the hot-reload development rhythm, the module market distribution method, and the ecosystem synergy of "installing an AI module adds one more capability"; or you need ApiMCP, a reverse channel that allows external AI to control the bot.

> [!NOTE]
> This comparison is based on the public documentation of both parties; it is an objective fact that AstrBot / LangBot has a larger user base and more plugins. For decisions, please refer to the [official documentation of AstrBot](https://astrbot.app/) / ([LangBot](https://docs.langbot.app/)).

## Next Steps

- **Coming from AstrBot**: [Migration Guide: From AstrBot to ErisPulse](migrate-from-astrbot.md)
- **Want to see what AI looks like on ErisPulse directly**: [QvQChat General-Purpose Agent](../ecosystem/qvqchat.md)
- **Want to get it running quickly**: [5-Minute Quick Start](../quick-start.md)