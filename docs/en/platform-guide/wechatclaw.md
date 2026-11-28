# WeChat ClawBot (WechatClaw) Adapter - Platform Features Documentation

## Basic Information
- Module Name: `ErisPulse-WechatClaw`
- Platform Identifier: `wechatclaw`
- Module Version: 0.1.0
- Maintainer: wsu2059q
- Last Updated: 2026-11-17
- Dependencies: `qrcode`, `pycryptodome`

## Platform Positioning

A WeChat personal account access adapter based on the **official Tencent iLink Bot API** (the WeChat ClawBot bot channel): QR code binding, automatic token write-back, and long-polling message reception. It uses an official compliant channel rather than a reverse-engineered protocol; the scope of capabilities is subject to what WeChat officially opens up.

## Integration and Binding

- When the `token` configuration is left empty, the adapter prints a login QR code upon startup (terminal ASCII art with a link as fallback); scanning and confirming with WeChat on your phone completes the binding
- **Dashboard panel QR code scanning** (recommended): The adapter registers a "Scan QR Code to Log In to WeChat" extension section in the "Add Account Wizard", allowing direct QR code scanning and binding within the panel (aligned with the bilibili adapter's panel QR code scanning convention)
- After successful binding, `token` / `bot_user_id` / `base_url` are automatically written back to `config.toml` via the framework's lossless TOML engine (preserving user comments), so no re-scan is needed after restarts
- When the token becomes invalid (long polling returns 401/403), the log explicitly indicates "clear the token and re-scan the QR code"

### QR Code Login Endpoints (Accessible to Third-Party Frontends)

The adapter registers `POST /wechatclaw/qr/start` and `POST /wechatclaw/qr/poll` at startup:

- `qr/start`: Retrieves the QR code and returns `{success, task_id, poll_token, qr_img}` (`qr_img` is an SVG data URI)
- `qr/poll`: The request carries `task_id` + `poll_token` (to prevent unauthorized polling; returns 403 if missing), and returns `{success, status}`, where status ∈ `pending` / `scan` / `done` / `timeout`
- When the status is `done`, credentials have already been automatically written to the configuration, and the response includes `account`

## Standardization Alignment

Events and responses follow the [Event Conversion Standard](../standards/event-conversion.md) and the [API Response Specification](../standards/api-response.md).

- Message events carry the standard `message_id` at the top level (using the official message_id, falling back to client_id/seq when missing)
- The event `id` includes the account dimension (`{bot_id}:{message_id}`), with idempotent deduplication and cross-account isolation handled by the framework
- Sending returns a standard response: `status` / `retcode` / `data` / `message_id` / `message` + top-level `wechatclaw_raw`

### Message Events

- Event types: `message` / `private` (the official channel supports personal account direct messages only, with no group chat capability)
- Inbound message segments: `text`, `image`, `voice`, `file`, `video`
- Media segments do not store files locally: they carry `wechatclaw_cdn` (CDN descriptor + key), and are downloaded and decrypted on demand via `call_api("download_media")`

### Context Tokens and Replies

The protocol requires replies to carry a `context_token` (delivered along with received messages). The adapter caches the most recent context per user:

- Replies within the event chain (`event.reply()` / `Send.To("user", ...)`) automatically carry that user's context
- **Proactive direct messages** are subject to protocol restrictions: users without conversation context may be rejected by the platform (reported via the response errcode)

## Supported Message Sending Types

| Method | Description | Official API |
|------|------|---------|
| `Text(text)` | Send text (Markdown is automatically downgraded to plain text) | `sendmessage` |
| `Image(file)` | Send image (URL/path/base64:///bytes, automatic encrypted upload) | `getuploadurl` + CDN |
| `Video(file)` | Send video | Same as above |
| `File(file)` | Send file | Same as above |
| `Voice(file)` | Send voice (SILK encoding only; other audio formats are downgraded to file messages) | Same as above |
| `Reply(message_id)` | Quote reply (the quoted target is the most recent received message in the conversation) | `sendmessage` + ref_msg |

> `mention` / `at` segments have no semantics in personal account direct messages and are silently ignored when sending.

## Extended API (call_api)

| Endpoint | Parameters | Description |
|------|------|------|
| `download_media` | `media` (the `wechatclaw_cdn` of an inbound media segment) | Downloads, decrypts, and saves to disk; `data.path` returns the local path |
| `send_typing` | `user_id`, optional `status` (1=typing 2=cancel) | "typing" status (requires a valid session context) |

## Platform Limitations

- Direct messages only (official channels do not support group chats)
- Some video messages may be missing decryption keys (a known issue with official channels); such media cannot be downloaded
- Voice messages require SILK encoding (encode_type=6, 24kHz)

## Configuration Reference

| Option | Default | Description |
|---|---|---|
| `token` | "" | Leave empty to log in via QR code; automatically written back after binding |
| `bot_user_id` | "" | Official account ID; automatically written back after binding |
| `base_url` | Official default | API base URL; may be updated automatically after binding |
| `login_timeout` | 300 | QR code login wait duration (seconds) |
| `poll_interval` | 1.0 | Long-polling batch interval (seconds; the server keeps a single request suspended for about 35 seconds) |