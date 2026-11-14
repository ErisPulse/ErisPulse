# Adapter Standardization Guide (Master Outline)

> [!TIP]
> **When to read this**: Read this document first when you are developing a new adapter, or adding a new capability for a platform and need to decide "whether it goes into the standard or becomes a `{platform}_` extension", how to name it, and how to handle platform differences. If you are only looking up a specific specification for one domain, you can jump directly to the corresponding document in the §2 Standard Map.

This document is the **master outline** of ErisPulse adapter standardization: it establishes the principles of cross-platform standardization, the standard map,
difference-handling patterns, and the process for promoting new capabilities into standards, and provides complete definitions of the **interactive component standards** (buttons/keyboards, select dropdowns, etc.)
and **interaction callback events**. Any adapter developer implementing new features should **prioritize standard definitions**,
so that module developers can get a consistent experience on any platform with the same codebase — consistent naming, consistent parameters, consistent returns.

---

## 1. Standardization Principles

1. **Consistent naming**: The same concept uses the same naming on all platforms (e.g., retraction is uniformly `delete_message`,
   and the button segment is uniformly `keyboard`), regardless of platform
2. **Consistent parameters**: The parameter structures of standard actions/segments/methods stay the same on all platforms; platform-specific parameters
   are provided as **optional extension parameters** or **extension fields**, without polluting the standard signature
3. **Consistent returns**: All API/send calls return the standard response structure (`status/retcode/data/message_id/message`);
   the standard fields within `data` (e.g., `user_id/user_name`) have consistent semantics; platform raw data goes into `{platform}_raw`
4. **Grounded extensions**: Platform-specific capabilities are named with the `{platform}_` prefix (segment: `yunhu_form`;
   action: `yunhu.board`; event field: `qqbot_button_id`), clearly marked as non-cross-platform
5. **Differences absorbed at the adapter layer**: Module code is written against the standard; platform differences are converted by the adapter
   (parameter mapping, field normalization, capability degradation); modules are not required to write platform-specific branches
6. **Capability degradation raises no errors**: When a platform does not support a standard capability, degrade gracefully (return `retcode=10002`,
   textualize components into `alt_message`) instead of throwing exceptions that interrupt module logic

## 2. Standard Map

| Domain | Standard Document | Coverage |
|------|---------|---------|
| Event conversion | [Event Conversion Standard](event-conversion.md) | Event structure, standard message segments (text/image/mention/reply/keyboard, etc.), platform extension segment specifications |
| Interactive components | **This document §5** | Buttons/keyboards, select dropdowns, cards, interaction callback event standard fields, decorator conventions, per-platform mappings |
| API actions | [API Action Standard](api-action-spec.md) | Unified interfaces for OneBot12 standard actions (user/group/channel/message management/meta actions) and `ApiDSL` |
| Request operations | [Request Action Specification](request-action-spec.md) | Request event fields (request_id), Request DSL (approve/reject), and request-type context retention |
| Send methods | [Send Method Specification](send-method-spec.md) | Send class method naming, parameters, decorators, reverse conversion (OB12→platform) |
| Session types | [Session Types Standard](session-types.md) | Definitions and mappings of session types such as user/group/channel/guild/dms |
| API responses | [API Response Standard](api-response.md) | Standard response structure and retcode conventions |

## 3. Standardization Workflow (How New Capabilities Enter the Standard)

```
Platform-specific capability ({platform}_ prefix)
        │  Similar capability appears on ≥2 platforms
        ▼
Identify commonalities (extract the common concept and parameter subset)
        │
        ▼
Standard draft (naming + parameters + returns + per-platform mapping tables)
        │  Review
        ▼
Write into this master outline / domain standard documents + framework base classes / adapters implement compatibility layers
        │
        ▼
Standard segment/action (no prefix) — usable cross-platform by modules
```

**Example**: Buttons were originally implemented independently per platform (`telegram_inline_keyboard` / Yunhu buttons /
QQBot keyboard) → appeared on ≥3 platforms → common structure extracted (`label/type/data` + rows)
→ standard `keyboard` segment published → each adapter implements a compatibility layer (decorators accept the common structure + standard segment conversion + native segment passthrough).

### 3.1 Naming Rules

| Object | Rule | Example |
|------|------|------|
| Standard message segments | lowercase, no prefix for common concepts | `keyboard`, `select`, `mention` |
| Platform extension segments | `{platform}_` prefix | `telegram_sticker`, `yunhu_form` |
| Standard API actions | OB12 standard names (snake_case) | `get_group_info`, `delete_message` |
| Platform extension actions | `{platform}.` prefix or protocol-common name | `yunhu.board`, `send_poke` (OB11 extension) |
| Decorators | PascalCase, common capabilities go into framework base classes | `.Keyboard(rows)`, `.At(uid)` |
| Standard event fields | no prefix for common concepts | `interaction_id`, `button_data`, `request_id` |
| Platform event fields | `{platform}_` prefix | `qqbot_event_id`, `telegram_chat_id` |

### 3.2 Parameter and Return Rules

- Standard parameters are **same name, same semantics** on all platforms; units/formats are explicit in the standard documents (e.g., second-level timestamps, string IDs)
- Required parameters take the **common subset** of all platform capabilities; platform-enhanced capabilities become optional parameters
- Platform hard constraints (e.g., QQBot rich media cannot be mixed with event_id) are handled/degraded automatically by the adapter and are not exposed to modules
- The standard fields in the returned `data` are identical across all platforms; extra platform information goes into platform-named fields within `data` or `{platform}_raw`

## 4. Difference Handling Patterns (Adapter Layer)

| Pattern | Description | Example |
|------|------|------|
| **Parameter mapping** | standard parameters → platform native parameters | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)` (chat_id filled in from the registry) |
| **Structure conversion** | standard segments → platform native structures | `keyboard` segment → `inline_keyboard` / buttons / QQBot keyboard |
| **Action mapping** | standard action names → platform action names | `get_self_info` → `get_login_info` (OB11) |
| **Field normalization** | platform responses → standard fields | `getMe()` → `{user_id, user_name, user_displayname}` |
| **Synthetic identifiers** | generate deterministic IDs when the platform has no native one | TG join request has no ID → `tjr_{chat}_{user}_{date}` |
| **Capability degradation** | textualize/return 10002 when unsupported | Kook has no keyboard → textualize into alt_message; `get_friend_list` → 10002 |
| **Normalization** | platform dirty data → standard format | QQBot @mention markup openid → bot_id (name normalization) |
| **Dual-track compatibility** | accept both standard structures and platform native structures | `.Keyboard()` accepts common rows or native structures |

---

## 5. Interactive Component Standards

### 5.1 Component Inventory and Status

| Component | Standard segment type | Status | Supported Platforms |
|------|------------|------|-----------|
| Buttons/Keyboard (keyboard) | `keyboard` | ✅ Standardized | Telegram / Yunhu / QQBot |
| Select dropdown (select) | `select` | 📋 Reserved (structure in §5.4) | Discord / Telegram(bot) |
| Card (card) | `card` | 📋 Reserved (see §5.5) | Kook / Yunhu(html) |
| Modal (modal) | `modal` | 📋 Reserved | Discord |

> Decorator layering convention: Send decorators for common interactive components are **implemented by the adapter's Send class** (not built into the
> framework base class); naming follows the §5.2 convention, and parameters follow the standard structures in this document.

### 5.2 keyboard Buttons/Inline Keyboard

#### Message Segment Structure (Send Direction)

The standard `keyboard` segment is a `rows` two-dimensional array, where each button is
`{"label": "display text", "type": "callback" | "link", "data": "callback data or link address"}`;
platform-specific optional fields are also allowed (adapters map or ignore them according to capability).

> **Authoritative structure definition**: For the complete message segment JSON, field tables, and field semantics, see
> [Event Conversion Standard §4.1.1 keyboard Buttons/Inline Keyboard Segment](event-conversion.md#411-keyboard-按钮内联键盘段跨平台通用);
> this section does not repeat them.

#### Per-Platform Mapping Comparison

| Platform | Standard segment → native structure | Native structure reference |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`: `[{text, callback_data \| url}]` | callback→`callback_data` (≤64 bytes), link→`url` |
| Yunhu | `content.buttons`: `[{label, action_type}]` | callback→`action_type:2` + `action` + `value`, link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`: `[{label, type, data}]` | callback→`type:2` + `data`, link→`type:0` + `data` (message must be of markdown type) |
| Kook | card `action-group` module: `[{type, text, value, click}]` | callback→`click:return` + `value`, link→`click:link` + `url` |
| Discord | `components[].components`: `[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`, link→`style:5` + `url` |

#### Send Decorators (Implemented by Each Adapter's Send Class)

Common decorators are **implemented by each adapter in its own Send class** (without modifying the framework base class):

- `.Keyboard(rows)`: standard naming, accepts the §5.2 common rows structure, internally generates the standard `keyboard`
  message segment (or directly converts it into the platform native structure); handled uniformly by `Raw_ob12`
- `.Buttons(rows)`: optional semantic alias with identical behavior
- **Backward compatibility**: platform native structures are passed through directly when detected (no error, no conversion)
- Platform native extension segments (e.g., `telegram_inline_keyboard`) continue to be passed through, unaffected

```python
# The same code, any platform (each adapter provides decorators and conversion)
rows = [[{"label": "Like", "type": "callback", "data": "like:1"},
         {"label": "Home", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("Please choose")
```

> Adapter compatibility list: QQBot / Telegram / Yunhu are implemented (decorators + standard segment conversion);
> new adapters can simply implement per this document (see §7 Checklist).

### 5.3 Interaction Callback Events (After a Button Click)

After a user clicks a button, the event pushed by the platform **must** provide the following standard fields (detail_type may keep platform naming):

| Standard Field | Type | Required | Description |
|---------|------|------|------|
| `interaction_id` | str | Yes | ID of this interaction (usable for responding, e.g., loading spinner/toast) |
| `button_data` | str | Yes | Data passed back by the button (i.e., the `data` from §5.2) |
| `button_label` | str | No | Button display text |
| `user_id` | str | Yes | The user who clicked |
| `message_id` | str | No | The message containing the button |
| `group_id` / `channel_id` | str | No | Source session |

**detail_type convention**: keep each platform's existing naming (`qqbot_interaction` / `telegram_callback_query` /
`yunhu_a2ui_button`, etc.), but **all standard fields must be present** — modules can read values cross-platform via `event.get("button_data")`.

**Recommended Event extension methods** (provided by the adapter EventMixin):

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**Responding to interactions** (depending on platform capability): `adapter.reply_interaction(interaction_id, code=0)` (QQBot) /
`answerCallbackQuery` (Telegram), etc.; naming follows the platform method family and is not forcibly unified.

#### Per-Platform Callback Event Mapping

| Platform | Native event | detail_type | interaction_id source | button_data source |
|------|---------|-------------|--------------------|-----------------|
| Telegram | `callback_query` | `telegram_callback_query` (notice) | `callback_query.id` | `callback_query.data` |
| Yunhu | button click event | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | button click event | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select Dropdown (Reserved)

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

Callback events reuse the §5.3 fields (`button_data` = the selected `data`; a JSON array for multi-select). First platforms to implement:
Discord (select menu), Telegram (keyboard switching). Platforms without an implementation should degrade this segment into a text list
in `alt_message` when receiving it.

### 5.5 card Card (Reserved, Standardization Deferred)

Card structures vary enormously (Kook full-featured card modules vs Yunhu html vs QQ markdown+keyboard), so no strict standard is imposed for now. Recommendations:

- Express rich-text cards with a `text` + `keyboard` combination (sufficient for most scenarios)
- Platform full-featured cards continue to use the `{platform}_card` extension segment (e.g., `kook_card`)
- Re-review and promote once isomorphic card capabilities appear on ≥2 platforms

---

## 6. Future Candidates (Roadmap)

The following capabilities have already appeared on ≥2 platforms or are expected to appear; standardization proceeds by priority:

| Candidate | Platforms Involved | Priority | Notes |
|------|---------|--------|------|
| select dropdown | Discord / Telegram | High | Structure draft in §5.4 |
| Emoji reactions (reactions) | QQBot / Telegram / Discord / Kook | High | Standardize both the action and event sides |
| Group management actions (mute/kick/approval) | QQBot / Yunhu / OB11 | High | Most already implemented as platform actions; standard signatures pending extraction |
| Announcements/boards | Yunhu / Telegram / Discord | Medium | `set_announcement`-type actions |
| File resource model (two-part file_id) | All platforms | Low (deferred) | Direct sending via `SendDSL.File(file, filename)` is already the standard path (direct pass-through of URL/path/bytes, see [Send Method Specification §2.1](send-method-spec.md)); the file_id model is passed through only when the backend natively provides it, see [API Action Standard §3.5](api-action-spec.md) |
| Card (card) | Kook / Yunhu | Low | Structures vary greatly, see §5.5 |
| Form (form) | Yunhu | Low | Platform-specific; keep the `{platform}_` prefix |
| Media transcoding/size detection | All platforms | Low | Implemented inside adapters; not standardized externally |

## 7. Standard Checklist for New Adapter Developers

When developing a new adapter, implement against this checklist (★ = required; the rest are recommended):

- [ ] ★ Convert events into OneBot12 standard structures, inheriting `BaseConverter`
- [ ] ★ Support sending and receiving standard message segments (text/image/mention/reply/keyboard…; media segments handled per the
      form classification and degradation ladder in [Send Method Specification §2.1](send-method-spec.md))
- [ ] ★ Implement `Raw_ob12` (including standard segment → platform structure conversion; the standard `keyboard` segment is mandatory)
- [ ] ★ Return standard response structures (`make_response`/`make_error`)
- [ ] ★ Multiple accounts: `AccountConfigClass(BotAccountConfig)` + account resolution (account name / `bot_id` matching)
- [ ] ★ Send class inherits `BaseAdapter.Send`, using `_apply_modifiers`/`send_context`
- [ ] ☆ Api DSL: map standard actions to platform APIs (see the API Action Standard)
- [ ] ☆ Request DSL: request events include `request_id` + `accept/reject` (heterogeneous-endpoint platforms include request-type context retention)
- [ ] ☆ Interactive components: `keyboard` segment conversion + interaction callback standard fields + `.Keyboard()`/`.Buttons()` decorators (implemented by the adapter Send class)
- [ ] ☆ EventMixin: platform extension methods such as `get_raw_event()` / `get_button_data()`
- [ ] ☆ Use `runtime.spawn_background` for lifecycle tasks
- [ ] ☆ Use `self.cfg` for configuration reading
- [ ] ☆ Framework soft dependency: no declared hard dependency on ErisPulse + runtime version detection
- [ ] ☆ i18n: multilingual configuration fields and logs
- [ ] ☆ platform-guide platform documentation + platform-features.md in the adapter repository

## 8. Related Documents

- Domain standards are listed in the §2 Standard Map
- The framework's built-in adapters can serve as reference implementations: QQBot (full v5 paradigm), OneBot11 (Api DSL mapping), Yunhu (BaseConverter + Web API extension)