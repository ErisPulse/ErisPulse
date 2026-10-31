# Terminal Platform Features Documentation

TerminalAdapter is a command-line terminal adapter—where the terminal serves as a chat session, enabling rapid local debugging of module logic.

---

## Documentation Information

- Corresponding Module Version: 1.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Introduction: Treat the local command line as a chat session, where stdin input is a message, and module responses are directly printed to the terminal
- Adapter Name: TerminalAdapter
- Platform Identifier: `terminal`
- Single account design (for local debugging scenarios)
- Framework Requirements: Soft dependency `ErisPulse>=2.7.1` (runtime detection prompts, not enforced)

## Configuration Description

```toml
[Terminal]
bot_id = "terminal_bot"   # Sandbox bot ID
bot_name = "Terminal"     # Display name
```

## v5 Paradigm Update (1.1.0)

- **spawn_background Task Ownership**: The stdin reading loop now uses `runtime.spawn_background`.
- **Framework Soft Dependency**: Runtime checks for `ErisPulse>=2.7.1` and provides a warning; version logs are output on startup.

## Usage Instructions

```python
# The module can listen to messages as usual
from ErisPulse.Core.Event import message

@message.on_message()
async def handle(event):
    if event.get("platform") == "terminal":
        await event.reply("Received: " + event.get_text())
```

- Text entered in the terminal is treated as user messages and supports multi-line input (terminated by an empty line)
- Suitable for quickly verifying module logic during development, without needing to connect to a real platform