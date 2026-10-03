# Module Testing (ErisPulse-Testing)

[ErisPulse-Testing](https://github.com/ErisPulse/ErisPulse-Testing) is the official testing toolkit (RFC EPRFC-2026-001 Direction 3):  
It provides `TestBot`, test event factories, outbound message capture and assertion interface, making module testing as simple as writing regular pytest.

```bash
pip install ErisPulse-Testing
```

> A one-way dependency development-time tool, with zero runtime intervention. For smoke tests that truly connect to adapter platforms, please use the framework repository's `tests/devs/test_adapter.py`.

## Quick Start

```python
import pytest
from ErisPulse.Core.Event.command import command
from ErisPulse_Testing import TestBot, create_command_event

async def test_daily(make_testbot):
    async with make_testbot(prefix="/") as bot:
        @command("daily", cooldown="1d", cooldown_reply="Today already checked in")
        async def daily(event):
            await event.reply("Check-in successful!")

        await bot.dispatch(create_command_event("daily", user_id="123"))
        assert bot.last_reply.text == "Check-in successful!"

        await bot.dispatch(create_command_event("daily", user_id="123"))
        bot.assert_reply_contains("Today already checked in")   # Second hit cooldown
```

`TestBot` is recommended to be used with `async with`: it registers MockAdapter (captures all outbound), disables event deduplication, and applies configuration overrides at startup; and automatically cleans up framework global state at exit, ensuring test cases do not pollute each other.

配套 pytest fixtures (automatically available after installation):

- `testbot`: standard TestBot at function level (platform=`test`, prefix `/`)
- `make_testbot(**kwargs)`: factory for custom parameters (`prefix` / `config` / `platform` / `bot_id` ...)

建议在测试项目配置 `asyncio_mode = "auto"` (`[tool.pytest.ini_options]`),  
or add `@pytest.mark.asyncio` to test cases.

## Event Factory

| Function | Description |
|----------|-------------|
| `create_message_event(text, user_id=..., group_id=None, ...)` | Message event; if `group_id` is empty, it is a private chat |
| `create_command_event("roll 3", prefix="/")` | Command message (automatically adds prefix, no duplication if already prefixed) |
| `create_notice_event(type, ...)` | Notice event (e.g., `friend_add`) |
| `create_request_event(type, ...)` | Request event (e.g., friend request) |
| `create_meta_event("connect", ...)` | Meta event (e.g., `connect` makes the Bot go online) |

All events use uuid for unique `id`, naturally avoiding framework event deduplication.

Note: Synthetic events **do not contain platform raw messages** (`event.get_raw()` returns an empty dict). To determine scenarios like group chat / private chat, use accessors such as `event.is_group_message()` / `event.get_detail_type()` / `event.get_group_id()`, do not read raw.

## TestBot API

### Dispatch

```python
trace = await bot.dispatch(event)          # Dispatch and wait for handlers to land, return decision chain
await bot.dispatch(event, drain=False)     # Interactive first message: no wait (wait_reply handlers stay active)
await bot.send_message("Hello")             # Shortcut for message dispatch
await bot.reply_as("18", user_id="u1")     # Simulate wait_reply user reply (automatically waits for waiter ready)
```

`dispatch()` gathers all in-flight handler tasks after emit, returns immediately after processing is complete — **no need for sleep in tests**.

### Outbound Assertions

```python
bot.replies                # All outbound (list of SentMessage)
bot.last_reply.text        # Text of the most recent reply
bot.replies_to("123")      # Filter by target
bot.clear_replies()        # Isolate assertions between stages
bot.assert_replied()                       # Presence of outbound
bot.assert_replied(contains="Check-in", to="123")
bot.assert_not_replied()                   # No outbound at all
bot.assert_reply_contains("Check-in successful")       # Presence of outbound containing specified text
await bot.wait_for_reply(timeout=2)        # Wait for asynchronous reply to appear
```

`SentMessage` fields: `text` (first text segment), `segments` (full message segments),  
`target_type` / `target_id` / `bot_id` (send context), `has_modifier("at")`, etc.

### Module Loading

```python
await bot.load_module("MyModule")   # Registered module name (requires framework sdk.init() to complete entry-point discovery)
await bot.load_module(MyModule)     # Or BaseModule subclass (auto register + load, recommended)
await bot.unload_module("MyModule")
```

Handlers registered in `on_load` are tied to the module, and are automatically cleaned up on unload, allowing direct assertions like "commands become invalid after unload".  
Note: String forms **do not perform entry-point scanning** (TestBot does not initialize framework discovery process); for testing soft-dependency modules, directly pass class objects (or manually `module.register` before passing the name).

### Dependency Replacement (requires EP>=2.9.0-dev)

```python
with bot.patch_dependency(get_session, fake_session) as mock:
    await bot.dispatch(create_command_event("query"))
    assert mock.called
```

Replaces the function referenced in the command registry via `Depends(get_session)`, restoring automatically when exiting the `with` block.

### Configuration Override

```python
bot = TestBot(prefix="//", config={
    "ErisPulse.event.command.case_sensitive": False,
    "MyModule.api_key": "test-key",     # Module configuration (self.cfg can read)
})
```

Configuration is injected into the memory layer, and changes like command prefix take effect immediately via hot update. Two points to note:

1. **Persistence**: Overrides will be written to disk following the framework's delayed write strategy (default ~5 seconds) into `config/config.toml` in the cwd—projects under test should add `config/` to `.gitignore`;
2. **Conflict with runtime module configuration writes (known limitation)**: When module runtime configuration writes (e.g., `self.cfg = ...` for subscription lists) coexist with these dot-separated overrides, there is a consistency issue in ConfigManager's read/write — modules reading entire sections may not see override values, and overrides may be overwritten during disk writes (fixed in ErisPulse 2.9.0-dev.2, still affected in 2.8.x). For test cases involving "runtime configuration writes", in 2.8.x it is recommended to reset relevant configuration sections via full-section write in the fixture.

## Dispatch Decision Chain (for troubleshooting "why command didn't trigger"; requires EP>=2.9.0-dev)

`dispatch()` returns `DispatchTrace` — the causal chain of each decision point in this dispatch:

```python
trace = await bot.dispatch(create_command_event("dailyx", user_id="123"))

trace.verdict        # executed / rejected / dropped / failed / no_match / passed
trace.explain()      # Line-by-line causal explanation (in current language)
trace.command        # Name of the matched command (None if not matched)
trace.steps("cooldown")  # Filter decision records by stage

trace.assert_executed("daily")  # Assert execution (failure includes full causal chain)
trace.assert_rejected()         # Assert rejection by permission-based decision
trace.assert_dropped()          # Assert silent discard (e.g., cooldown)
trace.assert_no_match()         # Assert no command matched
```

Decision coverage: command text matching, command hit (with spelling suggestions if unmatched), scope, user ACL, owner check, permission functions, cooldown silent discard, parameter parsing, execution result, middleware rejection.

The production environment can also use the framework's built-in `ErisPulse.Core.Event.trace` (`start_dispatch_trace()` / `format_dispatch_trace()`) to collect and render the decision chain.