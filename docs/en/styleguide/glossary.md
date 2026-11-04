# Glossary (Single Source of Truth)

> [!TIP]
> **When to read this**: when writing or revising documentation and you are unsure what to call a concept, or when you find two documents describing the same concept inconsistently. Skip it otherwise.

This table consolidates the core concepts whose names were previously inconsistent across multiple places in the ErisPulse documentation. Each term is given exactly one **official name**, one set of **English equivalents**, and a note on **historical aliases**. When any other document conflicts with this table, this table prevails — please fix the conflicting documents as you go.

Inclusion criteria:

- Only concepts whose naming has historically drifted, or that are prone to ambiguity from mixed Chinese/English usage, are included; pure code identifiers (such as `BaseModule`) are not included
- Every definition was first verified by grepping actual usage across the entire `docs/en` corpus and the source code; each definition matches mainstream usage
- Give the full term at its first occurrence in a document (with a parenthetical gloss), then use the short form

---

## 1. Client and HttpClient

| Item | Content |
|------|------|
| Official name | `Client` (base class `BaseClient`) |
| English equivalent | Client (unified HTTP/WS client) |
| Historical aliases | `HttpClient` (class name before 2.8.0, retained as a compatibility alias); `BaseHttpClient` (base class name before 2.8.0, retained as a compatibility alias) |

**Sole definition**: the unified HTTP/WS client. It wraps the underlying request library (currently aiohttp) behind an abstraction layer and provides request statistics, retries, logging, a WebSocket client, and the ErisPulse exception system. As of 2.8.0 the class name was renamed from `HttpClient` to `Client`; **the `sdk.client` attribute name is unchanged**.

**Documentation style**: always write `Client`; mention `HttpClient` only in "legacy code migration / compatibility" contexts, annotated as a "compatibility alias". For the canonical definitions, see [http-client](../advanced/client.md) and [Architecture Overview](../architecture.md).

## 2. storage, env, and StorageManager

| Item | Content |
|------|------|
| Official name | Instance: `storage` (type `BaseStorage`); base class: `BaseStorage` |
| English equivalent | storage (storage); StorageManager (storage manager, legacy class name) |
| Historical aliases | `env` (legacy v1 alias; the same instance); `StorageManager` (original class name of the SQLite implementation before the multi-backend refactor, now a compatibility alias for `SQLiteStorage`) |

**Sole definition**: runtime storage is accessed through the `storage` instance (`sdk.storage` or `from ErisPulse import storage`); the concrete backend is dispatched according to the `ErisPulse.storage.backend` configuration (default: sqlite; switchable to mysql / postgres), and all three backends expose the same API.

**Documentation style**: when describing "the storage system / storage capability" in prose, use "storage"; use `BaseStorage` to refer to the type; use `SQLiteStorage` / `MySQLStorage` / `PostgresStorage` to refer to concrete backends. `StorageManager` is **only a legacy compatibility name of the SQLite implementation class** — it does not represent the storage system as a whole and must not be used in new documents. `env` is a legacy v1 alias (the same instance) kept only for existing legacy code; documents and examples must always use `sdk.storage`. For the canonical definitions, see [Storage Backends](../advanced/storage-backends.md) and [SQL Builder](../advanced/sql-builder.md).

## 3. BaseConfig and AdapterConfig (including the ui / webui metadata keys)

| Item | Content |
|------|------|
| Official name | Config base class: `BaseConfig`; field widget config key: `"ui"` |
| English equivalent | BaseConfig (declarative config base class); AdapterConfig (legacy name, compatibility alias) |
| Historical aliases | `AdapterConfig` (backward-compatibility alias for `BaseConfig`); the `"webui"` field metadata key (legacy name, still compatible) |

**Sole definition**: `BaseConfig` is the general-purpose declarative configuration base class, applicable to adapters, modules, external projects, and any other scenario (the config class is attached to a module / adapter by declaring the nested class `ConfigClass`). Within field `metadata`, the official name of the WebUI widget config key is `"ui"`; read precedence is `"ui"` > `"webui"`, and `"webui"` exists only for compatibility with legacy code.

**Documentation style**: always write `BaseConfig` and `"ui"`. Note the distinction: names such as `MyAdapterConfig` in example code are **a naming habit for developers' own config subclasses** and have nothing to do with the `AdapterConfig` alias. For the canonical definitions, see [Adapter Core Concepts](../developer-guide/adapters/core-concepts.md) and [Module Core Concepts](../developer-guide/modules/core-concepts.md).

## 4. The Three Dimensions of Scope

| Item | Content |
|------|------|
| Official name | Overall: scope; three dimensions: **module dimension / identity dimension / outbound dimension** |
| English equivalent | module dimension; identity dimension; outbound dimension |
| Historical aliases | No legacy name, but inaccurate generic labels such as "permission system / blacklist-whitelist system" have appeared historically |

**Sole definition** (corresponding to the three decision entry points in `Core/scope.py`):

- **Module dimension**: which modules are available in a given context — `scope.is_allowed`; three binding levels: platform / Bot / session (precedence: session > Bot > platform)
- **Identity dimension**: whose events are accepted (event admission) — `scope.is_identity_allowed`; four policy levels: user / session / Bot / adapter (the most specific one takes precedence)
- **Outbound dimension**: what a module can do outward (outbound action restrictions) — `scope.is_action_allowed`; everything is allowed by default and only explicit tightening forbids, with method-level granularity

**Documentation style**: the three dimension names are fixed as "module dimension / identity dimension / outbound dimension"; variants such as "module filtering / identity validation / action restriction" must not be used as official names. The ①②③ numbering used in documents is only a prose marker and not part of the name. Blacklist/whitelist is merely one form of module-dimension configuration and must not be used to refer to the scope system as a whole. For the canonical definitions, see [Scope](../advanced/scope.md).

## 5. owner / Ownership / owner context

| Item | Content |
|------|------|
| Official name | System name: **ownership (owner) system**; mechanism name: **owner context** |
| English equivalent | ownership; owner context; `current_owner` (the current owner) |
| Historical aliases | Mixed Chinese/English usage: "ownership" and "owner" were previously used interchangeably in the docs for the same system |

**Sole definition**: ownership is the cornerstone of module "plug-and-play" — every framework resource a module registers within an owner context (tasks, connections, timers, translation domains, etc.) is automatically attributed by name and reclaimed together when the module is unloaded. The **owner context** is the current owner recorded by the framework while module code executes (the `current_owner` context variable); resources created within this context belong to the current module. When the context is unavailable (e.g., callbacks on tool threads), the `owner` parameter should be passed explicitly. The unified reclamation facade is `ErisPulse.Core.ownership`.

**Documentation style**: use "ownership" in prose; on first occurrence, write the system name in full as "ownership (owner) system". Keep the code identifier and the context mechanism name in English (owner context, `current_owner`, `owner_scope`). Do not use alternative renderings such as "possession" or "proprietor". For the canonical definitions, see [The Ownership (Owner) System](../advanced/ownership.md).

## 6. The Three-Term Boundary of module.call: Service Contract / Service Catalog / Service Whitelist

| Item | Content |
|------|------|
| Mechanism name | **Service Contract** (the declaration side of `meta.services`) |
| Interface name | **Service Catalog** (the query side of `sdk.module.services()`) |
| Descriptive term | **Service Whitelist** (only describes the tightening semantics after declaration; not used as a mechanism title) |

**Sole definition**:

- **Service Contract (`meta.services`)**: module authors declare externally callable methods in the `services` field of `get_meta()` — the **declaration side** of the contract. When nothing is declared, any public method is callable (backward compatibility); once declared, the callable surface is tightened, and calls outside the contract raise `ServiceNotProvidedError`
- **Service Catalog (`services()`)**: the `sdk.module.services()` runtime query interface, listing the modules that have explicitly declared a contract along with their method signatures and descriptions — the **consumer-side** view of the contract, providing the data foundation for MCP-ification (exposing call points to AI)
- **Service Whitelist**: a prose term used only to **describe** the semantics that "after declaration, only whitelisted methods are callable"; it must not appear in titles as the name of a mechanism or interface

The boundary in one sentence: **the author's declaration is the contract, the runtime query is the catalog, and "whitelist" only describes the tightened semantics**. For the canonical definitions, see [Inter-Module Communication](../advanced/module-communication.md) and [Core Modules API](../api-reference/core-modules.md).

---

## Related Pages

- [Docstring Style Conventions](docstring.md) - how the special tags inside docstrings are written and their parsing contract
- [Documentation and Public-Facing Writing Rules](docs-writing.md) - prose and structure conventions beyond terminology