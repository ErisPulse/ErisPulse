# ErisPulse-ApiMCP: Control Your Bot with AI Clients

> [!TIP]
> **When to read this**: Read this when you want MCP-capable AI clients such as Claude Desktop to directly control your bot—sending messages, reading messages, calling modules, managing adapters, observing event streams. Skip it otherwise.

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) exposes the bot's runtime capabilities to AI clients through **MCP (Model Context Protocol)**: once installed, 17 new tools appear in Claude Desktop, and the AI can send and receive messages on your behalf, troubleshoot module issues, subscribe to group chat events, and search the framework documentation—turning the bot from "a program you manage" into "the AI's hands and eyes."

> [!IMPORTANT]
> ApiMCP requires separate installation, and the bridge is only enabled after **explicitly configuring a token**:
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> Set `token = "<long random string>"` in the `[ApiMCP]` section of `config.toml` (or via the `ERISPULSE_APIMCP_TOKEN` environment variable). When not configured, all endpoints return 503 except the health check, preventing silent token leakage.

## How It Works

A two-layer architecture, with no AI dependencies introduced into the bot itself:

- **Inside the bot process**: The ApiMCP module mounts a REST bridge on the framework's built-in HTTP server (`/apimcp/*`, token authentication, default rate limit of 30 requests/minute)
- **Independent process**: The `erispulse-apimcp` command starts a stdio server using the official `mcp` SDK, forwarding MCP tool calls to the bot's HTTP bridge

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► Bot Process REST Bridge ──► sdk.*
```

When the bot is offline or the bridge is not configured, tools return readable errors with troubleshooting guidance instead of throwing stack traces.

## Claude Desktop Integration

Edit `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\`; macOS: `~/Library/Application Support/Claude/`):

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "your-token"
      }
    }
  }
}
```

After saving, fully restart Claude Desktop. The integration is successful once the `erispulse` server appears in the tool list. Any client that supports MCP stdio servers (Claude Code, Cursor, etc.) can connect in the same way.

## Overview of the 17 Tools

| Category | Tools | Description |
|---|---|---|
| Module | `list_modules` / `get_module_info` / `call_module` / `reload_module` | View and call the public services of installed modules, trigger hot reload |
| Adapter | `list_adapters` / `get_adapter_status` / `reload_adapter` | Platform online status; adapter reload is disabled by default |
| Message | `send_message` / `recent_messages` | Send text/images/audio/video/files to any platform; in multi-bot deployments, use `account` to specify the sending account; review recent messages via [transcript](../advanced/transcript.md) |
| Event | `subscribe_events` / `unsubscribe` / `poll_events` | Subscribe to events such as messages/notifications, with a ring buffer (1000 entries by default) and incremental polling |
| Docs | `search_erispulse_docs` / `read_erispulse_doc` / `refresh_erispulse_docs` | Search and read the ErisPulse framework documentation; a standalone docs engine that downloads and caches docs by framework version, without depending on other modules |
| Runtime | `get_topology` / `sdk_health` | Runtime topology (sanitized) and health summary |

A typical use case: the AI first calls `subscribe_events(["message"])`, then periodically polls `poll_events` to observe what is being discussed in a group chat, and decides whether to `send_message` to join the conversation or `call_module` to trigger a module's capability. When unsure how to use a certain framework feature, the AI can also call `search_erispulse_docs` to check the documentation first before taking action.

## Security Essentials

- **The token grants full control**: it can read messages, send messages, and call whitelisted module methods. Never commit it to the repository or post it in public channels; in multi-tenant scenarios, split into multiple bot instances
- **Least privilege**: use `module_call_whitelist` to narrow the callable modules (supports precise `module.method` format for exact allowlisting), `send_target_whitelist` to narrow send targets (e.g., only allowing a specific group), and keep `allow_adapter_reload` disabled by default
- **Listen on localhost only**: when used only on the local machine, set the framework HTTP server to `server.host = "127.0.0.1"`; cross-machine access must use an intranet + reverse proxy with TLS
- Output is sanitized at the key-name level (key/path-type keys are dropped entirely); deep sanitization is the module's own responsibility—do not enable subscriptions for sensitive sessions

For the complete configuration options (buffer capacity, backtrack window, event type whitelist, etc.) and detailed REST endpoints, see the [project README](https://github.com/wsu2059q/ErisPulse-ApiMCP).

---

## Next Steps

- **Want the AI to come "alive" in group chats rather than just being remotely controlled**: QvQChat is the forward direction—the agent proactively chats and gets work done, see [QvQChat General Agent](qvqchat.md); ApiMCP is the reverse direction—external AI controlling the bot. Both can be installed together
- **Want to know where the recent message data comes from**: [Conversation Inbox transcript](../advanced/transcript.md)
- **Want to learn about the bot's HTTP server**: [Routing System](../advanced/router.md)