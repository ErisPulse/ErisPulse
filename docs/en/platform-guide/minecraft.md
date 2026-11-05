# Minecraft Platform Features Documentation

MinecraftAdapter is a Minecraft Java Edition server adapter based on the RCON protocol, supporting command execution, message sending, and log event listening.

---

## Documentation Info

- Corresponding module version: 0.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform overview: Minecraft Java Edition server bot (via the RCON remote console)
- Adapter name: MinecraftAdapter
- Multi-server support: Supported (one server per account, automatic reconnection on disconnect)
- Connection method: RCON TCP persistent connection (keep-alive + exponential backoff reconnection)
- Event listening: Log tail (optional, chat/join/leave)
- Chain modifier support: Supports chain modifier methods such as `.At()`
- OneBot12 compatibility: `text` segment only (RCON cannot send media)

## Server Prerequisite Configuration

`server.properties`:

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_rcon_password
```

## Configuration

```toml
[MinecraftAdapter.accounts.default]
host = "127.0.0.1"             # RCON server address
port = 25575                   # RCON port
password = "your_rcon_password"
bot_id = ""                    # Defaults to the account name if left empty
enable_log_tail = false        # Enable log listening (chat/join/leave events)
log_path = "logs/latest.log"   # Log file path
poll_interval = 1.0            # Log scan interval (seconds)
enabled = true
```

**Configuration Options (per account):**

- `host` / `port` / `password`: RCON endpoint (required)
- `bot_id`: Bot identifier in events (defaults to the account name), also used as the `group_id` for server-wide broadcasts
- `enable_log_tail`: Log event switch (disabled by default). When disabled, the adapter operates in pure command mode (send only, no events generated)
- `log_path`: Log file path. Requires the adapter and the server to **run on the same machine**, or the log directory to be mounted; supports log rotation (automatically resets the read position after latest.log rotation)
- `poll_interval`: Log scan interval (seconds, minimum 0.2)

## Message Sending

All send methods return a Task; awaiting it yields the standard response (see "Send Method Return Values").

### Basic Sending

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# Single-player message (tellraw plain text)
await mc.Send.To("user", "Steve").Text("Hello Steve")

# Server-wide broadcast (say)
await mc.Send.To("server", "myserver").Text("Server broadcast")
```

### Chain Modifier Methods

```python
# @player (rendered inline as the player name in tellraw)
await mc.Send.To("server", "myserver").At("Steve").Text(" Check this out")
```

### Multi-Server Sending

```python
await mc.Send.Using("server2").To("server", "s2").Text("From the second server")
```

### Supported and Unsupported Message Segments

| Segment | Supported | Description |
|---------|-----------|-------------|
| `text` | Supported | Concatenated and converted to tellraw / say depending on the target type |
| `mention` | Supported | Rendered inline as the player name |
| `reply` | Partially supported | Accepted, but Minecraft has no quoted display |
| `image` / `audio` / `video` / `file` | Not supported | Returns `retcode=10002` and lists the segment types |

### Target Types

| target_type | Behavior |
|-------------|----------|
| `user` | `tellraw <player_name> {"text":"..."}` visible only to that player |
| `server` / `group` | `say <content>` server-wide broadcast (group_id is bot_id) |

## Standard API Actions (Api)

```python
from ErisPulse import sdk
mc = sdk.adapter.get("minecraft")

# Online player list (parses the output of the `list` command)
result = await mc.Api.get_player_list()       # {"players": ["Steve", "Alex"], "raw": "..."}

# Connection status
result = await mc.Api.get_status()            # {"status": "ok", "connected": true}

# Server identity
result = await mc.Api.get_self_info()         # {user_id, user_name, host}

# Version
result = await mc.Api.get_version()

# Multi-server
result = await mc.Api.Using("server2").get_player_list()
```

### Supported Standard Actions

| Method | Description | Data Source |
|--------|-------------|-------------|
| `get_status()` | RCON connection status | Local |
| `get_self_info()` | Server identity (bot_id/account name/host:port) | Local |
| `get_player_list()` | Online player list (parses the output of the `list` command) | RCON |
| `get_version()` | Adapter version | Local |

### Platform Extension Actions

Execute arbitrary RCON commands via `Api.exec(cmd)` (equivalent to `call_api("exec", command=...)`):

```python
# Whitelist management
await mc.Api.exec("whitelist add Alex")
await mc.Api.exec("whitelist remove Alex")

# Server management
await mc.Api.exec("time set day")
await mc.Api.exec("weather clear")
await mc.Api.exec("op Alex")
await mc.Api.exec("kick Steve")

# Data and scoreboard
await mc.Api.exec("scoreboard objectives add kills deathCount")
```

> **Security Reminder**: `Api.exec` carries full server console privileges (including stop/deop, etc.); do not expose unauthenticated entry points to untrusted callers.

### Unsupported Standard Actions

The following standard actions have no corresponding RCON capability; calls return `retcode=10002` or `33001` (not connected):

- `delete_message` (Minecraft has no message recall)
- `get_friend_list` / `get_group_list` (use `get_player_list` instead)

### Generic Action Entry

```python
# send_message: equivalent to the Send chain
result = await mc.call_api(
    "send_message",
    _account_id="default",
    target_type="user", target_id="Steve",
    message=[{"type": "text", "data": {"text": "hi"}}],
)
```

## Send Method Return Values

```python
{
    "status": "ok",                  # ok / failed
    "retcode": 0,                    # 0 = success; 33001 = not connected/execution failed; 10002 = unsupported
    "data": {"command_output": "..."},  # RCON command echo
    "self": {"platform": "minecraft", "user_id": "mc1"},
    "message_id": "uuid",            # Generated message identifier (tellraw/say have no real message ID)
    "message": "",
    "minecraft_raw": {"output": "..."}
}
```

## Event Types (enable_log_tail = true)

Detect with `platform == "minecraft"` before using these platform features. **The RCON protocol cannot receive chat events** (it is a pure request-response protocol); the event side relies on log listening.

### Event Mapping

| Server Log Line | Adapter Event | Description |
|-----------------|---------------|-------------|
| `[12:34:56] [...]: <Steve> Hello` | message (`detail_type: server`) | Player chat |
| `[12:35:00] [...]: Alex joined the game` | notice (`detail_type: server_joined`) | Player joined |
| `[12:36:00] [...]: Alex left the game` | notice (`detail_type: server_left`) | Player left |

### Event Field Example

```python
# Chat
{
  "id": "uuid",
  "time": 1793277000,
  "type": "message",
  "detail_type": "server",
  "platform": "minecraft",
  "self": {"platform": "minecraft", "user_id": "mc1", "user_name": "mc1", "account_id": "default"},
  "user_id": "Steve",                      # Player name
  "message": [{"type": "text", "data": {"text": "Hello world"}}],
  "alt_message": "Hello world",
  "group_id": "mc1",                       # bot_id
  "minecraft_raw": {"line": "[12:34:56] [Server thread/INFO]: <Steve> Hello world"},
  "minecraft_raw_type": "log_line"
}

# Join (notice)
{
  "type": "notice",
  "detail_type": "server_joined",          # or server_left
  "user_id": "Alex",
  "operator_id": "Alex",
  "group_id": "mc1",
  "minecraft_raw": {"line": "..."},
  "minecraft_raw_type": "log_line"
}
```

### Echo Deduplication

The echo of `say` / `tellraw` commands is also written to the log. The adapter records a content fingerprint at send time (30-second window); when the same content appears in the log, emission is skipped to prevent messages sent by the bot from looping back as received events.

## Notes

1. **RCON cannot receive chat events**: A limitation of the protocol itself (pure request-response); log listening must be enabled for the event side
2. **Log path accessibility**: The adapter and the server must run on the same machine, or the log directory must be mounted (mount `logs/` in container scenarios)
3. **Log format**: Relies on the default format of vanilla / mainstream server implementations (Paper, Fabric, etc.); plugins that modify the log format (e.g., custom chat plugins) may fail to be parsed
4. **RCON concurrency limit**: Minecraft RCON processes commands serially over a single connection; the adapter has built-in locking and keep-alive (an empty command every 30 seconds)
5. **Echo deduplication window**: Identical content is emitted only once within 30 seconds
6. **Security**: `Api.exec` carries console-level privileges; do not expose it to untrusted callers