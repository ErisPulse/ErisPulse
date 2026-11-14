# Module Testing (ErisPulse-Testing)

> [!TIP]
> **When to read this**: When writing automated tests for your own modules. If not needed, feel free to skip — this won't affect the use of any other features.

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) is the official testing toolkit:
providing `TestBot`, test event factories, outbound message capture, and assertion interfaces, making module testing as easy as writing ordinary pytest tests.

```bash
pip install ErisPulse-Testing
```

> A development-time tool with a one-way dependency on the framework and zero runtime intervention. For smoke tests that actually connect to adapter platforms, use `tests/devs/test_adapter.py` from the framework repository.

## Quick Start

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="Already checked in today")
        async def daily(event):
            await event.reply("Check-in successful!")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "Check-in successful!"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("Already checked in today")   # Second attempt hits the cooldown
```

`TestBot` is recommended to be used with `async with`: on startup it registers the MockAdapter (capturing all outbound messages), disables event deduplication, and applies config overrides; on exit it automatically cleans up the framework's global state, so test cases do not pollute one another.

Accompanying pytest fixtures (automatically available after installation):

- `testbot`: function-scoped standard TestBot (platform=`test`, prefix `/`)
- `make_testbot(**kwargs)`: factory with customizable parameters (`prefix` / `config` / `platform` / `bot_id` ...)

It is recommended to set `asyncio_mode = "auto"` (`[tool.pytest.ini_options]`) in your test project's configuration, or add `@pytest.mark.asyncio` to your test cases.

## Event Factories

| Function | Description |
|------|------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | Message event; an empty `group_id` means a private chat |
| `create_command_event("roll 3", prefix="/")` | Command message (prefix added automatically; not duplicated if already present) |
| `create_notice_event(type, ...)` | Notice event (e.g., `friend_add`) |
| `create_request_event(type, ...)` | Request event (e.g., friend request) |
| `create_meta_event("connect", ...)` | Meta event (connect brings the Bot online) |

All events use a unique uuid `id`, naturally bypassing the framework's event deduplication.

Note: Synthetic events **do not contain the platform's raw payloads** (`event.get_raw()` returns an empty dict). To determine scenarios such as group chat / private chat, use accessors like `event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()`, instead of reading raw data.

## TestBot API

### Dispatch

```python
trace = await bot.dispatch(event)          # Dispatch and wait for handlers to settle; returns the decision chain
await bot.dispatch(event, drain=False)     # First message of an interaction: don't wait (wait_reply handlers stay resident)
await bot.send_message("Hello")            # Shortcut for message dispatch
await bot.reply_as("18", user_id="u1")     # Simulate a user reply to wait_reply (automatically waits for the waiter to be ready)
```

`dispatch()` gathers all in-flight handler Tasks after emit; by the time it returns, processing is complete — **no need for sleep in tests**.

### Outbound Assertions

```python
bot.replies                # All outbound messages (list of SentMessage)
bot.last_reply.text        # Text of the most recent reply
bot.replies_to("123")      # Filter by target
bot.clear_replies()        # Isolate assertions between phases
bot.assert_replied()                       # Outbound messages exist
bot.assert_replied(contains="check-in", to="123")
bot.assert_not_replied()                   # No outbound messages at all
bot.assert_reply_contains("Check-in successful")       # An outbound message containing the specified text exists
await bot.wait_for_reply(timeout=2)        # Wait for an asynchronous reply to appear
```

`SentMessage` fields: `text` (the first text segment), `segments` (full message segments), `target_type` / `target_id` / `bot_id` (sending context), `has_modifier("at")`, and more.

### Module Loading

```python
await bot.load_module("MyModule")   # Registered module name (requires the framework's sdk.init() to complete entry-point discovery)
await bot.load_module(MyModule)     # Or a BaseModule subclass (automatic register + load, recommended)
await bot.unload_module("MyModule")
```

Commands / event handlers registered inside `on_load` belong to the module and are automatically cleaned up on unload, so you can directly assert that "commands stop working after unloading".
Note: The string form **does not perform entry-point scanning** (TestBot does not initialize the framework's discovery process); to test modules that are soft dependencies, pass the class object directly (or call `module.register` yourself and then pass the name).

### Dependency Replacement (requires EP>=2.9.0-dev)

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

What is replaced is the function referenced by the `Depends(get_session)` declaration in the command registry; upon exiting the with block, everything is automatically restored.

### Config Overrides

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # Module config (readable via self.cfg)
})
```

Injected through the config memory layer; command prefixes and the like take effect immediately via hot reload. Two caveats:

1. **Persistence to disk**: Overrides will be written to `config/config.toml` under the cwd according to the framework's deferred disk-write policy (about 5 seconds by default) — please add `config/` to `.gitignore` in the repository of the project under test;
2. **Conflict with module runtime write-backs (known limitation)**: When a module under test writes back entire config sections (`self.cfg = ...`, e.g., subscription lists) alongside the dotted overrides here, there is a read/write consistency issue in ConfigManager — a module reading an entire section may not see the overridden values, and overrides may be overwritten by whole-section write-backs when persisted (fixed in ErisPulse 2.9.0-dev.2; 2.8.x is still affected). For test cases involving "runtime config write-backs" on 2.8.x, it is recommended to reset the relevant config sections in a fixture using whole-section write-backs.

## Dispatch Decision Chain (troubleshooting "why didn't the command trigger"; requires EP>=2.9.0-dev)

`dispatch()` returns a `DispatchTrace` — the causal chain of every decision point traversed during this dispatch:

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # Line-by-line causal explanation (in the current language)
trace.command        # Name of the matched command (None if not matched)
trace.steps("cooldown")  # Filter decision records by phase

trace.assert_executed("daily")  # Assert execution (attaches the full causal chain on failure)
trace.assert_rejected()         # Assert rejection by a permission-related verdict
trace.assert_dropped()          # Assert silent dropping (cooldown, etc.)
trace.assert_no_match()         # Assert no command was matched
```

Verdict coverage: command text validation, command matching (with spelling suggestions when unmatched), scopes, user ACLs, owner checks, permission functions, silent cooldown drops, argument parsing, execution results, and middleware vetoes.

In production environments, you can likewise use the framework's built-in `ErisPulse.Core.Event.trace` (`start_dispatch_trace()` / `format_dispatch_trace()`) to collect and render decision chains.

## Next Steps

### Testing for "Command Not Triggered" Type Issues

### Tests Passed, Ready for Distribution

- [Module Core Concepts](modules/core-concepts.md) — Details on module architecture and configuration declarations
- [Publishing and Module Store Guide](publishing.md) — Complete process for publishing to PyPI and the module store