# Sandbox Platform Feature Documentation

SandboxAdapter is the built-in sandbox adapter of ErisPulse, used for local development and module debugging—simulating message sending and receiving without requiring a real platform.

---

## Documentation Information

- Corresponding Module Version: 4.1.0
- Maintainer: ErisPulse

## Basic Information

- Platform Overview: Local sandbox environment, providing virtual users/groups, a web debugging panel, and message persistence.
- Adapter Name: SandboxAdapter
- Platform Identifier: `sandbox`
- Single account design (for local debugging scenarios)
- Framework Requirement: Soft dependency `ErisPulse>=2.7.1` (runtime detection prompt, not mandatory)

## v5 Paradigm Update (4.1.0)

- **Minimal API DSL**: `get_self_info` / `get_status` / `get_version` / `get_supported_actions`
- **spawn_background Task Ownership**: Heartbeat tasks now use `runtime.spawn_background`
- **Framework Soft Dependencies**: Runtime detection of `ErisPulse>=2.7.1` with prompt
- Import path updated to `Core.Bases` (BaseConfig)

## Standard API Action Examples

```python
from ErisPulse import sdk
sandbox = sdk.adapter.get("sandbox")

result = await sandbox.Api.get_self_info()   # Sandbox bot identity
result = await sandbox.Api.get_status()
result = await sandbox.Api.get_supported_actions()
```

## Usage Instructions

- The sandbox provides virtual users and groups, and modules can send and receive messages just like on a real platform.
- The web debugging panel allows you to manually send messages to trigger the module's processing logic.
- Message data is persistently stored and can be restored after a restart.