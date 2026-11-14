# Sandbox Platform Features Documentation

SandboxAdapter is the built-in sandbox adapter of ErisPulse, designed for local development and module debugging—enabling you to simulate message sending and receiving without a real platform.

---

## Document Information

- Corresponding module version: 4.2.3
- Maintainer: ErisPulse
- Last updated: 2026-11-10

## Basic Information

- Platform Overview: A local sandbox environment providing virtual users/groups, a web debug panel, and message persistence
- Adapter Name: SandboxAdapter
- Platform Identifier: `sandbox`
- Single-account design (for local debugging scenarios)
- Framework Requirement: Soft dependency on `ErisPulse>=2.7.1` (runtime detection prompt, not enforced)

## v5 Paradigm Update (4.1.0)

- **Api DSL minimal set**: `get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background task ownership**: heartbeat tasks now use `runtime.spawn_background`
- **Framework soft dependency**: detects `ErisPulse>=2.7.1` at runtime and prompts accordingly
- Import path updated to `Core.Bases` (BaseConfig)

## Standardization Alignment (4.2.3)

Response structure and error codes follow the [API Response Specification](../standards/api-response.md).

### HTML Sending Methods

- `.Html(html: str)`: Sends an HTML message (rendered to the web panel via the html channel)
- `.HTML(html: str)`: Alias for `.Html()` (consistent with standard Send method naming)

### Meta Actions (Standardized)

Standard meta actions return standard responses:

| Action | data Content |
|--------|-------------|
| `get_self_info` | `user_id` (the configured `self_id`) / `user_name` (`sandbox`) |
| `get_status` | `good` (running status) / `bots` (list of accounts) |
| `get_version` | `impl` (ErisPulse-SandboxAdapter) / `version` / `onebot_version` |
| `get_supported_actions` | List of supported action names |

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # sandbox bot identity
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_version()
result = await sandbox.Api.get_supported_actions()
```

### Request Event Handling (Request stub)

The sandbox synthesizes `type="request"` events (friend/group join requests, with `request_id` passed through from the simulated event), and modules can approve them in the standard way (see the [Request Action Specification](../standards/request-action-spec.md) for the full specification):

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    await event.approve()   # or event.reject()
```

The adapter-side Request DSL is a **simulated stub**: `accept()` / `reject()` validate the `request_id` (returning a standard error with `retcode=34001` when missing, which belongs to the request action family of error codes). After validation passes, the approval is simulated as successful and a standard success response is returned, facilitating downstream joint debugging of the `approve()` / `reject()` flow.

### Error Code Specification

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Success | — |
| 10002 | Unsupported | The platform has no corresponding capability |
| 10003 | Invalid parameters | Missing or invalid parameters |
| 10006 | Invalid message segment data | `MergeForward` nodes have no valid text content |
| 34001 | Request not found | `Request.accept()/reject()` missing `request_id` (request action family) |

## Configuration

```toml
[Sandbox]
self_id = "sandbox_bot"  # Sandbox bot ID
enable = true            # Whether to enable
```

## Usage

- The sandbox provides virtual users and groups, allowing modules to send and receive messages just like on a real platform
- The web debug panel allows you to manually send messages to trigger module processing logic
- Message data is persistently stored (`sdk.storage`) and can be restored after restart

## Supported Message Send Types

All send methods are implemented via chained syntax, for example:

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

await sandbox.Send.To("private", "user1").Text("Hello")
await sandbox.Send.To("group", "group1").Markdown("**Bold**")
```

The supported send types include:

| Method | Description |
|------|------|
| `.Text(text)` | Send a text message |
| `.Image(file, summary=None)` | Send an image |
| `.Face(face_id)` | Send an emoji |
| `.Record(file, magic=False)` | Send a voice message |
| `.Voice(file)` | Send a voice message (via the audio channel) |
| `.Video(file)` | Send a video |
| `.File(file, filename=None)` | Send a file |
| `.Html(html)` / `.HTML(html)` | Send an HTML message (the latter is an alias) |
| `.Markdown(markdown)` | Send a Markdown message |
| `.Json(json_data)` | Send a JSON card message |
| `.Xml(xml_data)` | Send an XML card message |
| `.Music(platform, id, title=None)` | Send a music message |
| `.Share(url, title, content=None, image=None)` | Send a link share |
| `.Location(lat, lon, title=None, content=None)` | Send a location message |
| `.Dice()` | Send a dice |
| `.Rps()` | Send rock-paper-scissors |
| `.Poke(user_id, type="poke")` | Send a poke |
| `.Recall(message_id)` | Simulate message recall |
| `.MergeForward(nodes, title="Merged Chat History")` | Send merged-forward messages (rendered as a collapsible `<details>` HTML card and sent via the html channel), used to verify a module's merged-forwarding logic |
| `.Raw_ob12(message)` | Send raw OneBot12 message segments (a pure node list is automatically routed to merged forwarding; a mixed list with node segments is downgraded to plain text) |

The `At` / `AtAll` / `Reply` modifiers are provided by the framework's SendDSL base class.