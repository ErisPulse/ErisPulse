# Adapter Standardization Guide (General Overview)

This document is the **general overview** of ErisPulse adapter standardization: it establishes cross-platform standardization principles, standard maps, difference handling models, the process for new capabilities to enter the standard, and provides complete definitions for **interaction component standards** (buttons/keyboard, dropdowns, etc.) and **interaction callback events**. Any adapter developer implementing new features should **prioritize using the standard definitions**, ensuring that module developers can achieve a consistent experience across any platform with the same code—consistent naming, consistent parameters, and consistent returns.

---

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

## 5. Interaction Component Standards

### 5.1 Component List and States

| Component | Standard Segment type | Status | Supported Platforms |
|-----------|-----------------------|--------|---------------------|
| Button/Keyboard (keyboard) | `keyboard` | ✅ Standardized | Telegram / Yunhu / QQBot |
| Dropdown Selection (select) | `select` | 📋 Reserved (structure in §5.4) | Discord / Telegram(bot) |
| Card (card) | `card` | 📋 Reserved (see §5.5) | Kook / Yunhu(html) |
| Modal (modal) | `modal` | 📋 Reserved | Discord |

> Modifier Hierarchy Convention: Send modifiers for generic interaction components are implemented by the **adapter's Send class** (not built into the framework base class), following the naming convention in §5.2, with parameters conforming to the standard structure defined in this document.

### 5.2 keyboard Button/Inline Keyboard

#### Message Segment Structure (Sending Direction)

```json
{
  "type": "keyboard",
  "data": {
    "rows": [
      [
        {"label": "Option A", "type": "callback", "data": "vote:A"},
        {"label": "Website",   "type": "link",     "data": "https://example.com"}
      ]
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.rows` | 2D array | Yes | Each sub-array represents a row of buttons |
| `rows[][].label` | str | Yes | Text displayed on the button |
| `rows[][].type` | str | Yes | `callback` (click sends back data) / `link` (redirects to URL) |
| `rows[][].data` | str | Yes | Callback data (for `callback`) or redirect address (for `link`) |
| `rows[][].*` | Any | No | Platform-specific optional fields (e.g., `web_app`, `menus`), adapter maps or ignores based on capability |

#### Platform Mapping Comparison

| Platform | Standard Segment → Native Structure | Native Structure Reference |
|----------|-------------------------------------|----------------------------|
| Telegram | `reply_markup.inline_keyboard`: `[{text, callback_data \| url}]` | callback→`callback_data` (≤64 bytes), link→`url` |
| Yunhu | `content.buttons`: `[{label, action_type}]` | callback→`action_type:2` + `action` + `value`, link→`action_type:1` + `url` |
| QQBot | `keyboard.content.rows`: `[{label, type, data}]` | callback→`type:2` + `data`, link→`type:0` + `data` (message must be markdown type) |
| Kook | Card `action-group` module: `[{type, text, value, click}]` | callback→`click:return` + `value`, link→`click:link` + `url` |
| Discord | `components[].components`: `[{label, style, custom_id \| url}]` | callback→`style:1` + `custom_id`, link→`style:5` + `url` |

#### Send Modifier (Implemented by Each Adapter's Send Class)

The generic modifier is implemented by **each adapter in its own Send class** (without modifying the framework base class):

- `.Keyboard(rows)`: Standard naming, accepts the generic rows structure in §5.2, internally generates the standard `keyboard` message segment (or directly converts to the platform-native structure), handled uniformly by `Raw_ob12`
- `.Buttons(rows)`: Optional semantic alias, behavior is identical
- **Backward Compatibility**: When platform-native structures are detected, they are directly passed through (no error, no conversion)
- Platform-native extension segments (e.g., `telegram_inline_keyboard`) continue to be passed through and remain unaffected

```python
# Same code, any platform (adapters provide modifier and conversion)
rows = [[{"label": "Like", "type": "callback", "data": "like:1"},
         {"label": "Homepage", "type": "link", "data": "https://example.com"}]]
await adapter.Send.To("group", gid).Keyboard(rows).Text("Please select")
```

> Adapter Compatibility List: QQBot / Telegram / Yunhu have implemented (modifier + standard segment conversion); new adapters can implement as described in this document (see §7 Checklist).

### 5.3 Interaction Callback Events (After Button Click)

After the user clicks a button, the event pushed by the platform **must** provide the following standard fields (detail_type may retain platform naming):

| Standard Field | Type | Required | Description |
|----------------|------|----------|-------------|
| `interaction_id` | str | Yes | ID for this interaction (can be used to respond, e.g., show loading/feedback) |
| `button_data` | str | Yes | Button callback data (i.e., `data` in §5.2) |
| `button_label` | str | No | Button display text |
| `user_id` | str | Yes | Clicker |
| `message_id` | str | No | Message where the button is located |
| `group_id` / `channel_id` | str | No | Source session |

**detail_type Convention**: Retain existing platform naming (`qqbot_interaction` / `telegram_callback_query` / `yunhu_a2ui_button` etc.), but **standard fields must be complete**—modules can retrieve values cross-platform using `event.get("button_data")`.

**Recommended Event Extension Methods** (provided by adapter EventMixin):

```python
def get_button_data(self) -> str: ...     # button_data
def get_interaction_id(self) -> str: ...  # interaction_id
```

**Responding to Interaction** (according to platform capability): `adapter.reply_interaction(interaction_id, code=0)` (QQBot) / `answerCallbackQuery` (Telegram), naming follows the platform method family, no mandatory unification.

#### Platform Callback Event Mapping

| Platform | Native Event | detail_type | interaction_id Source | button_data Source |
|----------|--------------|-------------|-----------------------|--------------------|
| Telegram | `callback_query` | `telegram_callback_query` (notice) | `callback_query.id` | `callback_query.data` |
| Yunhu | Button click event | `yunhu_button_click` / `yunhu_a2ui_button` | `buttonId` / `sourceComponentId` | `value` / `actionName` |
| QQBot | `INTERACTION_CREATE` | `qqbot_interaction` | `interaction.id` | `data.resolved.button_data` |
| Kook | Button click event | `kook_button_click` | `msg_id`+`value` | `value` |
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

Callback events reuse the fields in §5.3 (`button_data` = selected `data`, array for multiple selections). First platforms to implement: Discord (select menu), Telegram (keyboard switching). Platforms not implementing this segment should degrade to a text list in `alt_message`.

### 5.5 card Card (Reserved, Postponed Standardization)

Card structures vary greatly (Kook full-featured card module vs Yunhu html vs QQ markdown+keyboard), so no strict standard is enforced yet. Suggestions:

- Express rich text cards using `text` + `keyboard` combinations (sufficient for most scenarios)
- Continue using `{platform}_card` extension segments (e.g., `kook_card`) for full-featured cards
- Re-evaluate and upgrade once ≥2 platforms have similar card capabilities

## 6. Future Candidates (Roadmap)

The following capabilities have appeared or are expected to appear on ≥2 platforms and are being prioritized for standardization:

| Candidate | Platforms Involved | Priority | Notes |
|-----------|--------------------|----------|-------|
| select dropdown selection | Discord / Telegram | High | Structural draft available in §5.4 |
| Reactions (emoji reactions) | QQBot / Telegram / Discord / Kook | High | Standardization of actions and events on both sides |
| Group management actions (mute/kick/approve) | QQBot / Yunhu / OB11 | High | Most implemented as platform actions, awaiting standardized signatures |
| Announcements/boards | Yunhu / Telegram / Discord | Medium | `set_announcement`-like actions |
| File upload standard (two-part file_id) | All platforms | Medium | See API action standard (currently available as a downgrade) |
| Card | Kook / Yunhu | Low | Large structural differences, see §5.5 |
| Form | Yunhu | Low | Platform-specific, maintain `{platform}_` prefix |
| Media transcoding/size detection | All platforms | Low | Implemented internally by adapters, not standardized externally |

## 7. Standard Checklist for New Adapter Developers

When developing a new adapter, please refer to this checklist to ensure implementation (★ indicates required, others are recommended):

- [ ] ★ Convert events into the OneBot12 standard structure, inherit `BaseConverter`
- [ ] ★ Support standard message segment sending and receiving (text/image/mention/reply/keyboard…)
- [ ] ★ Implement `Raw_ob12` (including standard segment → platform structure conversion; standard `keyboard` segment must be implemented)
- [ ] ★ Return standard response structure (`make_response`/`make_error`)
- [ ] ★ Multi-account: `AccountConfigClass(BotAccountConfig)` + `_resolve_account`
- [ ] ★ `Send` class inherits `BaseAdapter.Send`, use `_apply_modifiers`/`send_context`
- [ ] ☆ Api DSL: Map standard actions to platform APIs (see API Action Standards)
- [ ] ☆ Request DSL: Request events include `request_id` + `accept/reject`
- [ ] ☆ Interactive components: `keyboard` segment conversion + standard fields for interactive callbacks + `.Keyboard()`/.Buttons()` decorators (implemented in adapter's `Send` class)
- [ ] ☆ EventMixin: Platform extension methods such as `get_raw_event()` / `get_button_data()`
- [ ] ☆ Use `runtime.spawn_background` for lifecycle tasks
- [ ] ☆ Use `self.cfg` for configuration reading
- [ ] ☆ Framework soft dependencies: Do not declare hard dependency on ErisPulse + runtime version detection
- [ ] ☆ i18n: Multi-language for configuration fields and logs
- [ ] ☆ Platform documentation (`platform-guide`) + `platform-features.md` in adapter repository

## 8. Related Documentation

- See §2 Standard Maps for standards in various domains.
- Built-in adapters in the framework can serve as reference implementations: QQBot (full v5 paradigm), OneBot11 (API DSL mapping), YunHu (BaseConverter + Web API extension).