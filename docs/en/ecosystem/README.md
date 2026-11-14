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

### ErisPulse-Dashboard: Management Dashboard in the Browser

Running a bot on a server? Need to start/stop modules, modify configurations, or check logs? The Dashboard brings all these tasks into your browser: start/stop modules, edit configurations, view logs, and monitor events. Other modules can also register custom views to the sidebar, centralizing all management pages in one place.

```bash
epsdk install Dashboard
```

Documentation: [Dashboard Usage and View Registration](dashboard.md) | Project Homepage: [PyPI](https://pypi.org/project/ErisPulse-Dashboard/)

### ErisPulse-Cron: Scheduled Tasks

Need to send daily check-in reminders, run periodic tasks using Cron expressions, or poll data every few minutes? Cron provides three task types: one-time, interval-based, and Cron expression-based tasks, with callback parameters and SQLite persistence (tasks are not lost after restarts).

```bash
epsdk install Cron
```

Documentation: [Cron Scheduled Tasks](cron.md) | Project Homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-Cron)

### ErisPulse-QvQChat: General-Purpose Agent

Want a bot in your group that can perform tasks, rather than just reply with keywords? QvQChat is a general-purpose agent: it cycles through sending and receiving messages, executing code, operating the computer, generating images, handling voice, integrating with MCP, and managing sub-agents. It supports streaming conversations and sequential tool playback, and comes with a built-in Dashboard view. It also includes three companion plugins: QvQStalker (eavesdropping and interjecting), QvQMemes (emoticons), and QvQCompanion (human-like companionship).

```bash
epsdk install ErisPulse-QvQChat
```

Documentation: [QvQChat Agent](qvqchat.md) | Project Homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-QvQChat)

### ErisPulse-ApiMCP: Let AI Clients Control the Bot

Using AI clients like Claude Desktop or Claude Code that support MCP? ApiMCP exposes the bot's runtime as 17 MCP tools: AI can directly send and receive messages, call installed modules, check platform status, and subscribe to group chat events—turning the bot into the AI's "hands and eyes."

```bash
epsdk install ErisPulse-ApiMCP
```

Documentation: [ApiMCP User Guide](apimcp.md) | Project Homepage: [GitHub](https://github.com/wsu2059q/ErisPulse-ApiMCP)

### ErisPulse-Takumi: Image Rendering

For scenarios requiring "image posting," such as leaderboards, reports, or schedules, simply write a template and render it into an image to post in the group: supports HTML / node tree / Jinja / SVG / animation (based on [takumi-py](https://github.com/BalconyJH/takumi-py)), comes with built-in Chinese and English fonts, ready to use out of the box.

```bash
epsdk install Takumi
```

Documentation: [Takumi Image Rendering](takumi.md) | Project Homepage: [GitHub](https://github.com/ccd2s/ErispulseTakumi) (Author: [@ccd2s](https://github.com/ccd2s))

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