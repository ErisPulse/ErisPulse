---
name: erispulse-ecosystem
description: "适用于：了解生态组件（Dashboard/Cron/AI 模块等）与各平台适配器的接入差异。覆盖场景：The ErisPulse framework itself only provides core capabilities (event system, module system, configuration, routing, logging, etc.), and **does not include** "heavyweight" features such as GUI, image rendering, and visualization. These capabilities are provided by community-maintained **third-party modules**, which can be installed on demand.。Read this when you want to manage your bot through a web-based visual interface (start/stop modules, edit configurations, view logs, monitor event streams), or when you want to register a Dashboard management page for your own module. Skip it if you don't need these.。Read this when your module needs to trigger logic at a scheduled or delayed time (such as reminders, periodic monitoring, or scheduling with Cron expressions), and you want the tasks to persist after a framework restart. Skip this if you don't need it.。Read this when you want to add AI agent capabilities (tool loops, streaming chat, MCP, long-term memory)..."
---

# ErisPulse 生态与多平台

This skill is auto-built from the ErisPulse documentation.
Repository: https://github.com/ErisPulse/ErisPulse
Source paths are annotated per section; see docs/ in the repository for the latest content.

## 内容大纲

AI 按需读取：只读需要的章节即可，不必全文加载。

- 生态总览: 54-73 行
- Recommended Modules: 75-125 行
- Official Client (Standalone Application): 127-137 行
- Want to list your own module here?: 139-147 行
- Dashboard: 149-176 行
- How It Works: 178-189 行
- Registration API: 191-229 行
- Two Injection Modes: 231-264 行
- Sidebar Groups: 266-292 行
- Common CSS Class Names: 294-329 行
- Authentication and API Calls: 331-353 行
- Complete Module Example: 355-465 行
- Unregistering a View: 467-479 行
- Notes: 481-491 行
- 定时任务: 493-513 行
- Feature Overview: 515-522 行
- Quick Start: 524-542 行
- API Overview: 544-597 行
- Behavior on Module Unload: 599-604 行
- AI 对话模块: 606-624 行
- Core Capabilities: 626-645 行
- Module Extensions: 647-717 行
- Event Subscription: 719-731 行
- Invoked as a Service: 733-739 行
- Companion Plugins: 741-747 行
- Interface: 749-757 行
- MCP 桥: 759-777 行
- How It Works: 779-790 行
- Claude Desktop Integration: 792-810 行
- The 14 Tools at a Glance: 812-822 行
- Security Essentials: 824-833 行
- 平台指南索引: 835-852 行
- Platform-Specific Features: 854-880 行
- Common Interfaces: 882-1062 行
- Standard Formats: 1064-1120 行
- Reference Links: 1122-1132 行
- Contributing: 1134-1143 行

## 生态总览

> 来源: `docs/en/ecosystem/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/ecosystem/README.md）

# Ecosystem Modules

The ErisPulse framework itself only provides core capabilities (event system, module system, configuration, routing, logging, etc.), and **does not include** "heavyweight" features such as GUI, image rendering, and visualization. These capabilities are provided by community-maintained **third-party modules**, which can be installed on demand.

> [!IMPORTANT]
> The documentation in this directory is divided into two categories, each with a different installation method:
>
> - **Modules** (such as Dashboard / Takumi) are installed using `epsdk install`:
>
>   ```bash
>   epsdk install <module-name>
>   ```
>
> - **Standalone programs** (such as the ErisPulse-App client) can be downloaded and installed directly from the corresponding GitHub Releases, without the need for `epsdk`.

---

## Recommended Modules

### ErisPulse-Dashboard: A management dashboard in your browser

Running your bot on a server, but still need to log into the terminal to start/stop modules, modify configurations, or view logs? Dashboard brings these functions into the browser: module start/stop, configuration editing, log viewing, and event monitoring. Other modules can also register custom panels to the sidebar, centralizing the management interface in one place.

```bash
epsdk install Dashboard
```

Docs: [Dashboard Usage & Panel Registration](dashboard.md) ｜ Project Homepage: [PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron: Scheduled Tasks

Need daily reminders, periodic tasks based on Cron expressions, or data polling every few minutes? Cron provides three types of tasks: one-time, interval-based, and Cron expression-based, with callback parameters and SQLite persistence (tasks are not lost after restart).

```bash
epsdk install Cron
```

Docs: [Cron Scheduled Tasks](cron.md) ｜ Project Homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat: General-purpose Agent

Want an AI assistant in your group that can perform tasks, rather than just reply with keywords? QvQChat is a general-purpose agent: tools cycle through message sending/receiving, code execution, computer operations, image generation, voice, MCP, and sub-agents. It supports streaming conversations and sequential tool replay, and comes with a built-in Dashboard panel. Also included are three companion plugins: QvQStalker (eavesdropping and interjecting), QvQMemes (meme generation), and QvQCompanion (human-like companionship).

```bash
epsdk install ErisPulse-QvQChat
```

Docs: [QvQChat Agent](qvqchat.md) ｜ Project Homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP: Let AI Clients Control Your Bot

Using AI clients like Claude Desktop or Claude Code that support MCP? ApiMCP exposes 14 MCP tools from the bot runtime, allowing AI to directly send/receive messages, call installed modules, check platform status, and subscribe to group chat events—effectively turning the bot into the AI’s "hands and eyes."

```bash
epsdk install ErisPulse-ApiMCP
```

Docs: [ApiMCP User Guide](apimcp.md) ｜ Project Homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

### ErisPulse-Takumi: Image Rendering

For scenarios requiring image generation—such as leaderboards, match reports, or schedules—simply create a template and render it as an image to send into the group: supports HTML / node trees / Jinja / SVG / animations (based on [takumi-py](https://github.com/BalconyJH/takumi-py)), with built-in Chinese and English fonts, ready to use out of the box.

```bash
epsdk install Takumi
```

Docs: [Takumi Image Rendering](takumi.md) ｜ Project Homepage: [GitHub](https://github.com/ccd2s/ErispulseTakumi) (by [@ccd2s](https://github.com/ccd2s))

## Official Client (Standalone Application)

### ErisPulse-App: Run Bots Directly on Your Phone

No always-on server, but still want to create instances, install modules, and view event streams anytime? ErisPulse-App is the official cross-platform client (Android / Windows / Linux / macOS): a native interface for creating / running / managing multiple bot instances, with a built-in module marketplace and event builder. **Runs directly on your phone**, and stays resident in the desktop tray on desktop.

Installation packages for all platforms can be downloaded from [GitHub Releases](https://github.com/ErisPulse/ErisPulse-App/releases); no need for `epsdk`.

Documentation: [ErisPulse-App Installation and Usage](app.md)

---

## Want to list your own module here?

We welcome recommendations of high-quality, widely reusable ErisPulse ecosystem modules. Requirements:

1. Published on [PyPI](https://pypi.org/), with a package name starting with `ErisPulse-`
2. Provides a basic README and usage examples
3. Actively maintained, with responses to Issues

Module authors who meet the above criteria can add a `<Module-Name>.md` document in this directory via a PR, and add the corresponding section to the recommendation list above.

## Dashboard

> 来源: `docs/en/ecosystem/dashboard.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/ecosystem/dashboard.md）

# ErisPulse-Dashboard

> [!TIP]
> **When to read this**: Read this when you want to manage your bot through a web-based visual interface (start/stop modules, edit configurations, view logs, monitor event streams), or when you want to register a Dashboard management page for your own module. Skip it if you don't need these.

[ErisPulse-Dashboard](https://pypi.org/project/ErisPulse-Dashboard/) is a **Web management panel module** maintained directly by ErisDev, providing ErisPulse with a visual runtime management interface: module start/stop, configuration editing, log viewing, event stream monitoring, and more.

> [!IMPORTANT]
> Dashboard is **not** a built-in feature of the ErisPulse framework and requires separate installation:
>
> ```bash
> epsdk install Dashboard
> ```

Dashboard also supports other ErisPulse modules registering custom management pages to the sidebar. Once registered, users can switch directly to the module's dedicated view page within the Dashboard, without needing to develop a standalone frontend interface.

> [!NOTE]
> View registration is an **optional feature**.
>
> - If the Dashboard module is **not installed** or **not loaded**, calling `sdk.Dashboard.register_view()` will raise an exception
> - Be sure to wrap the registration code in `try/except` to ensure that other functionality of the module itself is not affected
> - It is recommended to check whether Dashboard is available before registering: `hasattr(sdk, 'Dashboard') and sdk.Dashboard`

---

## How It Works

```
Module on_load()
  → Calls sdk.Dashboard.register_view(...)
  → Dashboard backend stores view information
  → WebSocket notifies the frontend
  → Frontend dynamically creates sidebar navigation item + page container
  → User clicks to view the module view
```

---

## Registration API

```python
sdk.Dashboard.register_view(
    id="MyModule",                    # Required, unique identifier
    title="My Module",                # Chinese name
    title_en="My Module",             # English name
    icon_svg='<svg>...</svg>',        # Sidebar icon SVG
    html_content='<div>...</div>',     # Page HTML content
    js_content='function xxx() {}',    # Page JavaScript logic
    css_content='.my-style {}',        # Optional custom CSS
    iframe_url='',                     # iframe mode URL (choose either this or html_content)
    loader="loadMyModuleView",         # JS function name called when switching to this page
    group="group_extensions",          # Sidebar group
    group_title="",                    # Custom group name in Chinese
    group_title_en="",                 # Custom group name in English
)
```

### Parameter Descriptions

| Parameter | Type | Required | Description |
|------|------|------|------|
| `id` | `str` | Yes | Unique identifier of the view; module name recommended |
| `title` | `str` | No | Chinese display name, defaults to `id` |
| `title_en` | `str` | No | English display name, defaults to `title` |
| `icon_svg` | `str` | No | Complete SVG string for the sidebar icon |
| `html_content` | `str` | No* | Page HTML content in injection mode |
| `js_content` | `str` | No | Page JavaScript code |
| `css_content` | `str` | No | Page custom CSS styles |
| `iframe_url` | `str` | No* | URL in iframe mode; `html_content` is ignored when set |
| `loader` | `str` | No | JS function name automatically called when the page is activated |
| `group` | `str` | No | Sidebar group identifier, defaults to `group_extensions` |
| `group_title` | `str` | No | Chinese title of the custom group |
| `group_title_en` | `str` | No | English title of the custom group |

> *At least one of `html_content` and `iframe_url` must be provided; otherwise the page will be blank.

---

## Two Injection Modes

### Mode 1: HTML/JS Injection (Recommended)

Provide HTML, JS, and CSS strings directly, and Dashboard will inject the content into the page. This mode is fully consistent with the Dashboard's styling; it is recommended to use the CSS class names provided by Dashboard.

```python
sdk.Dashboard.register_view(
    id="HelloPage",
    title="Hello Page", title_en="Hello",
    icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>',
    html_content='<h1 class="page-title">Hello World</h1><div class="card"><div class="card-body">This is a sample page</div></div>',
    group="group_tools",
)
```

> For a complete weather module example (including API routes, JS interactions, etc.), see [Complete Module Example](#complete-module-example) below.

### Mode 2: iframe Embedding

The module provides its own HTML page URL (routes must be registered by the module itself), and Dashboard embeds it via an iframe. Suitable for scenarios that require a completely independent UI or complex interactions.

```python
sdk.Dashboard.register_view(
    id="MyVisualizer",
    title="Data Visualization", title_en="Data Visualizer",
    iframe_url="/MyVisualizer/view",
    group="group_tools",
)
```

> In iframe mode, a `token` parameter is automatically appended to the URL for authentication.

---

## Sidebar Groups

Modules can specify the sidebar group in which the view is placed. Dashboard includes the following built-in groups:

| Group Identifier | Chinese Name | Position |
|---------|--------|------|
| `group_overview` | Overview | Group 1 |
| `group_events` | Events | Group 2 |
| `group_extensions` | Extensions | Group 3 (Default) |
| `group_system` | System | Group 4 |
| `group_tools` | Tools | Group 5 |

Specifying a built-in group name will append the module view to the end of that group:

```python
group="group_tools"  # Appended to the "Tools" group
```

You can also use a custom group name (not starting with `group_`), and Dashboard will automatically create a new group:

```python
group="my_group",
group_title="My Group",
group_title_en="My Group",
```

---

## Common CSS Class Names

When the module view uses HTML injection mode, you can directly use Dashboard's existing CSS class names to maintain visual consistency:

| Class Name | Purpose |
|------|------|
| `page-title` | Page title, e.g., `<h1 class="page-title">Title</h1>` |
| `card` | Card container |
| `card-header` | Card header bar |
| `card-body` | Card content area |
| `grid-2` | Two-column grid layout |
| `grid-3` | Three-column grid layout |
| `btn` | Basic button |
| `btn-primary` | Primary button (blue) |
| `btn-secondary` | Secondary button |
| `btn-icon` | Icon button |
| `btn-danger` | Danger action button |

Dashboard uses CSS variables to control theme colors, which you can reference directly in your module view:

| CSS Variable | Purpose |
|----------|------|
| `var(--bg-p)` | Primary background color |
| `var(--bg-s)` | Secondary background color |
| `var(--bg-t)` | Tertiary background color (cards, etc.) |
| `var(--tx-p)` | Primary text color |
| `var(--tx-s)` | Secondary text color |
| `var(--tx-t)` | Auxiliary text color |
| `var(--bd)` | Border color |
| `var(--accent)` | Accent color |
| `var(--ok-c)` | Success color |
| `var(--er-c)` | Error color |

These variables switch automatically according to Dashboard's light/dark theme, so modules do not require additional handling.

---

## Authentication and API Calls

When calling your module's own API from the JS in a module view, you need to carry the Dashboard Token for authentication:

```javascript
var token = localStorage.getItem('__ep_tk__');
var resp = await fetch('/YourModule/api/data', {
    headers: { 'Authorization': 'Bearer ' + token }
});
var data = await resp.json();
```

The module's API endpoint can decide on its own whether to verify the Token. If verification is needed, it can be extracted from the request headers:

```python
async def _api_data(self, request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return {"error": "Unauthorized"}, 401
    return {"data": "hello"}
```

---

## Complete Module Example

Below is a complete weather module example demonstrating how to register a view, provide API data, and clean up resources on unload:

```python
from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseModule
from ErisPulse.Core.Event import command


class Main(BaseModule):
    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("Weather")
        self.config = self._load_config()

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(lazy_load=False, priority=50)

    async def on_load(self, event):
        self._register_routes()
        self._register_dashboard_view()
        self.logger.info("Weather module loaded")

    async def on_unload(self, event):
        self._unregister_routes()
        if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
            self.sdk.Dashboard.unregister_view("Weather")
        self.logger.info("Weather module unloaded")

    def _load_config(self):
        config = self.sdk.config.getConfig("Weather")
        if not config:
            default = {"city": "Beijing", "api_key": ""}
            self.sdk.config.setConfig("Weather", default)
            return default
        return config

    def _register_routes(self):
        r = self.sdk.router
        r.register_http_route("Weather", "/api/current",
                              handler=self._api_current, methods=["GET"])

    def _unregister_routes(self):
        r = self.sdk.router
        try:
            r.unregister_http_route("Weather", "/api/current")
        except Exception:
            pass

    async def _api_current(self, request):
        return {
            "city": self.config.get("city", "Beijing"),
            "temp": 25,
            "humidity": 60,
        }

    def _register_dashboard_view(self):
        try:
            dashboard = self.sdk.Dashboard
            dashboard.register_view(
                id="Weather",
                title="Weather", title_en="Weather",
                icon_svg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
                html_content='''
                    <h1 class="page-title">Weather Query</h1>
                    <p style="color:var(--tx-s);margin-bottom:16px">View current weather information</p>
                    <div class="grid-2">
                        <div class="card">
                            <div class="card-header">Current Weather</div>
                            <div class="card-body">
                                <div id="weather-info" style="font-size:14px;color:var(--tx-s)">Click refresh to load</div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">Actions</div>
                            <div class="card-body">
                                <button class="btn btn-primary" onclick="refreshWeather()">Refresh</button>
                            </div>
                        </div>
                    </div>
                ''',
                js_content='''
                    async function loadWeatherView() { await refreshWeather(); }
                    async function refreshWeather() {
                        var el = document.getElementById('weather-info');
                        if (!el) return;
                        el.textContent = 'Loading...';
                        try {
                            var resp = await fetch('/Weather/api/current', {
                                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('__ep_tk__') }
                            });
                            var data = await resp.json();
                            el.innerHTML = '<p>City: ' + (data.city || '--') + '</p>' +
                                           '<p>Temperature: ' + (data.temp || '--') + '°C</p>' +
                                           '<p>Humidity: ' + (data.humidity || '--') + '%</p>';
                        } catch (e) {
                            el.textContent = 'Load failed: ' + e.message;
                        }
                    }
                ''',
                loader="loadWeatherView",
                group="group_tools",
            )
        except Exception as e:
            self.logger.warning(f"Failed to register Dashboard view: {e}")
```

---

## Unregistering a View

When a module is unloaded, it should call `unregister_view()` to clean up registered views:

```python
async def on_unload(self, event):
    if hasattr(self.sdk, 'Dashboard') and self.sdk.Dashboard:
        self.sdk.Dashboard.unregister_view("Weather")
```

After unregistration, the Dashboard frontend will remove the sidebar navigation item and page content in real time via WebSocket, with no user refresh required.

---

## Notes

1. **Loading Order** — Dashboard's load priority is `99999` (high priority); your module's priority should be lower than this value (e.g., `50`) to ensure Dashboard is fully loaded first
2. **Defensive Programming** — Wrap view registration in `try/except`, since the Dashboard module may not be installed or loaded
3. **Resource Cleanup** — Call `unregister_view()` in `on_unload` to remove registered views
4. **ID Uniqueness** — The `id` parameter must be unique across the entire Dashboard; using the module name directly is recommended
5. **SVG Icons** — `icon_svg` should be a complete `<svg>` tag, with a recommended size of `viewBox="0 0 24 24"`; use `stroke="currentColor"` to inherit the Dashboard theme color
6. **JS Function Naming** — Function names in `js_content` should be unique (e.g., `loadWeatherView`) to avoid conflicts with other modules
7. **Dynamic Updates** — After a module registers/unregisters a view, the Dashboard frontend updates the sidebar in real time via WebSocket, with no page refresh needed

---

## 定时任务

> 来源: `docs/en/ecosystem/cron.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/ecosystem/cron.md）

# ErisPulse-Cron

> [!TIP]
> **When to read this**: Read this when your module needs to trigger logic at a scheduled or delayed time (such as reminders, periodic monitoring, or scheduling with Cron expressions), and you want the tasks to persist after a framework restart. Skip this if you don't need it.

[ErisPulse-Cron](https://github.com/wsu2059q/ErisPulse-Cron) is the **scheduling module** in the ErisPulse ecosystem, providing a unified API for other modules to schedule timed tasks: it supports one-time timers, interval loops, and Cron expressions, with callback parameters and SQLite persistence (tasks are not lost after a restart).

> [!IMPORTANT]
> Cron is **not** a built-in feature of the ErisPulse framework and must be installed separately:
>
> ```bash
> epsdk install Cron
> ```

After installation, access all interfaces through `sdk.Cron`.

---

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

## AI 对话模块

> 来源: `docs/en/ecosystem/qvqchat.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/ecosystem/qvqchat.md）

# ErisPulse-QvQChat General Agent

> [!TIP]
> **When to read this**: Read this when you want to add AI agent capabilities (tool loops, streaming chat, MCP, long-term memory) to your robot, or when you want to expose your module's services for agent calls. Skip if not needed.

[ErisPulse-QvQChat](https://pypi.org/project/ErisPulse-QvQChat/) is a **general-purpose agent module** built around tool loops: sending and receiving messages, calling ecosystem module services, writing and running code, operating the computer, generating images and voice, managing scheduled tasks and long-term memory—all through the same tool protocol.

> [!IMPORTANT]
> QvQChat needs to be installed separately:
>
> ```bash
> epsdk install ErisPulse-QvQChat
> ```
>
> You also need to add at least one OpenAI-compatible model (Base URL, API Key, model name) to the "Model Pool".

## Core Capabilities

| Capability | Description |
|---|---|
| Tool Loop | Model outputs tool calls → concurrent execution → result backfill → continue reasoning until a final answer is given |
| Streaming Chat | SSE outputs characters one by one, tool steps are visible in real time; refreshing or switching away and returning won't lose progress |
| Context Compression | Automatically compresses old conversations into summaries when exceeding the token threshold (default 128000 estimate, customizable) |
| Ecosystem Service Bridge | Automatically discovers services declared by modules and converts them into tools, adding or removing modules adds or removes capabilities |
| MCP Client | stdio and Streamable HTTP, MCP tools are included in the same tool set |
| Sub-Agent | `spawn_agent` spawns a sub-agent in a separate session to explore tasks, only reporting conclusions |
| In-Process Execution | `run_python_sdk` runs Python in the main process, directly accessing runtime objects |
| Computer Operation | Three-level security sandbox (strict / standard / permissive), dangerous operations require confirmation, full audit trail |
| Visual Understanding | Images are automatically injected into the model (automatically stripped and retried if image support is not available) |
| Attachments | Any file is deduplicated by hash and saved to disk, with paths given to the AI for handling; Ctrl+V pastes screenshots |
| Share Session | Temporary read-only link (with expiration + token budget), export as Markdown |
| Scheduled Tasks | Cron / one-time / interval, persistent, permissions follow the creator |
| Session Takeover | Administrators can make an agent exclusively own a session |
| Personality System | System prompt + opening dialogue + tool whitelist, can be bound to sessions |
| Long-term Memory | Each session has memory entries, retrieved and injected based on similarity |
| AI Auto-naming | Generates a short title automatically after the first reply in a session |

## Module Extensions

Any ErisPulse module that declares `services` automatically becomes a tool for QvQChat, without requiring a dedicated interface:

```python
from ErisPulse.Core.Bases import BaseModule, ModuleMeta

class Main(BaseModule):
    @staticmethod
    def get_meta() -> ModuleMeta:
        return ModuleMeta(name="Draw", services=[
            {"name": "draw", "description": "Generate an image based on a description and return the image URL"},
        ])

    async def draw(self, prompt: str, size: str = "1024x1024"):
        return {"image_url": "https://..."}
```

The method signature is automatically mapped to the tool's JSON Schema parameter definition, and the first line of the docstring serves as the parameter description.

### Deep Integration (Optional)

Modules can optionally implement any of the following services. Each service is **independent and optional**—a module can provide only personality extensions, or only inject system prompts.

#### `qvq_prompts()` → Inject system prompts

Returns a `list[str]` or `list[{"text": str, "priority": int}]`, which are concatenated in ascending order of `priority`.

```python
async def qvq_prompts(self):
    return [
        {"text": "After drawing, use send_message to send the image to the user.", "priority": 10},
        {"text": "Supported styles: anime, realistic, watercolor, pixel art.", "priority": 20},
    ]
```

#### `qvq_personas()` → Register personality presets

Returns a list of personalities. The `id` is automatically prefixed with `ext.<module_name>.`, and the module is automatically cleaned up when unloaded. This is suitable for modules dedicated to personality extensions (such as emotional companionship, translation specialists, code reviewers, etc.).

```python
async def qvq_personas(self):
    return [
        {"id": "companion", "name": "Warm Man", "system": "You are a warm and considerate chat partner..."},
        {"id": "coder", "name": "Code Mentor", "system": "...", "tools": ["read_file", "run_python"]},
    ]
```

The `tools` field is optional and can limit the subset of tools available to that personality.

#### `qvq_schemas()` → Explicit parameter schema

Returns a `dict[service_name, JSON Schema]`, which overrides the inferred schema from the method signature. Use this when parameters are complex or strict validation is required.

```python
async def qvq_schemas(self):
    return {
        "draw": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "A description of the image"},
                "size": {"type": "string", "enum": ["512x512", "1024x1024"]},
            },
            "required": ["prompt"],
        },
    }
```

### Refresh Timing

The refresh timing for deep integration services: startup, module loading/unloading, and manual refresh on the Dashboard "Tools" page.

## Event Subscription

QvQChat broadcasts two lifecycle events:

| Event | Timing | Payload |
|---|---|---|
| `qvq.message` | When a user message is received | `chat_key` `platform` `sender_id` `sender_name` `text` `is_group` |
| `qvq.replied` | After a reply is sent | `chat_key` `reply` `tools` |

```python
async def setup(self):
    sdk.lifecycle.on("qvq.message", self.on_message)
```

## Invoked as a Service

| Service | Signature | Description |
|---|---|---|
| `chat` | `(session_id, prompt, persona="")` | Interact with the agent, return text |
| `run_prompt` | `(chat_key, prompt, ...)` | Execute a prompt, the result can be sent to the target session |
| `get_status` | `()` | Status summary of execution |

## Companion Plugins

Three independent modules extend QvQChat and also demonstrate what extension points can do—install QvQChat first and add plugins as needed:

| Plugin | What it does |
|---|---|
|

## Interface

Access independently via `/QvQChat/view`, or embed in the Dashboard sidebar.

![Overview](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/overview.png)

![Conversation](https://raw.githubusercontent.com/wsu2059q/ErisPulse-QvQChat/main/.github/assets/chat.png)

---

## MCP 桥

> 来源: `docs/en/ecosystem/apimcp.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/ecosystem/apimcp.md）

# ErisPulse-ApiMCP: Control Your Bot with AI Clients

> [!TIP]
> **When to read this**: Read this when you want MCP-capable AI clients such as Claude Desktop to directly operate your bot—sending messages, viewing messages, invoking modules, managing adapters, and observing event streams. Skip it otherwise.

[ErisPulse-ApiMCP](https://github.com/wsu2059q/ErisPulse-ApiMCP) exposes the bot's runtime capabilities to AI clients via **MCP (Model Context Protocol)**: once installed, 14 new tools appear in Claude Desktop, allowing the AI to send and receive messages on your behalf, troubleshoot module issues, and subscribe to group chat events—turning the bot from "a program you manage" into "the AI's hands and eyes".

> [!IMPORTANT]
> ApiMCP must be installed separately, and the bridge only becomes active after a **token is explicitly configured**:
>
> ```bash
> epsdk install ErisPulse-ApiMCP
> ```
>
> Set `token = "long-random-string"` in the `[ApiMCP]` section of `config.toml` (or use the environment variable `ERISPULSE_APIMCP_TOKEN`). When not configured, all endpoints return 503 except the health check, preventing silent token leakage.

## How It Works

A two-layer architecture, with no AI dependencies introduced into the bot itself:

- **Inside the bot process**: The ApiMCP module mounts a REST bridge on the framework's built-in HTTP server (`/apimcp/*`, token authentication, default rate limit of 30 requests/minute)
- **Independent process**: The `erispulse-apimcp` command starts a stdio server using the official `mcp` SDK, forwarding MCP tool calls to the bot's HTTP bridge

```
Claude Desktop ──MCP(stdio)──► erispulse-apimcp ──HTTP──► Bot Process REST Bridge ──► sdk.*
```

When the bot is offline or the bridge is not configured, tools return readable errors with troubleshooting guidance instead of throwing stack traces.

## Claude Desktop Integration

Edit `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\`; macOS: `~/Library/Application Support/Claude/`):

```json
{
  "mcpServers": {
    "erispulse": {
      "command": "erispulse-apimcp",
      "env": {
        "ERISPULSE_APIMCP_URL": "http://127.0.0.1:8000",
        "ERISPULSE_APIMCP_TOKEN": "your-token"
      }
    }
  }
}
```

After saving, fully restart Claude Desktop. The integration is successful once the `erispulse` server appears in the tool list. Any client that supports MCP stdio servers (Claude Code, Cursor, etc.) can connect in the same way.

## The 14 Tools at a Glance

| Category | Tools | Description |
|---|---|---|
| Module | `list_modules` / `get_module_info` / `call_module` / `reload_module` | View and invoke public services of installed modules, and trigger hot reload |
| Adapter | `list_adapters` / `get_adapter_status` / `reload_adapter` | Platform online status; adapter reload is disabled by default |
| Message | `send_message` / `recent_messages` | Send text/images/audio/video/files to any platform; review recent messages via [transcript](../advanced/transcript.md) |
| Event | `subscribe_events` / `unsubscribe` / `poll_events` | Subscribe to events such as messages/notifications, with a ring buffer (1000 entries by default) and incremental polling |
| Runtime | `get_topology` / `sdk_health` | Runtime topology (sanitized) and health summary |

A typical usage: the AI first calls `subscribe_events(["message"])`, then periodically runs `poll_events` to observe what's being discussed in the group, and decides whether to chime in via `send_message` or use `call_module` to trigger a module's capability.

## Security Essentials

- **The token grants full control**: it can read messages, send messages, and call whitelisted module methods. Never commit it to the repository or post it in public channels; in multi-tenant scenarios, split into multiple bot instances
- **Least privilege**: use `module_call_whitelist` to narrow the callable modules (supports precise `module.method` format for exact allowlisting), `send_target_whitelist` to narrow send targets (e.g., only allowing a specific group), and keep `allow_adapter_reload` disabled by default
- **Listen on localhost only**: when used only on the local machine, set the framework HTTP server to `server.host = "127.0.0.1"`; cross-machine access must use an intranet + reverse proxy with TLS
- Output is sanitized at the key-name level (key/path-type keys are dropped entirely); deep sanitization is the module's own responsibility—do not enable subscriptions for sensitive sessions

For the complete configuration options (buffer capacity, backtrack window, event type whitelist, etc.) and detailed REST endpoints, see the [project README](https://github.com/wsu2059q/ErisPulse-ApiMCP).

---

## 平台指南索引

> 来源: `docs/en/platform-guide/README.md`（https://github.com/ErisPulse/ErisPulse/blob/main/docs/en/platform-guide/README.md）

# ErisPulse PlatformFeatures Documentation

> Baseline protocol: [OneBot12](https://12.onebot.dev/) 
> 
> This document is a **platform-specific features guide**, including:
> - Chained Send method call examples supported by each adapter
> - Descriptions of platform-specific event/message formats
> 
> For general usage, please refer to:
> - [Basic Concepts](../getting-started/basic-concepts.md)
> - [Event Conversion Standard](../standards/event-conversion.md)  
> - [API Response Specification](../standards/api-response.md)

---

## Platform-Specific Features

This section is maintained by each adapter's developer, and is used to explain the adapter's differences from and extensions to the OneBot12 standard. Please refer to the detailed documentation for each platform below:

- [Maintenance Notes](maintain-notes.md)

- [Yunhu Platform Features](yunhu.md)
- [Yunhu User Platform Features](yunhu_user.md)
- [Telegram Platform Features](telegram.md)
- [OneBot11 Platform Features](onebot11.md)
- [OneBot12 Platform Features](onebot12.md)
- [SnowLuma Platform Features](snowluma.md)
- [Email Platform Features](email.md)
- [Kook Platform Features](kook.md)
- [Matrix Platform Features](matrix.md)
- [WeCom (Enterprise WeChat) Platform Features](wecom.md)
- [Bilibili Platform Features](bilibili.md)
- [Minecraft Platform Features](minecraft.md)
- [QQ Official Bot Platform Features](qqbot.md)
- [Kaede Café](ideaura.md)
- [Discord](discord.md)
- [Webhook Protocol Bridge](webhook.md)
- [WeChat Official Account](wechatmp.md)

> There is also a `sandbox` adapter, but this adapter does not require a platform features document to be maintained

---

## Common Interfaces

### Send Chained Calls
All adapters support the following standard calling methods:

> **Note:** `{AdapterName}` in the documentation should be replaced with the actual adapter name (e.g., `yunhu`, `telegram`, `onebot11`, `email`, etc.).

1. Specify type and ID: `To(type,id).Func()`
   ```python
   # Get adapter instance
   my_adapter = adapter.get("{AdapterName}")
   
   # Send message
   await my_adapter.Send.To("user", "U1001").Text("Hello")
   
   # Example:
   yunhu = adapter.get("yunhu")
   await yunhu.Send.To("user", "U1001").Text("Hello")
   ```
2. Specify ID only: `To(id).Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.To("U1001").Text("Hello")
   
   # Example:
   telegram = adapter.get("telegram")
   await telegram.Send.To("U1001").Text("Hello")
   ```
3. Specify the sending account: `Using(account_id)`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Using("bot1").To("U1001").Text("Hello")
   
   # Example:
   onebot11 = adapter.get("onebot11")
   await onebot11.Send.Using("bot1").To("U1001").Text("Hello")
   ```
4. Direct call: `Func()`
   ```python
   my_adapter = adapter.get("{AdapterName}")
   await my_adapter.Send.Text("Broadcast message")
   
   # Example:
   email = adapter.get("email")
   await email.Send.Text("Broadcast message")
   ```

#### Async Send and Result Handling

The Send DSL methods return `asyncio.Task` objects, which means you can choose whether to await the result immediately:

```python
# Get adapter instance
my_adapter = adapter.get("{AdapterName}")

# Without awaiting, the message is sent in the background
task = my_adapter.Send.To("user", "123").Text("Hello")

# If you need the send result, you can await it later
result = await task
```

#### Send Rule Decorators

In real-world development, you often need to: execute follow-up logic only after a successful send, retry automatically on failure, cancel on timeout, monitor send progress, etc. The Send DSL comes with a built-in set of send rule decorators; attach rules via chained methods:

| Method | Description |
|--------|------|
| `.Hook(callback)` | Callback executed after a successful send (can be called multiple times) |
| `.Retry(times=1)` | Automatically retry N times on failure (N+1 attempts in total including the first) |
| `.Timeout(seconds)` | Timeout for a single send; cancels on timeout (can be combined with Retry) |
| `.Defer(seconds)` | Delayed send (in-process scheduling, not persisted) |
| `.OnProgress(callback)` | Progress callback for each stage, receiving a SendContext |
| `.OnError(callback)` | Error callback on final failure (triggered only once) |

```python
yunhu = adapter.get("yunhu")

# Deduct points only after the send succeeds
await (yunhu.Send.To("user", "123")
       .Hook(lambda r: deduct_points("123"))
       .Text("Consumption successful"))

# Retry on failure + timeout cancellation + progress monitoring
def on_progress(ctx):
    print(f"Stage: {ctx.stage}, Attempt: {ctx.attempt + 1}/{ctx.max_attempts}")

task = (yunhu.Send.To("user", "123")
        .Retry(3)              # Retry up to 3 times
        .Timeout(10)           # 10-second timeout per attempt
        .OnProgress(on_progress)
        .OnError(lambda ctx: notify_admin(ctx.error))
        .Text("Important notice"))
```

Rule methods return `self` and must be called before the send method (Text/Image, etc.). `SendContext` contains fields such as `stage` (pending/sending/retrying/success/failed/timeout), `attempt`, `elapsed`, `error`, and `result`, making monitoring easy.

#### Batch Build Mode (Build)

Build multiple send methods in a single chain and execute them all together at the end. Suitable for scenarios where you want to "send multiple messages in one go":

```python
yunhu = adapter.get("yunhu")

# Build multiple messages and send them together
results = await (yunhu.Send.To("user", "123")
                .Build()                     # Enter build mode
                .Text("Notice one")
                .Image("pic.jpg")
                .Text("Notice two")
                .send_all())                 # Execute all together
# results = [Text result, Image result, Text result]
```

`.send_all()` executes **in parallel** by default (concurrent sending, more efficient). When message arrival order must be guaranteed, call `.Sequential()` to execute serially:

```python
# Serial execution (order guaranteed) + retry on failure
await (yunhu.Send.To("group", "456")
       .Build()
       .Sequential()                # Send one by one in order
       .Retry(2)                    # Each failed entry retries independently
       .Text("First message").Text("Second message")
       .send_all())
```

Batch execution adopts a **fail-and-continue** strategy: one failure does not interrupt the other entries, and failed entries are retried automatically. Batch mode also supports batch-level `Hook` (triggered after all succeed), `OnError` (triggered when any entry fails), and `OnProgress` (progress callback).

> For more detailed rules and batch build descriptions, please refer to [SendDSL in Detail](../developer-guide/adapters/send-dsl.md).

### Event Listening
There are three ways to listen for events:

1. Platform-native event listening:
   ```python
   from ErisPulse.Core import adapter, logger
   
   @adapter.on("event_type", raw=True, platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} native event: {data}")
   ```

2. OneBot12 standard event listening:
   ```python
   from ErisPulse.Core import adapter, logger

   # Listen for OneBot12 standard events
   @adapter.on("event_type")
   async def handler(data):
       logger.info(f"Received standard event: {data}")

   # Listen for standard events from a specific platform
   @adapter.on("event_type", platform="{AdapterName}")
   async def handler(data):
       logger.info(f"Received {AdapterName} standard event: {data}")
   ```

3. Event module listening:
    The events of `Event` are based on the `adapter.on()` function, so the event format provided by `Event` is a OneBot12 standard event

    ```python
    from ErisPulse.Core.Event import message, notice, request, command

    message.on_message()(message_handler)
    notice.on_notice()(notice_handler)
    request.on_request()(request_handler)
    command("hello", help="Send a greeting message", usage="hello")(command_handler)

    async def message_handler(event):
        logger.info(f"Received message: {event}")
    async def notice_handler(event):
        logger.info(f"Received notice: {event}")
    async def request_handler(event):
        logger.info(f"Received request: {event}")
    async def command_handler(event):
        logger.info(f"Received command: {event}")
    ```

Among these, using the `Event` module for event handling is the most recommended option, because the `Event` module provides rich event types as well as rich event handling methods.

---

## Standard Formats
For convenience of reference, simple event formats are given here. If you need detailed information, please refer to the links above.

> **Note:** The formats below are the basic OneBot12 standard formats; each adapter may have extension fields on top of them. For specifics, please refer to each adapter's platform-specific feature descriptions.

### Standard Event Format
The event conversion format that all adapters must implement:
```json
{
  "id": "event_123",
  "time": 1752241220,
  "type": "message",
  "detail_type": "group",
  "platform": "example_platform",
  "self": {"platform": "example_platform", "user_id": "bot_123"},
  "message_id": "msg_abc",
  "message": [
    {"type": "text", "data": {"text": "Hello"}}
  ],
  "alt_message": "Hello",
  "user_id": "user_456",
  "user_nickname": "ExampleUser",
  "group_id": "group_789"
}
```

### Standard Response Format
#### Message Send Success
```json
{
  "status": "ok",
  "retcode": 0,
  "data": {
    "message_id": "1234",
    "time": 1632847927.599013
  },
  "message_id": "1234",
  "message": "",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

#### Message Send Failure
```json
{
  "status": "failed",
  "retcode": 10003,
  "data": null,
  "message_id": "",
  "message": "Missing required parameter",
  "echo": "1234",
  "{platform}_raw": {...}
}
```

---

## Reference Links
ErisPulse projects:
- [Main Repository](https://github.com/ErisPulse/ErisPulse/)
- [Yunhu Adapter Repository](https://github.com/ErisPulse/ErisPulse-YunhuAdapter)
- [Telegram Adapter Repository](https://github.com/ErisPulse/ErisPulse-TelegramAdapter)
- [OneBot Adapter Repository](https://github.com/ErisPulse/ErisPulse-OneBotAdapter)

Related official documentation:
- [OneBot V11 Protocol Documentation](https://github.com/botuniverse/onebot-11)
- [Telegram Bot API Official Documentation](https://core.telegram.org/bots/api)
- [Yunhu Official Documentation](https://www.yhchat.com/document/1-3)

## Contributing

We welcome more developers to participate in writing and maintaining adapter documentation! Please follow these steps to submit your contributions:
1. Fork the [ErisPuls](https://github.com/ErisPulse/ErisPulse) repository.
2. Create a Markdown file under the `docs/platform-features/` directory, named in the format `<platform-name>.md`.
3. Add a link to your contributed adapter and its related official documentation in this `README.md` file.
4. Submit a Pull Request.

Thank you for your support!
