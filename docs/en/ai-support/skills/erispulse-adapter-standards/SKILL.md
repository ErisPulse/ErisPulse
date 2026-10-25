---
name: erispulse-adapter-standards
description: "适用于：实现/评审适配器时需要对照的硬性技术规范。覆盖场景：When you are developing a new adapter, or adding new capabilities to a platform and need to decide whether to integrate into the standard or use a `{platform}_` extension, how to name things, or how to handle platform differences, read this first. If you are just looking up specific standards for a particular domain, you can directly jump to §2, the document corresponding to the standard map.。When mapping platform-native session types to standard types (private/group/channel/guild/thread) in an adapter, or when unsure what target type to pass to `Send.To()` in a module, or to understand the automatic conversion of `event.reply()` — refer to this document. Skip it otherwise.。When you are converting platform-native events to OneBot12 standard events in an adapter—use this document as a reference for verifying required fields, message segment structure, extension field naming (the `{platform}_` prefix), and session type inference. Otherwise, skip it.。When implementing the `Send` ..."
---

# ErisPulse 适配器技术标准

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 标准化总纲: 88-97 行
- 1. Standardization Principles: 99-106 行
- 2. Standard Maps: 108-118 行
- 3. Standardized Workflow (How New Capabilities Enter the Standard): 120-157 行
- 4. Differential Handling Modes (Adapter Layer): 159-170 行
- 5. Standard for Interactive Components: 172-284 行
- 6. Future Candidates (Roadmap): 286-299 行
- 7. Standard Checklist for New Adapter Developers: 301-319 行
- 8. Related Documentation: 321-324 行
- 会话类型: 326-335 行
- 1. Core Concepts: 337-363 行
- 2. Standard Session Types: 365-411 行
- 3. Platform Type Mapping: 413-452 行
- 4. Custom Type Extension: 454-496 行
- 5. Automatic Type Inference: 498-533 行
- 6. API Usage Examples: 535-574 行
- 7. Core API Reference: 576-624 行
- 8. Utility Methods: 626-648 行
- 9. Best Practices: 650-670 行
- 10. FAQ: 672-692 行
- 11. Related Documentation: 694-702 行
- 事件转换: 704-711 行
- 1. Core Principles: 713-719 行
- 2. Standard Field Requirements: 721-771 行
- 3. Event Format Examples: 773-851 行
- 4. Message Segment Standard: 853-954 行
- 5. Handling Unknown Events: 956-972 行
- 6. Extension Naming Convention: 974-1067 行
- 7. Session Type Extension: 1069-1103 行
- 8. Module Developer Guide: 1105-1218 行
- 9. Session Type Inference for notice / request Events: 1220-1285 行
- 10. Related Documentation: 1287-1298 行
- 发送方法规范: 1300-1309 行
- 0. Keyword Definitions: 1311-1319 行
- 1. Standard Method Naming: 1321-1373 行
- 2. Parameter Specification Details: 1375-1544 行
- 3. Platform-Specific Method Naming: 1546-1575 行
- 4. Parameter Naming Convention: 1577-1587 行
- 5. Return Value Convention: 1589-1594 行
- 6. Reverse Conversion Convention (OneBot12 → Platform): 1596-1778 行
- 7. Method Discovery: 1780-1801 行
- 9. Adapter Development Notes: 1803-1809 行
- 10. Adapter Implementation Checklist: 1811-1841 行
- 11. MessageBuilder - Adapter-Side Notes: 1843-1854 行
- 12. Related Documents: 1856-1864 行
- API 动作规范: 1866-1882 行
- 1. Design Background: 1884-1896 行
- 2. Three Parallel DSL Classes: 1898-1913 行
- 3. Standard Action List: 1915-2039 行
- 4. Usage: 2041-2094 行
- 5. Adapter Implementation: 2096-2169 行
- 6. Response Format: 2171-2186 行
- 7. Relationship with SendDSL / RequestDSL: 2188-2196 行
- 8. Adapter Implementation Checklist: 2198-2211 行
- 9. Related Documents: 2213-2223 行
- API 响应规范: 2225-2232 行
- 1. Description: 2234-2242 行
- 2. Basic Return Structure: 2244-2260 行
- 3. Full Field Specification: 2262-2331 行
- 4. Implementation Requirements: 2333-2337 行
- 5. Extension Specifications: 2339-2410 行
- 6. Notes: 2412-2416 行
- 请求动作规范: 2418-2427 行
- 1. Overview: 2429-2462 行
- 2. Request Event Field Requirements: 2464-2508 行
- 3. Request DSL: 2510-2575 行
- 4. Event Convenience Methods: 2577-2611 行
- 5. Adapter Implementation Requirements: 2613-2758 行
- 6. Adapter Implementation Checklist: 2760-2777 行
- 7. Error Code Extensions: 2779-2794 行
- 8. Related Documents: 2796-2805 行

## 标准化总纲

> 来源: `docs/en/standards/standardization-guide.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/standardization-guide.md）

# Adapter Standardization Guide (General Overview)

> [!TIP]
> **When to read this**: When you are developing a new adapter, or adding new capabilities to a platform and need to decide whether to integrate into the standard or use a `{platform}_` extension, how to name things, or how to handle platform differences, read this first. If you are just looking up specific standards for a particular domain, you can directly jump to §2, the document corresponding to the standard map.

This document serves as the **general overview** of ErisPulse adapter standardization: it establishes cross-platform standardization principles, standard maps, difference handling patterns, and the process for new capabilities to enter the standard. It also provides complete definitions for **standardized interactive components** (such as buttons, keyboard inputs, dropdown selections) and **interactive callback events**. Any adapter developer should **prioritize using standard definitions** when implementing new features, so that module developers can achieve a consistent experience on any platform with the same code—consistent naming, parameters, and return values.

## 1. Standardization Principles

1. **Consistent Naming**: The same concept uses the same name across all platforms (e.g., `delete_message` for message deletion, `keyboard` for button segments), regardless of the platform.
2. **Consistent Parameters**: The parameter structure for standard actions/segments/methods remains consistent across all platforms; platform-specific parameters are provided as **optional extended parameters** or **extended fields**, without polluting the standard signature.
3. **Consistent Return**: All API/send calls return a standard response structure (`status/retcode/data/message_id/message`), and standard fields within `data` (such as `user_id/user_name`) have consistent semantics; platform-specific raw data is placed in `{platform}_raw`.
4. **Reasoned Extension**: Platform-specific capabilities are named with a `{platform}_` prefix (segments: `yunhu_form`; actions: `yunhu.board`; event fields: `qqbot_button_id`), clearly indicating non-cross-platform features.
5. **Platform Differences Absorbed in Adapter Layer**: Module code is designed for standard programming, and platform differences are handled by the adapter (parameter mapping, field standardization, capability degradation), eliminating the need for modules to write platform-specific branches.
6. **Graceful Degradation for Unsupported Capabilities**: When a platform does not support a standard capability, it gracefully degrades (returns `retcode=10002`, component textification into `alt_message`), without throwing exceptions that interrupt module logic.

## 2. Standard Maps

| Domain | Standard Document | Coverage |
|--------|-------------------|----------|
| Event Conversion | [Event Conversion Standard](event-conversion.md) | Event structure, standard message segments (text/image/mention/reply/keyboard, etc.), platform extension segment specifications |
| Interactive Components | **This Document §5** | Buttons/keyboards, dropdown selection, cards, standard fields for interactive callback events, modifier conventions, and platform mappings |
| API Actions | [API Action Standard](api-action-spec.md) | OneBot12 standard actions (user/group/channel/message management/meta actions) with unified interfaces and `ApiDSL` |
| Request Operations | [Request Operation Specification](request-action-spec.md) | Request event fields (`request_id`) and Request DSL (`approve`/`reject`) |
| Send Methods | [Send Method Specification](send-method-spec.md) | Naming, parameters, modifiers, and reverse conversion (OB12→platform) for Send class methods |
| Session Types | [Session Type Standard](session-types.md) | Definitions and mappings for session types such as user/group/channel/guild/dms |
| API Responses | [API Response Standard](api-response.md) | Standard response structure and `retcode` conventions |

## 3. Standardized Workflow (How New Capabilities Enter the Standard)

```
Platform-specific capabilities ({platform}_ prefix)
        │  ≥2 platforms exhibit similar capabilities
        ▼
Identify commonalities (extract generic concepts and parameter subsets)
        │
        ▼
Standard draft (naming + parameters + return + mapping table across platforms)
        │  Review
        ▼
Integrate into this overview/field-specific standard documents + implement compatibility layer via framework base class/adapters
        │
        ▼
Standard segments/actions (no prefix) — modules can be used across platforms
```

**Example**: Buttons were initially independently implemented across platforms (`telegram_inline_keyboard` / Yunhu buttons / QQBot keyboard) → appeared in ≥3 platforms → extracted generic structure (`label/type/data` + rows) → released standard segment `keyboard` → each adapter implements compatibility layer (decorator accepts generic structure + standard segment conversion + native segment passthrough).

### 3.1 Naming Rules

| Object | Rule | Example |
|------|------|------|
| Standard message segment | lowercase, generic concept with no prefix | `keyboard`, `select`, `mention` |
| Platform extension segment | `{platform}_` prefix | `telegram_sticker`, `yunhu_form` |
| Standard API action | OB12 standard name (snake_case) | `get_group_info`, `delete_message` |
| Platform extension action | `{platform}.` prefix or protocol-agnostic name | `yunhu.board`, `send_poke` (OB11 extension) |
| Decorator | PascalCase, generic capabilities integrated into framework base class | `.Keyboard(rows)`, `.At(uid)` |
| Event standard field | generic concept with no prefix | `interaction_id`, `button_data`, `request_id` |
| Event platform field | `{platform}_` prefix | `qqbot_event_id`, `telegram_chat_id` |

### 3.2 Parameter and Return Rules

- Standard parameters must be **name and meaning consistent** across all platforms; units/format are explicitly defined in the standard documentation (e.g., second-level timestamps, string IDs)
- Required parameters must be the **common subset** of all platform capabilities; platform-enhanced capabilities are optional parameters
- Platform-specific strong constraints (e.g., QQBot rich media cannot be mixed with event_id) are automatically handled/downgraded by adapters, not exposed to modules
- Standard fields returning `data` must be consistent across all platforms; platform-specific additional information is placed in platform-named fields within `data` or in `{platform}_raw`

## 4. Differential Handling Modes (Adapter Layer)

| Mode | Description | Example |
|------|-------------|---------|
| **Parameter Mapping** | Standard parameters → platform-native parameters | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)` (chat_id filled from registration table) |
| **Structure Conversion** | Standard segment → platform-native structure | `keyboard` segment → `inline_keyboard` / buttons / QQBot keyboard |
| **Action Mapping** | Standard action name → platform action name | `get_self_info` → `get_login_info` (OB11) |
| **Field Standardization** | Platform response → standard fields | `getMe()` → `{user_id, user_name, user_displayname}` |
| **Synthetic Identification** | Generate deterministic ID when platform lacks native ID | TG join request without ID → `tjr_{chat}_{user}_{date}` |
| **Capability Degradation** | Textualize or return 10002 if not supported | Kook lacks keyboard → alt_message textified; `get_friend_list` → 10002 |
| **Normalization** | Platform dirty data → standard format | QQBot @-tagged openid → bot_id (name normalized) |
| **Dual-track Compatibility** | Accept both standard and platform-native structures | `.Keyboard()` accepts either generic rows or native structure |

## 5. Standard for Interactive Components

### 5.1 Component List and States

| Component | Standard Segment type | Status | Supported Platforms |
|---------|----------------------|--------|-------------------|
| Button/Keyboard (keyboard) | `keyboard` | ✅ Standardized | Telegram / Yunhu / QQBot |
| Dropdown Selection (select) | `select` | 📋 Reserved (structure in §5.4) | Discord / Telegram(bot) |
| Card (card) | `card` | 📋 Reserved (see §5.5) | Kook / Yunhu(html) |
| Modal (modal) | `modal` | 📋 Reserved | Discord |

> **Decorator Hierarchy Convention**: The Send decorators for generic interactive components are implemented by the **adapter's Send class** (not built into the framework base class), named according to the conventions in §5.2, and parameters follow the standard structure defined in this document.

### 5.2 keyboard Button/Inline Keyboard

#### Message Segment Structure (Sending Direction)

The standard `keyboard` segment is a `rows` 2D array, with each button defined as:
`{"label": "display text", "type": "callback" | "link", "data": "callback data or redirect address"}`,
with optional platform-specific fields allowed (adapter maps or ignores based on capability).

> **Authoritative Structure Definition**: The complete message segment JSON, field table, and field semantics are defined in [Event Conversion Standard §4.1.1 keyboard Button/Inline Keyboard Segment (Cross-platform Common)](event-conversion.md#411-keyboard-按钮内联键盘段跨平台通用). This section does not repeat them.

#### Platform Mapping Comparison

| Platform | Standard Segment → Native Structure | Native Structure Reference |
|---------|----------------------------------|--------------------------|
| Telegram | `reply_markup.inline_keyboard`: `[{text, callback_data \| url}]` | callback→`callback_data` (≤64 bytes), link→`url` |
| Yunhu | `content.buttons`: `[{label, action_type}]` | callback→`action_type:2` + `action` + `value`, link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`: `[{label, type, data}]` | callback→`type:2` + `data`, link→`type:0` + `data` (message must be markdown type) |
| Kook | Card `action-group` module: `[{type, text, value, click}]` | callback→`click:return` + `value`, link→`click:link` + `url` |
| Discord | `components[].components`: `[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`, link→`style:5` + `url` |

#### Send Decorators (Implemented by Each Adapter's Send Class)

The generic decorators are implemented by **each adapter in their own Send class** (without modifying the framework base class):

- `.Keyboard(rows)`: Standard naming, accepts the generic rows structure defined in §5.2, internally generates the standard `keyboard` message segment (or directly converts to native platform structure), handled uniformly by `Raw_ob12`.
- `.Buttons(rows)`: Optional semantic alias, behavior is identical.
- **Backward Compatibility**: If native platform structures are detected, they are directly passed through (no error, no conversion).
- Platform-native extended segments (e.g., `telegram_inline_keyboard`) continue to be passed through, unaffected.

```python
# Same code, any platform (adapters provide decorators and conversion)
rows = [[{"label": "Like", "type": "callback", "data": "like:1"},
         {"label": "Homepage", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("Please select")
```

> Adapter Compatibility List: QQBot / Telegram / Yunhu have implemented (decorators + standard segment conversion); new adapters should implement according to this document (see §7 Checklist).

### 5.3 Interactive Callback Events (After Button Click)

After a user clicks a button, the event pushed by the platform **must** provide the following standard fields (detail_type may retain platform naming):

| Standard Field | Type | Required | Description |
|---------------|------|----------|-------------|
| `interaction_id` | str | Yes | ID for this interaction (can be used for response, e.g., spinning/loading indicator) |
| `button_data` | str | Yes | Button return data (i.e., `data` in §5.2) |
| `button_label` | str | No | Button display text |
| `user_id` | str | Yes | Clicker |
| `message_id` | str | No | Message containing the button |
| `group_id` / `channel_id` | str | No | Source session |

**detail_type Convention**: Retain existing platform naming (`qqbot_interaction` / `telegram_callback_query` / `yunhu_a2ui_button`, etc.), but **standard fields must be complete**—modules can retrieve values cross-platform using `event.get("button_data")`.

**Event Extension Method Suggestion** (provided by adapter EventMixin):

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**Responding to Interaction** (according to platform capability): `adapter.reply_interaction(interaction_id, code=0)` (QQBot) / `answerCallbackQuery` (Telegram), etc., named following platform method families, no forced unification.

#### Platform Callback Event Mapping

| Platform | Native Event | detail_type | interaction_id Source | button_data Source |
|---------|-------------|-------------|----------------------|-------------------|
| Telegram | `callback_query` | `telegram_callback_query` (notice) | `callback_query.id` | `callback_query.data` |
| Yunhu | Button Click Event | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | Button Click Event | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select Dropdown Selection (Reserved)

```json
{
  "type": "select",
  "data": {
    "placeholder": "Please select",
    "options": [
      {"label": "Option A", "data": "opt:A"},
      {"label": "Option B", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

Callback events reuse the fields from §5.3 (`button_data` = selected `data`, array for multiple selections). First platforms to implement: Discord (select menu), Telegram (keyboard switching). Platforms not implementing this segment should degrade to a text list in `alt_message`.

### 5.5 card Cards (Reserved, Postponed Standardization)

Card structures vary greatly (Kook full-featured card module vs Yunhu html vs QQ markdown+keyboard), so no strong standard is enforced yet. Suggested approaches:

- Express rich text cards using `text` + `keyboard` combinations (sufficient for most scenarios)
- Continue using platform-specific extended segments for full-featured cards (e.g., `kook_card`)
- Re-evaluate and upgrade when ≥2 platforms have similar card capabilities

---

## 6. Future Candidates (Roadmap)

The following capabilities have appeared or are expected to appear on ≥2 platforms, and are prioritized for standardization:

| Candidate | Involved Platforms | Priority | Notes |
|-----------|-------------------|----------|-------|
| select dropdown selection | Discord / Telegram | High | Structural draft in §5.4 |
| Reactions/emoji responses | QQBot / Telegram / Discord / Kook | High | Standardization of actions and events on both sides |
| Group management actions (mute/kick/approve) | QQBot / Yunhu / OB11 | High | Most have been implemented as platform actions, awaiting extraction of standardized signatures |
| Announcements/boards | Yunhu / Telegram / Discord | Medium | `set_announcement`-like actions |
| File resource model (two-stage file_id) | All platforms | Low (postponed) | Direct upload `SendDSL.File(file, filename)` is already a standard path (URL/path/bytes direct upload, see [Send Method Specification §2.1](send-method-spec.md)); the file_id model is only passed through when the backend naturally supports it, see [API Action Standard §3.5](api-action-spec.md) |
| Card | Kook / Yunhu | Low | Significant structural differences, see §5.5 |
| Form | Yunhu | Low | Platform-specific, maintain `{platform}_` prefix |
| Media transcoding/size detection | All platforms | Low | Implemented internally by adapters, not exposed for standardization |

## 7. Standard Checklist for New Adapter Developers

When developing a new adapter, please follow this checklist for implementation (★ indicates required, others are recommended):

- [ ] ★ Convert events into OneBot12 standard structure, inherit `BaseConverter`
- [ ] ★ Support for standard message segment sending and receiving (text/image/mention/reply/keyboard…; media segments handled with hierarchical up/downgrading according to the form in [Sending Method Specification §2.1](send-method-spec.md))
- [ ] ★ Implement `Raw_ob12` (including standard segment → platform structure conversion; standard `keyboard` segment must be implemented)
- [ ] ★ Return standard response structure (`make_response`/`make_error`)
- [ ] ★ Multi-account: `AccountConfigClass(BotAccountConfig)` + `_resolve_account`
- [ ] ★ Send class inherits `BaseAdapter.Send`, use `_apply_modifiers`/`send_context`
- [ ] ☆ API DSL: Map standard actions to platform APIs (see API Action Standards)
- [ ] ☆ Request DSL: Request events include `request_id` + `accept/reject`
- [ ] ☆ Interactive components: `keyboard` segment conversion + standard interactive callback fields + `.Keyboard()`/.Buttons()` decorators (implemented in adapter's Send class)
- [ ] ☆ EventMixin: Platform extension methods such as `get_raw_event()` / `get_button_data()`
- [ ] ☆ Use `runtime.spawn_background` for lifecycle tasks
- [ ] ☆ Use `self.cfg` for configuration reading
- [ ] ☆ Framework soft dependencies: Do not declare hard dependency on ErisPulse + runtime version detection
- [ ] ☆ i18n: Multi-language configuration fields and logs
- [ ] ☆ Platform documentation + adapter repository platform-features.md

## 8. Related Documentation

- See §2 Standard Maps for standards in various domains.
- Built-in adapters in the framework can serve as reference implementations: QQBot (full v5 paradigm), OneBot11 (API DSL mapping), YunHu (BaseConverter + Web API extension).

## 会话类型

> 来源: `docs/en/standards/session-types.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/session-types.md）

# ErisPulse Session Type Standard

> [!TIP]
> **When to read this**: When mapping platform-native session types to standard types (private/group/channel/guild/thread) in an adapter, or when unsure what target type to pass to `Send.To()` in a module, or to understand the automatic conversion of `event.reply()` — refer to this document. Skip it otherwise.

This document defines the session type standard supported by ErisPulse, covering receive event types and send target types.

## 1. Core Concepts

### 1.1 Receive Types && Send Types

ErisPulse distinguishes between two session types:

- **Receive Type**: The `detail_type` field of received events
- **Send Type**: The target type of the `Send.To()` method when sending messages

### 1.2 Type Mapping Relationships

```
Receive Type (detail_type)     Send Type (Send.To)
─────────────────        ────────────────
private                 →        user
group                   →        group
channel                 →        channel
guild                   →        guild
thread                  →        thread
user                    →        user
```

**Key Points**:
- `private` is the receive-time type; the standard send type is `user`
- `group`, `channel`, `guild`, and `thread` use the same type for both receiving and sending
- **Recommended path**: Use `event.reply()` directly — it automatically completes type conversion and target inference, with no manual handling needed (the `private` → `user` automatic conversion happens here)
- **For manual sending**: Pass the send type directly (e.g., `Send.To("user", ...)`); manually passing a receive type such as `Send.To("private", ...)` can still be auto-converted, but is not recommended (see §6.1)

## 2. Standard Session Types

### 2.1 OneBot12 Standard Types

#### private
- **Receive Type**: `private`
- **Send Type**: `user`
- **Description**: One-to-one private chat messages
- **ID Field**: `user_id`
- **Applicable Platforms**: All platforms supporting private chats

#### group
- **Receive Type**: `group`
- **Send Type**: `group`
- **Description**: Group chat messages, including various forms of groups (e.g., Telegram supergroup)
- **ID Field**: `group_id`
- **Applicable Platforms**: All platforms supporting group chats

#### user
- **Receive Type**: `user`
- **Send Type**: `user`
- **Description**: User type; some platforms (e.g., Telegram) represent private chats as user instead of private
- **ID Field**: `user_id`
- **Applicable Platforms**: Telegram and similar platforms

### 2.2 ErisPulse Extension Types

#### channel
- **Receive Type**: `channel`
- **Send Type**: `channel`
- **Description**: Channel messages, supporting broadcast-style messages to multiple users
- **ID Field**: `channel_id`
- **Applicable Platforms**: Discord, Telegram, Line, etc.

#### guild
- **Receive Type**: `guild`
- **Send Type**: `guild`
- **Description**: Server/community messages, typically used for Discord Guild-level events
- **ID Field**: `guild_id`
- **Applicable Platforms**: Discord, etc.

#### thread
- **Receive Type**: `thread`
- **Send Type**: `thread`
- **Description**: Thread/sub-channel messages, used for sub-discussion areas within a community
- **ID Field**: `thread_id`
- **Applicable Platforms**: Discord Threads, Telegram Topics, etc.

## 3. Platform Type Mapping

### 3.1 Mapping Principles

Adapters are responsible for mapping platform-native types to ErisPulse standard types:

```
Platform Native Type → ErisPulse Standard Type → Send Type
```

### 3.2 Common Platform Mapping Examples

#### Telegram
```
Telegram Type          ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
private                private                 user
group                  group                   group
supergroup             group                   group  # Mapped to group
channel                channel                 channel
```

#### Discord
```
Discord Type          ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
Direct Message         private                user
Text Channel           channel                channel
Guild                  guild                  guild
Thread                 thread                 thread
```

#### OneBot11
```
OneBot11 Type        ErisPulse Receive Type    Send Type
─────────────────      ────────────────       ───────────
private                private                user
group                  group                  group
discuss                group                  group  # Mapped to group
```

## 4. Custom Type Extension

### 4.1 Registering Custom Types

Adapters can register custom session types:

```python
from ErisPulse.Core.Event import register_custom_type

# Register a custom type
register_custom_type(
    receive_type="my_custom_type",
    send_type="custom",
    id_field="custom_id",
    platform="MyPlatform"
)
```

### 4.2 Using Custom Types

After registration, the system automatically handles conversion and inference for that type:

```python
# Automatic inference
receive_type = infer_receive_type(event, platform="MyPlatform")
# Returns: "my_custom_type"

# Convert to send type
send_type = convert_to_send_type(receive_type, platform="MyPlatform")
# Returns: "custom"

# Get the corresponding ID
target_id = get_target_id(event, platform="MyPlatform")
# Returns: event["custom_id"]
```

### 4.3 Unregistering Custom Types

```python
from ErisPulse.Core.Event import unregister_custom_type

unregister_custom_type("my_custom_type", platform="MyPlatform")
```

## 5. Automatic Type Inference

When an event has no explicit `detail_type` field, the system automatically infers the type based on existing ID fields:

> [!NOTE]
> **2.7.0+ Behavior Change**: `detail_type` is adopted directly only when it is a **known session type** (standard or custom). The `detail_type` of notice/request events (such as `group_member_increase` and `friend_increase`) are **semantic subtypes** rather than session types, so the correct session type is instead inferred from ID fields.

### 5.1 Inference Priority

```
Priority (high to low):
1. group_id     → group
2. channel_id   → channel
3. guild_id     → guild
4. thread_id    → thread
5. user_id      → private
```

### 5.2 Usage Examples

```python
# Event has only group_id
event = {"group_id": "123", "user_id": "456"}
receive_type = infer_receive_type(event)
# Returns: "group" (group_id takes priority)

# Event has only user_id
event = {"user_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "private"

# A notice event's detail_type is a semantic subtype; 2.7.0+ infers from ID fields
event = {"type": "notice", "detail_type": "group_member_increase", "group_id": "123"}
receive_type = infer_receive_type(event)
# Returns: "group" (not "group_member_increase")
```

## 6. API Usage Examples

### 6.1 Sending Messages

```python
from ErisPulse import adapter

# Send to a user
await adapter.myplatform.Send.To("user", "123").Text("Hello")

# Send to a group
await adapter.myplatform.Send.To("group", "456").Text("Hello")

# Automatic private → user conversion: manually passing a receive type is not recommended (may cause compatibility issues)
await adapter.myplatform.Send.To("private", "789").Text("Hello")
# Internally auto-converted to: Send.To("user", "789")
# Recommended practice: use the send type user directly for manual sending, or use event.reply() to complete the conversion automatically (see 6.2)
```

### 6.2 Event Reply

```python
from ErisPulse.Core.Event import Event

# Event.reply() automatically handles type conversion (recommended path)
await event.reply("Reply content")
# Internally uses the correct send type automatically (conversions like private → user happen here)
```

### 6.3 Command Handling

```python
from ErisPulse.Core.Event import command

@command(name="test")
async def handle_test(event):
    # The system automatically handles session types
    # No need to manually check whether it is group_id or user_id
    await event.reply("Command executed successfully")
```

## 7. Core API Reference

### 7.1 Type Conversion

```python
from ErisPulse.Core.Event import convert_to_send_type, convert_to_receive_type

# Receive type → Send type
convert_to_send_type("private")  # → "user"
convert_to_send_type("group")    # → "group"

# Send type → Receive type
convert_to_receive_type("user")   # → "private"
convert_to_receive_type("group")  # → "group"
```

### 7.2 ID Field Query

```python
from ErisPulse.Core.Event import get_id_field, get_receive_type

get_id_field("group")    # → "group_id"
get_id_field("private")  # → "user_id"

get_receive_type("group_id")  # → "group"
get_receive_type("user_id")   # → "private"
```

### 7.3 One-Step Send Information Retrieval

```python
from ErisPulse.Core.Event import get_send_type_and_target_id

event = {"detail_type": "private", "user_id": "123"}
send_type, target_id = get_send_type_and_target_id(event)
# send_type = "user", target_id = "123"

# Use directly with Send.To()
await adapter.Send.To(send_type, target_id).Text("Hello")
```

### 7.4 Getting the Target ID

```python
from ErisPulse.Core.Event import get_target_id

event = {"detail_type": "group", "group_id": "456"}
get_target_id(event)  # → "456"
```

## 8. Utility Methods

```python
from ErisPulse.Core.Event import (
    is_standard_type,
    is_valid_send_type,
    get_standard_types,
    get_send_types,
    clear_custom_types,
)

is_standard_type("private")     # True
is_standard_type("custom_type") # False

is_valid_send_type("user")      # True
is_valid_send_type("invalid")   # False

get_standard_types()  # {"private", "group", "channel", "guild", "thread", "user"}
get_send_types()      # {"user", "group", "channel", "guild", "thread"}

clear_custom_types()                # Clear all
clear_custom_types(platform="discord")  # Clear only those for the specified platform
```

## 9. Best Practices

### 7.1 Adapter Developers

1. **Use standard mappings**: Map to standard types whenever possible, rather than creating new types
2. **Convert correctly**: Ensure the mapping relationship between receive and send types is correct
3. **Preserve original data**: Keep original event types in `{platform}_raw`
4. **Document it**: Describe the type mapping relationships in the adapter documentation

### 7.2 Module Developers

1. **Use utility methods**: Use utility methods such as `get_send_type_and_target_id()`
2. **Avoid hardcoding**: Do not write code like `if group_id else "private"`
3. **Consider all types**: Code should support all standard types, not just private/group
4. **Design flexibly**: Use event wrapper methods instead of accessing fields directly

### 7.3 Type Inference

- **Prefer detail_type**: If an explicit field exists, do not perform inference
- **Use inference sensibly**: Only use it when there is no explicit type
- **Mind the priority**: Understand the inference priority to avoid unexpected results

## 10. FAQ

### Q1: Why is private converted to user when sending?

A: This is required by the OneBot12 standard. `private` is a receive-time concept; `user` is more semantically appropriate when sending.

### Q2: How do I support new session types?

A: Register custom types via `register_custom_type()`, or directly use standard types such as `channel` and `guild`.

### Q3: What if an event has no detail_type?

A: The system automatically infers it based on existing ID fields. Priority: group > channel > guild > thread > user.

### Q4: How should adapters map Telegram supergroup?

A: In the adapter's conversion logic, map `supergroup` to the standard `group` type.

### Q5: How are special platforms like email handled?

A: For non-universal or platform-specific types, use `{platform}_raw` and `{platform}_raw_type` to preserve the original data, and let the adapter handle them itself.

## 11. Related Documentation

**Adapter side (mapping and conversion)**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification
- [Send Method Specification](send-method-spec.md) - Send class method naming and parameter specifications
- [Adapter Development Guide](../developer-guide/adapters/) - Complete guide to adapter development

**Module side (avoiding manual type conversion)**:
- Use `event.reply()` to automatically complete type conversion and target inference; see [Event Wrapper Class Explained](../developer-guide/modules/event-wrapper.md) for details

## 事件转换

> 来源: `docs/en/standards/event-conversion.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/event-conversion.md）

# Adapter Standardization Conversion Specification

> [!TIP]
> **When to read this**: When you are converting platform-native events to OneBot12 standard events in an adapter—use this document as a reference for verifying required fields, message segment structure, extension field naming (the `{platform}_` prefix), and session type inference. Otherwise, skip it.

## 1. Core Principles

1. Strict Compatibility: All standard fields must fully comply with the OneBot12 specification.
2. Explicit Extension: Platform-specific features must be prefixed with `{platform}_` (e.g., `yunhu_form`).
3. Data Integrity: Original event data must be preserved in the `{platform}_raw` field, and the original event type must be preserved in the `{platform}_raw_type` field.
4. Time Standardization: All timestamps must be converted to 10-digit Unix timestamps (seconds precision).
5. Platform Consistency: The `platform` field name must match the name/alias you registered for in ErisPulse.

## 2. Standard Field Requirements

### 2.1 Mandatory Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique event identifier |
| time | integer | Unix timestamp (seconds precision) |
| type | string | Event type |
| detail_type | string | Event detail type (see [Session Type Standard](session-types.md)) |
| platform | string | Platform name |
| self | object | Bot self information |
| self.platform | string | Platform name |
| self.user_id | string | Bot user ID |

**detail_type Specification**:
- Must use ErisPulse standard session types (see [Session Type Standard](session-types.md)).
- Supported types: `private`, `group`, `user`, `channel`, `guild`, `thread`.
- The adapter is responsible for mapping native platform types to standard types.

### 2.2 Message Event Fields

| Field | Type | Description |
|-------|------|-------------|
| message | array | Message segment array |
| alt_message | string | Alternate message text |
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |

### 2.3 Notice Event Fields

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| operator_id | string | Operator ID (optional) |

### 2.4 Request Event Fields

| Field | Type | Description |
|-------|------|-------------|
| user_id | string | User ID |
| user_nickname | string | User nickname (optional) |
| comment | string | Request comment (optional) |
| request_id | string | Request identifier (strongly recommended, used for approve/reject request operations) |

**`request_id` Field Explanation**:
- `request_id` is the unique operation identifier for request events, used to execute approve/reject operations via the `HandleRequest` DSL.
- The adapter, when converting request events, should map the native platform request identifier to this field.
- If the platform does not have a request ID, the adapter should generate a unique identifier (e.g., based on a hash of timestamp + user ID).
- When `request_id` is missing, `event.approve()` / `event.reject()` will raise a `ValueError`.

## 3. Event Format Examples

### 3.1 Message Event (message)

```json
{
  "id": "1234567890",
  "time": 1752241223,
  "type": "message",
  "detail_type": "group",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "message": [
    {
      "type": "text",
      "data": {
        "text": "抽奖 超级大奖"
      }
    }
  ],
  "alt_message": "抽奖 超级大奖",
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "yunhu_raw": {...},
  "yunhu_raw_type": "message.receive.normal",
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  }
}
```

### 3.2 Notice Event (notice)

```json
{
  "id": "1234567891",
  "time": 1752241224,
  "type": "notice",
  "detail_type": "group_member_increase",
  "platform": "yunhu",
  "self": {
    "platform": "yunhu",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "group_id": "group_789",
  "operator_id": "",
  "yunhu_raw": {...},
  "yunhu_raw_type": "bot.followed"
}
```

### 3.3 Request Event (request)

```json
{
  "id": "1234567892",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "请加好友",
  "request_id": "req_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 4. Message Segment Standard

### 4.1 Standard Message Segments

Standard message segments **do not** require a platform prefix.

| Type | Description | data fields |
|------|-------------|-------------|
| `text` | Plain text | `text: str` |
| `image` | Image | `file`, `url: str` |
| `audio` | Audio | `file`, `url: str` |
| `video` | Video | `file`, `url: str` |
| `file` | File | `file`, `url: str`, `filename: str` |
| `mention` | @User | `user_id: str`, `user_name: str` |
| `reply` | Reply | `message_id: str` |
| `face` | Emoji | `id: str` |
| `location` | Location | `latitude: float`, `longitude: float` |
| `keyboard` | Button/Inline Keyboard | `rows: list[list[button]]` (see 4.1.1) |

**Media Segment `file` Field Format** (send direction, `image` / `audio` / `video` / `file` generic):

| Form | Example | Adapter Requirement |
|------|---------|---------------------|
| HTTP(S) URL | `https://example.com/a.png` | **Must** accept |
| Local File Path | `/tmp/a.png`, `C:\tmp\a.png` | **Must** accept |
| Binary Data | `bytes` | **Must** accept |
| `file://` URI / Base64 / Data URI | `file:///tmp/a.png`, `data:image/png;base64,...` | **Should** accept |

> Complete media sending protocol (form determination order, filename derivation, capability degradation ladder) see
> [Sending Method Specification §2.1](send-method-spec.md#21-media-message-sending-protocolimage--voice--video--file).

**Field Direction Semantics**:

- `file`: **Send direction** content source (above forms); **Receive direction** filled by adapter with platform retrievable forms
  (usually downloadable URL, or resource identifiers usable by `get_file`-type actions)
- `url`: **Receive direction** platform backlink (adapter should fill as much as possible when converting platform events, for modules to directly use); **Send direction** can be left blank
- `filename`: `file` segment filename (send direction optional, default to adapter generating by
  [Sending Method Specification §2.1.3](send-method-spec.md) derivation order; receive direction **should** fill platform original filename)

```json
{
  "type": "text",
  "data": {
    "text": "Hello World"
  }
}
```

### 4.1.1 keyboard Button/Inline Keyboard Segment (Cross-Platform Universal)

Buttons/inline keyboards exist in multiple platforms (Telegram / Yunhu / QQBot / Kook / Discord), and are a **cross-platform universal concept**, thus as a standard message segment (no platform prefix). Adapters should convert standard segments to platform-native structures; platform-native extension segments (e.g., `telegram_inline_keyboard`) continue to be retained and passed through.

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Option A", "type": "callback", "data": "vote:A"},
        {"label": "Official Site", "type": "link", "data": "https://example.com"}
      ]
    ]
  }
}
```

**Field Explanation**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rows` | 2D array | Yes | Each sub-array is a row of buttons |
| `rows[][].label` | str | Yes | Button display text |
| `rows[][].type` | str | Yes | `callback` (click back data) / `link` (jump to URL) |
| `rows[][].data` | str | Yes | Callback data (type=callback) or jump address (type=link) |
| `rows[][].*` | Any | No | Platform-specific optional fields (e.g., `web_app`, `menus`), adapter maps or ignores as capability allows |

**Adapter Conversion Reference** (full mapping and interaction callback event standard see [Cross-Platform Interaction Component Standard](standardization-guide.md)):

| Platform | Standard Segment → Platform Native |
|----------|------------------------------------|
| Telegram | `inline_keyboard`: `[{text, callback_data \| url}]` |
| Yunhu | `buttons`: `[{label, action_type: 2=callback \| 1=jump, ...}]` |
| QQBot | `keyboard.content.rows`: `[{label, type: 2=callback \| 0=jump, data}]` (requires markdown-type message) |
| Kook | Card action-group module |
| Discord | components: `action_row` + `buttons` (custom_id/url) |

### 4.2 Platform Extension Message Segments

Platform-specific message segments must be prefixed with the platform name:

```json
// Yunhu - Form
{"type": "yunhu_form", "data": {"form_id": "123456", "form_name": "Registration Form"}}

// Telegram - Sticker
{"type": "telegram_sticker", "data": {"file_id": "CAACAgIAAxkBAA...", "emoji": "😂"}}
```

**Extension Message Segment Requirements**:
1. **No prefix in `data` internal fields**: `{"type": "yunhu_form", "data": {"form_id": "..."}}` instead of `{"type": "yunhu_form", "data": {"yunhu_form_id": "..."}}`
2. **Provide fallback solutions**: Modules may not recognize extension message segments, adapters should provide text alternatives in `alt_message`
3. **Complete documentation**: Each extension message segment must be documented in the adapter documentation, specifying `type`, `data` structure, and usage scenarios

## 5. Handling Unknown Events

For events that cannot be recognized, a warning event should be generated:
```json
{
  "id": "1234567893",
  "time": 1752241223,
  "type": "unknown",
  "platform": "yunhu",
  "yunhu_raw": {...},
  "yunhu_raw_type": "unknown",
  "warning": "Unsupported event type: special_event",
  "alt_message": "This event type is not supported by this system."
}
```

---

## 6. Extension Naming Convention

### 6.1 Field Naming

**Rule**: `{platform}_{field_name}`

```
Platform Prefix    Field Name            Full Field Name
────────────────── ───────────────────── ─────────────────────
yunhu              command               yunhu_command
telegram           sticker_file_id       telegram_sticker_file_id
onebot11           anonymous             onebot11_anonymous
email              subject               email_subject
```

**Requirements**:
- `platform` must exactly match the platform name registered in the adapter (case-sensitive)
- `field_name` uses `snake_case` naming
- Double underscores `__` are prohibited (reserved for Python)
- No field name should conflict with standard fields (e.g., `type`, `time`, `message`, etc.)

### 6.2 Message Segment Type Naming

**Rule**: `{platform}_{segment_type}`

Standard message segment types (`text`, `image`, `audio`, `video`, `mention`, `reply`, etc.) **must not** have a platform prefix. Only platform-specific message segment types require a prefix.

### 6.3 Raw Data Field Naming

The following field names are **reserved fields** that all adapters must follow:

| Reserved Field | Type | Description |
|----------------|------|-------------|
| `{platform}_raw` | `any` | A deep copy of the raw event data from the platform |
| `{platform}_raw_type` | `string` | The raw event type identifier from the platform |

**Requirements**:
- `{platform}_raw` must be a deep copy of the raw data, not a reference
- `{platform}_raw_type` must be a string, even if the platform uses a numeric type, it must be converted to a string
- These two fields must be present in all events (if unavailable, use `null` and empty string `""`)

### 6.4 Examples of Platform-Specific Fields

```json
{
  "yunhu_command": {
    "name": "抽奖",
    "args": "超级大奖"
  },
  "yunhu_form": {
    "form_id": "123456"
  },
  "telegram_sticker": {
    "file_id": "CAACAgIAAxkBAA..."
  }
}
```

### 6.5 Nested Extension Fields

Extension fields can be simple values or nested objects:

```json
{
  "telegram_chat": {
    "id": 123456,
    "type": "supergroup",
    "title": "My Group"
  },
  "telegram_forward_from": {
    "user_id": "789",
    "user_name": "ForwardUser"
  }
}
```

**Nested Field Requirements**:
- The top-level key must have a platform prefix
- Nested internal fields **do not** have platform prefixes
- Nesting depth should not exceed 3 levels

### 6.6 Extension of `self` Field

The standard required fields of the `self` object (`platform`, `user_id`) are listed in §2.1. The following are ErisPulse extensions for optional fields:

| Field | Type | Description |
|-------|------|-------------|
| `self.user_name` | `string` | Bot nickname |
| `self.avatar` | `string` | Bot avatar URL |
| `self.account_id` | `string` | Account identifier in multi-account mode |

> **Bot Status Tracking**: Adapters inform the framework of the bot's connection status by sending `type: "meta"` events. Supported `detail_type`: `connect` (online), `heartbeat` (heartbeat), `disconnect` (offline). The system automatically extracts bot metadata from the `self` field in these events for status tracking. Additionally, the `self` field in regular events is also automatically detected as the bot. See [Adapter System API - Bot Status Management](../api-reference/adapter-system.md).

---

## 7. Session Type Extension

ErisPulse extends the OneBot12 standard `private`, `group` with the following session types:

| Type | OneBot12 Standard | ErisPulse Extension | Description |
|------|:-----------------:|:-------------------:|-------------|
| `private` | ✅ | — | One-on-one private chat |
| `group` | ✅ | — | Group chat |
| `user` | — | ✅ | User type (Telegram, etc.) |
| `channel` | — | ✅ | Channel (broadcast-style) |
| `guild` | — | ✅ | Server/community |
| `thread` | — | ✅ | Topic/sub-channel |

**Adapter Custom Type Extension**:

```python
from ErisPulse.Core.Event.session_type import register_custom_type

# Register in adapter startup
register_custom_type(
    receive_type="email",      # detail_type in receive events
    send_type="email",         # target type when sending
    id_field="email_id",       # corresponding ID field name
    platform="email"           # platform identifier
)
```

**Custom Type Requirements**:
- Must be registered in the adapter `start()` and unregistered in `shutdown()`
- `receive_type` should not conflict with standard types
- `id_field` should follow the `{target}_id` naming pattern

> Full session type definition and mapping relationship see [Session Type Standard](session-types.md).

---

## 8. Module Developer Guide

### 8.1 Accessing Extension Fields

```python
from ErisPulse.Core.Event import message

@message()
async def handle_message(event):
    # Access standard fields
    text = event.get_text()
    user_id = event.get_user_id()

    # Access platform extension fields - Method 1: Direct get
    yunhu_command = event.get("yunhu_command")

    # Access platform extension fields - Method 2: Dot-style access (Event wrapper class)
    # event.yunhu_command

    # Access raw data
    raw_data = event.get("yunhu_raw")
    raw_type = event.get_raw_type()

    # Platform judgment
    platform = event.get_platform()
    if platform == "yunhu":
        pass
    elif platform == "telegram":
        pass
```

### 8.2 Handling Extension Message Segments

```python
@message()
async def handle_message(event):
    message_segments = event.get("message", [])

    for segment in message_segments:
        seg_type = segment.get("type")
        seg_data = segment.get("data", {})

        if seg_type == "text":
            text = seg_data["text"]
        elif seg_type.startswith("yunhu_"):
            if seg_type == "yunhu_form":
                form_id = seg_data["form_id"]
        elif seg_type.startswith("telegram_"):
            if seg_type == "telegram_sticker":
                file_id = seg_data["file_id"]
```

### 8.3 Best Practices

1. **Prefer standard fields**: Do not assume extension fields will always exist
2. **Platform judgment**: Use `event.get_platform()` to determine the platform, not by checking the existence of extension fields
3. **Graceful degradation**: Use `alt_message` as a fallback when unable to handle extension message segments
4. **Do not hardcode prefixes**: Use `platform` variable to dynamically construct

```python
# ✅ Recommended
platform = event.get_platform()
raw_data = event.get(f"{platform}_raw")

# ❌ Not recommended
raw_data = event.get("yunhu_raw")
```

### 8.4 Request Event Handling

Module developers can use `event.approve()` and `event.reject()` to handle request events:

```python
from ErisPulse.Core.Event import request

# Friend request: Automatically approve
@request.on_friend_request()
async def handle_friend_request(event):
    user_name = event.get_user_nickname() or event.get_user_id()
    comment = event.get_comment()
    
    # Approve request
    result = await event.approve()
    if result.get("status") == "ok":
        print(f"Approved friend request from {user_name}")
    else:
        print(f"Failed to approve friend request: {result.get('message')}")

# Group request: Decide based on conditions
@request.on_group_request()
async def handle_group_request(event):
    comment = event.get_comment()
    
    # Reject request
    result = await event.reject(comment="Not joining new group for now")
```

**Direct operation via adapter** (for non-event handler scenarios):

```python
from ErisPulse import adapter

# Directly operate via request_id
await adapter.myplatform.Request("req_abc123").accept()
await adapter.myplatform.Request("req_abc123").reject()

# Specify bot account for operation
await adapter.myplatform.Request("req_abc123").Using("bot1").accept()

# With comment
await adapter.myplatform.Request("req_abc123").accept(comment="Welcome")
```

---

## 9. Session Type Inference for notice / request Events

### 9.1 Problem Background

The `detail_type` of `notice` events and `request` events are **semantic subtypes** (e.g., `group_member_increase`, `friend_increase`), not session types (e.g., `group`, `private`).

```
type        detail_type                  Meaning            Session Type
────        ───────────                  ────            ────────
message     group                        Group message         group (detail_type is session type)
message     private                      Private message       private (detail_type is session type)
notice      group_member_increase        Group member increase group (inferred from group_id)
notice      friend_increase              Friend increase       private (inferred from user_id)
request     friend                       Friend request        private (inferred from user_id)
request     group                        Group request         group (detail_type is session type)
```

### 9.2 Inference Rules

The inference order of `infer_receive_type()`:

1. If `detail_type` is a known session type (`private`/`group`/`channel`/`guild`/`thread`/`user`), use it directly.
2. If `detail_type` is a custom session type, use it directly.
3. Otherwise (for semantic subtypes of notice/request), infer from ID fields:
   - If `group_id` exists → `"group"`
   - If `channel_id` exists → `"channel"`
   - If `guild_id` exists → `"guild"`
   - If `thread_id` exists → `"thread"`
   - If `user_id` exists → `"private"`

### 9.3 `event.reply()` Target Inference

The sending target of `event.reply()` in notice/request events is determined by the inferred session type:

- Group notice events (with `group_id`) → reply to the **group**
- Friend notice events (with only `user_id`) → reply to the **private user**

```python
from ErisPulse.Core.Event import notice

@notice.on_group_increase()
async def handle_welcome(event):
    group_id = event.get("group_id")    # "group_789"
    user_id = event.get("user_id")      # "user_456"

    # event.reply() sends to group (group/group_789)
    await event.reply("Welcome to the group!")

    # To notify admin (private chat), specify target explicitly:
    await adapter.Send.To("user", "admin_id").Text(f"New member {user_id} joined {group_id}")
```

### 9.4 Adapter Development Recommendations

Ensure `notice`/`request` events contain correct ID fields:

| detail_type | Required ID Fields | Inferred Session Type |
|-------------|-------------------|-----------------------|
| `group_member_increase` | `group_id` + `user_id` | `group` |
| `group_member_decrease` | `group_id` + `user_id` | `group` |
| `friend_increase` | `user_id` | `private` |
| `friend_decrease` | `user_id` | `private` |
| `friend` (request) | `user_id` | `private` |
| `group` (request) | `group_id` | `group` |

---

## 10. Related Documentation

**Companion reference when implementing converters**:
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships
- [API Response Standard](api-response.md) - Adapter API response format standard

**Sending side of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming, parameter specifications for Send-type methods, and reverse conversion requirements
- [API Action Standard](api-action-spec.md) - Unified interface for OneBot12 standard API actions

**Look up known extended events and message segments for each platform**:
- [Platform Features Documentation](../platform-guide/README.md) - You can visit this documentation to learn about the features of each platform, as well as known extended events and message segments.

## 发送方法规范

> 来源: `docs/en/standards/send-method-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/send-method-spec.md）

# ErisPulse Send Method Specification

> [!TIP]
> **When to read this**: When implementing the `Send` class in your adapter—refer to this document for method naming, media parameter (URL/path/bytes) support, `Raw_ob12` reverse conversion, and merge forwarding capabilities. Skip if not needed.

This document defines the naming, parameter, and reverse conversion requirements for send methods in ErisPulse adapters.

## 0. Keyword Definitions

The terms **must (MUST)**, **should (SHOULD)**, and **may (MAY)** in this document are interpreted as follows (referencing RFC 2119):

| Keyword | Meaning | Consequence of Violation |
|--------|------|---------|
| **Must** | Mandatory requirement; framework behavior/cross-platform consistency depends on it | Adapter is considered non-compliant; module code may not work |
| **Should** | Strongly recommended; follow unless there is a compelling reason | If deviated, the adapter documentation must explain the reason and alternative behavior |
| **May** | Optional; decide based on platform capability | None |

## 1. Standard Method Naming

All send methods use **PascalCase** (capitalized first letter).

### 1.1 Standard Send Methods

| Method Name | Description | Parameter Type | Implementation Requirement |
|-------|------|---------|---------|
| `Text` | Send text message | `str` | Must |
| `Image` | Send image | `str` \| `bytes` | Must (built-in in base class; see §6.4) |
| `Voice` | Send voice | `str` \| `bytes` | Must (built-in in base class; if platform does not support voice, follow §2.1.5) |
| `Video` | Send video | `str` \| `bytes` | Must (built-in in base class; if platform does not support video, follow §2.1.5) |
| `File` | Send file | `str` \| `bytes`, `filename: str \| None = None` | Must (built-in in base class) |
| `At` | @ user/group | `str` (user_id) | Modifier method, optional |
| `Face` | Send emoji | `str` (emoji) | May |
| `Reply` | Reply to message | `str` (message_id) | Modifier method, optional |
| `Forward` | Forward message | `str` (message_id) | May |
| `Markdown` | Send Markdown message | `str` | May |
| `HTML` | Send HTML message | `str` | May |
| `Card` | Send card message | `dict` | May |

> Standard methods (`Text`/`Image`/`Voice`/`Video`/`File`) are built into the base class `SendDSL` and default to delegating to `Raw_ob12`. Adapters **do not need to re-implement** these methods to obtain type signatures; only override individual methods when the platform requires special logic (see §6.4).

### 1.2 Chained Modifier Methods

| Method Name | Description | Parameter Type |
|-------|------|---------|
| `At` | @ user (can be called multiple times) | `str` (user_id) |
| `AtAll` | @ all members | None |
| `Reply` | Reply to message | `str` (message_id) |

### 1.3 Protocol Methods

| Method Name | Description | Required? |
|-------|------|---------|
| `Raw_ob12` | Send OneBot12 format message segment | Must |

**`Raw_ob12` is a required method**. This is one of the adapter's core responsibilities: receiving OneBot12 standard message segments and converting them into native platform API calls. `Raw_ob12` serves as the unified entry point for reverse conversion (OneBot12 → platform), ensuring modules can send messages using standard message segments without relying on platform-specific methods.

**Behavior when `Raw_ob12` is not overridden**: The default base class implementation will log an **error-level** message and return a standard error response format (`status: "failed"`, `retcode: 10002`), indicating that the adapter developer must implement this method.

### 1.4 Recommended Extension Naming Convention

If adapters need to support sending non-OneBot12 format raw data (such as platform-specific JSON, XML, etc.), the following naming convention is recommended:

| Recommended Method Name | Description |
|-----------|------|
| `Raw_json` | Send arbitrary JSON data |
| `Raw_xml` | Send arbitrary XML data |

**Note**: These methods are **not** default methods provided by the base class, nor are they mandatory to implement. They are only naming conventions, and adapters can define them as needed. If an adapter does not support these formats, it does not need to define them.

**MessageBuilder**: ErisPulse provides the `MessageBuilder` utility class for easily constructing OneBot12 message segment lists, which can be used in conjunction with `Raw_ob12`. See [MessageBuilder Detailed Explanation](../advanced/message-builder.md).

## 2. Parameter Specification Details

### 2.1 Media Message Sending Protocol (`Image` / `Voice` / `Video` / `File`)

This section is the **unified protocol standard** for media sending: modules can use the same code to call the four media methods, and adapters are responsible for converting the various forms of the `file` parameter into native platform upload/send behavior.

#### 2.1.1 Valid Forms of the `file` Parameter

| Form | Example | Adapter Requirement |
|------|------|-----------|
| HTTP(S) URL | `https://example.com/image.jpg` | **Must** accept |
| Local file path | `/path/to/file.jpg`, `C:\path\to\file.jpg` | **Must** accept |
| Binary data | `b"\x89PNG..."` | **Must** accept |
| `file://` URI | `file:///path/to/file.jpg` | **Should** accept (can be forwarded as a local path) |
| Base64 string / Data URI | `iVBORw0KGgo=...`, `data:image/png;base64,...` | **Should** accept (compatible with OneBot12 ecosystem conventions) |

> Adapters **must** behave consistently across the three required forms—modules receive the same message regardless of whether they pass a URL, path, or bytes. If the platform cannot directly use a certain form (e.g., the platform API does not support referencing external URLs), the adapter should download/read and then upload, **not** require the module to retry with a different form.

#### 2.1.2 Form Determination Order

When implementing media parameter handling, adapters **should** determine the form in the following order:

1. `bytes` type → upload directly
2. String starting with `http://` / `https://` → handle as URL (direct reference or download and upload, depending on platform capability)
3. String starting with `file://` → strip prefix and handle as local path
4. Other strings → handle as local path (read and upload if exists; return standard error response if does not exist)

```python
def _resolve_media(self, file: "str | bytes") -> bytes:
    """Form determination and normalization (example)"""
    if isinstance(file, (bytes, bytearray)):
        return bytes(file)
    if file.startswith(("http://", "https://")):
        return self._download(file)          # download if platform cannot reference URL
    if file.startswith("file://"):
        file = file[len("file://"):]
    with open(file, "rb") as f:              # local path
        return f.read()
```

#### 2.1.3 File Name Semantics for `File`

`File` method signature: `File(file, filename=None)` (where `filename` is optional; built-in in base class).

File name **derivation order** (when adapter generates file name without explicit `filename`):

1. Explicit `filename` parameter (highest priority)
2. URL's basename (e.g., `https://host/a/b/report.pdf` → `report.pdf`, query string stripped)
3. Local path's basename (e.g., `/tmp/data/backup.zip` → `backup.zip`)
4. Platform default generation (e.g., `file_{timestamp}`; **should** retain real extension—extension affects platform-side type recognition and preview behavior)

> `Image` / `Voice` / `Video` can also accept `filename` (passed via message segment `data.filename`), but only `File`'s file name has cross-platform semantic guarantees.

#### 2.1.4 Declaration Obligation for Platform Restrictions

Platforms have different constraints on media size, format (MIME), duration (audio/video), etc. Adapters **should**:

- Declare supported media types and limits in the adapter documentation
- Return **standard error response** for over-limit or unsupported input (`status: "failed"`; `retcode` uses `10002` or platform-specific error code, `message` explains the reason), **not** throw an exception to interrupt module logic

#### 2.1.5 Capability Degradation Steps

When a platform does not support a certain media **type**, follow the following degradation steps (in line with the "capability degradation without error" principle):

| Scenario | Degradation Behavior |
|------|---------|
| `Voice` does not support voice messages | **Should** send as `File` (or platform-adjacent form); if cannot express, return `retcode=10002` |
| `Video` does not support video messages | Same as above |
| Media type completely unsupported (no file capability) | Return `retcode=10002`, `message` indicates unsupported data type |
| Form not supported (e.g., cannot handle base64) | Return `retcode=10002`, **can** in `message` prompt module to use URL/bytes |

**Prohibited actions**: Silent discard (no return), throw an exception, or require module to write platform-specific handling.

### 2.2 @ User Parameter Specification

**Method:** `At` (modifier method)

**Parameter:** `user_id` (`str`)

**Requirements:**
- `user_id` should be a string-type user identifier
- The `user_id` format may differ across platforms (numbers, UUIDs, strings, etc.)
- The adapter is responsible for converting `user_id` into the platform-specific format
- Note that the actual send method call should be placed at the last position.

**Example:**
```python
# Single @ user
Send.To("group", "g123").At("123456").Text("Hello")

# Multiple @ users (chained call)
send.To("group", "g123").At("123456").At("789012").Text("Hello everyone")
```

### 2.3 Reply Message Parameter Specification

**Method:** `Reply` (modifier method)

**Parameter:** `message_id` (`str`)

**Requirements:**
- `message_id` should be a string-type message identifier
- Should be the ID of a previously received message
- Some platforms may not support the reply function; adapters should degrade gracefully

**Example:**
```python
send.To("group", "g123").Reply("msg_123456").Text("Received")
```

### 2.4 Merge Forward Capability (`MergeForward`, Optional)

`MergeForward(nodes)` is an **optional capability method**: it packages multiple contents into a "merged forward / rich text collapse" form for sending, with the adapter deciding the best presentation based on platform capability. This differs semantically from `Forward(from_chat_id, message_id)` (forwarding **existing** messages) in §1.1; both coexist.

> **Standard Background**: The OneBot12 core standard does not have a node message segment or a merged forward API—"message node" is a concept implemented at the OneBot v11 ecosystem level (go-cqhttp extension), and v12 has delegated such platform-specific capabilities to the extension mechanism. ErisPulse's landing approach is equivalent to the extension mechanism: **no new standard message segments are added, but optional capability methods + `list_sends` runtime detection**—adapters that implement `MergeForward` automatically gain capability, and those that do not implement it automatically fall back to plain text, with zero module modifications.

**Method Signature:**

```python
def MergeForward(self, nodes: List[Dict]) -> asyncio.Task:
    """
    Send merged forward / rich text collapse message

    :param nodes: List of merged forward nodes (go-cqhttp extension's OneBot v11 node format):
        [
            {
                "type": "node",
                "data": {
                    "user_id": "10000",     # Displayed sender ID
                    "nickname": "MyBot",     # Displayed sender nickname
                    "content": [            # List of message segments, currently text segments
                        {"type": "text", "data": {"text": "【1/3】Title\nBody…"}}
                    ],
                },
            },
        ]
    :return: asyncio.Task, await to return standard response format
    """
```

**Implementation Requirements:**

1. **Platform has native merged forward** (OneBot11 system): **Must** call the dedicated protocol endpoint (`send_group_forward_msg` / `send_private_forward_msg`)—NapCat implementations will reject `send_msg` carrying node segments (retcode 1400); if the dedicated endpoint fails, **can** fall back to `send_msg` sending node segments directly
2. **Platform has no native forward but has rich text** (Yunhu / Telegram / Kook / Discord / Matrix, etc.): **Should** render nodes into the platform's rich text collapse form (HTML collapse card / Card / Embed / blockquote list), refer to style and adapter-specific task list in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`
3. **Neither exists**: **Should not** implement this method (and must not return success while sending node dictionaries as plain text)—if not implemented, `list_sends` does not contain `MergeForward`, and the caller automatically falls back to plain text
4. **Failure semantics**: Return standard error response (`status: "failed"`) or throw an exception is acceptable; the caller will fall back to plain text sending, and content is not lost
5. **Should not** call `Raw_ob12` to send the same nodes inside `MergeForward` (OneBot11's `Raw_ob12` has built-in automatic routing of pure node segments, which would cause a loop)
6. **Outbound node segment parsing** (universal adapter convention): Each adapter's `Raw_ob12` segment distribution should register `node` segments—pure node lists are automatically routed to the adapter's merged forward presentation (platforms with `MergeForward` are equivalent to direct calls; platforms without this method extract each node's text to output "nickname: body" line by line in original form); text from node segments in mixed lists is merged into the body.
   Any adapter receiving a node segment must not silently discard it.

**Platform Implementation Forms** (see `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`):

- Native endpoint: OneBot11, SnowLuma (three-tiered fallback: `send_group/private_forward_msg` dedicated endpoint → `upload_forward_msg` to get resid and send forward segment → send node segments directly; SnowLuma API aligns fully with NapCat, adapters can directly connect to NapCat backend)
- Folded HTML `<details>` card: Yunhu (bot/user protocol), Email, Sandbox, Allons(Ideaura)
- Whitelisted HTML / quote block: Telegram (`<b>`+`<blockquote>`), Matrix (blockquote variant, whitelisted stripping of details/internal styles)
- Platform card: Kook (Card header+section), Discord (Embed fields)
- Official Markdown quote list: QQBot (official md has no collapse syntax, server-side validation rejects invalid tags 40034011)
- Not implemented (node segments output as original text for degradation): OneBot12 (standard has no node segments), WeCom, Terminal, Webhook, WechatMp

**Caller Detection Example:**

```python
sends = adapter.list_sends(platform)
if "MergeForward" in sends:
    await adapter.Send.To("group", "123").MergeForward(nodes)
else:
    await adapter.Send.To("group", "123").Text(plain_text)
```

> Reference Implementation: `ErisPulse-OneBot11Adapter` (dedicated endpoint → `send_msg` fallback); rendering templates and adapter-specific task lists are in `SDK/Adapter/ADAPTER_FORWARD_GUIDE.md`.

## 3. Platform-Specific Method Naming

**Not recommended** to directly add platform-prefixed methods in the `Send` class. Use generic method names or `Raw_{protocol}` methods.

**Not recommended:**
```python
def YunhuForm(self, form_id: str):  # ❌ Not recommended
    pass

def TelegramSticker(self, sticker_id: str):  # ❌ Not recommended
    pass
```

**Recommended:**
```python
def Form(self, form_id: str):  # ✅ Generic method name
    pass

def Sticker(self, sticker_id: str):  # ✅ Generic method name
    pass

def Raw_ob12(self, message):  # ✅ Send OneBot12 format
    pass
```

**Extension Method Requirements**:
- Method names use PascalCase, no platform prefix
- Must return an `asyncio.Task` object
- Must provide complete type annotations and docstrings
- Parameter design should be as consistent as possible with standard method styles

## 4. Parameter Naming Convention

| Parameter Name | Description | Type |
|-------|------|------|
| `text` | Text content | `str` |
| `file` | Media content (URL/path/bytes, see §2.1.1) | `str` / `bytes` |
| `filename` | File name (`File` optional, see §2.1.3) | `str` / `None` |
| `user_id` | User ID | `str` / `int` |
| `group_id` | Group ID | `str` / `int` |
| `message_id` | Message ID | `str` |
| `data` | Data object (e.g., card data) | `dict` |

## 5. Return Value Convention

- **Send methods** (e.g., `Text`, `Image`): Must return an `asyncio.Task` object
- **Modifier methods** (e.g., `At`, `Reply`, `AtAll`): Must return `self` to support chained calls

---

## 6. Reverse Conversion Convention (OneBot12 → Platform)

Adapters must not only convert platform-native events into OneBot12 format (forward conversion), but also **must** provide the ability to convert OneBot12 message segments back into platform-native API calls (reverse conversion). The unified entry point for reverse conversion is the `Raw_ob12` method.

### 6.1 Conversion Model

```
Forward Conversion (Receiving Direction)                Reverse Conversion (Sending Direction)
─────────────────                ─────────────────
Platform-native Event                       OneBot12 Message Segment List
    │                                  │
    ▼                                  ▼
Converter.convert()               Send.Raw_ob12()
    │                                  │
    ▼                                  ▼
OneBot12 Standard Event                  Platform-native API Call
(Containing {platform}_raw)             (Return Standard Response Format)
```

**Core Symmetry**: Forward conversion retains original data in `{platform}_raw`, and reverse conversion accepts OneBot12 standard format and restores it into a platform call.

### 6.2 `Raw_ob12` Implementation Convention

`Raw_ob12` receives OneBot12 standard message segment lists and must convert them into platform-native API calls.

**Method Signature**:

```python
def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
    """
    Send OneBot12 Standard Message Segments

    :param message_segments: List of OneBot12 message segments
        [
            {"type": "text", "data": {"text": "Hello"}},
            {"type": "image", "data": {"file": "https://..."}},
            {"type": "mention", "data": {"user_id": "123"}},
        ]
    :return: asyncio.Task, await to return standard response format
    """
```

**Implementation Requirements**:

1. **Must handle all standard message segment types**: At least support `text`, `image`, `audio`, `video`, `file`, `mention`, `reply`
2. **Must handle platform extension message segments**: For `{platform}_xxx` type message segments, convert them into corresponding platform-native calls
3. **Must return standard response format**: Follow [API Response Standard](api-response.md)
4. **Unsupported message segments should be skipped and warning logged**, not throw an exception causing the entire message to fail

### 6.3 Message Segment Conversion Rules

#### 6.3.1 Standard Message Segment Conversion

Adapters must implement the following standard message segment conversions:

| OneBot12 Message Segment | Conversion Requirement |
|----------------|---------|
| `text` | Directly use `data.text` |
| `image` | `data.file` handled according to §2.1 media protocol (three must forms + determination order) |
| `audio` | Same handling logic as image |
| `video` | Same handling logic as image |
| `file` | Same handling logic as image; filename handled according to §2.1.3 derivation order for `data.filename` |
| `mention` | Convert to platform's @ user mechanism (e.g., Telegram's `entities`, Yunhu's `at_uid`) |
| `reply` | Convert to platform's reply reference mechanism |
| `face` | Convert to platform's emoji sending mechanism, skip if not supported |
| `location` | Convert to platform's location sending mechanism, skip if not supported |

#### 6.3.2 Platform Extension Message Segment Conversion

For message segments with platform prefixes, adapters should recognize and convert them:

```python
def _convert_ob12_segments(self, segments: List[Dict]) -> Any:
    """Convert OneBot12 message segments to platform-native format"""
    platform_prefix = f"{self._platform_name}_"
    
    for segment in segments:
        seg_type = segment["type"]
        seg_data = segment["data"]
        
        if seg_type.startswith(platform_prefix):
            # Platform extension message segment → platform-native call
            self._handle_platform_segment(seg_type, seg_data)
        elif seg_type in self._standard_segment_handlers:
            # Standard message segment → platform equivalent operation
            self._standard_segment_handlers[seg_type](seg_data)
        else:
            # Unknown message segment → log warning and skip
            logger.warning(f"Unsupported message segment type: {seg_type}")
```

#### 6.3.3 Handling of Composite Message Segments

A message may contain multiple message segments, and adapters need to handle composite messages correctly:

```python
# Module sends a message containing text+image+@ user
await send.Raw_ob12([
    {"type": "mention", "data": {"user_id": "123"}},
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "image", "data": {"file": "https://example.com/img.jpg"}}
])
```

**Handling Strategy**:
- **Prioritize merging**: If the platform supports combining text, image, @, etc., in a single message, merge and send
- **Fallback to splitting**: If the platform does not support merging, send as multiple messages in sequence
- **Maintain order**: The sending order of message segments should match the list order

### 6.4 Relationship Between `Raw_ob12` and Standard Methods

The adapter's standard send methods (`Text`, `Image`, etc.) are **already implemented and default-delegated to `Raw_ob12` by the `SendDSL` base class**; adapter subclasses do not need to re-implement them:

```python
class Send(SendDSL):
    def Raw_ob12(self, message_segments: List[Dict]) -> asyncio.Task:
        """Core implementation: OneBot12 message segments → platform API (must implement)"""
        return asyncio.create_task(self._send_ob12(message_segments))

    # Text/Image/Voice/Video/File inherited from base class, automatically delegated to Raw_ob12
    # If platform-specific logic is needed, override individual methods:
    # def Text(self, text: str) -> asyncio.Task:
    #     return self.Raw_ob12([{"type": "text", "data": {"text": text}}])
```

**Benefits**:
- Conversion logic is centralized in `Raw_ob12`, reducing duplicate code
- Standard methods and `Raw_ob12` have identical behavior
- Modules get the same result whether using `Text()` or `Raw_ob12()`
- The base class provides type signatures, allowing IDE to complete standard methods

### 6.5 Implementation Example

```python
class YunhuSend(SendDSL):
    """Yunhu platform Send implementation"""
    
    def Raw_ob12(self, message_segments: list) -> asyncio.Task:
        """OneBot12 message segments → Yunhu API call"""
        return asyncio.create_task(self._do_send(message_segments))
    
    async def _do_send(self, segments: list) -> dict:
        """Actual sending logic"""
        # 1. Parse modifier state
        at_users = self._at_users or []
        reply_to = self._reply_to
        at_all = self._at_all
        
        # 2. Convert message segments
        yunhu_elements = []
        for seg in segments:
            seg_type = seg["type"]
            seg_data = seg["data"]
            
            if seg_type == "text":
                yunhu_elements.append({"type": "text", "content": seg_data["text"]})
            elif seg_type == "image":
                yunhu_elements.append({"type": "image", "url": seg_data["file"]})
            elif seg_type == "mention":
                at_users.append(seg_data["user_id"])
            elif seg_type == "reply":
                reply_to = seg_data["message_id"]
            elif seg_type == "yunhu_form":
                # Platform extension message segment
                yunhu_elements.append({"type": "form", "form_id": seg_data["form_id"]})
            else:
                logger.warning(f"Yunhu does not support message segment: {seg_type}")
        
        # 3. Call Yunhu API
        response = await self._call_yunhu_api(yunhu_elements, at_users, reply_to, at_all)
        
        # 4. Return standard response format
        return {
            "status": "ok" if response["code"] == 0 else "failed",
            "retcode": response["code"],
            "data": {"message_id": response.get("msg_id", ""), "time": int(time.time())},
            "message_id": response.get("msg_id", ""),
            "message": "",
            "yunhu_raw": response
        }
```

---

## 7. Method Discovery

Module developers can query the adapter's supported send methods (don't hardcode the platform's method list in the module—each adapter's extension methods evolve with version changes, so runtime discovery is the standard):

```python
from ErisPulse import adapter

# List all send methods
methods = adapter.list_sends("myplatform")
# ["Batch", "Form", "Image", "Recall", "Sticker", "Text", ...]

# View method details
info = adapter.send_info("myplatform", "Form")
# {
#     "name": "Form",
#     "parameters": [{"name": "form_id", "type": "str", ...}],
#     "return_type": "Awaitable[Any]",
#     "docstring": "Send Yunhu form"
# }
```

---

## 9. Adapter Development Notes

For how to correctly override `BaseAdapter`, `Send`, `Request`'s `__init__`, see [Adapter Development Guide - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-注意事项).

---

---

## 10. Adapter Implementation Checklist

### Send Methods
- [ ] Standard methods (`Text`, `Image`, etc.) implemented
- [ ] Return values are all `asyncio.Task`
- [ ] Modifier methods (`At`, `Reply`, `AtAll`) return `self`
- [ ] Platform extension methods use PascalCase, no platform prefix
- [ ] All methods have complete type annotations and docstrings

### Media Sending Protocol
- [ ] `file` parameter **must forms** all supported: HTTP(S) URL / local path / `bytes` (see §2.1.1)
- [ ] Form determination order follows §2.1.2 (bytes → URL → `file://` → path)
- [ ] `File`'s filename derivation order follows §2.1.3 (explicit `filename` > URL basename > path basename > platform default)
- [ ] Platform's media restrictions (size / MIME / duration) are declared in adapter documentation (§2.1.4)
- [ ] Unsupported media types handled by the degradation ladder in §2.1.5: degraded to similar type or return `retcode=10002`, no exception thrown, no silent discard

### Merge Forward (Optional, see §2.4)
- [ ] Platform has native merged forward: `MergeForward` uses protocol dedicated endpoint, fails back to `send_msg` (OneBot11 system)
- [ ] Platform has no native forward but has rich text: `MergeForward` renders into platform's folded form (HTML card / Card / Embed / blockquote)
- [ ] Neither exists: **do not implement** `MergeForward`, do not return success while sending node dictionary as plain text
- [ ] `MergeForward` does not call `Raw_ob12` to forward the same nodes internally

### Reverse Conversion
- [ ] `Raw_ob12` **implemented** (required, cannot skip)
- [ ] `Raw_ob12` can handle all standard message segments (`text`, `image`, `audio`, `video`, `file`, `mention`, `reply`)
- [ ] `Raw_ob12` can handle platform extension message segments (`{platform}_xxx` type)
- [ ] Standard send methods (`Text`, `Image`, etc.) internally delegate to `Raw_ob12`, not implement separate conversion logic
- [ ] Unsupported message segments are skipped and warning logged, not thrown as an exception
- [ ] Composite message segments are correctly handled (merged or sent sequentially)

---

## 11. MessageBuilder - Adapter-Side Notes

`MessageBuilder` is a OneBot12 message segment builder tool provided by ErisPulse, for **module-side** message construction:
Chained calls (or static quick construction) ultimately produce a standard message segment list `[{"type": ..., "data": ...}]`,
which is directly passed to `Raw_ob12` by the caller.

**Adapter-side only needs to know this**: `Raw_ob12` receives exactly this product—structurally identical to a hand-written message segment list,
and processed according to the segment distribution logic in §6.2, without needing to perceive whether it comes from `MessageBuilder` or a literal list.

> Full usage (dual-mode mechanism, all message segment methods, `copy()` / `clear()` utility methods, and examples) is in [MessageBuilder Detailed Explanation](../advanced/message-builder.md), not repeated here.

---

## 12. Related Documents

**For implementing send return values, refer to:**
- [API Response Standard](api-response.md) - Standard format for adapter API responses

**For other sides of the same adapter:**
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification, extension naming, and message segment standard
- [Session Type Standard](session-types.md) - Definition and mapping of session types
- [Request Operation Specification](request-action-spec.md) - Field requirements for request events, HandleRequest DSL, and adapter implementation requirements

## API 动作规范

> 来源: `docs/en/standards/api-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/api-action-spec.md）

# ErisPulse API Action Standard

> [!TIP]
> **When to read this**: When implementing Api DSL standard actions in an adapter (get_user_info / delete_message, etc.), or calling these standard actions cross-platform in a module and needing to confirm parameters and data fields. Skip it if you don't need it.

This document defines the unified interface specification for **OneBot12 standard API actions** in ErisPulse adapters, allowing module developers to program against a standard interface while adapters are responsible for mapping to platform-native APIs.

> **Scope**: Among the OneBot12 standard actions, `ApiDSL` provides strongly typed methods for user /
> group / guild / message management / Meta regular interfaces (`send_message` is
> handled by `SendDSL.Raw_ob12`). File resource actions (`upload_file` / `get_file` / fragmented) are
> retained only as degraded pass-through, see §3.5. Platform extension actions are invoked through
> the `Api.call("prefix.action", ...)` escape hatch. Action parameters and return structures follow
> the OneBot12 specification (`onebot/specs/interface/` in the repository).

## 1. Design Background

In ErisPulse, message segments (message send/receive) and event formats already fully follow the OneBot12 standard, but **API action calls** (such as getting user info, getting group lists, recalling messages, etc.) were previously not unified—module developers had to write different `call_api` calls for each platform.

`ApiDSL` solves this problem by providing strongly typed standard action methods:

```
Module code (cross-platform unified)       Adapter implementation (platform-specific)
─────────────────              ──────────────────
adapter.Api.get_user_info("123")  →  adapter call_api / override
adapter.Api.get_group_list()      →  adapter call_api / override
adapter.Api.delete_message("id")  →  adapter call_api / override
```

## 2. Three Parallel DSL Classes

ErisPulse adapters have three parallel DSL inner classes, each with its own responsibility:

```
BaseAdapter
├── Send(SendDSL)       ← Message sending (Text/Image/Raw_ob12)
├── Request(RequestDSL)  ← Request operations (accept/reject)
└── Api(ApiDSL)          ← Standard API actions (user/group/guild/message management/file/meta) ★
```

| DSL | Responsibility | Method Style | Return Value |
|-----|------|---------|--------|
| `Send` | Send messages | Chained + `asyncio.Task` | Standard response |
| `Request` | Handle request events | `asyncio.Task` | Standard response |
| `Api` | Query/management operations | `async` methods | Standard response |

## 3. Standard Action List

### 3.1 User-Related

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_self_info()` | `get_self_info` | None | `user_id`, `user_name`, `user_displayname` |
| `get_user_info(user_id)` | `get_user_info` | `user_id: str` | `user_id`, `user_name`, `user_displayname`, `user_remark` |
| `get_friend_list()` | `get_friend_list` | None | `list[get_user_info response]` |

### 3.2 Group-Related

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_group_info(group_id)` | `get_group_info` | `group_id: str` | `group_id`, `group_name` |
| `get_group_list()` | `get_group_list` | None | `list[get_group_info response]` |
| `get_group_member_info(group_id, user_id)` | `get_group_member_info` | `group_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_group_member_list(group_id)` | `get_group_member_list` | `group_id: str` | `list[get_group_member_info response]` |
| `set_group_name(group_id, group_name)` | `set_group_name` | `group_id: str`, `group_name: str` | None |
| `leave_group(group_id)` | `leave_group` | `group_id: str` | None |

### 3.3 Message Management

| Method | OB12 Action | Parameters | Description |
|------|----------|------|------|
| `delete_message(message_id)` | `delete_message` | `message_id: str` | Recall/delete a message |

> **Message sending** (`send_message`) is handled by `SendDSL`'s `Raw_ob12` and is not duplicated in `ApiDSL`.

### 3.4 Guild-Related

The OneBot12 guild system has two levels: **guild** and **channel**.

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_guild_info(guild_id)` | `get_guild_info` | `guild_id: str` | `guild_id`, `guild_name` |
| `get_guild_list()` | `get_guild_list` | None | `list[get_guild_info response]` |
| `set_guild_name(guild_id, guild_name)` | `set_guild_name` | `guild_id: str`, `guild_name: str` | None |
| `get_guild_member_info(guild_id, user_id)` | `get_guild_member_info` | `guild_id: str`, `user_id: str` | `user_id`, `user_name`, `user_displayname` |
| `get_guild_member_list(guild_id)` | `get_guild_member_list` | `guild_id: str` | `list[get_guild_member_info response]` |
| `leave_guild(guild_id)` | `leave_guild` | `guild_id: str` | None |
| `get_channel_info(guild_id, channel_id)` | `get_channel_info` | `guild_id: str`, `channel_id: str` | `channel_id`, `channel_name` |
| `get_channel_list(guild_id, *, joined_only)` | `get_channel_list` | `guild_id: str`, `joined_only: bool=false` | `list[get_channel_info response]` |
| `set_channel_name(guild_id, channel_id, channel_name)` | `set_channel_name` | `guild_id`, `channel_id`, `channel_name` | None |
| `get_channel_member_info(guild_id, channel_id, user_id)` | `get_channel_member_info` | `guild_id`, `channel_id`, `user_id` | `user_id`, `user_name`, `user_displayname` |
| `get_channel_member_list(guild_id, channel_id)` | `get_channel_member_list` | `guild_id`, `channel_id` | `list[get_channel_member_info response]` |
| `leave_channel(guild_id, channel_id)` | `leave_channel` | `guild_id`, `channel_id` | None |

> The guild system and groups are independent of each other: platforms such as Discord / QQ Guild / Kook implement the guild interfaces, while traditional QQ / WeChat implement the group interfaces; both may exist simultaneously or only one of them.

### 3.5 File Resource Operations

> [!WARNING]
> **The file resource model (two-stage file_id) is "degraded availability" in ErisPulse**:
> File send/receive in ErisPulse does not follow the "upload first to get a file_id, then reference it" model—modules send files with
> `SendDSL.File(file, filename)` (URL / path / bytes are **transmitted directly at send time**, see the
> [Send Method Specification](send-method-spec.md)).
> The `upload_file` / `get_file` / fragmented actions in this section depend on platform-specific `file_id` file resource
> capabilities, which are **not general-purpose**; pass-through is only possible when the adapter backend natively has this capability. The framework's built-in
> adapters **neither implement nor recommend implementing** them; calls typically return `retcode=10002`.
> When a module needs to transfer files cross-platform, use `SendDSL.File` and do not rely on file_id.
>
> **Outlook**: Standardizing the `file_id` resource model at the framework layer is a future direction; the current version does not provide it.

Whole-file transfer (small files):

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `upload_file(*, type, name, ...)` | `upload_file` | `type`, `name`, `url`/`path`/`data`, `headers?`, `sha256?` | `file_id` |
| `get_file(file_id, type)` | `get_file` | `file_id: str`, `type: str` | `name`, `url`/`path`/`data` |

The `type` parameter of `upload_file`:
- `"url"`: Upload via URL (requires `url`)
- `"path"`: Upload via local path (requires `path`)
- `"data"`: Upload via binary data (requires `data`)

#### 3.5.1 Fragmented Transfer (Large Files, Within the Above Degraded Scope)

OneBot12 fragmented actions distinguish phases by `stage`. `ApiDSL` splits the three/two phases of the same action into independent methods
(`offset` is a byte offset, and `data` is Base64 in JSON); the tables below are retained for reference only, and adapters need not and should not be forced to implement them:

**Three-step fragmented upload**: `prepare` → `transfer` (loop chunk by chunk) → `finish`

| Method | Corresponding stage | Parameters | data Return |
|------|-----------|------|----------|
| `upload_file_fragmented_prepare(name, total_size)` | `prepare` | `name: str`, `total_size: int` | `file_id` (used during transfer) |
| `upload_file_fragmented_transfer(file_id, offset, data)` | `transfer` | `file_id`, `offset: int`, `data: bytes` | None |
| `upload_file_fragmented_finish(file_id, sha256)` | `finish` | `file_id`, `sha256: str` (whole-file checksum) | `file_id` |

```python
total = os.path.getsize(path)
r = await adapter.Api.upload_file_fragmented_prepare(os.path.basename(path), total)
fid = r["data"]["file_id"]
offset = 0
with open(path, "rb") as f:
    while chunk := f.read(65536):
        await adapter.Api.upload_file_fragmented_transfer(fid, offset, chunk)
        offset += len(chunk)
sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
await adapter.Api.upload_file_fragmented_finish(fid, sha256)
```

**Two-step fragmented download**: `prepare` → `transfer` (loop fetching chunks)

| Method | Corresponding stage | Parameters | data Return |
|------|-----------|------|----------|
| `get_file_fragmented_prepare(file_id)` | `prepare` | `file_id` | `name`, `total_size`, `sha256` |
| `get_file_fragmented_transfer(file_id, offset, size)` | `transfer` | `file_id`, `offset: int`, `size: int` | `data` (bytes of the current chunk) |

### 3.6 Meta Actions

Meta actions do not target a specific account and do not require `Using()` to specify a Bot.

| Method | OB12 Action | Parameters | data Return |
|------|----------|------|----------|
| `get_latest_events(limit, timeout)` | `get_latest_events` | `limit: int=0`, `timeout: int=0` | Array of event objects (excluding meta events) |
| `get_supported_actions()` | `get_supported_actions` | None | `list[str]` of supported action names |
| `get_status()` | `get_status` | None | `good: bool`, `bots: list[{self, online, ...}]` |
| `get_version()` | `get_version` | None | `impl`, `version`, `onebot_version` |

### 3.7 Generic Extension Actions

| Method | Description |
|------|------|
| `call(action, **params)` | Escape hatch for platform extension actions, following the OB12 extension naming rule `{prefix}.{action}` |

## 4. Usage

### 4.1 Basic Calls

```python
from ErisPulse import adapter

# Get user info (cross-platform unified)
result = await adapter.myplatform.Api.get_user_info("123456")
if result["status"] == "ok":
    user_name = result["data"]["user_name"]
    print(f"Username: {user_name}")

# Get group list
result = await adapter.myplatform.Api.get_group_list()
groups = result["data"]

# Recall a message
await adapter.myplatform.Api.delete_message("msg_123456")
```

### 4.2 Specifying a Bot Account (Multi-Account Mode)

```python
# Execute operations with a specified Bot account
info = await adapter.myplatform.Api.Using("bot1").get_self_info()
```

### 4.3 Platform Extension Actions

```python
# Call a platform-specific extension action (use the {prefix}.{action} naming convention)
result = await adapter.telegram.Api.call(
    "telegram.send_sticker",
    sticker_id="CAACAgIAAxkBAA...",
)
```

### 4.4 Use in Event Handlers

```python
from ErisPulse.Core.Event import message

@message()
async def handle(event):
    # Get detailed sender info
    user_id = event.get_user_id()
    platform = event.get_platform()

    result = await getattr(adapter, platform).Api.get_user_info(user_id)
    if result["status"] == "ok":
        user_name = result["data"]["user_name"]
        await event.reply(f"Hello, {user_name}!")
```

## 5. Adapter Implementation

### 5.1 Default Behavior (Zero Configuration)

The default implementation of `ApiDSL` passes the standard action name directly to `adapter.call_api()` as the `endpoint`:

```python
# The ApiDSL default implementation is equivalent to:
async def get_user_info(self, user_id: str) -> dict:
    return await self._adapter.call_api("get_user_info", user_id=user_id, account_id=self._account_id)
```

**Applicable scenario**: When the adapter's underlying backend itself follows the OneBot12 standard action protocol, `call_api` naturally supports standard action names (e.g., when directly connecting to a server that follows this protocol).

### 5.2 Overriding Standard Methods (Mapping to Platform-Native APIs)

An adapter can override individual standard methods, mapping them to platform-native APIs:

```python
class MyAdapter(BaseAdapter):

    class Api(BaseAdapter.Api):
        """MyPlatform standard API action implementation"""

        async def get_user_info(self, user_id: str) -> dict:
            # Map to platform-native API
            raw = await self._adapter._request("GET", f"/users/{user_id}")
            if raw.get("code") != 0:
                # Platform-side error: use the 341xx–345xx range for the custom low three digits (346xx is reserved by the framework, do not use)
                return self._adapter.make_error(retcode=34400, message="User not found")

            user = raw["data"]
            return self._adapter.make_response(
                data={
                    "user_id": str(user["id"]),
                    "user_name": user.get("nick", ""),
                    "user_displayname": user.get("display_name", ""),
                    "user_remark": user.get("remark", ""),
                },
                raw=raw,
            )

        async def get_friend_list(self) -> dict:
            raw = await self._adapter._request("GET", "/friends")
            friends = [
                {
                    "user_id": str(u["id"]),
                    "user_name": u.get("nick", ""),
                    "user_displayname": u.get("display_name", ""),
                    "user_remark": u.get("remark", ""),
                }
                for u in raw.get("data", [])
            ]
            return self._adapter.make_response(data=friends, raw=raw)
```

### 5.3 Unsupported Actions

Standard methods not overridden by the adapter use the default implementation (delegating to `call_api`). If `call_api` also does not support the action, it should return a standard error response:

```python
async def call_api(self, endpoint: str, **params):
    if endpoint not in self._supported_endpoints:
        return self.make_error(retcode=10002, message=f"Unsupported action: {endpoint}")
    # ... platform API call
```

Module developers can check the `retcode` in the return value to determine whether an action is supported:

```python
result = await adapter.myplatform.Api.get_friend_list()
if result["retcode"] == 10002:
    print("This platform does not support getting the friend list")
```

## 6. Response Format

All `ApiDSL` methods return the standard API response format (see the [API Response Standard](api-response.md) for details):

```json
{
    "status": "ok",
    "retcode": 0,
    "data": { ... },
    "message_id": "",
    "message": "",
    "myplatform_raw": { ... }
}
```

> **Note**: For information-query actions, `message_id` is an empty string (only message-sending actions have a `message_id`).

## 7. Relationship with SendDSL / RequestDSL

| Scenario | DSL to Use | Example |
|------|---------|------|
| Send a message | `Send` | `adapter.Send.To("group", "123").Text("hi")` |
| Accept/reject a request | `Request` | `adapter.Request("req_id").accept()` |
| Get user/group info | `Api` | `adapter.Api.get_user_info("123")` |
| Recall a message | `Api` | `adapter.Api.delete_message("msg_id")` |
| Leave a group | `Api` | `adapter.Api.leave_group("group_id")` |

## 8. Adapter Implementation Checklist

### Standard Actions
- [ ] `call_api` can handle standard action names (or override the corresponding `ApiDSL` methods)
- [ ] Unsupported actions return `retcode=10002`
- [ ] Return values follow the standard API response format
- [ ] The `data` field contains the fields defined by the OB12 standard
- [ ] Guild platforms must implement `get_guild_*` / `get_channel_*` / `leave_guild` / `leave_channel`
- [ ] Meta actions (`get_status` / `get_version` / `get_supported_actions`) are recommended to be implemented
- [ ] **File send/receive uses `SendDSL.File` (direct transmission)**; file resource actions (upload_file/get_file/fragmented) are **not mandatory to implement**; pass-through is only needed when the backend has `file_id` resource capability

### Extension Actions
- [ ] Platform extension actions use the `{prefix}.{action}` naming convention
- [ ] Extension action parameters and responses still follow the OB12 action request/response structure

## 9. Related Documents

**Companion reference when implementing Api DSL return values**:
- [API Response Standard](api-response.md) - Adapter API response format standard

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specification for the Send class
- [Request Action Specification](request-action-spec.md) - How to use the Request DSL

**Event-side companion**:
- [Event Conversion Standard](event-conversion.md) - Event format and message segment standard

## API 响应规范

> 来源: `docs/en/standards/api-response.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/api-response.md）

# ErisPulse Adapter Standardized Return Specification

> [!TIP]
> **When to read this**: When you are implementing the return values of `call_api` / Send / Request in an adapter and need to confirm that the response structure and return codes conform to the ErisPulse standard, or when troubleshooting the meaning of a particular `retcode`, refer to this document. Skip if not needed.

## 1. Description

Why does this specification exist?

To ensure the uniformity of API response formats across different platforms and maintain compatibility with OneBot12, the ErisPulse adapter adopts the message sending return structure standard defined by OneBot12.

However, the ErisPulse protocol has some special definitions:
- 1. In the base fields, `message_id` is required, but this field does not exist in the OneBot12 standard.
- 2. The response content needs to include a `{platform_name}_raw` field to store the raw response data.

## 2. Basic Return Structure

All action responses must include the following basic fields:

| Field Name | Data Type | Required | Description |
|-----------|-----------|----------|-------------|
| status | string | Yes | Execution status, must be "ok" or "failed" |
| retcode | int64 | Yes | Return code, follows OneBot12 return code rules |
| data | any | Yes | Response data, contains the request result on success, null on failure |
| message_id | string | Yes | Message ID, used to identify the message, empty string if not available |
| message | string | Yes | Error message, empty string on success |
| {platform_name}_raw | any | No | Raw response data |

Optional fields:
| Field Name | Data Type | Required | Description |
|-----------|-----------|----------|-------------|
| echo | string | No | Returned verbatim when the request contains an echo field |

## 3. Full Field Specification

### 3.1 Common Fields

#### Successful Response Example
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": "1234",
        "time": 1632847927.599013
    },
    "message_id": "1234",
    "message": "",
    "echo": "1234",
    "telegram_raw": {...}
}
```

#### Failed Response Example
```json
{
    "status": "failed",
    "retcode": 10003,
    "data": null,
    "message_id": "",
    "message": "Missing required parameter: user_id",
    "echo": "1234",
    "telegram_raw": {...}
}
```

### 3.2 Return Code Specification

#### 0 Success (OK)
- 0: Success (OK)

#### 1xxxx Request Error
| Error Code | Error Name | Description |
|------------|------------|-------------|
| 10001 | Bad Request | Invalid action request |
| 10002 | Unsupported Action | Unsupported action request |
| 10003 | Bad Param | Invalid action request parameter |
| 10004 | Unsupported Param | Unsupported action request parameter |
| 10005 | Unsupported Segment | Unsupported message segment type |
| 10006 | Bad Segment Data | Invalid message segment parameter |
| 10007 | Unsupported Segment Data | Unsupported message segment parameter |
| 10101 | Who Am I | Robot account not specified |
| 10102 | Unknown Self | Unknown robot account |

#### 2xxxx Handler Error
| Error Code | Error Name | Description |
|------------|------------|-------------|
| 20001 | Bad Handler | Action handler implementation error |
| 20002 | Internal Handler Error | Exception thrown during action handler execution |

#### 3xxxx Execution Error
| Error Code Range | Error Type | Description |
|------------------|------------|-------------|
| 31xxx | Database Error | Database error |
| 32xxx | Filesystem Error | Filesystem error |
| 33xxx | Network Error | Network error |
| 34xxx | Platform Error | Robot platform error |
| 35xxx | Logic Error | Action logic error |
| 36xxx | I Am Tired | Implementation decided to strike |

#### Reserved Error Ranges
- 4xxxx, 5xxxx: Reserved ranges, should not be used
- 6xxxx–9xxxx: Other error ranges, for custom implementation use

## 4. Implementation Requirements
1. All responses must contain the fields: `status`, `retcode`, `data`, and `message`.
2. When the request contains a non-empty `echo` field, the response must include an `echo` field with the same value.
3. Return codes must strictly follow the OneBot12 specification.
4. Error messages (`message`) should be human-readable descriptions.

## 5. Extension Specifications

ErisPulse extends the OneBot12 standard return structure as follows:

### 5.1 `message_id` Required Field

In the OneBot12 standard, `message_id` is located within the `data` object and is not mandatory. ErisPulse elevates it to a **required** top-level field:

- When `message_id` cannot be obtained, it should be set as an empty string `""`
- Ensure `message_id` always exists, so modules do not need to perform null checks

### 5.2 `{platform}_raw` Raw Response Field

The return value should include the `{platform}_raw` field, which stores a complete copy of the raw response data from the platform:

```json
{
    "status": "ok",
    "retcode": 0,
    "data": {"message_id": "1234", "time": 1632847927},
    "message_id": "1234",
    "message": "",
    "telegram_raw": {
        "ok": true,
        "result": {"message_id": 1234, "date": 1632847927, ...}
    }
}
```

**Requirements**:
- `{platform}_raw` must be a deep copy of the original response, not a reference
- `platform` must exactly match the platform name registered by the adapter (case-sensitive)
- Error information from the original response should also be retained for debugging purposes

### 5.3 Framework Extension Return Codes (Custom Low Three Digits in the 34xxx Platform Error Segment)

The OneBot12 specification allows implementations to define custom low three digits of `3xxxx`. The `34xxx` segment semantics are **Platform Error** (robot platform error, such as failures caused by platform restrictions). The `34xxx` segment is used hierarchically according to responsibilities:

| Low Three Digits Segment | Ownership | Purpose |
|---------|------|------|
| `340xx` | Adapter Implementation | Request operation group (Request Not Found / Already Handled / Not Supported / Permission Denied, see request-action-spec §7) |
| `341xx`～`345xx` | Adapter Implementation | Platform-side permission / risk control / account restriction errors (implement custom low three digits, original error placed in `{platform}_raw`) |
| `346xx` | **ErisPulse Framework (reserved)** | Framework-level interception and general failures; adapters/modules should not occupy these codes |
| `347xx`～`349xx` | Adapter Implementation | Other platform execution errors |

ErisPulse framework currently uses the `346xx` codes:

| Error Code | Error Name | Description |
|-------|-------|------|
| 34600 | SDK Failure | General failure in the framework (`make_error()` default return code) |
| 34601 | Action Denied | Outbound action denied by scope (`scope.actions`), call not initiated, directly return this response |

> Responsibility distinction: `34601` is **framework-level interception before the call** (the module has no right to initiate the action); `34004` / `34xxx` platform codes are **actions already sent but rejected by the platform** (e.g., Bot lacks permission, is restricted). When modules check for permission issues, they should check both types: first check `34601` (the module's own scope is disabled), then check `34xxx` (platform-side restrictions).

The return structure is the standard failure response as defined in §2:

```json
{
    "status": "failed",
    "retcode": 34601,
    "data": null,
    "message_id": "",
    "message": "action 'send' denied by scope.actions"
}
```

### 5.4 Adapter Implementation Checklist

- [ ] Include `status`, `retcode`, `data`, `message_id`, `message` fields
- [ ] Return codes follow the OneBot12 specification (see §3.2)
- [ ] `message_id` always exists (set as empty string if unavailable)
- [ ] `{platform}_raw` contains the raw response data from the platform

## 6. Notes
- For error codes starting with 3xxxx, the last three digits can be defined by the implementation.
- Avoid using reserved error ranges (4xxxx, 5xxxx).
- **`34600` / `34601` are reserved error codes for the ErisPulse framework** (see §5.3); adapters/modules should avoid using them.
- Error messages should be concise and clear for easier debugging.

## 请求动作规范

> 来源: `docs/en/standards/request-action-spec.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/standards/request-action-spec.md）

# ErisPulse Request Operation Specification

> [!TIP]
> **When to read this**: When your adapter needs to handle friend requests/group invitations (converting request events, implementing `accept`/`reject`), or when your module needs to use `event.approve()` / `event.reject()` to approve requests, refer to this document. Otherwise, skip it.

This document defines the standardized specification for request event operations in ErisPulse adapters, including field requirements for request events, usage of the Request DSL, and adapter implementation requirements.

## 1. Overview

Request events (`type: "request"`) are a special event type defined in the OneBot12 standard, representing requests that require the Bot to make a decision (such as friend requests, group invitations, etc.).

Unlike message events, request events require **two-way interaction**:
1. **Receiving**: The adapter converts platform-native requests into standard request events
2. **Responding**: Modules perform operations via the `Request` DSL or `Event.approve()`/`Event.reject()`

```
Platform-native request event
    │
    ▼
Converter.convert()        ← Adapter implementation (forward conversion)
    │
    ▼
Standard request event (with request_id)
    │
    ├─→ Module handler @request.on_friend_request()
    │       │
    │       ├─→ event.approve()     ← Approve request
    │       └─→ event.reject()      ← Reject request
    │               │
    │               ▼
    │       adapter.Request(request_id).accept()
    │               │
    │               ▼
    │       BaseAdapter.Request.accept()  ← Adapter override
    │               │
    │               ▼
    │       Platform API call
    │
    └─→ Or operate directly through the adapter
            await adapter.Request("req_id").accept()
```

## 2. Request Event Field Requirements

### 2.1 Standard Fields

In addition to the required OneBot12 standard fields, request events must include the following fields:

| Field | Type | Required | Description |
|------|------|------|------|
| `request_id` | string | **Strongly recommended** | Request identifier, used for accept/reject operations |
| `user_id` | string | Yes | ID of the requester |
| `user_nickname` | string | No | Nickname of the requester |
| `comment` | string | No | Message attached to the request |

### 2.2 The `request_id` Field

`request_id` is the core identifier for request operations:

- **Purpose**: Identifies an operable request, used by the `Request` DSL
- **Generation rules**:
  - Prefer the platform's native request identifier (e.g., OneBot11's `flag` field, Telegram's `chat_invite_link`, etc.)
  - If the platform has no native request ID, the adapter should generate a unique identifier (suggested format: `{platform}_{timestamp}_{user_id}`)
- **Uniqueness**: Should remain unique within the same platform scope
- **Missing behavior**: When `request_id` is missing, `event.approve()` / `event.reject()` will raise `ValueError`

### 2.3 Request Event Example

```json
{
  "id": "evt_123456",
  "time": 1752241225,
  "type": "request",
  "detail_type": "friend",
  "platform": "onebot11",
  "self": {
    "platform": "onebot11",
    "user_id": "bot_123"
  },
  "user_id": "user_456",
  "user_nickname": "YingXinche",
  "comment": "Please add me as a friend",
  "request_id": "flag_abc123",
  "onebot11_raw": {...},
  "onebot11_raw_type": "request"
}
```

## 3. Request DSL

### 3.1 Chained Calls

`Request` provides a chained call interface consistent with the `Send` style:

```python
# Basic usage
await adapter.Request("req_id").accept()
await adapter.Request("req_id").reject()

# Specify a Bot account
await adapter.Request("req_id").Using("bot1").accept()

# With a note (via kwargs)
await adapter.Request("req_id").accept(comment="Welcome")
await adapter.Request("req_id").reject(comment="Not adding for now")

# Combined usage
await adapter.Request("req_id").Using("bot1").accept(comment="Welcome")
```

### 3.2 Method List

| Method | Description | Return Value |
|------|------|--------|
| `Using(account_id)` | Specify the Bot account to perform the operation | `RequestDSL` (supports chaining) |
| `accept(**kwargs)` | Approve the request | `asyncio.Task` (returns the standard response after await) |
| `reject(**kwargs)` | Reject the request | `asyncio.Task` (returns the standard response after await) |

### 3.3 Return Value Format

Operations return the standard API response format:

**Success**:
```json
{
    "status": "ok",
    "retcode": 0,
    "data": null,
    "message_id": "",
    "message": ""
}
```

**Failure**:
```json
{
    "status": "failed",
    "retcode": 34001,
    "data": null,
    "message_id": "",
    "message": "The request has expired or does not exist"
}
```

**Not implemented** (adapter does not override `accept`/`reject`):
```json
{
    "status": "failed",
    "retcode": 10002,
    "data": null,
    "message_id": "",
    "message": "Platform MyAdapter has not implemented request operations (accept)"
}
```

## 4. Event Convenience Methods

The `Event` wrapper class provides convenience methods suitable for use in request event handlers:

```python
from ErisPulse.Core.Event import request

@request.on_friend_request()
async def handle_friend_request(event):
    # Check the request ID
    request_id = event.get_request_id()
    if not request_id:
        print("Warning: request event is missing request_id")
        return
    
    # Approve the request
    result = await event.approve()
    
    # Or reject the request
    # result = await event.reject(comment="Not adding friends for now")
    
    # Check the result
    if result.get("status") == "ok":
        print("Operation succeeded")
    else:
        print(f"Operation failed: {result.get('message')}")
```

### 4.1 Event Method List

| Method | Description | Return Value |
|------|------|--------|
| `get_request_id()` | Get the request ID | `str` |
| `approve(comment=None)` | Approve the current request event | Standard response format |
| `reject(comment=None)` | Reject the current request event | Standard response format |

## 5. Adapter Implementation Requirements

### 5.1 Converter Requirements

When converting request events, the adapter's converter **must** correctly set the `request_id` field:

```python
def convert_request_event(self, raw_event: dict) -> dict:
    """Convert a platform-native request event"""
    return {
        "id": self._generate_event_id(raw_event),
        "time": int(time.time()),
        "type": "request",
        "detail_type": self._map_request_type(raw_event),  # "friend" or "group"
        "platform": self._platform_name,
        "self": {
            "platform": self._platform_name,
            "user_id": str(self._bot_id),
        },
        "user_id": str(raw_event.get("user_id", "")),
        "user_nickname": raw_event.get("nickname", ""),
        "comment": raw_event.get("message", ""),
        "request_id": self._extract_request_id(raw_event),  # ← Key field
        f"{self._platform_name}_raw": raw_event,
        f"{self._platform_name}_raw_type": raw_event.get("type", ""),
    }

def _extract_request_id(self, raw_event: dict) -> str:
    """
    Extract the request ID from a platform-native event
    
    Prefer the platform's native request identifier; generate a unique ID if unavailable
    """
    # Prefer the platform's native ID
    if flag := raw_event.get("flag"):
        return str(flag)
    if request_key := raw_event.get("request_key"):
        return str(request_key)
    
    # Fallback: generate a unique ID
    import hashlib
    raw = f"{self._platform_name}_{raw_event.get('user_id')}_{raw_event.get('timestamp')}"
    return hashlib.md5(raw.encode()).hexdigest()
```

### 5.2 Request Inner Class Implementation

The adapter only needs to override `accept` and `reject` in the `Request` inner class:

```python
from ErisPulse.Core import BaseAdapter, RequestDSL

class MyAdapter(BaseAdapter):
    
    class Request(RequestDSL):
        """MyPlatform request operation implementation"""
        
        def accept(self, **kwargs):
            """
            Approve the request
            
            :param kwargs: Extended parameters, e.g., comment="a note"
            :return: asyncio.Task
            """
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=True,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Request operation failed: {e}",
                    }
            
            return self._create_task(_do())
        
        def reject(self, **kwargs):
            """Reject the request"""
            async def _do():
                try:
                    result = await self._adapter.call_api(
                        endpoint="/set_request",
                        request_id=self._request_id,
                        approve=False,
                        **kwargs,
                    )
                    return {
                        "status": "ok" if result.get("code") == 0 else "failed",
                        "retcode": result.get("code", 0),
                        "data": None,
                        "message_id": "",
                        "message": result.get("message", ""),
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "retcode": 34001,
                        "data": None,
                        "message_id": "",
                        "message": f"Request operation failed: {e}",
                    }
            
            return self._create_task(_do())
```

### 5.3 Platforms That Do Not Support Request Operations

If the platform itself does not support friend request/group invitation operations (e.g., some platforms handle requests automatically), the adapter can:

1. **Not override the `Request` inner class**: Use the base class's default implementation; calling `accept()`/`reject()` returns `retcode=10002`
2. **Skip `request_id` during conversion**: Do not generate `request_id`, letting `event.approve()` raise `ValueError`
3. **Log warnings**: Log a warning in `accept`/`reject` and return an appropriate error code

### 5.4 Summary: Send and Request in Parallel

The adapter has two parallel DSL inner classes, each with its own responsibility:

```
BaseAdapter
├── Send(SendDSL)     ← Message sending
│   ├── Raw_ob12()    ← Must be implemented
│   ├── Text()        ← Recommended to implement
│   └── Image()       ← Implement as needed
│
└── Request(RequestDSL) ← Request operations
    ├── accept()        ← Implement as needed
    └── reject()        ← Implement as needed
```

### 5.5 Adapter `__init__` Notes

When overriding the `__init__` of the `Request` inner class, you must pass through the parameters and call `super().__init__()`. See [Adapter Development Getting Started - `__init__` Notes](../developer-guide/adapters/getting-started.md#init-notes) (`Request` works the same way, with parameters `adapter, request_id, account_id`).

## 6. Adapter Implementation Checklist

### Basic Requirements
- [ ] If `__init__` is overridden, `super().__init__()` has been called (ensures Send / Request factory initialization)

### Request Event Conversion
- [ ] Request events include the `request_id` field (strongly recommended)
- [ ] `detail_type` is correctly mapped to `"friend"` or `"group"`
- [ ] Platform raw data is preserved in the `{platform}_raw` field
- [ ] The `request_id` generation rules are documented

### Request Operations
- [ ] The `Request` inner class is implemented (if the platform supports request operations)
- [ ] The `accept()` method is implemented
- [ ] The `reject()` method is implemented
- [ ] Operations return the standard API response format
- [ ] Unsupported operations return `retcode=10002`
- [ ] Network errors return `retcode=33xxx` (following the API response standard)

## 7. Error Code Extensions

Recommended error codes for the **adapter implementation layer** related to request operations (following the [API Response Standard](api-response.md) §3.2,
customized in the last three digits of the `34xxx` platform error range):

| Error Code | Error Name | Description |
|-------|-------|------|
| 34001 | Request Not Found | The request does not exist or has expired |
| 34002 | Request Already Handled | The request has already been handled |
| 34003 | Request Not Supported | The platform does not support this type of request operation |
| 34004 | Permission Denied | The Bot has no permission to handle this request (returned by the platform) |

> **Boundary with framework codes**: The `340xx` codes above are request handling failures returned by the **platform/adapter**;
> when the ErisPulse framework disables a module's request action via `scope.actions`, it **returns `34601` directly before calling the adapter**
> (Action Denied, see [API Response Standard §5.3](api-response.md#53-framework-extension-return-codes-last-three-digits-of-the-34xxx-platform-error-range)).
> The two do not replace each other: first pass the `34601` framework gate, then fall to the platform-layer `340xx` errors.

## 8. Related Documents

**Reference alongside when implementing request operations**:
- [Event Conversion Standard](event-conversion.md) - Complete event conversion specification (including `request_id` field requirements)
- [API Response Standard](api-response.md) - Adapter API response format standard (operation return values and error codes)

**Other DSLs of the same adapter**:
- [Send Method Specification](send-method-spec.md) - Method naming and parameter specifications for the Send class
- [Session Types Standard](session-types.md) - Session type definitions and mapping relationships
