# Configuration and UI Metadata

> Applicable to: all configurations inheriting `BaseConfig` / `BotAccountConfig` (adapter global config, account config, module config).

ErisPulse's configuration system is **declarative**: developers describe configuration fields using dataclass fields and metadata, and the framework's `get_config_schema()` translates them into JSON Schema, which can be rendered by any consumer (Dashboard, third-party panels, CLI wizard, etc.). This document defines the **specification** for this metadata—widget semantics, value shapes, conditional visibility, and compatibility obligations are all based on this document. Each consumer is responsible for its own implementation, but the semantics must be consistent with this document.

## Declaration Structure

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """Adapter global configuration"""

@dataclass
class MyAccountConfig(BotAccountConfig):
    """Account configuration (for multi-account adapters)"""
    token: str = field(
        default="",
        metadata={
            "description": "Access token",
            "required": True,
            "secret": True,
            "ui": {
                "widget": "password",
                "group": "basic",
                "order": 1,
                "placeholder": "Paste platform token",
            },
        },
    )
```

## Basic Metadata (Top-level keys in `metadata`)

| Key | Type | Semantics |
|---|---|---|
| `description` | `str` or `{"i18n": key, "default": text}` | Configuration item description (supports i18n reference) |
| `required` | `bool` | Required (validation and UI prompt; if account required fields are empty, consumers can prompt incomplete configuration) |
| `secret` | `bool` | Sensitive value: UI must present as password, and log must be masked |

## UI Metadata (`metadata["ui"]` sub-table)

`ui` is the standard key; `webui` is an old alias (equivalent, consumers must support both).

### Container Types (`list[T]` / `dict[str, T]`)

When the field annotation is a **typed container**, the member type is automatically included in the schema:

- `list[int]` / `list[str]` etc. scalar arrays: schema includes `item` (scalar schema of the member), and if `widget` is not declared, it is automatically inferred as `list` control (panel renders as a dynamic row list).
- `list[SomeDataclass]`: `item` is `{"type": "object", "fields": {...}}`, and the panel renders as **inline multi-field** object rows (inline fields recursively support all controls and bindings).
- `dict[str, T]`: dynamic key table, `item` carries the value type; panel renders as key-value editor.
- Manual `ui.item` takes precedence over auto-generated (explicit declaration overrides inference).

During loading (`dict_to_dataclass`), members are normalized by their declared type: scalar types are converted (`["1", 2.0]` → `[1, 2]`), dataclass members are instantiated (non-dict scalar is wrapped as the first field), and the entire JSON string is parsed first (for panel JSON editing state / env override). During validation (`validate_config`), member types and nested constraints of dataclass fields are recursively checked, and error messages include member paths (`rules[0]` / `quotas.q`).

In TOML templates, elements / values of dataclass containers are rendered as `[[table array]]` / `[table.key]` blocks (elements are expanded one by one if present, otherwise a comment skeleton is output; empty containers **do not** output `key = []`—static empty arrays and subsequent `[[key]]` appends are mutually exclusive, making it impossible for users to add via table array format).

```python
@dataclass
class RetryRule(BaseConfig):
    host: str = field(default="", metadata={"description": "Target host"})
    port: int = field(default=0, metadata={"description": "Port", "required": True})

@dataclass
class MyConfig(BaseConfig):
    rules: list[RetryRule] = field(default_factory=list)   # Panel: list of object rows
    quotas: dict[str, RetryRule] = field(default_factory=dict)  # Panel: key-value table
    nums: list[int] = field(default_factory=list)          # Panel: list of scalar rows
```

### General Keys

| Key | Semantics |
|---|---|
| `widget` | Control type (see widget catalog); inferred by field type if not declared |
| `group` | Group name; same group name is provided display name by `_schema_meta["group_labels"]` (also supports i18n dictionary) |
| `order` | Group sort weight (smaller first, default 100) |
| `options` | Enum options `[{label, value}]` (`label` supports i18n dictionary; used for select/multiselect) |
| `placeholder` | Input placeholder text (supports i18n dictionary) |
| `min` / `max` / `step` | Numeric range and step (number/slider) |
| `rows` | Number of rows for multi-line text (textarea) |
| `presets` | Preset color palette (color; `["#rrggbb", ...]`, default uses consumer's built-in) |

### Conditional Visibility/Disablement (Field Linkage)

| Key | Semantics |
|---|---|
| `show_if` | Hides the field if the condition is not met (value retained, not deleted) |
| `disabled_if` | Disables the field if the condition is met (grayed out, value retained) |

Condition object: `{"field": <field name in same scope or full config key>, "op": <operator>, "value": <comparison value>}`. Operator set:

| op | Semantics |
|---|---|
| `eq` / `ne` | Equal / Not equal (stringified comparison) |
| `in` / `nin` | `value` is an array, member / non-member |
| `gt` / `gte` / `lt` / `lte` | Numerical comparison |
| `truthy` | Truthy (non-empty, not `"false"`, not `"0"`) |

`op` defaults to `eq`. Field resolution: first by **short name in same config scope**, then by full key (e.g., `accounts.default.mode`).

### Value Shape (`value_type`, used for `multiselect`)

| Value | Storage Shape | Applicable |
|---|---|---|
| `json` (default) | JSON array **string** (e.g. `"[0, 25]"`) | Field type is `str`, storing array as JSON text |
| `array` | Native array | Field type is `list` |
| `mask` | Bitmask **integer** (selected values summed as `2^v`) | Field type is `int` bitmask, `options[].value` is bit position |

**Consumer obligation**: If `value_type` is missing, it must be inferred by field type (`int` + numeric options → `mask`; `list` → `array`; otherwise `json`), ensuring correct type storage even when only `widget: multiselect` is declared.

## Widget Catalog

Consumers must implement the following semantics; **unrecognized widgets must fall back to single-line text**, without error reporting.

| widget | Value Type | Semantics |
|---|---|---|
| `text` | str | Single-line text (default fallback target) |
| `textarea` | str | Multi-line text (with `rows`) |
| `password` | str | Password (automatically inferred if `secret: True`) |
| `number` | int/float | Number input (with `min`/`max`/`step`; numeric fields automatically inferred) |
| `switch` | bool | Toggle switch (bool fields automatically inferred) |
| `select` | str | Single-select dropdown (with `options`; string fields with options automatically inferred) |
| `multiselect` | See value shape | Multi-select (checkbox group; `options` + `value_type`) |
| `slider` | int/float | Slider (with `min`/`max`/`step`) |
| `color` | str | Color (in `#rrggbb` format) |
| `date` / `time` / `datetime` | str | Date / Time / DateTime (ISO string) |
| `kv` | dict | Key-value editor (for `dict[str, str]`) |
| `list` | list | List editor (with `item` declaring inline fields: `{"widget": ...}` or `{"fields": {...}}` supports inline nesting; typed array fields automatically inferred) |

## Compatibility Contract (Consumers Must Comply)

1. **Ignore unknown keys**: Unknown keys in metadata (including future additions) are silently ignored, without error.
2. **Unknown widget falls back to text**: New declarations must still be editable on old consumers.
3. **Condition not met ≠ value deletion**: Hidden fields by `show_if` retain their original values.
4. **Type inference fallback**: If extension keys like `value_type` are missing, infer correct storage shape by field type.

## Complete Example

```python
@dataclass
class OneBotAccountDemo(BotAccountConfig):
    mode: str = field(
        default="server",
        metadata={
            "description": "Connection mode",
            "ui": {
                "widget": "select",
                "group": "connection",
                "order": 1,
                "options": [
                    {"label": "Server (passive)", "value": "server"},
                    {"label": "Client (active)", "value": "client"},
                ],
            },
        },
    )
    url: str = field(
        default="ws://127.0.0.1:3001",
        metadata={
            "description": "WebSocket address",
            "ui": {
                "widget": "text",
                "group": "connection",
                "order": 2,
                "show_if": {"field": "mode", "op": "eq", "value": "client"},
            },
        },
    )
    intents: int = field(
        default=33281,
        metadata={
            "description": "Bitmask multi-select (field is int, automatically stored as mask)",
            "ui": {
                "widget": "multiselect",
                "group": "advanced",
                "order": 3,
                "options": [
                    {"label": "Channel basic", "value": 0},
                    {"label": "Channel message", "value": 9},
                    {"label": "Message content (privileged)", "value": 15},
                ],
            },
        },
    )
```

## Schema Output

`ErisPulse.Core.Bases.config_schema.get_config_schema(cls)` outputs JSON Schema (`fields`/`groups`/`account_based`/`meta`), and **transparently passes through** all `ui` sub-table keys defined in this document, for direct consumption by consumers.