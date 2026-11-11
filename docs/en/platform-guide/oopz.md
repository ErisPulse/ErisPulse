# Oopz Platform Feature Documentation

## Documentation Information

| Item | Content |
|---|---|
| Module Version | 0.1.0 |
| Platform Identifier | `oopz` |
| Maintainer | ErisPulse Team |
| Last Updated | 2026-11-11 |

> ⚠️ Oopz does not have an official bot platform. This adapter connects via a reverse-engineered community protocol as a **user account** and is not an official interface. The interface may become invalid at any time; use a test account. See the README for risk disclosures.

## Basic Information

- Adapter class: `OopzAdapter` (entry-point `oopz`)
- Access method: WebSocket (`wss://ws.oopz.cn`) + REST gateway (`https://gateway.oopz.cn`), RSA-signed request headers + JWT
- Credentials: "either password or token" — `password` (phone number + password + client private key, auto-login session renewal) or `token` (uid/JWT/device_id/private key four-piece set)
- Multi-account: Supported (`[Oopz_Adapter.accounts.<name>]`), events marked with `self.account_id` to indicate source
- Framework soft dependency: ErisPulse ≥ 2.7.1

## Session Model

| ErisPulse Goal | Oopz Concept | Description |
|---|---|---|
| `Send.To("group", <channel ID>)` | Channel | The domain is automatically resolved by the adapter via "channel→area cache + joined domain scanning" |
| `Send.To("user", <对方UID>)` | Private Chat Session | Automatically `PATCH /client/v1/chat/v1/to` initiates a session and caches the sessionId |
| `guild_id` field / guild semantics | Area | Area-level operations use `get_guild_*` and `oopz.*` management extensions |

## Standardized Alignment (0.1.0)

### Error Code Specification

| retcode | Meaning |
|---|---|
| 0 | Success |
| 10002 | Unsupported action/Message segment downgrade (Voice, video file sending, upload_file, keyboard, etc.) |
| 10003 | Missing/invalid parameter (e.g., channel cannot be located in the domain) |
| 33001 | Network exception/Rate limiting (429, respect Retry-After, retry once) |
| 34100 | Platform returned failure (Original response in `oopz_raw`) |
| 34005 | Account not resolved (Not configured or session not established) |

### Response Structure

All responses contain `status / retcode / data / message_id / message / oopz_raw`; the `message_id` of the send response is taken from the platform's returned `messageId`; `data.self_info.user_id` is filled back in `get_self_info`.

### Event Field Completeness

- All events must have `id / time / type / detail_type / sub_type / platform / self`, and `oopz_raw` + `oopz_raw_type` always exist.
- Message events must have `message_id` at the top level; microsecond timestamps are unified into second strings.
- Event `id` is deduplicated by account domain (`<account>:<type>:<platformID>`).
- Unknown events are converted to `type="unknown"` + `warning`, and are not silently discarded.
- Internal protocol frames (handshake/authentication/heartbeat/subscription) do not generate platform events.

### Downgrade Semantics

- `voice/audio/video/file` send segment → `retcode=10002` (Platform only supports image upload), no exception thrown.
- `guild` send target → `retcode=10003` (Please specify the channel).
- JWT token mode expiration → `retcode=34100` prompts credential update; password mode automatically relogs in and retries once.

## Supported Message Sending Types

| Method | Platform Implementation |
|---|---|
| `Text` | Text (dual write of text/content) |
| `Image` | COS signature ticket upload (images only), text placeholder `![IMAGEw{w}h{h}]({fileKey})` + attachments |
| `At / AtAll / Reply` | `mentionList` / `isMentionAll` / `referenceMessageId` |
| `Important()` modifier | `styleTags=["IMPORTANT"]` announcement style |
| `Recall(messageId)` | `recallGim` (channel) / `recallIm` (private message, only self-sent messages can be recalled) |
| `Raw_ob12` | OneBot12 segment → platform payload (text/mention/mention_all/reply/image; other segments downgraded to 10002) |
| Voice/Video/File/Keyboard | Not supported → 10002 |

## Standard API Actions (ApiDSL)

### Supported Standard Actions

`get_self_info`, `get_user_info`, `get_friend_list`, `get_group_info` (channel + domain merged information), `get_group_list` (flattened list of joined domains/channels), `get_guild_info`, `get_guild_list`, `get_channel_list`, `get_guild_members`, `delete_message` (requires `channel_id` or `user_id` context), `get_file` (attachment URL → base64), `leave_guild`, `get_status`, `get_version`, `get_supported_actions`

### Unsupported Standard Actions (retcode=10002)

`send_message` (use Send DSL), `upload_file`, `get_latest_events`, `set_group_name`, `set_group_admin`, `set_group_leave`, `set_group_card`, `leave_group`, `leave_channel`

### Platform Extension Actions (oopz.*)

| Action | Required Parameters | Description |
|---|---|---|
| `oopz.create_channel` | `area_id, name` | Optional: `channel_type/group_id/secret/max_member` |
| `oopz.delete_channel` | `area_id, channel_id` | |
| `oopz.mute_member` / `oopz.unmute_member` | `area_id, user_id` | Mute, `duration` in minutes automatically adjusted to predefined intervals (5 minutes / 1 hour / 1 day / 3 days / 7 days) |
| `oopz.mute_mic` / `oopz.unmute_mic` | `area_id, user_id` | Mute microphone |
| `oopz.kick_member` | `area_id, user_id` | Remove user from domain |
| `oopz.block_user` / `oopz.unblock_user` | `area_id, user_id` | Domain blacklist |
| `oopz.get_area_members` | `area_id` | Optional: `offset_start/offset_end` |
| `oopz.get_assignable_roles` | `area_id, target_id` | Assignable roles |
| `oopz.assign_role` / `oopz.revoke_role` | `area_id, target_id, role_id` | Submit after reading full role list |
| `oopz.react_message` / `oopz.unreact_message` | `message_id, channel_id, emoji` | Optional: `user_id` (private message) / `area_id` |
| `oopz.get_reactions` | `message_id` | Optional: `message_ids` (≤50) / `user_id` |
| `oopz.get_reaction_persons` | `message_id, channel_id, emoji` | Paginated list of reaction users |
| `oopz.top_message` | `message_id, area_id, channel_id` | Pin/unpin message (`cancel=True` to unpin) |
| `oopz.get_history_messages` | `area_id, channel_id` | Optional: `size` (default 50) |
| `oopz.get_friend_requests` | — | List of friend requests |
| `oopz.respond_friend_request` | `target, friend_request_id, agree` | Approve/reject request (typically handled via Request DSL) |

## Friend Request Handling

- Event: `request/friend`, `request_id` is a **stateless composite key** `<target>:<friendRequestId>`
- `event.approve()` / `event.reject()` → POST `/client/v1/friendship/v1/response`
- Single endpoint isomorphic, no need to retain request type context table

## Return Value of Send Method

```json
{
  "status": "ok",
  "retcode": 0,
  "data": {"message_id": "14283..."},
  "message_id": "14283...",
  "message": "",
  "oopz_raw": {"messageId": "14283...", "timestamp": "..."}
}
```

## Unique Event Types

- Message event extension fields: `oopz_area_id`, `guild_id` (channel message); `oopz_reference_message_id` (reply)
- Notification extensions: `oopz_edited_text`, `oopz_emoji`, `oopz_reaction_type`, `oopz_persons`, `oopz_from_channel`, `oopz_channel_name`, `oopz_channel_type`, `oopz_area_name`, `oopz_role_id`, `oopz_role_name`, `oopz_ban_until`, `oopz_login_state`
- `EventMixin` convenience methods: `get_raw_event()`, `get_area_id()`, `get_edited_text()`, `get_emoji()`, `get_reaction_type()`, `get_voice_persons()`