# Adapter Standardization Guide (Master Document)

> [!TIP]
> **When to read this**: Read this document first when you are developing a new adapter, adding new capabilities for a platform, deciding "whether a capability enters the standard or goes through a `{platform}_` extension", choosing names, or handling platform differences. If you only need to look up specific specifications for a particular domain, you can jump directly to the corresponding document in the §2 standard map.

This document is the **master document** of ErisPulse adapter standardization: it establishes the principles of cross-platform standardization, the standard map, difference-handling patterns, and the process by which new capabilities enter the standard, and provides complete definitions of the **interactive component standard** (buttons/keyboard, dropdown select, etc.) and **interaction callback events**. Any adapter developer implementing new features should **prioritize adopting the standard definitions**, so that module developers get a consistent experience with the same code on any platform — consistent naming, consistent parameters, consistent returns.

---

## 1. Standardization Principles

1. **Consistent naming**: the same concept uses the same name across all platforms (e.g., deletion is uniformly `delete_message`, the button segment is uniformly `keyboard`), regardless of platform
2. **Consistent parameters**: the parameter structures of standard actions/segments/methods remain consistent across all platforms; platform-specific parameters are provided as **optional extension parameters** or **extension fields** without polluting the standard signature
3. **Consistent returns**: all API/send calls return the standard response structure (`status/retcode/data/message_id/message`); standard fields within `data` (e.g., `user_id/user_name`) have consistent semantics; platform raw data goes into `{platform}_raw`
4. **Grounded extensions**: platform-specific capabilities are named with the `{platform}_` prefix (segment: `yunhu_form`; action: `yunhu.board`; event field: `qqbot_button_id`), clearly marking them as non-cross-platform
5. **Differences absorbed at the adapter layer**: module code is written against the standard, and platform differences are converted by the adapter (parameter mapping, field normalization, capability degradation); modules are not required to write platform branches
6. **Capability degradation without errors**: when a platform does not support a standard capability, degrade gracefully (return `retcode=10002`, textualize components into `alt_message`) instead of throwing exceptions that interrupt module logic

## 2. Standard Map

| Domain | Standard Document | Coverage |
|------|---------|---------|
| Event conversion | [Event Conversion Standard](event-conversion.md) | Event structure, standard message segments (text/image/mention/reply/keyboard, etc.), platform extension segment specifications |
| Interactive components | **This document §5** | Buttons/keyboard, dropdown select, card, standard fields of interaction callback events, decorator conventions, per-platform mappings |
| API actions | [API Action Standard](api-action-spec.md) | Unified interfaces and `ApiDSL` for OneBot12 standard actions (user/group/channel/message management/meta actions) |
| Request handling | [Request Action Specification](request-action-spec.md) | Request event fields (request_id) and the Request DSL (approve/reject) |
| Send methods | [Send Method Specification](send-method-spec.md) | Send class method naming, parameters, decorators, reverse conversion (OB12→platform) |
| Session types | [Session Type Standard](session-types.md) | Definitions and mappings of session types such as user/group/channel/guild/dms |
| API responses | [API Response Standard](api-response.md) | Standard response structure and retcode conventions |

## 3. Standardization Workflow (How New Capabilities Enter the Standard)

```
Platform-specific capability ({platform}_ prefix)
        │  a similar capability appears on ≥2 platforms
        ▼
Identify commonalities (extract the generic concept and parameter subset)
        │
        ▼
Standard draft (naming + parameters + returns + per-platform mapping table)
        │  review
        ▼
Write into this master document/domain standard documents + framework base class/adapter compatibility layer
        │
        ▼
Standard segment/action (no prefix) — usable cross-platform by modules
```

**Example**: buttons were initially implemented independently per platform (`telegram_inline_keyboard` / Yunhu buttons / QQBot keyboard) → appeared on ≥3 platforms → extracted the generic structure (`label/type/data` + rows) → published the standard `keyboard` segment → each adapter implements a compatibility layer (decorators accept the generic structure + standard segment conversion + native segment passthrough).

### 3.1 Naming Rules

| Object | Rule | Example |
|------|------|------|
| Standard message segment | lowercase, generic concepts without prefix | `keyboard`, `select`, `mention` |
| Platform extension segment | `{platform}_` prefix | `telegram_sticker`, `yunhu_form` |
| Standard API action | OB12 standard name (snake_case) | `get_group_info`, `delete_message` |
| Platform extension action | `{platform}.` prefix or protocol-generic name | `yunhu.board`, `send_poke` (OB11 extension) |
| Decorator | PascalCase; generic capabilities go into the framework base class | `.Keyboard(rows)`, `.At(uid)` |
| Standard event field | generic concepts without prefix | `interaction_id`, `button_data`, `request_id` |
| Platform event field | `{platform}_` prefix | `qqbot_event_id`, `telegram_chat_id` |

### 3.2 Parameter and Return Rules

- Standard parameters are **identical in name and meaning** on all platforms; units/formats are explicitly specified in the standard documents (e.g., second-level timestamps, string IDs)
- Required parameters take the **common subset** of platform capabilities; platform-enhanced capabilities become optional parameters
- Hard platform constraints (e.g., QQBot rich media cannot be mixed with event_id) are automatically handled/degraded by the adapter and not exposed to modules
- Standard fields in the returned `data` are consistent across all platforms; extra platform information goes into platform-named fields within `data` or `{platform}_raw`

## 4. Difference-Handling Patterns (Adapter Layer)

| Pattern | Description | Example |
|------|------|------|
| **Parameter mapping** | standard parameters → platform native parameters | `delete_message(message_id)` → TG `deleteMessage(chat_id, message_id)` (registry fills in chat_id) |
| **Structure conversion** | standard segment → platform native structure | `keyboard` segment → `inline_keyboard` / buttons / QQBot keyboard |
| **Action mapping** | standard action name → platform action name | `get_self_info` → `get_login_info` (OB11) |
| **Field normalization** | platform response → standard fields | `getMe()` → `{user_id, user_name, user_displayname}` |
| **Synthesized identifiers** | generate deterministic IDs when the platform has no native identifier | TG join request has no ID → `tjr_{chat}_{user}_{date}` |
| **Capability degradation** | textualize/return 10002 when unsupported | Kook has no keyboard → textualize into alt_message; `get_friend_list` → 10002 |
| **Normalization** | dirty platform data → standard format | QQBot @ marker openid → bot_id (name normalization) |
| **Dual-track compatibility** | accept both standard structures and platform native structures | `.Keyboard()` accepts generic rows or native structures |

---

## 5. Interactive Component Standard

### 5.1 Component List and Status

| Component | Standard segment type | Status | Supported platforms |
|------|------------|------|-----------|
| Button/keyboard (keyboard) | `keyboard` | ✅ Standardized | Telegram / Yunhu / QQBot |
| Dropdown select (select) | `select` | 📋 Reserved (structure in §5.4) | Discord / Telegram(bot) |
| Card (card) | `card` | 📋 Reserved (see §5.5) | Kook / Yunhu(html) |
| Modal (modal) | `modal` | 📋 Reserved | Discord |

> Decorator layering convention: Send decorators for generic interactive components are **implemented by the adapter's Send class** (not built into the framework base class); naming follows the §5.2 conventions and parameters follow the standard structures in this document.

### 5.2 keyboard Buttons/Inline Keyboard

#### Message Segment Structure (Send Direction)

The standard `keyboard` segment = a two-dimensional `rows` array, where each button is
`{"label": "Display text", "type": "callback" | "link", "data": "callback data or link URL"}`;
platform-specific optional fields are also allowed (adapters map or ignore them according to capability).

> **Authoritative structure definition**: for the complete message segment JSON, field table, and field semantics, see
> [Event Conversion Standard §4.1.1 keyboard button/inline keyboard segment](event-conversion.md#411-keyboard-buttoninline-keyboard-segment-cross-platform-universal);
> this section does not repeat them.

#### Per-Platform Mapping Reference

| Platform | Standard segment → native structure | Native structure reference |
|------|------------------|-------------|
| Telegram | `reply_markup.inline_keyboard`: `[{text, callback_data \| url}]` | callback→`callback_data` (≤64 bytes), link→`url` |
| Yunhu | `content.buttons`: `[{label, action_type}]` | callback→`action_type:2` + `action` + `value`, link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`: `[{label, type, data}]` | callback→`type:2` + `data`, link→`type:0` + `data` (message must be of markdown type) |
| Kook | card `action-group` module: `[{type, text, value, click}]` | callback→`click:return` + `value`, link→`click:link` + `url` |
| Discord | `components[].components`: `[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`, link→`style:5` + `url` |

#### Send Decorators (Implemented by Each Adapter's Send Class)

Generic decorators are **implemented by each adapter in its own Send class** (without modifying the framework base class):

- `.Keyboard(rows)`: standard naming; accepts the §5.2 generic rows structure; internally generates the standard `keyboard`
  message segment (or directly converts to the platform native structure), uniformly processed by `Raw_ob12`
- `.Buttons(rows)`: optional semantic alias with identical behavior
- **Backward compatibility**: when a platform native structure is detected, it is passed through directly (no error, no conversion)
- Platform native extension segments (e.g., `telegram_inline_keyboard`) continue to be passed through, unaffected

```python
# The same code, on any platform (each adapter provides the decorators and conversion)
rows = [[{"label": "Like", "type": "callback", "data": "like:1"},
         {"label": "Homepage", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("Please choose")
```

> Adapter compatibility list: QQBot / Telegram / Yunhu are already implemented (decorators + standard segment conversion);
> new adapters simply need to implement per this document (see §7 Checklist).

### 5.3 Interaction Callback Events (After a Button Is Clicked)

After a user clicks a button, the event pushed by the platform **must** provide the following standard fields (detail_type may keep the platform naming):

| Standard field | Type | Required | Description |
|---------|------|------|------|
| `interaction_id` | str | Yes | ID of this interaction (can be used to respond, e.g., spinner/toast) |
| `button_data` | str | Yes | Data returned by the button (i.e., the `data` of §5.2) |
| `button_label` | str | No | Button display text |
| `user_id` | str | Yes | The user who clicked |
| `message_id` | str | No | Message containing the button |
| `group_id` / `channel_id` | str | No | Source session |

**detail_type convention**: keep each platform's existing naming (`qqbot_interaction` / `telegram_callback_query` /
`yunhu_a2ui_button`, etc.), but **the standard fields must be complete** — modules can fetch values cross-platform simply with `event.get("button_data")`.

**Suggested Event extension methods** (provided by the adapter's EventMixin):

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**Responding to interactions** (per platform capability): `adapter.reply_interaction(interaction_id, code=0)` (QQBot) /
`answerCallbackQuery` (Telegram), etc.; naming follows the platform's method family and is not forcibly unified.

#### Per-Platform Callback Event Mapping

| Platform | Native event | detail_type | interaction_id source | button_data source |
|------|---------|-------------|--------------------|-----------------|
| Telegram | `callback_query` | `telegram_callback_query` (notice) | `callback_query.id` | `callback_query.data` |
| Yunhu | Button click event | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | Button click event | `kook_button_click` | `msg_id`+`value` | `value` |
| Discord | `INTERACTION_CREATE` | `discord_interaction` | `interaction.id` | `data.custom_id` |

### 5.4 select Dropdown Select (Reserved)

```json
{
  "type": "select",
  "data": {
    "placeholder": "Please choose",
    "options": [
      {"label": "Option A", "data": "opt:A"},
      {"label": "Option B", "data": "opt:B"}
    ],
    "min_values": 1,
    "max_values": 1
  }
}
```

The callback event reuses the §5.3 fields (`button_data` = the selected `data`; a JSON array for multiple selections).
First batch of implementing platforms: Discord (select menu), Telegram (keyboard switching). Platforms without an implementation should degrade this segment into a text list in `alt_message` when received.

### 5.5 card Card (Reserved, Standardization Deferred)

Card structures vary greatly (Kook full-featured card modules vs Yunhu html vs QQ markdown+keyboard),
so no strict standard is imposed for now. Recommendations:

- Express rich-text cards with a `text` + `keyboard` combination (sufficient for most scenarios)
- Platform full-featured cards continue to use the `{platform}_card` extension segment (e.g., `kook_card`)
- Re-evaluate for promotion to standard once isomorphic card capabilities appear on ≥2 platforms

---

## 6. Future Candidates (Roadmap)

The following capabilities have appeared or are expected to appear on ≥2 platforms; standardization proceeds by priority:

| Candidate | Platforms involved | Priority | Notes |
|------|---------|--------|------|
| select dropdown | Discord / Telegram | High | Structure draft in §5.4 |
| Reactions (reactions) | QQBot / Telegram / Discord / Kook | High | Standardize both the action side and the event side |
| Group management actions (mute/kick/approval) | QQBot / Yunhu / OB11 | High | Most already implemented as platform actions; standard signatures to be extracted |
| Announcements/boards | Yunhu / Telegram / Discord | Medium | Actions like `set_announcement` |
| File resource model (two-part file_id) | All platforms | Low (deferred) | Direct-send `SendDSL.File(file, filename)` is already the standard path (URL/path/bytes direct upload, see [Send Method Specification §2.1](send-method-spec.md)); the file_id model is passed through only when the backend natively supports it, see [API Action Standard §3.5](api-action-spec.md) |
| card Card | Kook / Yunhu | Low | Structures vary greatly, see §5.5 |
| form Form | Yunhu | Low | Platform-specific; keep the `{platform}_` prefix |
| Media transcoding/size probing | All platforms | Low | Implemented inside adapters; not standardized externally |

## 7. Standard Checklist for New Adapter Developers

When developing a new adapter, implement against this checklist (★ = required, the rest recommended):

- [ ] ★ Convert events to OneBot12 standard structures, inheriting `BaseConverter`
- [ ] ★ Support sending and receiving standard message segments (text/image/mention/reply/keyboard…; media segments handled per the form tiers and degradation ladder in
      [Send Method Specification §2.1](send-method-spec.md))
- [ ] ★ Implement `Raw_ob12` (including standard segment → platform structure conversion; the standard `keyboard` segment is mandatory)
- [ ] ★ Return the standard response structure (`make_response`/`make_error`)
- [ ] ★ Multi-account: `AccountConfigClass(BotAccountConfig)` + account resolution (account name / `bot_id` matching)
- [ ] ★ Send class inherits `BaseAdapter.Send`, using `_apply_modifiers`/`send_context`
- [ ] ☆ Api DSL: map standard actions to platform APIs (see API Action Standard)
- [ ] ☆ Request DSL: request events include `request_id` + `accept/reject`
- [ ] ☆ Interactive components: `keyboard` segment conversion + interaction callback standard fields + `.Keyboard()`/`.Buttons()` decorators (implemented in the adapter's Send class)
- [ ] ☆ EventMixin: platform extension methods such as `get_raw_event()` / `get_button_data()`
- [ ] ☆ Use `runtime.spawn_background` for lifecycle tasks
- [ ] ☆ Use `self.cfg` for configuration access
- [ ] ☆ Soft framework dependency: no hard ErisPulse dependency declared + runtime version detection
- [ ] ☆ i18n: multilingual config fields and logs
- [ ] ☆ platform-guide platform documentation + platform-features.md in the adapter repository

## 8. Related Documents

- For domain-specific standards, see the §2 standard map
- Built-in framework adapters can serve as reference implementations: QQBot (full v5 paradigm), OneBot11 (Api DSL mapping), Yunhu (BaseConverter + Web API extension)