# Terminal Platform Features Documentation

TerminalAdapter is a command-line terminal adapter—the terminal acts as a chat session, used for quickly debugging module logic locally.

---

## Document Information

- Corresponding module version: 1.2.2
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform Overview: Treats the local command line as a chat session, where stdin input serves as messages and module replies are printed directly to the terminal
- Adapter Name: TerminalAdapter
- Platform Identifier: `terminal`
- Single-account design (for local debugging scenarios)
- Framework Requirement: Soft dependency on `ErisPulse>=2.7.1` (runtime detection with a prompt, not enforced)

## Configuration

```toml
[Terminal]
bot_id = "terminal_bot"    # User ID of the bot
bot_name = "TerminalBot"   # Bot nickname
user_id = "terminal_user"  # ID of the simulated user (the end user chatting with the bot)
user_name = "User"         # Nickname of the simulated user
prompt = "> "              # Input prompt
reply_prefix = "[Bot] "    # Line prefix for bot replies (leave empty for no prefix)
echo_input = false         # Whether to echo user input (enable for piped input scenarios)
```

## v5 Paradigm Update (1.1.0)

- **spawn_background task ownership**: The stdin reading loop now uses `runtime.spawn_background`
- **Framework soft dependency**: Runtime detection of `ErisPulse>=2.7.1` with a prompt; version log output at startup

## Standardization Alignment (1.2.2)

The response structure and error codes follow the [API Response Specification](../standards/api-response.md).

### message_id Added to Message Events

stdin message events now include the standard top-level `message_id` field (generated via uuid), allowing modules to reliably reference terminal messages for replies/deduplication.

### Send Inherits BaseAdapter.Send

`Send` inherits the framework's `BaseAdapter.Send`; **the standard decorator chain (`At` / `AtAll` / `Reply`, etc.) now takes effect**, with decorator segments rendered together with text segments in the output; `node` (merged forward) segments are degraded to plain-text raw output (no content is lost).

### Meta Actions Completed

Standard meta actions have been fully implemented and return standard responses:

| Action | data Content |
|------|----------|
| `get_status` | `enabled` (running state) / `boot_time` (boot timestamp) |
| `get_version` | `impl` (TerminalAdapter) / `version` / `onebot_version` |
| `get_supported_actions` | List of supported action names |

```python
from ErisPulse import sdk
terminal = sdk.adapter.get("terminal")

result = await terminal.Api.get_status()
result = await terminal.Api.get_version()
result = await terminal.Api.get_supported_actions()
result = await terminal.Api.get_self_info()    # user_id/user_name
result = await terminal.Api.get_user_info("terminal_user")
result = await terminal.Api.get_friend_list()
```

### delete_message Capability Fallback Semantics Corrected

The terminal has no message recall capability: `delete_message` has been corrected from "returning success" to the **standard capability-fallback semantics**—it returns `retcode=10002` (unsupported operation), so modules can detect the fallback accordingly.

### Error Code Specification

| retcode | Meaning | Description |
|---------|------|------|
| 0 | Success | — |
| 10002 | Unsupported | Group operations, message recall, unimplemented standard actions |

## Usage Instructions

```python
# The module simply listens for messages as usual
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("Received: " + event.get_text())
```

- Text entered in the terminal is treated as user messages, supporting multiple lines (terminated by an empty line)
- Event structure example (stdin message):

```json
{
  "id": "<uuid>",
  "time": 1700000000,
  "message_id": "<uuid>",
  "type": "message",
  "detail_type": "private",
  "platform": "terminal",
  "self": {"platform": "terminal", "user_id": "terminal_bot", "user_name": "TerminalBot"},
  "user_id": "terminal_user",
  "message": [{"type": "text", "data": {"text": "Input content"}}],
  "alt_message": "Input content",
  "terminal_raw": {"text": "Input content"},
  "terminal_raw_type": "stdin_line"
}
```

- Send example (decorator chains are supported):

```python
terminal = sdk.adapter.get("terminal")

await terminal.Send.To("private", "terminal_user").Text("Hello")
await terminal.Send.To("private", "terminal_user").At("terminal_user").Text("Message with decorator")
await terminal.Send.To("private", "terminal_user").Raw_ob12([
    {"type": "text", "data": {"text": "OneBot12 segment"}}
])
```

- Suitable for quickly verifying module logic during development, without connecting to a real platform