# Webhook Generic Bridge Adapter Platform Features Documentation

WebhookAdapter is a protocol-level bidirectional bridge adapter that is not bound to any specific platform: it converts JSON POSTed by external systems on the inbound side into OneBot12 events, and on the outbound side it converts module Send into POST requests to external systems.

---

## Documentation Information

- Corresponding Module Version: 4.3.2
- Maintainer: ErisPulse
- Last Updated: 2026-11-10

## Basic Information

- Platform Introduction: Any system capable of initiating HTTP requests can connect to ErisPulse via this adapter.
- Adapter Name: WebhookAdapter
- Platform Identifier: `webhook`
- Multi-Account Support: Each account is an independent bridge configuration (bot_id / callback_path / outgoing_url / secret)
- Framework Requirements: Soft dependency `ErisPulse>=2.7.1` (runtime detection prompt, not enforced)

## Connected Platform Capabilities

- **Inbound**: External systems POST to `callback_path` → Translated to OneBot12 events (json/text segments are passed through)
- **Outbound**: Module Send → POST to `outgoing_url` (dual bridge)
- **API**: Bridge identity information and runtime status (minimal set)

## v5 Paradigm Update (4.2.0)

- **Minimal API DSL**: `get_self_info`, `get_status`, `get_version`, `get_supported_actions`
- **Framework Soft Dependency**: Runtime detection of ErisPulse>=2.7.1 with prompt; version logs output on startup
- Import path updated to Core.Bases

## Standardized Alignment (4.3.2)

The response structure and error codes follow the [API Response Specification](../standards/api-response.md).

### Event Fields

- **Message Event Top-Level `message_id` Completion**: Prioritize passing through the `message_id` from the inbound body; if missing, use a uuid as fallback (to avoid downstream deduplication/reply operations receiving empty values based on `message_id`)
- **Event Injection of `self.account_id`** (Account Name): In multi-account scenarios, `event.reply()` automatically routes to the account that received the event
- **`alt_message` Fallback with Empty String**: If not provided in the inbound message, fill with an empty string to ensure complete standard fields
- **JSON Segment Name Changed to `webhook_json`**: Raw `json` segments without platform prefixes are unified under `webhook_json` (following platform extension segment naming rules)
- Converter reuses framework `BaseConverter` (common fields are uniformly built by `build_base_event`)
- `get_self_info` Completes Standard Fields: `user_id` (account bot_id) / `user_name` / `user_displayname` (`webhook:{account name}`)

### Error Code Specification

| retcode | Meaning | Description |
|---------|---------|-------------|
| 0 | Success | — |
| 33001 | Network Error | Outbound POST target failure (connection timeout, etc.) |
| 10003 | Parameter Error | Outbound URL not configured, missing parameters, etc. |

### Account and Multi-Account

- `call_api` supports dual-compatible account fields: `account_id` (standard name) / `_account_id` (old name), the framework ApiDSL (`Api.Using(...)`) automatically adapts
- `Send` reads `send_context` (event account fallback): When calling `Send` from the event context, it defaults to falling back to the originating account

## Overview

The Webhook Adapter is a **protocol-level bridge**, not tied to any specific platform. It exchanges messages via HTTP, enabling any system capable of initiating HTTP requests to integrate with ErisPulse.

```
Inbound Direction                          Outbound Direction
────────────────                          ────────────────
External System                            ErisPulse Module
   │                                         │
   │ POST JSON                               │ Send.Text(...)
   ▼                                         ▼
┌──────────────────────────────────────────────────────┐
│                WebhookAdapter                          │
│  ┌──────────────────┐    ┌──────────────────┐     │
│  │ Inbound Routes    │    │ Outbound Forward │     │
│  │ GET  (Health Check)│    │ client.post()    │     │
│  │ POST (Receive Event)│   │ → outgoing_url   │     │
│  └────────┬─────────┘    └────────▲─────────┘     │
│           │                      │                 │
│           ▼                      │                 │
│  ┌──────────────────┐    ┌──────────────────┐     │
│  │ WebhookConverter │    │ Send Class       │     │
│  │ JSON → OneBot12  │    │ Message Segment → JSON │
│  └────────┬─────────┘    └────────▲─────────┘     │
└───────────┼──────────────────────┼─────────────────┘
            ▼                      │
     adapter.emit(event)    call_api("send_message")
            │                      │
            ▼                      │
       ErisPulse Event System ◄────────┘
```

## Multi-Account Model

Each account is an independent bridge configuration, isolated from one another:

| Account | bot_id | callback_path | outgoing_url | secret |
|---------|--------|---------------|--------------|--------|
| `default` | `webhook_bot` | `/webhook/default` | `https://a.com/recv` | `key1` |
| `discord` | `discord_bot` | `/webhook/discord` | `https://b.com/send` | `key2` |

Each account registers routes independently and emits connect events independently upon startup.

### Account Configuration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `bot_id` | No | Bot identity ID (used to represent this bridge) |
| `callback_path` | No | Inbound callback path (supports `{account}` placeholder) |
| `outgoing_url` | No | Outbound target URL (modules POST messages to this address) |
| `secret` | No | Authentication key (leave empty to disable verification; stored as encrypted text in the configuration panel) |

## Inbound Protocols

### 1. Health Check (GET)

- **Path**: `{callback_path}`
- **Method**: `GET`
- **Authentication**: None
- **Response**:

```json
{"status": "ok", "account": "default"}
```

### 2. Receive Event (POST)

- **Path**: `{callback_path}`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication** (when secret is configured): Header `X-Webhook-Secret` or Query `?secret=`

#### Request Body

```json
{
  "user_id": "u123",
  "user_nickname": "用户名",
  "group_id": "群组ID（仅群组会话）",
  "detail_type": "private",
  "message_id": "可选，透传为事件 message_id（缺失时自动生成 uuid）",
  "alt_message": "可选，纯文本备援",
  "message": [
    {"type": "text", "data": {"text": "消息内容"}}
  ],
  "raw": {}
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `user_id` | Yes | Sender ID |
| `user_nickname` | No | Sender nickname |
| `group_id` | No | Group/channel ID (provided for group sessions) |
| `detail_type` | No | Session type (`private`/`group`), default to account default |
| `message_id` | No | Message ID, passed through as event-level `message_id` (uuid fallback if missing) |
| `alt_message` | No | Plain text fallback, empty string fallback if missing |
| `message` | Yes | OneBot12 message segment array |
| `raw` | No | Raw data, stored as `webhook_raw` |

#### Response

```json
{"status": "ok"}
```

Error responses include HTTP status codes:

| Status Code | Meaning |
|-------------|---------|
| 400 | Invalid JSON / body not an object |
| 401 | Authentication failed |
| 404 | Unknown account |
| 500 | Event dispatch failed |

### 3. Field Mapping (Inbound JSON → OneBot12 Event)

| Inbound JSON | OneBot12 Event Field | Description |
|--------------|----------------------|-------------|
| — | `id` | Auto-generated |
| — | `time` | Current Unix timestamp (seconds) |
| — | `type` | Fixed as `message` |
| `detail_type` | `detail_type` | Default to account default value if missing |
| — | `platform` | Fixed as `webhook` |
| — | `self.platform` | Fixed as `webhook` |
| — | `self.user_id` | Account `bot_id` |
| — | `self.account_id` | Account name (4.3.2 injection, multi-account routing) |
| `user_id` | `user_id` | Passed through |
| `user_nickname` | `user_nickname` | Passed through (optional) |
| `group_id` | `group_id` | Passed through (optional) |
| `message_id` | `message_id` | Passed through, uuid fallback if missing (4.3.2) |
| `alt_message` | `alt_message` | Passed through, empty string fallback if missing (4.3.2) |
| `message` | `message` | Passed through |
| Full body | `webhook_raw` | Raw request |
| Account name | `webhook_account` | Account name that generated the event |
| `type` or `message` | `webhook_raw_type` | Original event type |

> Raw `json` segments (`{"type": "json", ...}`) are unified as `webhook_json` segments on both inbound and outbound sides.

## Outbound Protocols

### 1. Sending Messages

When the module calls methods such as `Send.To(...).Text(...)`, the adapter sends a POST request to `outgoing_url`:

- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication Header** (when secret is configured): `X-Webhook-Secret: {secret}`

#### Request Body

```json
{
  "target_type": "private",
  "target_id": "target_user_id",
  "account": "default",
  "message": [
    {"type": "text", "data": {"text": "Message content"}}
  ],
  "timestamp": 1700000000
}
```

| Field | Description |
|-------|-------------|
| `target_type` | Target type (from `Send.To(type, id)`), defaults to the account's default if not provided |
| `target_id` | Target ID (from `Send.To`) |
| `account` | Sender account name |
| `message` | Array of OneBot12 message segments |
| `timestamp` | Timestamp of sending (in seconds) |

### 2. Response Standardization

The adapter standardizes the response from the outbound target into the ErisPulse standard response format:

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "...", ...},
  "message_id": "...",
  "message": "",
  "webhook_raw": {}
}
```

The message ID is extracted from the `message_id` field of the target's response JSON. If the target does not return a `message_id`, it will be an empty string.

If the request fails, an error response is returned (with `status: "failed"`, `retcode: 33001`).

## Send Method

| Method | Description |
|--------|-------------|
| `Text(text)` | Sends text, wrapped as `[{"type":"text","data":{"text":text}}]` |
| `Image(file)` | Sends an image, wrapped as `[{"type":"image","data":{"file":file}}]` |
| `Raw_ob12(message)` | Sends a raw OneBot12 message segment |
| `Json(data)` | Passes raw JSON, wrapped as `[{"type":"webhook_json","data":{"raw":data}}]` |

The `At` / `AtAll` / `Reply` decorators are provided by the framework base class and merged into message segments via `_apply_modifiers`.

## Event Extension Methods (WebhookEventMixin)

| Method | Description |
|--------|-------------|
| `get_raw_data()` | Get the raw request body (`webhook_raw`) |
| `get_detail_type()` | Get the session type |
| `get_webhook_account()` | Get the account name that generated the event |

## Feature Matrix

| Feature | Support Status |
|---------|----------------|
| Multi-account | ✅ Each account has an independent bridge |
| Inbound Authentication | ✅ Header / Query dual mode |
| Health Check | ✅ GET returns status |
| Outbound Authentication | ✅ Secret carried in Header |
| OneBot12 Standard Events | ✅ Complete standard fields |
| Meta Events | ✅ connect / disconnect |
| Route Discovery | ✅ Registered to `webhook` namespace |
| WebSocket | ❌ Only HTTP |
| Media Upload | ❌ Pass-through via URL, no binary relay |

## Notes

1. **One-way outbound**: If `outgoing_url` is left blank, the account is only used for inbound reception, and sending operations will return an error (`retcode: 10003`)
2. **Secret security**: `secret` is stored as ciphertext in the configuration (metadata secret), and HTTPS is recommended for transmission
3. **Unique path**: The `callback_path` for multiple accounts must be unique to avoid routing conflicts
4. **Idempotency**: The adapter does not guarantee deduplication of inbound events; external systems should handle retries themselves
5. **Timeout**: Outbound requests use ErisPulse's built-in `client` and inherit the global timeout configuration