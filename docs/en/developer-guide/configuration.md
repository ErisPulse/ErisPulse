# Configuration and UI Metadata

> Scope: All configuration declarations that inherit from `BaseConfig` / `BotAccountConfig` (adapter global configuration, account configuration, module configuration).

ErisPulse's configuration system is **declarative**: developers describe configuration items using dataclass fields + metadata, and the framework's `get_config_schema()` translates them into JSON Schema for any consumer (Dashboard, third-party panels, CLI wizards, etc.) to render. This document serves as the **normative definition** of this metadata—widget semantics, value forms, conditional visibility, and compatibility obligations are all governed by it; each consumer is responsible for its own implementation, and its semantics must remain consistent with this document.

## Declaration Structure

```python
from dataclasses import dataclass, field
from ErisPulse.Core.Bases import BaseConfig, BotAccountConfig

@dataclass
class MyAdapterConfig(BaseConfig):
    """Adapter global configuration"""

@dataclass
class MyAccountConfig(BotAccountConfig):
    """Account configuration (multi-account adapter)"""
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

## Basic Metadata (metadata top-level keys)

| Key | Type | Semantics |
|---|---|---|
| `description` | `str` or `{"i18n": key, "default": text}` | Description of the configuration item (supports i18n references) |
| `required` | `bool` | Required (validation and UI hints; when a required account field is empty, the consumer can be prompted that the configuration is incomplete) |
| `secret` | `bool` | Sensitive value: the UI must render it as a password field, and it must be masked in logs |

## UI Metadata (the `metadata["ui"]` Subtable)

`ui` is the standard key; `webui` is a legacy alias (equivalent, and consumers must support both).

### Common Keys

| Key | Semantics |
|---|---|
| `widget` | Widget type (see the widget catalog); inferred from the field type when omitted |
| `group` | Group name; the display name for a group is provided by `_schema_meta["group_labels"]` (also supports i18n dictionaries) |
| `order` | Sorting weight within the group (smaller comes first, defaults to 100) |
| `options` | Enumerated options `[{label, value}]` (`label` supports i18n dictionaries; used for select/multiselect) |
| `placeholder` | Input placeholder text (supports i18n dictionaries) |
| `min` / `max` / `step` | Numeric range and step (number/slider) |
| `rows` | Number of rows for multi-line text (textarea) |

### Conditional Show/Hide and Disable (Field Linkage)

| Key | Semantics |
|---|---|
| `show_if` | **Hides** the field when the condition is not met (the value is kept, not deleted) |
| `disabled_if` | **Disables** the field when the condition is met (grayed out and locked, the value is kept) |

Condition object: `{"field": <field name in the same scope or full config key>, "op": <operator>, "value": <comparison value>}`. Operator set:

| op | Semantics |
|---|---|
| `eq` / `ne` | Equal / not equal (stringified comparison) |
| `in` / `nin` | `value` is an array; membership / non-membership |
| `gt` / `gte` / `lt` / `lte` | Numeric comparison |
| `truthy` | Truthy (non-empty, not `"false"`, not `"0"`) |

`op` defaults to `eq`. Field resolution: first by the **short name within the same config scope**, then by the full key (e.g., `accounts.default.mode`).

### Value Form (`value_type`, used for `multiselect`)

| Value | Storage Form | Applicability |
|---|---|---|
| `json` (default) | JSON array as a **string** (e.g., `"[0, 25]"`) | Field type is `str`, storing the array as JSON text |
| `array` | Native array | Field type is `list` |
| `mask` | Bitmask as an **integer** (checked values are summed via `2^v`) | Field type is `int` used as bit flags, where `options[].value` is the bit index |

**Consumer obligation**: when `value_type` is omitted, it must be inferred from the field type (`int` + numeric options → `mask`; `list` → `array`; otherwise `json`), ensuring that declaring only `widget: multiselect` still writes the correct type.

## Widget Catalog

Consumers implement the following semantics; **unrecognized widgets must fall back to single-line text** and must not raise errors.

| widget | Value Type | Semantics |
|---|---|---|
| `text` | str | Single-line text (default fallback target) |
| `textarea` | str | Multi-line text (`rows`) |
| `password` | str | Password (automatically inferred when `secret: True`) |
| `number` | int/float | Number input (`min`/`max`/`step`; automatically inferred for numeric-typed fields) |
| `switch` | bool | Toggle switch (automatically inferred for bool fields) |
| `select` | str | Single-select dropdown (`options`; automatically inferred for string fields with options) |
| `multiselect` | see value forms | Multi-select (checkbox group; `options` + `value_type`) |
| `slider` | int/float | Slider (`min`/`max`/`step`) |
| `color` | str | Color (`#rrggbb`) |
| `date` / `time` / `datetime` | str | Date / time / datetime (ISO string) |
| `kv` | dict | Key-value pair editor (`dict[str, str]`) |
| `list` | list | List editor (`item` declares inline fields: `{"widget": ...}` or `{"fields": {...}}` supports inline nesting) |

## Compatibility Contract (Consumers Must Comply)

1. **Ignore unknown keys**: Keys in metadata that are outside the specification (including those added in the future) must be silently ignored without raising errors
2. **Unknown widgets fall back to text**: Ensures that new declarations remain editable on older consumers
3. **Unmet condition ≠ value deletion**: Field values hidden by `show_if` are preserved as-is
4. **Type inference as fallback**: When extension keys such as `value_type` are missing, the correct storage form is inferred from the field type

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
                    {"label": "Server (Passive)", "value": "server"},
                    {"label": "Client (Active)", "value": "client"},
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
            "description": "Bitmask multi-select (field is int, values are stored automatically by mask)",
            "ui": {
                "widget": "multiselect",
                "group": "advanced",
                "order": 3,
                "options": [
                    {"label": "Guild Base", "value": 0},
                    {"label": "Guild Messages", "value": 9},
                    {"label": "Message Content (Privileged)", "value": 15},
                ],
            },
        },
    )
```

## Schema Output

`ErisPulse.Core.Bases.config_schema.get_config_schema(cls)` outputs a JSON Schema (`fields`/`groups`/`account_based`/`meta`), and **passes through as-is** all `ui` sub-table keys defined in this document, for consumers to consume directly.