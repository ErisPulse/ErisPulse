# ErisPulse-ApiMCP: Control Your Bot with AI Clients

> [!TIP]
> **When to read this**: Read this when you want MCP-capable AI clients such as Claude Desktop to directly operate your bot—sending messages, viewing messages, invoking modules, managing adapters, and observing event streams. Skip it otherwise.

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) exposes the bot's runtime capabilities to AI clients via **MCP (Model Context Protocol)**: once installed, 14 new tools appear in Claude Desktop, allowing the AI to send and receive messages on your behalf, troubleshoot module issues, and subscribe to group chat events—turning the bot from "a program you manage" into "the AI's hands and eyes".

> [!IMPORTANT]
> ApiMCP must be installed separately, and the bridge only becomes active after a **token is explicitly configured**:
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> Set `token = "long-random-string"` in the `[ApiMCP]` section of `config.toml` (or use the environment variable `ERISPULSE_APIMCP_TOKEN`). When not configured, all endpoints return 503 except the health check, preventing silent token leakage.

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

## The 14 Tools at a Glance

| Category | Tools | Description |
|---|---|---|
| Module | `list_modules` / `get_module_info` / `call_module` / `reload_module` | View and invoke public services of installed modules, and trigger hot reload |
| Adapter | `list_adapters` / `get_adapter_status` / `reload_adapter` | Platform online status; adapter reload is disabled by default |
| Message | `send_message` / `recent_messages` | Send text/images/audio/video/files to any platform; review recent messages via [transcript](../advanced/transcript.md) |
| Event | `subscribe_events` / `unsubscribe` / `poll_events` | Subscribe to events such as messages/notifications, with a ring buffer (1000 entries by default) and incremental polling |
| Runtime | `get_topology` / `sdk_health` | Runtime topology (sanitized) and health summary |

A typical usage: the AI first calls `subscribe_events(["message"])`, then periodically runs `poll_events` to observe what's being discussed in the group, and decides whether to chime in via `send_message` or use `call_module` to trigger a module's capability.

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