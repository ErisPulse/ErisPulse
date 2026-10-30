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