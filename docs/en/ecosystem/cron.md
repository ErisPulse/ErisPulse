# ErisPulse-Cron

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) is the **scheduling module** for ErisPulse, providing a unified API for other modules to handle scheduled tasks: supports one-time, interval-based, and Cron expression-based tasks, callback parameters, and SQLite persistence (tasks are not lost after restart).

> [!IMPORTANT]
> Cron is **not** a built-in feature of the ErisPulse framework and must be installed separately:
>
> ```bash
> epsdk install Cron
> ```

After installation, access all interfaces via `sdk.Cron`.

## Feature Overview

- **Three Scheduling Types**: One-time (`once`), interval loop (`interval`), and Cron expression (`cron`)
- **Callback Data**: Pass `callback_data` when creating a task, and it will be returned unchanged during execution, making it easy to identify the task source
- **Persistence**: Tasks are stored in SQLite (via `sdk.storage`), and are automatically restored after framework restart
- **Missed Trigger Strategy**: Immediate execution, skip, or rescheduling, selectable per task
- **Task Management**: Pause, resume, cancel, manually trigger, and clean up expired tasks
- **Dashboard Integration**: Automatically registers management windows when [ErisPulse-Dashboard](dashboard.md) is installed

## Quick Start

```python
from ErisPulse import sdk

# 1. Register a callback handler
@sdk.Cron.on_trigger
async def handle_trigger(info):
    data = info["callback_data"]
    print(f"Task triggered: {info['task_id']}, Data: {data}")

# 2. Create a scheduled task
task_id = sdk.Cron.once(
    delay=60,
    callback_data={"type": "reminder", "msg": "It's time to drink water"},
)
```

---

## API Overview

### Create Tasks

```python
# One-time: trigger after a delay of 600 seconds
sdk.Cron.once(delay=600, callback_data={"order_id": "123"}, label="Order timeout reminder")

# Interval loop: trigger every 300 seconds, up to 100 times
sdk.Cron.interval(interval_seconds=300, callback_data={"monitor": "server-1"}, max_runs=100)

# Cron expression: trigger daily at 9:30 AM on weekdays
sdk.Cron.cron(expression="30 9 * * 1-5", callback_data={"type": "daily_report"})

# General optional parameters: trigger_at (absolute timestamp), delay (first delay), timezone,
# max_runs (0 = unlimited), label, source (module name of creator), missed_policy (missed trigger policy)
```

Common Cron expressions: `*/5 * * * *` (every 5 minutes), `0 8 * * *` (every day at 8 AM), `30 9 * * 1-5` (every weekday at 9:30 AM), `0 0 1 * *` (every 1st day of the month).

### Callback

```python
@sdk.Cron.on_trigger
async def my_handler(info):
    # info contains task_id / task_type / callback_data / label / source /
    # run_count / max_runs / created_at / last_run / trigger_time
    ...
```

Multiple handlers can be registered and will be called in sequence. An exception in one handler does not affect others.

### Manage Tasks

```python
sdk.Cron.cancel(task_id)                  # Cancel
sdk.Cron.pause(task_id)                   # Pause
sdk.Cron.resume(task_id)                  # Resume (reschedule=True recalculates next trigger time)
await sdk.Cron.trigger_now(task_id)       # Manually trigger immediately (does not affect original schedule)
sdk.Cron.get_task(task_id)                # View a single task
sdk.Cron.list_tasks(source="MyModule")    # List tasks (supports filtering by source/status/task_type)
sdk.Cron.delete_task(task_id)             # Delete task record
sdk.Cron.cleanup()                        # Clean up completed/canceled tasks older than 7 days
```

### Missed Policy (`missed_policy`)

When the framework restarts, for tasks that missed their trigger time:

| Policy | Behavior |
|--------|----------|
| `fire_immediately` | Trigger immediately (default) |
| `skip` | Skip this trigger, wait for the next one |
| `reschedule` | Recalculate the next trigger time from the current time |

## Behavior on Module Unload

Cron's task data is a **persistent asset**: unloading or disabling the module that created the task does not delete the created task. However, the callback handles registered by the module will be cleaned up. Based on the ownership system's [external cleanup hooks](../advanced/ownership.md#Tool_Module_Guide_Handling_Handles_of_Other_Modules), Cron automatically names callbacks it manages on behalf of other modules. When the corresponding module is unloaded or disabled, its callback handles are automatically discarded, ensuring that the module instance can be properly reclaimed.

- After the task creator module is **reloaded**, re-registering `on_trigger` resumes receiving triggers.
- Tasks that are no longer needed can be cleaned up using `sdk.Cron.cancel(task_id)` / `delete_task(task_id)`.

## Related Links

- [GitHub Repository](https://github.com/wsu2059q/ErisPulse-Cron)
- [PyPI Page](https://pypi.org/project/ErisPulse-Cron/)
- [Ownership (owner) System](../advanced/ownership.md)