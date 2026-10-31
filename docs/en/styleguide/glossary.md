# Glossary (Single Source of Truth)

> [!TIP]
> **When to read this**: When writing or editing documentation and unsure what to call a concept, or when you find two documents using inconsistent terms for the same concept. Skip if unnecessary.

This document converges core concepts that have been inconsistently named across ErisPulse documentation. Each term is given a single **official name**, a set of **Chinese-English equivalents**, and a brief **historical alias explanation**; if the main text or other documents contradict this, use this table as the authoritative reference and please update conflicting documents accordingly.

Inclusion criteria:

- Only include terms that have historically had shifting names or ambiguous Chinese-English usage; purely code identifiers (e.g., `BaseModule`) are not included
- Each definition has been verified by grepping the entire `docs/zh-CN` directory and source code to ensure alignment with mainstream usage
- In documents, use the full term (Chinese + English in parentheses) on first appearance, then use the abbreviated form thereafter

---

## 1. Client and HttpClient

| Item | Content |
|------|------|
| Official Name | `Client` (base class `BaseClient`) |
| Chinese-English Equivalents | Client (unified HTTP/WS client) |
| Historical Aliases | `HttpClient` (class name before 2.8.0, kept as a backward-compatible alias); `BaseHttpClient` (base class name before 2.8.0, kept as a backward-compatible alias) |

**Single Definition**: A unified HTTP/WS client that abstracts the underlying request library (currently aiohttp), providing request statistics, retry mechanisms, logging, WebSocket client functionality, and ErisPulse's exception system. As of version 2.8.0, the class name was changed from `HttpClient` to `Client`, but the `sdk.client` attribute name remains unchanged.

**Documentation Style**: Always write `Client`; mention `HttpClient` only in contexts related to legacy code migration or compatibility, and note it as a "backward-compatible alias." See [http-client](../advanced/http-client.md) and [Architecture Overview](../architecture.md) for definition references.

## 2. storage, env, and StorageManager

| Item | Content |
|------|------|
| Official Name | Instance: `storage` (type `BaseStorage`); Base class: `BaseStorage` |
| Chinese-English Equivalents | storage (storage); StorageManager (storage manager, old class name) |
| Historical Aliases | `env` (v1 legacy alias, = same instance); `StorageManager` (original class name before multi-backend refactoring for SQLite implementation, now a backward-compatible alias for `SQLiteStorage`) |

**Single Definition**: Runtime storage is accessed via the `storage` instance (`sdk.storage` or `from ErisPulse import storage`), and the specific backend is configured through `ErisPulse.storage.backend` (default sqlite, can switch to mysql / postgres), with consistent APIs across all three backends.

**Documentation Style**: When describing the "storage system" or "storage capability," use 「storage (storage)」; when referring to types, use `BaseStorage`; for specific backends, use `SQLiteStorage` / `MySQLStorage` / `PostgresStorage`. `StorageManager` is **only a legacy class name for the SQLite implementation**, not representative of the storage system as a whole, and should not be used in new documentation; `env` is a v1 legacy alias (same instance), used only for legacy code compatibility. Use `sdk.storage` in documentation and examples. See [Storage Backends](../advanced/storage-backends.md) and [SQL Builder](../advanced/sql-builder.md) for definition references.

## 3. BaseConfig and AdapterConfig (including ui / webui metadata keys)

| Item | Content |
|------|------|
| Official Name | Base class: `BaseConfig`; Field control configuration key: `"ui"` |
| Chinese-English Equivalents | BaseConfig (declarative configuration base class); AdapterConfig (old name, backward-compatible alias) |
| Historical Aliases | `AdapterConfig` (= `BaseConfig` backward-compatible alias); `"webui"` field metadata key (old name, still compatible) |

**Single Definition**: `BaseConfig` is a generic declarative configuration base class applicable to adapters, modules, external projects, and any scenario (configuration classes are declared as nested `ConfigClass` and attached to modules/adapters). The official name for the WebUI control configuration key in the field `metadata` is `"ui"`; the priority order is `"ui"` > `"webui"`, with `"webui"` only retained for legacy code compatibility.

**Documentation Style**: Always use `BaseConfig` and `"ui"`. Note: In example code, names like `MyAdapterConfig` are **developer-defined sub-class naming conventions** and are unrelated to the `AdapterConfig` alias. See [Adapter Core Concepts](../developer-guide/adapters/core-concepts.md) and [Module Core Concepts](../developer-guide/modules/core-concepts.md) for definition references.

## 4. Scope (three-dimensional)

| Item | Content |
|------|------|
| Official Name | Overall: scope; Three dimensions: **module dimension / identity dimension / outbound dimension** |
| Chinese-English Equivalents | module dimension (module dimension), identity dimension (identity dimension), outbound dimension (outbound dimension) |
| Historical Aliases | No old names, but historically there have been inaccurate generic terms like "permission system" or "whitelist/blacklist system" |

**Single Definition** (corresponding to the three decision points in the source code `Core/scope.py`):

- **Module Dimension**: Which modules are available in a given context — `scope.is_allowed`, bound to three levels: platform / Bot / session (priority: session > Bot > platform)
- **Identity Dimension**: Whether an event is accepted (event admission) — `scope.is_identity_allowed`, with four strategies: user / session / Bot / adapter (take the most specific one)
- **Outbound Dimension**: What actions a module can perform outwardly (outbound action restrictions) — `scope.is_action_allowed`, default allows all, only explicitly restricts, supports fine-grained method-level restrictions

**Documentation Style**: Use the fixed three dimension names "module dimension / identity dimension / outbound dimension"; do not use variants like "module filtering / identity validation / action restriction" as official names; the numbered markers ①②③ in the document are only for text flow and do not belong to the name. Whitelist/blacklist is only one form of module dimension configuration, and should not be used to refer to the entire scope system. See [Scope (scope)](../advanced/scope.md) for definition references.

## 5. owner / ownership / owner context

| Item | Content |
|------|------|
| Official Name | System name: **ownership (owner) system**; Mechanism name: **owner context** |
| Chinese-English Equivalents | ownership (ownership), owner context (owner context), `current_owner` (current owner) |
| Historical Aliases | Mixed Chinese-English usage: the term "ownership" and "owner" have alternated in documentation to refer to the same system |

**Single Definition**: Ownership is the cornerstone of a module's "plug-and-play" capability — all framework resources (tasks, connections, timers, translation domains, etc.) registered by a module within an owner context are automatically named, and are collectively reclaimed when the module is unloaded. **Owner context** refers to the current owner (the `current_owner` context variable) recorded by the framework during module code execution; resources created within this context belong to the current module; when the context is unavailable (e.g., in a utility thread callback), the `owner` parameter should be explicitly passed. The unified reclaim interface is `ErisPulse.Core.ownership`.

**Documentation Style**: Use 「ownership」 in Chinese text, and write the full system name 「ownership (owner) system」 on first appearance; retain English for code identifiers and mechanism names (owner context, `current_owner`, `owner_scope`). Do not use translations like "ownership rights" or "owner." See [Ownership (owner) System](../advanced/ownership.md) for definition references.

## 6. Three-word boundary of module.call: service contract / service directory / service whitelist

| Item | Content |
|------|------|
| Mechanism Name | **Service Contract** (`meta.services` declaration end) |
| Interface Name | **Service Directory** (`sdk.module.services()` query end) |
| Descriptive Term | **Service Whitelist** (only used to describe the semantic tightening after declaration, not as a mechanism title) |

**Single Definition**:

- **Service Contract (`meta.services`)**: The module author declares externally callable methods in the `services` field of `get_meta()` — the **declaration end** of the contract. If not declared, any public method can be called (for backward compatibility); after declaration, the callable surface is narrowed, and calling outside the contract throws `ServiceNotProvidedError`.
- **Service Directory (`services()`)**: The runtime query interface `sdk.module.services()`, listing modules and their method signatures and descriptions that have explicitly declared contracts — the **consumption end** view of the contract, providing data for MCPization (exposing call points to AI).
- **Service Whitelist**: Only used as a **descriptive term** to refer to the semantic tightening of "only methods in the whitelist are callable after declaration," not as a mechanism or interface name in titles.

One-sentence boundary: **The author declares a contract, the runtime queries the directory, and "whitelist" only describes the tightening semantic.** See [Module Communication](../advanced/module-communication.md) and [Core Module API](../api-reference/core-modules.md) for definition references.

---

## Related Pages

- [Comment Style Guidelines](docstring.md) - Writing and parsing conventions for special tags within docstrings
- [Documentation and External Writing Rules](docs-writing.md) - Writing and structural guidelines beyond terminology