# The runtime Toolbelt

> [!TIP]
> **When to read this**: When you want a one-stop overview of the
> runtime tools that the `ErisPulse.runtime` package provides for
> direct import. Detailed usage of each capability lives in its
> corresponding topic documentation; this page serves as a
> quick-reference index plus usage notes for a few capabilities
> without a dedicated topic.

`ErisPulse.runtime` is the framework's aggregated export layer: it gathers
runtime tools scattered across modules into a single entry point, so scripts,
modules, and adapter code uniformly use `from ErisPulse.runtime import X`,
without needing to remember deep import paths.

## Capability Quick Reference

| Category | Name | Purpose | Details |
|------|------|------|------|
| Ownership | `bind_owner` | Sew owner context into callbacks / thread entry points | [Ownership System](ownership.md) |
| Ownership | `owner_scope` / `get_current_owner` | Code-block-level ownership context | [Ownership System](ownership.md) |
| Ownership | `get_owner_tasks` / `cancel_owner_tasks` | Query / cancel background tasks of an owner | [Ownership System](ownership.md) |
| Background Tasks | `spawn_background` / `spawn_later` / `spawn_thread` | Background coroutines / delayed tasks / thread tasks | [Lifecycle Management](lifecycle.md) |
| Background Tasks | `cancel_all_background_tasks` / `run_main_loop` | Finalizing background tasks and main loop registration | [Lifecycle Management](lifecycle.md) |
| Event Context | `get_current_trace_id` | Read the current trace ID | [Trace ID](interaction.md#trace-id) |
| Event Context | `get_send_receipts` | Read the send receipt ledger of message transactions | [Message Tx](interaction.md#message-tx) |
| Event Context | `get_current_event_account` / `get_current_caller` / `get_handler_waits` | Event account / caller / wait table reading | [Interaction Session System](interaction.md) |
| Memory | `snapshot` / `log_snapshot` | RSS + tracemalloc snapshots with labels (increments computed automatically) | [Memory Diagnostics](performance.md#memory-diagnostics) |
| Memory | `get_rss_mb` / `get_traced_mb` | Current process memory readings | [Memory Diagnostics](performance.md#memory-diagnostics) |
| Config Parsing | `dict_to_dataclass` | dict → type-safe dataclass instance | See the next section |
| Config Parsing | `dataclass_to_defaults_dict` / `dataclass_to_toml_with_comments` | dataclass → defaults dict / TOML serialization with comments | [Declarative Configuration](../developer-guide/configuration.md) |
| Troubleshooting | `explain_module` / `explain_event` / `explain_trace` | Module / event / message chain diagnostics | [Startup Troubleshooting](startup.md) and [Event Handling](../getting-started/event-handling.md) |
| Troubleshooting | `format_diagnostic_block` / `log_diagnostic` / `extract_user_frame` | Exception diagnostic block rendering and user frame extraction | [Startup Flow](startup.md) |
| Exception Fallback | `setup_exception_handling` / `global_exception_handler` | Mounting the global exception handler | [Startup Flow](startup.md) |
| Security | `redact_secret` | Redact sensitive values in logs / reports | [Startup Flow](startup.md) |
| Metrics | `metrics` / `MetricsRegistry` | Runtime metrics registry (data source for the `/metrics` endpoint) | [Deployment Guide](../user-guide/deployment.md) |

## dict_to_dataclass: dict → Type-Safe Objects

The "reverse direction" of declarative dataclass configuration — parse any dict (API responses, webhook
payloads, user input) into type-safe instances according to declarations, replacing hand-written
`data.get("x", default)` chains:

```python
from dataclasses import dataclass, field
from ErisPulse.runtime import dict_to_dataclass

@dataclass
class WebhookPayload:
    order_id: str
    amount: float = 0.0
    tags: list = field(default_factory=list)
    remark: str = ""

payload = dict_to_dataclass(WebhookPayload, {
    "order_id": "A-1024",
    "amount": "99.5",           # str → float auto-converted
    "unknown_key": "ignored",   # undeclared fields are automatically ignored
})
payload.amount                  # 99.5 (float)
```

- Type conversion (str → int/float, etc.), default value filling, and recursive filling of nested dataclasses
- Environment variable override: when a field declares `metadata={"env": "NAME"}`, the priority order is environment variable > data > default value
- The hot-reload callback of declarative configuration classes (`ConfigClass` / `BaseConfig`) internally uses it to perform the dict → config object conversion

## Related Documentation

- [Declarative Configuration](../developer-guide/configuration.md) - Declarative configuration with ConfigClass / BaseConfig
- [Ownership (owner) System](ownership.md) - Resource ownership and automatic reclamation
- [Lifecycle Management](lifecycle.md) - Background tasks and the main loop